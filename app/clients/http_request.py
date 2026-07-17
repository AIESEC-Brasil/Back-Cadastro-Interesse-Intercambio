"""
Cliente HTTP assíncrono baseado em httpx, com suporte a base_url, prefixo e
controle de timeout temporário por request.

Observação: todos os métodos HTTP retornam (status_code, body), sendo body o
JSON decodificado quando disponível, ou None/texto conforme o caso.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import asyncio                              # Necessário para interagir com o Event Loop ativo do Python/Flask
import logging
from typing import Dict, Any, Tuple, Optional  # Tipagem para melhor suporte a IDEs (Autocompletar e validação)
import httpx                                  # Cliente HTTP assíncrono de alta performance
from urllib.parse import urlencode            # Para codificação segura de query parameters na URL

from httpx import AsyncClient

# Configuração de log para ajudar no rastreio de conexões em produção/testes
logger = logging.getLogger(__name__)


async def _safe_close_client(client: httpx.AsyncClient) -> None:
    """
    Helper assíncrono para garantir que as conexões TCP pendentes do cliente
    antigo sejam fechadas corretamente, evitando sockets órfãos.
    """
    try:
        await client.aclose()
    except Exception as e:
        logger.warning(f"Falha ao fechar AsyncClient antigo de forma assíncrona: {e}")


class HttpClient:
    """
    Cliente HTTP assíncrono modular e de alta performance.

    Utiliza um pool de conexões persistentes (httpx.AsyncClient) que é gerenciado
    de forma dinâmica. Se o Flask fechar o loop de eventos atual e abrir um novo
    na próxima requisição, a classe detecta isso e reconstrói o cliente sem quebrar.

    - timeout_base: timeout padrão da instância (estratégia de longo prazo).
    - timeout: override temporário (estratégia de curto prazo para chamadas específicas).
    """

    def __init__(
            self,
            base_url: str = "",            # URL raiz (ex: https://api.podio.com)
            prefix: str = "",              # Prefixo de rota (ex: /item)
            timeout: Optional[float] = None  # Tempo limite padrão em segundos
    ):
        # 🔒 Infraestrutura Base
        self._lock = None
        self._base_url = base_url.rstrip("/")  # Garante que não termine com barra para evitar double slashes (//)
        self._prefix = prefix

        # 🌐 Controle de Timeout
        self._timeout_base = timeout
        self._timeout_override: Optional[float] = None

        # ⚡ Pool de Conexões Adaptativo
        self._active_client: Optional[httpx.AsyncClient] = None
        self._loop_associado: Optional[asyncio.AbstractEventLoop] = None

        # 🛡️ Configuração de Limites do Pool (Essencial para Testes de Estresse)
        # Sem isso, o HTTPX abre conexões ilimitadas, deixando milhares de sockets órfãos
        # no estado TIME_WAIT do sistema operacional.
        self._limits = httpx.Limits(
            max_connections=100,          # Máximo de sockets abertos simultaneamente (segurança para o SO)
            max_keepalive_connections=20, # Quantidade de conexões mantidas quentes no pool para reuso imediato
            keepalive_expiry=5.0          # Descarta conexões ociosas após 5s (libera recursos rapidamente no estresse)
        )

    # ==========================================
    # GERENCIAMENTO DINÂMICO DE EVENT LOOP (A Mágica)
    # ==========================================

    @property
    def _client(self) -> httpx.AsyncClient:
        """
        Retorna o AsyncClient ativo. Se o loop de eventos mudou ou o cliente
        ainda não foi criado, reconstrói o cliente de forma transparente.
        """
        try:
            loop_atual = asyncio.get_running_loop()
        except RuntimeError as e:
            # Se não há loop rodando, disparar requisições assíncronas é impossível.
            raise RuntimeError(
                "Nenhum Event Loop ativo foi encontrado nesta thread. "
                "Certifique-se de que está chamando os métodos dentro de um contexto assíncrono."
            ) from e

        # Verifica se precisamos criar ou reconstruir o cliente
        if self._active_client is None or self._loop_associado != loop_atual:
            with self._lock:
                # Reavaliação de segurança (Double-checked locking)
                if self._active_client is None or self._loop_associado != loop_atual:
                    if self._active_client is not None:
                        # O loop mudou! Precisamos descartar o cliente antigo para evitar erros.
                        old_client = self._active_client
                        if loop_atual.is_running():
                            # Despara o fechamento do cliente antigo em background, sem bloquear o fluxo atual
                            loop_atual.create_task(_safe_close_client(old_client))
                        else:
                            # Fallback síncrono emergencial se o loop estiver parando
                            try:
                                old_client.close()
                            except Exception as err:
                                logger.debug(f"Erro ao fechar cliente de forma síncrona: {err}")

                    # Cria o novo AsyncClient associado ao loop atual
                    self._active_client = httpx.AsyncClient(limits=self._limits)
                    self._loop_associado = loop_atual

        # 💡 O truque está aqui: garantimos ao linter que o retorno não é None
        assert self._active_client is not None
        return self._active_client

    # ================================
    # GERENCIAMENTO DE CICLO DE VIDA
    # ================================

    async def close(self) -> None:
        """
        Fecha o pool de conexões de forma assíncrona e explícita.
        Chame isso ao desligar a aplicação Flask para liberar recursos de rede imediatamente.
        """
        if self._active_client is not None:
            await self._active_client.aclose()
            self._active_client = None
            self._loop_associado = None

    async def __aenter__(self) -> "HttpClient":
        """Permite o uso do cliente com gerenciadores de contexto (async with HttpClient() as client)"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Garante o fechamento automático do pool ao sair do bloco 'async with'"""
        await self.close()

    # ================================
    # CONTROLE DE TIMEOUT
    # ================================

    @property
    def timeout(self) -> Optional[float]:
        """
        Retorna o timeout aplicável, dando prioridade ao override temporário de requisição única.
        """
        return (
            self._timeout_override
            if self._timeout_override is not None
            else self._timeout_base
        )

    @timeout.setter
    def timeout(self, value: Optional[float]):
        """
        Define o timeout apenas para a requisição que será executada IMEDIATAMENTE a seguir.
        """
        self._timeout_override = value

    def _consume_timeout(self) -> httpx.Timeout:
        """
        Recupera o timeout, limpa o override temporário (evitando vazamento para outras chamadas)
        e retorna um objeto httpx.Timeout balanceado de forma inteligente.
        """
        t = self.timeout
        self._timeout_override = None  # Reseta o override (Auto-reset garantido)

        if t is not None:
            # Em testes de estresse, não podemos dar muito tempo para a etapa de CONEXÃO (connect),
            # pois se o servidor cair, acumulamos conexões abertas esperando o handshake.
            # Limitamos a conexão em no máximo 5 segundos, mas permitimos o tempo total (t) para a leitura (read).
            connect_timeout = min(5.0, t)
            return httpx.Timeout(timeout=t, connect=connect_timeout, read=t)

        # Padrão de segurança adaptado para evitar lentidão extrema sob alta carga
        return httpx.Timeout(
            connect=5.0,   # Limite para estabelecer a conexão de rede TCP/TLS
            read=20.0,     # Limite de espera pelo processamento interno da API externa (ex: Podio)
            write=10.0,    # Limite para envio do corpo da requisição (payloads grandes)
            pool=5.0       # Limite de espera para obter uma conexão livre do pool interno
        )

    # ================================
    # CONSTRUTOR DE URL (URL BUILDER)
    # ================================

    def _build_url(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Monta e higieniza a URL final do endpoint.
        Previne a duplicação indesejada de barras (ex: http://api.com//v1//endpoint).
        """
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

            # Transforma parâmetros de dicionário em query string segura (ex: {'id': 1} vira ?id=1)
            if params:
                url += f"?{urlencode(params, doseq=True)}"

            return url
        return path

    # ===================================
    # MÉTODOS DE PARSE INTERNOS (HELPER)
    # ===================================

    def _handle_response(self, response: httpx.Response) -> Tuple[int, Any]:
        """
        Centraliza e trata a conversão da resposta do servidor de forma segura.
        Evita quebras (erros do interpretador) caso a API retorne corpo vazio,
        texto plano (HTML de erro 502/504) ou status 204 (No Content).
        """
        # Se for um status 204 ou não houver bytes no corpo, retorna None sem tentar fazer parse de JSON
        if response.status_code == 204 or not response.content:
            return response.status_code, None

        try:
            # Tenta decodificar o JSON retornado pela API
            return response.status_code, response.json()
        except Exception:
            # Fallback seguro: se não for um JSON estruturado válido, retorna como texto puro
            return response.status_code, response.text

    # ================================
    # MÉTODOS HTTP (Métodos de Entrada)
    # ================================

    async def get(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição GET e retorna (status_code, body).
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        # Dispara a requisição usando o cliente ativo atrelado ao loop atual
        response = await self._client.get(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True  # Redireciona de forma transparente se necessário (301/302)
        )
        return self._handle_response(response)

    async def post(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            as_form: bool = False,  # Define se envia como formulário clássico ou JSON puro
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição POST e retorna (status_code, body).
        """
        if headers is None:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded" if as_form else "application/json",
                "Accept": "application/json"
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        if as_form:
            # Envia codificado como par chave/valor padrão web
            response = await self._client.post(
                url, data=payload, headers=headers, timeout=timeout, follow_redirects=True
            )
        else:
            # Envia serializado automaticamente como JSON string no payload
            response = await self._client.post(
                url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
            )
        return self._handle_response(response)

    async def put(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição PUT (Substituição de recurso) e retorna (status_code, body).
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.put(
            url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
        )
        return self._handle_response(response)

    async def patch(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição PATCH (Modificação parcial de recurso) e retorna (status_code, body).
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.patch(
            url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
        )
        return self._handle_response(response)

    async def delete(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição DELETE e retorna (status_code, body).
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.delete(
            url, headers=headers, timeout=timeout, follow_redirects=True
        )
        return self._handle_response(response)

    def clone(self, **kwargs) -> "HttpClient":
        """
        Cria uma cópia idêntica das configurações do cliente atual.
        Útil para herdar cabeçalhos/URLs bases sem herdar o mesmo ciclo de vida
        ou travar o pool de conexões do cliente pai.
        """
        new_prefix = kwargs.get("prefix", self._prefix)

        client = HttpClient(
            base_url=kwargs.get("base_url", self._base_url),
            prefix=new_prefix,
            timeout=kwargs.get("timeout", self._timeout_base),
        )
        client._timeout_override = kwargs.get("timeout_override", self._timeout_override)
        return client


# ==============================
# Exportações do Módulo
# ==============================
__all__ = ["HttpClient"]