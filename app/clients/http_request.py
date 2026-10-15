"""
Cliente HTTP Assíncrono baseado no HTTPX.

Este módulo disponibiliza uma abstração robusta sobre o `httpx.AsyncClient`,
projetada para funcionar em ambientes assíncronos e híbridos (como Flask com Asyncio).

Recursos principais:
- Gerenciamento e re-associação automática de Event Loops entre threads.
- Suporte a múltiplos formatos no POST: JSON, Form-UrlEncoded e Multipart (Arquivos).
- Limpeza e fechamento gracioso de sockets TCP órfãos.
- Controle flexível de timeout com suporte a overrides temporários.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================

import asyncio  # Gerenciamento de tarefas assíncronas e detecção do Event Loop ativo
import logging  # Registro de diagnósticos, avisos e erros de comunicação de rede
from typing import Any, Dict, Optional, Tuple  # Anotações para tipagem estática e segurança do código
from urllib.parse import urlencode  # Utilitário para formatação segura de parâmetros na URL

import httpx  # Cliente HTTP assíncrono de alto desempenho

# Instancia o logger específico para o módulo de infraestrutura de rede
logger = logging.getLogger(__name__)


# =================================================================
# 2. FUNÇÕES AUXILIARES DE LIMPEZA E CICLO DE VIDA DE CONEXÕES
# =================================================================

def _force_sync_close_client(client: httpx.AsyncClient) -> None:
    """Realiza o fechamento síncrono emergencial do cliente HTTPX.

    Utilizado quando o Event Loop original em que o cliente foi criado já foi
    encerrado ou destruído pela thread (comum em workers de aplicações Web/Flask).
    O fechamento direto do transport libera os sockets no nível do Sistema Operacional.

    Args:
        client (httpx.AsyncClient): Instância do cliente HTTPX a ser encerrada.
    """
    try:
        # Verifica se o cliente possui um transportador de rede ativo antes de fechar
        if hasattr(client, "_transport") and client.transport is not None:
            client.transport.close()
            logger.debug("Transportador do cliente antigo fechado com sucesso de forma síncrona.")
    except Exception as e:
        logger.debug(f"Falha ao tentar fechar o transportador do cliente antigo de forma síncrona: {e}")


async def _safe_close_client(client: httpx.AsyncClient) -> None:
    """Encerra as conexões TCP do cliente de forma assíncrona e graciosa.

    Garante a finalização do handshake de encerramento TCP, evitando a permanência
    de conexões pendentes no estado TIME_WAIT.

    Args:
        client (httpx.AsyncClient): Instância do cliente HTTPX a ser encerrada.
    """
    try:
        await client.aclose()
        logger.debug("AsyncClient antigo encerrado com sucesso via aclose().")
    except Exception as e:
        logger.warning(f"Falha ao fechar AsyncClient antigo de forma assíncrona: {e}")


# =================================================================
# 3. CLASSE PRINCIPAL HTTP CLIENT
# =================================================================

class HttpClient:
    """Cliente HTTP assíncrono modular com suporte a pool de conexões reutilizável.

    Gerencia conexões persistentes HTTP/1.1 e HTTP/2, tratando automaticamente
    a re-criação do cliente em casos de troca de thread ou encerramento de Event Loops.
    """

    def __init__(
            self,
            base_url: str = "",
            prefix: str = "",
            timeout: Optional[float] = None,
    ):
        """Inicializa as configurações de base da URL, rotas e políticas do pool de conexões.

        Args:
            base_url (str, optional): URL raiz do serviço remetente (ex: 'https://api.podio.com'). Padrão é "".
            prefix (str, optional): Sufixo/Prefixo do recurso (ex: '/file' ou '/item'). Padrão é "".
            timeout (Optional[float], optional): Timeout padrão para as requisições em segundos. Padrão é None.
        """
        # Normalização da URL base: Remove barras finais para evitar duplicidade na concatenação
        self._base_url = base_url.rstrip("/")
        self._prefix = prefix

        # Armazenamento das configurações padrão de timeout
        self._timeout_base = timeout
        self._timeout_override: Optional[float] = None  # Permite alterar o timeout para uma única requisição

        # Controle interno do ciclo de vida do cliente e vinculação de loop
        self._active_client: Optional[httpx.AsyncClient] = None
        self._loop_associado: Optional[asyncio.AbstractEventLoop] = None

        # Configuração de resiliência e reutilização de conexões TCP no pool
        self._limits = httpx.Limits(
            max_connections=100,           # Limite máximo de conexões simultâneas (ativas + ociosas)
            max_keepalive_connections=20,  # Conexões mantidas 'quentes' no pool para reuso imediato
            keepalive_expiry=5.0,          # Tempo máximo (em segundos) que uma conexão ociosa permanece aberta
        )

    # =================================================================
    # PROPRIEDADES E GERENCIAMENTO DINÂMICO DE EVENT LOOP
    # =================================================================

    @property
    def _client(self) -> Optional[httpx.AsyncClient]:
        """Obtém ou instancia o AsyncClient vinculado ao Event Loop atual da thread.

        Garante a saúde do pool de conexões: se a requisição estiver rodando em um
        Event Loop diferente daquele em que o cliente foi criado, o cliente antigo é
        descartado e um novo é instanciado para prevenir erros de RuntimeError.

        Returns:
            httpx.AsyncClient: Instância pronta para uso.
        """
        # Identifica ou inicializa o Event Loop em execução na thread corrente
        try:
            loop_atual = asyncio.get_running_loop()
        except RuntimeError:
            loop_atual = asyncio.new_event_loop()
            asyncio.set_event_loop(loop_atual)

        # Se o cliente não existe ou pertence a outro Event Loop, recria o pool
        if self._active_client is None or self._loop_associado != loop_atual:
            if self._active_client is not None:
                # Limpa os recursos do cliente associado ao loop antigo
                _force_sync_close_client(self._active_client)

            # Instancia um novo cliente associado ao loop ativo da thread
            self._active_client = httpx.AsyncClient(limits=self._limits)
            self._loop_associado = loop_atual

        assert self._active_client is not None
        return self._active_client

    # =================================================================
    # GERENCIAMENTO DE CICLO DE VIDA (CONTEXT MANAGER)
    # =================================================================

    async def close(self) -> None:
        """Encerra o cliente HTTPX e libera todas as conexões mantidas no pool."""
        if self._active_client is not None:
            await self._active_client.aclose()
            self._active_client = None
            self._loop_associado = None
            logger.debug("Pool de conexões do HttpClient finalizado com sucesso.")

    async def __aenter__(self) -> "HttpClient":
        """Permite o uso da classe em blocos de contexto assíncronos (`async with`)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Garante a limpeza e encerramento do pool ao sair do contexto `async with`."""
        await self.close()

    # =================================================================
    # CONTROLE E RESOLUÇÃO DE TIMEOUTS
    # =================================================================

    @property
    def timeout(self) -> Optional[float]:
        """Retorna o valor de timeout ativo, priorizando substituições temporárias (override)."""
        return (
            self._timeout_override
            if self._timeout_override is not None
            else self._timeout_base
        )

    @timeout.setter
    def timeout(self, value: Optional[float]):
        """Define um valor de timeout temporário que será aplicado exclusivamente na próxima chamada."""
        self._timeout_override = value

    def _consume_timeout(self) -> httpx.Timeout:
        """Constrói a estrutura de Timeout do HTTPX e reseta overrides pontuais.

        Returns:
            httpx.Timeout: Objeto contendo os limites configurados para cada etapa da requisição.
        """
        t = self.timeout
        self._timeout_override = None  # Reseta a substituição temporária para chamadas futuras

        # Aplica o timeout personalizado se configurado
        if t is not None:
            connect_timeout = min(10.0, t)  # Mantém o limite de conexão razoável
            return httpx.Timeout(timeout=t, connect=connect_timeout, read=t)

        # Timeout padrão de infraestrutura para requisições convencionais
        return httpx.Timeout(
            connect=10.0,  # Tempo limite para estabelecimento da conexão TCP/TLS
            read=30.0,     # Tempo limite para aguardar os pacotes de resposta do servidor
            write=15.0,    # Tempo limite para transmissão de dados/payload no socket
            pool=5.0,      # Tempo limite de espera por um socket disponível no pool
        )

    # =================================================================
    # CONSTRUÇÃO DE URL E TRATAMENTO DE RESPOSTA
    # =================================================================

    def _build_url(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Formata e higieniza a URL final evitando barras duplicadas e anexando query params.

        Args:
            path (str, optional): Caminho complementar do endpoint. Padrão é "".
            params (Optional[Dict[str, Any]], optional): Parâmetros de URL (Query String). Padrão é None.

        Returns:
            str: URL absoluta montada.
        """
        if self._base_url:
            parts = [self._base_url.rstrip("/")]

            # Inclui o prefixo caso configurado na classe
            if self._prefix:
                clean_prefix = self._prefix.strip("/")
                if clean_prefix:
                    parts.append(clean_prefix)

            # Inclui o caminho específico da requisição
            if path:
                clean_path = path.strip("/")
                if clean_path:
                    parts.append(clean_path)

            url = "/".join(parts)

            # Anexa os parâmetros de busca formatados (?chave=valor&...)
            if params:
                url += f"?{urlencode(params, doseq=True)}"

            return url
        return path

    def _handle_response(self, response: httpx.Response) -> Tuple[int, Any]:
        """Processa o resultado do HTTPX e normaliza o retorno em uma tupla (Status, Dados).

        Args:
            response (httpx.Response): Resposta bruta retornada pela requisição HTTP.

        Returns:
            Tuple[int, Any]: Código de Status HTTP e o corpo decodificado (JSON, Texto ou None).
        """
        # Respostas HTTP 204 (No Content) ou corpos vazios não possuem payload
        if response.status_code == 204 or not response.content:
            return response.status_code, None

        # Tenta interpretar o conteúdo primeiramente como JSON
        try:
            return response.status_code, response.json()
        except Exception:
            # Fallback para string/texto puro caso o formato não seja um JSON válido
            return response.status_code, response.text

    # =================================================================
    # MÉTODOS DE REQUISIÇÃO HTTP (VERBOS)
    # =================================================================

    async def get(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição assíncrona com o método HTTP GET.

        Args:
            path (str, optional): Rota complementar do endpoint. Padrão é "".
            params (Optional[Dict[str, Any]], optional): Parâmetros de consulta (Query Parameters). Padrão é None.
            headers (Optional[Dict[str, str]], optional): Cabeçalhos HTTP adicionais. Padrão é None.

        Returns:
            Tuple[int, Any]: Tupla contendo o status da resposta e o conteúdo processado.
        """
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
            files: Optional[Any] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """Dispara uma requisição assíncrona com o método HTTP POST.

        Suporta três modos de envio automaticamente gerenciados:
        1. Multipart/Form-Data: Quando `files` é fornecido.
        2. Form UrlEncoded: Quando `as_form=True`.
        3. JSON: Modo padrão quando `payload` é um dicionário e `files=None`.

        Args:
            path (str, optional): Rota complementar do endpoint. Padrão é "".
            payload (Optional[Dict[str, Any]], optional): Dados para o corpo da requisição. Padrão é None.
            params (Optional[Dict[str, Any]], optional): Parâmetros para a Query String. Padrão é None.
            as_form (bool, optional): Se True, envia como 'application/x-www-form-urlencoded'. Padrão é False.
            files (Optional[Any], optional): Dicionário contendo arquivos no formato para HTTPX. Padrão é None.
            headers (Optional[Dict[str, str]], optional): Cabeçalhos HTTP customizados. Padrão é None.

        Returns:
            Tuple[int, Any]: Tupla contendo o status HTTP e a resposta decodificada.
        """
        timeout = self._consume_timeout()
        url = self._build_url(path, params)
        client = self._client

        assert client is not None

        # -------------------------------------------------------------
        # CASO 1: UPLOAD DE ARQUIVOS (MULTIPART / FORM-DATA)
        # -------------------------------------------------------------
        if files is not None:
            headers_req = headers.copy() if headers else {}

            # O HTTPX gera automaticamente o cabeçalho 'Content-Type: multipart/form-data; boundary=...'
            # Removemos qualquer 'Content-Type: application/json' manual para evitar conflitos na API remota.
            headers_req = {
                k: v for k, v in headers_req.items()
                if k.lower() != "content-type"
            }
            if "Accept" not in headers_req:
                headers_req["Accept"] = "application/json"

            response = await client.post(
                url,
                data=payload,
                files=files,
                headers=headers_req,
                timeout=timeout,
                follow_redirects=True,
            )

        # -------------------------------------------------------------
        # CASO 2: FORMULÁRIO URLENCODED
        # -------------------------------------------------------------
        elif as_form:
            headers_req = headers if headers is not None else {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            response = await client.post(
                url,
                data=payload,
                headers=headers_req,
                timeout=timeout,
                follow_redirects=True,
            )

        # -------------------------------------------------------------
        # CASO 3: CORPO EM FORMATO JSON (PADRÃO REST)
        # -------------------------------------------------------------
        else:
            headers_req = headers if headers is not None else {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            response = await client.post(
                url,
                json=payload,
                headers=headers_req,
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
        """Dispara uma requisição assíncrona com o método HTTP PUT (Normalmente atualização total).

        Args:
            path (str, optional): Rota complementar do endpoint. Padrão é "".
            payload (Optional[Dict[str, Any]], optional): Dados em formato dicionário para serialização JSON.
            params (Optional[Dict[str, Any]], optional): Parâmetros de consulta URL. Padrão é None.
            headers (Optional[Dict[str, str]], optional): Cabeçalhos HTTP adicionais. Padrão é None.

        Returns:
            Tuple[int, Any]: Status HTTP e payload processado da resposta.
        """
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
        """Dispara uma requisição assíncrona com o método HTTP PATCH (Atualização parcial).

        Args:
            path (str, optional): Rota complementar do endpoint. Padrão é "".
            payload (Optional[Dict[str, Any]], optional): Campos a serem alterados no JSON.
            params (Optional[Dict[str, Any]], optional): Parâmetros da Query String. Padrão é None.
            headers (Optional[Dict[str, str]], optional): Cabeçalhos adicionais. Padrão é None.

        Returns:
            Tuple[int, Any]: Status HTTP e payload processado.
        """
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
        """Dispara uma requisição assíncrona com o método HTTP DELETE.

        Args:
            path (str, optional): Rota do recurso a ser deletado. Padrão é "".
            params (Optional[Dict[str, Any]], optional): Parâmetros adicionais na URL. Padrão é None.
            headers (Optional[Dict[str, str]], optional): Cabeçalhos adicionais da requisição. Padrão é None.

        Returns:
            Tuple[int, Any]: Status HTTP e resposta (geralmente None em caso de 204).
        """
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
        """Clona a instância atual do cliente preservando ou alterando parâmetros base.

        Útil para criar sub-clientes que compartilham as configurações gerais, mas alteram
        o prefixo da rota ou parâmetros específicos de timeout.

        Args:
            **kwargs: Atributos a sobrescrever ('base_url', 'prefix', 'timeout').

        Returns:
            HttpClient: Uma nova instância configurada.
        """
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
    "HttpClient",  # Classe base do cliente HTTP assíncrono com suporte a pool e upload
]