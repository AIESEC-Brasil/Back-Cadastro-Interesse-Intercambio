"""Cliente HTTP assíncrono baseado no HTTPX.

Oferece suporte a base_url, prefixo, pool de conexões com reuso automático
e controle dinâmico de timeout e re-associação de Event Loop (Flask/Asyncio).

Observação: todos os métodos HTTP retornam uma tupla (status_code, body),
sendo body o JSON decodificado quando disponível ou texto/None conforme a resposta.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import asyncio  # Gerenciamento e re-associação com o Event Loop ativo
import logging  # Registro de logs e rastreio de erros de rede
from typing import Any, Dict, Optional, Tuple  # Anotação formal de tipos
from urllib.parse import urlencode  # Codificação segura de parâmetros de URL

import httpx  # Cliente HTTP assíncrono de alta performance

# Configuração de logger específico para o módulo de rede
logger = logging.getLogger(__name__)


# =================================================================
# 2. FUNÇÕES AUXILIARES DE LIMPEZA DE CONEXÃO
# =================================================================

def _force_sync_close_client(client: httpx.AsyncClient) -> None:
    """Fecha o cliente antigo de forma síncrona.

    Utilizado quando o event loop original já foi encerrado, prevenindo o erro
    'Event loop is closed' no ambiente assíncrono.
    """
    try:
        # Se o loop morreu, fechar o transport diretamente limpa os sockets do SO
        if hasattr(client, "_transport") and client.transport is not None:
            client.transport.close()
    except Exception as e:
        logger.debug(f"Erro ao limpar transportador do cliente antigo: {e}")


async def _safe_close_client(client: httpx.AsyncClient) -> None:
    """Encerra as conexões TCP de forma assíncrona.

    Helper que garante o fechamento graceful prevenindo sockets órfãos.
    """
    try:
        await client.aclose()
    except Exception as e:
        logger.warning(
            f"Falha ao fechar AsyncClient antigo de forma assíncrona: {e}"
        )


# =================================================================
# 3. CLASSE PRINCIPAL HTTP CLIENT
# =================================================================

class HttpClient:
    """Cliente HTTP assíncrono modular e resiliente a trocas de Event Loop.

    Mantém um pool de conexões persistentes que se adapta dinamicamente caso
    a thread/requisição do Flask instancie ou troque o Event Loop ativo.
    """

    def __init__(
            self,
            base_url: str = "",  # URL raiz (ex: https://api.podio.com)
            prefix: str = "",  # Prefixo do endpoint (ex: /item)
            timeout: Optional[float] = None,  # Timeout base padrão em segundos
    ):
        """Inicializa as configurações de URL, timeout e pool de conexões."""
        # 🔒 Infraestrutura Base
        self._base_url = base_url.rstrip("/")  # Remove barra final extra
        self._prefix = prefix

        # 🌐 Controle de Timeout
        self._timeout_base = timeout
        self._timeout_override: Optional[float] = None

        # ⚡ Pool de Conexões e Gerenciamento do Event Loop
        self._active_client: Optional[httpx.AsyncClient] = None
        self._loop_associado: Optional[asyncio.AbstractEventLoop] = None

        # 🛡️ Limites do Pool para Prevenção de Sockets Órfãos (TIME_WAIT)
        self._limits = httpx.Limits(
            max_connections=100,  # Máximo de conexões concorrentes
            max_keepalive_connections=20,  # Conexões mantidas quentes no pool
            keepalive_expiry=5.0,  # Tempo limite de ociosidade do socket (s)
        )

    # =================================================================
    # PROPRIEDADES E GERENCIAMENTO DINÂMICO
    # =================================================================

    @property
    def _client(self) -> Optional[httpx.AsyncClient]:
        """Garante e devolve uma instância válida de AsyncClient.

        Detecta se o Event Loop mudou ou foi encerrado e reconstrói o cliente
        se necessário, evitando exceções do tipo RuntimeError.
        """
        try:
            loop_atual = asyncio.get_running_loop()
        except RuntimeError:
            loop_atual = asyncio.new_event_loop()
            asyncio.set_event_loop(loop_atual)

        # Recria o cliente se for a primeira execução ou se o loop foi alterado
        if self._active_client is None or self._loop_associado != loop_atual:
            if self._active_client is not None:
                _force_sync_close_client(self._active_client)

            self._active_client = httpx.AsyncClient(limits=self._limits)
            self._loop_associado = loop_atual

        assert self._active_client is not None
        return self._active_client

    # =================================================================
    # GERENCIAMENTO DE CICLO DE VIDA E CONTEXT MANAGER
    # =================================================================

    async def close(self) -> None:
        """Fecha o pool ativo de conexões de forma assíncrona."""
        if self._active_client is not None:
            await self._active_client.aclose()
            self._active_client = None
            self._loop_associado = None

    async def __aenter__(self) -> "HttpClient":
        """Suporte para uso como Context Manager Assíncrono (`async with`)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Garante o encerramento do cliente ao sair do bloco `async with`."""
        await self.close()

    # =================================================================
    # CONTROLE DE TIMEOUT
    # =================================================================

    @property
    def timeout(self) -> Optional[float]:
        """Obtém o timeout ativo priorizando o override de requisição única."""
        return (
            self._timeout_override
            if self._timeout_override is not None
            else self._timeout_base
        )

    @timeout.setter
    def timeout(self, value: Optional[float]):
        """Define um timeout temporário para a próxima requisição."""
        self._timeout_override = value

    def _consume_timeout(self) -> httpx.Timeout:
        """Retorna a configuração de timeout do HTTPX e limpa o override temporário."""
        t = self.timeout
        self._timeout_override = None  # Reseta o override (Auto-reset)

        if t is not None:
            connect_timeout = min(10.0, t)
            return httpx.Timeout(timeout=t, connect=connect_timeout, read=t)

        # Configuração padrão de resiliência e tempos de resposta
        return httpx.Timeout(
            connect=10.0,  # Tempo limite para conexão TCP/TLS
            read=30.0,  # Tempo limite de leitura da resposta
            write=15.0,  # Tempo limite de escrita/envio de payload
            pool=5.0,  # Tempo limite para obtenção de conexão livre do pool
        )

    # =================================================================
    # CONSTRUTOR DE URLS E HELPER DE RESPOSTAS
    # =================================================================

    def _build_url(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Monta e limpa a URL do endpoint prevenindo barras duplicadas."""
        if self._base_url:
            parts = [self._base_url.rstrip("/")]

            if self._prefix:
                clean_prefix = self._prefix.strip("/")
                if clean_prefix:
                    parts.append(clean_prefix)

            if path:
                clean_path = path.strip("/")
                if clean_path:
                    parts.append(clean_path)

            url = "/".join(parts)

            if params:
                url += f"?{urlencode(params, doseq=True)}"

            return url
        return path

    def _handle_response(self, response: httpx.Response) -> Tuple[int, Any]:
        """Normaliza e extrai o payload da resposta de forma segura."""
        if response.status_code == 204 or not response.content:
            return response.status_code, None

        try:
            return response.status_code, response.json()
        except Exception:
            return response.status_code, response.text

    # =================================================================
    # MÉTODOS DE REQUISIÇÃO HTTP
    # =================================================================

    async def get(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição HTTP GET."""
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None
        response = await client.get(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        return self._handle_response(response)

    async def post(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            as_form: bool = False,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição HTTP POST (Suporta JSON ou Form/UrlEncoded)."""
        if headers is None:
            headers = {
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                    if as_form
                    else "application/json"
                ),
                "Accept": "application/json",
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None
        if as_form:
            response = await client.post(
                url,
                data=payload,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
            )
        else:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
            )
        return self._handle_response(response)

    async def put(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição HTTP PUT."""
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None
        response = await client.put(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        return self._handle_response(response)

    async def patch(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição HTTP PATCH."""
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None
        response = await client.patch(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        return self._handle_response(response)

    async def delete(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição HTTP DELETE."""
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None
        response = await client.delete(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        return self._handle_response(response)

    def clone(self, **kwargs) -> "HttpClient":
        """Cria uma nova instância do cliente mantendo as configurações bases."""
        new_prefix = kwargs.get("prefix", self._prefix)

        client = HttpClient(
            base_url=kwargs.get("base_url", self._base_url),
            prefix=new_prefix,
            timeout=kwargs.get("timeout", self._timeout_base),
        )
        client._timeout_override = kwargs.get(
            "timeout_override", self._timeout_override
        )
        return client


# =================================================================
# 4. EXPORTAÇÃO PÚBLICA (INTERFACE DO MÓDULO)
# =================================================================

__all__ = [
    "HttpClient",  # Classe base do cliente HTTP assíncrono
]