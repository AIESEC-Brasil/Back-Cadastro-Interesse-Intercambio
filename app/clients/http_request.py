"""
Cliente HTTP assíncrono baseado em httpx, com suporte a base_url, prefixo e
controle de timeout temporário por request.

Observação: todos os métodos HTTP retornam (status_code, body), sendo body o
JSON decodificado quando disponível, ou None/texto conforme o caso.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import asyncio                                # Necessário para interagir com o Event Loop ativo do Python/Flask
from typing import Dict, Any, Tuple, Optional  # Tipagem para melhor suporte a IDEs (Autocompletar e validação)
import httpx                                  # Cliente HTTP assíncrono de alta performance
from urllib.parse import urlencode            # Para codificação segura de query parameters na URL


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
        self._base_url = base_url.rstrip("/")  # Garante que não termine com barra para evitar double slashes (//)
        self._prefix = prefix

        # 🌐 Controle de Timeout
        self._timeout_base = timeout
        self._timeout_override: Optional[float] = None

        # ⚡ Pool de Conexões Adaptativo
        # Não instanciamos o httpx.AsyncClient aqui no __init__. Como o __init__ pode ser chamado
        # fora de um contexto assíncrono, deixamos para inicializar o cliente "on-demand" (sob demanda)
        # assim que a primeira requisição for feita.
        self._active_client: Optional[httpx.AsyncClient] = None
        self._loop_associado: Optional[asyncio.AbstractEventLoop] = None

    # ==========================================
    # GERENCIAMENTO DINÂMICO DE EVENT LOOP (A Mágica)
    # ==========================================

    @property
    def _client(self) -> httpx.AsyncClient:
        """
        Propriedade dinâmica que substitui o antigo atributo síncrono 'self._client'.

        Por que isso é necessário?
        No Flask, cada requisição assíncrona pode rodar em um Event Loop diferente que abre e
        fecha rapidamente. Se guardássemos o AsyncClient no __init__, na segunda requisição o
        loop estaria fechado e o HTTPX lançaria o erro: "RuntimeError: Event loop is closed".

        Como funciona:
        1. Toda vez que uma requisição (GET, POST, etc.) chama 'self._client', este método é executado.
        2. Ele captura o loop de eventos que está rodando no exato momento.
        3. Se o loop mudou (ou se é a primeira chamada), ele fecha o cliente antigo de forma segura,
           abre um novo AsyncClient atrelado ao loop atual e salva essa referência.
        4. Se o loop continuar o mesmo, ele apenas retorna o cliente já existente, mantendo o pooling
           de conexões ativo e rápido.
        """
        try:
            # Captura o loop que está executando a thread/request atual
            loop_atual = asyncio.get_running_loop()
        except RuntimeError:
            # Se não houver nenhum loop rodando (chamada fora de contexto async)
            loop_atual = None

        # Se o cliente não existe, ou se o loop de eventos atual mudou/foi reiniciado pelo Flask
        if self._active_client is None or self._loop_associado != loop_atual:

            # Se já tínhamos um cliente aberto no loop antigo, fazemos o descarte
            if self._active_client is not None:
                try:
                    # Usamos .close() síncrono para descarte rápido, pois o loop antigo já morreu
                    # e um 'await aclose()' falharia por não ter um loop ativo associado a ele.
                    self._active_client.close()
                except Exception:
                    pass  # Ignora falhas se o cliente antigo já estiver completamente inacessível

            # Cria o novo pool de conexões associado estritamente ao novo loop ativo
            self._active_client = httpx.AsyncClient()
            self._loop_associado = loop_atual

        return self._active_client

    # ================================
    # GERENCIAMENTO DE CICLO DE VIDA
    # ================================

    async def close(self) -> None:
        """
        Fecha o pool de conexões persistentes do cliente httpx de forma assíncrona.
        Recomendado chamar ao encerrar o ciclo de vida da aplicação para liberar recursos do sistema.
        """
        if self._active_client is not None:
            await self._active_client.aclose()
            self._active_client = None
            self._loop_associado = None

    async def __aenter__(self) -> "HttpClient":
        """Suporte para uso do cliente como gerenciador de contexto assíncrono (async with HttpClient() as client)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Fecha o pool de conexões automaticamente ao sair do bloco de contexto 'async with'."""
        await self.close()

    # ================================
    # CONTROLE DE TIMEOUT
    # ================================

    @property
    def timeout(self) -> Optional[float]:
        """
        Retorna o timeout que será usado na próxima chamada.
        Prioriza o override temporário se ele tiver sido definido especificamente para a chamada.
        """
        return (
            self._timeout_override
            if self._timeout_override is not None
            else self._timeout_base
        )

    @timeout.setter
    def timeout(self, value: Optional[float]):
        """
        Define um timeout temporário que durará apenas para a PRÓXIMA requisição realizada.
        """
        self._timeout_override = value

    def _consume_timeout(self) -> httpx.Timeout:
        """
        Recupera o valor de timeout aplicável e limpa o override imediatamente.
        Retorna um objeto httpx.Timeout configurado.

        Auto-reset: garante que o override não "vaze" para chamadas subsequentes por acidente.
        """
        t = self.timeout
        self._timeout_override = None  # Reseta o override de curto prazo
        return httpx.Timeout(t)

    # ================================
    # CONSTRUTOR DE URL (URL BUILDER)
    # ================================

    def _build_url(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Monta a URL final combinando base_url, prefix e path, tratando barras extras e query params.

        Lógica de higienização:
        - Limpa barras repetidas (ex: base//prefix/path -> base/prefix/path).
        - Sanitiza cada parte da URL antes de concatenar.
        """
        if self._base_url:
            # 1. Base: Raiz da API (remove barra no final para evitar duplicidade)
            parts = [self._base_url.rstrip("/")]

            # 2. Prefixo: Módulos específicos (ex: /app ou /org)
            if self._prefix:
                clean_prefix = self._prefix.strip("/")
                if clean_prefix:
                    parts.append(clean_prefix)

            # 3. Path: O endpoint final da requisição
            if path:
                clean_path = path.strip("/")
                if clean_path:
                    parts.append(clean_path)

            # Junta todas as partes usando uma barra única como separador
            url = "/".join(parts)

            # Adiciona Query Params formatados de forma segura, se existirem (ex: ?id=123&status=active)
            if params:
                url += f"?{urlencode(params, doseq=True)}"

            return url
        return path

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
        Executa requisição GET usando o pool persistente e retorna (status_code, json_body).
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        # 'self._client' acessa a nossa property que garante que o loop de eventos está aberto!
        response = await self._client.get(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True  # Segue redirecionamentos automaticamente (ex: HTTP 301, 302)
        )
        return response.status_code, response.json()

    async def post(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            as_form: bool = False,  # Define se envia como JSON ou Formulário x-www-form-urlencoded
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição POST usando o pool persistente com suporte a JSON ou Form Data.
        """
        if headers is None:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded" if as_form else "application/json",
                "Accept": "application/json"
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        if as_form:
            # 'data' envia como formulário clássico (form-urlencoded)
            response = await self._client.post(
                url, data=payload, headers=headers, timeout=timeout, follow_redirects=True
            )
        else:
            # 'json' serializa automaticamente o dicionário Python para string JSON
            response = await self._client.post(
                url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
            )
        return response.status_code, response.json()

    async def put(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição PUT (substituição total) usando o pool persistente com corpo JSON.
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.put(
            url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
        )
        return response.status_code, response.json()

    async def patch(
            self,
            path: str = "",
            payload: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição PATCH (atualização parcial) usando o pool persistente com corpo JSON.
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.patch(
            url, json=payload, headers=headers, timeout=timeout, follow_redirects=True
        )
        return response.status_code, response.json()

    async def delete(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None,
            headers=None
    ) -> Tuple[int, Any]:
        """
        Executa requisição DELETE usando o pool persistente e trata casos de corpo vazio ou texto plano.
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        response = await self._client.delete(
            url, headers=headers, timeout=timeout, follow_redirects=True
        )

        # 🛡️ Tratamento de status 204 (No Content) ou corpo realmente vazio para evitar quebras no .json()
        if response.status_code == 204 or not response.content:
            return response.status_code, None

        try:
            return response.status_code, response.json()
        except Exception:
            # Fallback para texto puro se a resposta não for um JSON estruturado válido
            return response.status_code, response.text

    def clone(self, **kwargs) -> "HttpClient":
        """
        Cria uma cópia das configurações da instância atual (Deep Copy parcial).
        Útil para criar clientes especializados a partir de uma configuração base,
        iniciando um pool de conexões independente para o clone caso necessário.
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