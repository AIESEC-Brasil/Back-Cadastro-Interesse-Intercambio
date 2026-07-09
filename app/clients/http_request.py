"""
Cliente HTTP assíncrono baseado em httpx, com suporte a base_url, prefixo e
controle de timeout temporário por request.

Observação: todos os métodos HTTP retornam (status_code, body), sendo body o
JSON decodificado quando disponível, ou None/texto conforme o caso.
"""

# ==============================
# Importações (Dependencies)
# ==============================
from typing import Dict, Any, Tuple, Optional # Tipagem
import httpx #liente HTTP assíncrono
from urllib.parse import urlencode                         # Para codificação segura de query parameters

#

class HttpClient:
    """
    Cliente HTTP assíncrono modular.

    - timeout_base: timeout padrão da instância (estratégia de longo prazo)
    - timeout: override temporário (estratégia de curto prazo para chamadas específicas)
    """

    def __init__(
        self,
        base_url: str = "", # URL raiz (ex: https://api.podio.com)
        prefix: str = "",   # Prefixo de rota (ex: /item)
        timeout: Optional[float] = None # Tempo limite padrão em segundos
    ):
        # 🔒 Infraestrutura Base
        self._base_url = base_url.rstrip("/") # Garante que não termine com barra
        self._prefix = prefix

        # 🌐 Controle de Timeout
        self._timeout_base = timeout
        self._timeout_override: Optional[float] = None

    # ================================
    # TIMEOUT CONTROL
    # ================================

    @property
    def timeout(self) -> Optional[float]:
        """
        Retorna o timeout que será usado na próxima chamada.
        Prioriza o override temporário se ele tiver sido definido.
        """
        return (
            self._timeout_override
            if self._timeout_override is not None
            else self._timeout_base
        )

    @timeout.setter
    def timeout(self, value: Optional[float]):
        """
        Define um timeout temporário para a PRÓXIMA requisição apenas.
        """
        self._timeout_override = value

    def _consume_timeout(self) -> Optional[float]:
        """
        Recupera o valor de timeout e limpa o override imediatamente.
        Auto-reset: garante que o override não afete chamadas subsequentes indesejadas.
        """
        timeout = self.timeout
        self._timeout_override = None
        return timeout

    # ================================
    # URL BUILDER
    # ================================

    def _build_url(
            self,
            path: str = "",
            params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Monta a URL final combinando base_url, prefix e path, anexando params.

        Lógica:
        - Limpa barras repetidas (ex: base//prefix/path -> base/prefix/path).
        - Sanitiza cada parte da URL antes de concatenar.
        """
        if self._base_url:
            # 1. Base: Raiz da API
            parts = [self._base_url.rstrip("/")]

            # 2. Prefixo: Módulos específicos da API (ex: /app ou /org)
            if self._prefix:
                clean_prefix = self._prefix.strip("/")
                if clean_prefix:
                    parts.append(clean_prefix)

            # 3. Path: O endpoint final da requisição
            if path:
                clean_path = path.strip("/")
                if clean_path:
                    parts.append(clean_path)

            # Junta as partes usando barra única como separador
            url = "/".join(parts)

            # Adiciona Query Params se existirem (ex: ?id=123&status=active)
            if params:
                url += f"?{urlencode(params, doseq=True)}"

            return url
        return path

    # ================================
    # HTTP METHODS
    # ================================

    async def get(
        self,
        path: str = "",
        params: Optional[Dict[str, Any]] = None,
        headers=None
    ) -> Tuple[int, Any]:
        """Executa requisição GET e retorna (status_code, json_body)."""

        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                headers=headers,
                follow_redirects=True # Segue redirecionamentos (301, 302)
            )
            return response.status_code, response.json()

    async def post(
        self,
        path: str = "",
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        as_form: bool = False, # Define se envia como JSON ou Formulário x-www-form-urlencoded
        headers = None
        ) -> Tuple[int, Any]:
        """
        Executa requisição POST com suporte a JSON ou Form Data.
        """

        if headers is None:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded" if as_form else "application/json",
                "Accept": "application/json"
            }

        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        async with httpx.AsyncClient(timeout=timeout) as client:
            if as_form:
                # 'data' envia como formulário clássico
                response = await client.post(url, data=payload, headers=headers, follow_redirects=True)
            else:
                # 'json' serializa automaticamente o dicionário
                response = await client.post(url, json=payload, headers=headers, follow_redirects=True)
            return response.status_code, response.json()

    async def put(
        self,
        path: str = "",
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers=None
    ) -> Tuple[int, Any]:
        """Executa requisição PUT (substituição total) com corpo JSON."""
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.put(url, json=payload, headers=headers, follow_redirects=True)
            return response.status_code, response.json()

    async def patch(
        self,
        path: str = "",
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers=None
    ) -> Tuple[int, Any]:
        """Executa requisição PATCH (atualização parcial) com corpo JSON."""
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(url, json=payload, headers=headers, follow_redirects=True)
            return response.status_code, response.json()

    async def delete(
        self,
        path: str = "",
        params: Optional[Dict[str, Any]] = None,
        headers = None
    ) -> Tuple[int, Any]:
        """
        Executa requisição DELETE e trata casos de corpo vazio ou texto.
        """
        if headers is None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        timeout = self._consume_timeout()
        url = self._build_url(path, params)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.delete(url, headers=headers, follow_redirects=True)

            # 🛡️ Tratamento de status 204 (No Content) ou corpo realmente vazio
            if response.status_code == 204 or not response.content:
                return response.status_code, None

            try:
                return response.status_code, response.json()
            except Exception:
                # Fallback para texto se a resposta não for um JSON válido
                return response.status_code, response.text

    def clone(self, **kwargs) -> "HttpClient":
        """
        Cria uma cópia da instância atual (Deep Copy parcial).
        Útil para criar clientes especializados a partir de uma base comum.
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