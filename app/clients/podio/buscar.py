"""Módulo de Serviços de Busca e Consulta para a API do Podio.

Este módulo encapsula as operações de comunicação e filtro HTTP direcionadas à
plataforma Podio, provendo funcionalidades avançadas de filtragem por campo,
varredura de itens e um algoritmo de funil com validação cruzada para busca de leads.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from typing import Any, Dict, List, Optional, Tuple, Union  # Type hints padrão do Python para tipagem estática
from app.dto import LeadPreCadastroInput  # DTO Pydantic com o esquema de entrada para pré-cadastro de Lead
from app.utils import resolve_response     # Utilitário assíncrono para resolver respostas HTTP e extrair o payload
from .podio import buscar_token             # Função utilitária para recuperar o token OAuth de autenticação do Podio
from ..http_request import HttpClient     # Cliente HTTP encapsulado para requisições externas


# =================================================================
# 2. CONFIGURAÇÕES E CLIENTE HTTP
# =================================================================

# Inicializa a instância do cliente HTTP direcionando para os endpoints de itens da API do Podio
http = HttpClient(base_url="https://api.podio.com", prefix="/item")

# Define apelidos de tipo (Type Aliases) para simplificar a assinatura dos métodos
ItemPodio = Dict[str, Any]   # Representa a estrutura de dicionário de um item completo do Podio
CampoPodio = Dict[str, Any]  # Representa a estrutura de dicionário de um campo interno do Podio


# =================================================================
# 3. CLASSE DE SERVIÇO E BUSCA
# =================================================================

class Buscar:
    """Centraliza e encapsula os métodos de consulta, filtragem e validação cruzada de leads.

    Esta classe abstrai as chamadas HTTP para o Podio e expõe métodos assíncronos
    especializados para buscar itens por campos específicos (ex: e-mail, telefone)
    e realizar deduplicação e validação estrita contra payloads de Leads.

    Attributes:
        app_id (Union[str, int]): Identificador numérico ou string do aplicativo do Podio.
    """

    def __init__(self, app_id: Union[str, int]) -> None:
        """Inicializa o serviço de busca associando-o a um App ID específico do Podio.

        Args:
            app_id (Union[str, int]): O identificador único (App ID) do aplicativo no Podio.
        """
        self.app_id: Union[str, int] = app_id

    @validar
    def get_field(
            self, item: Optional[ItemPodio], field_name: str
    ) -> Optional[CampoPodio]:
        """Varre a lista de campos de um item do Podio para localizar um campo pelo seu external_id.

        Args:
            item (Optional[ItemPodio]): Dicionário representando o item retornado pela API do Podio.
            field_name (str): O identificador externo (`external_id`) do campo procurado.

        Returns:
            Optional[CampoPodio]: O dicionário contendo a estrutura do campo encontrado,
                                  ou `None` caso o item seja inválido ou o campo não exista.
        """
        # Valida se o item possui a chave 'fields' estruturada como lista
        if not item or "fields" not in item or not isinstance(item["fields"], list):
            return None

        # Percorre cada campo buscando a correspondência exata do external_id
        for field in item["fields"]:
            if isinstance(field, dict) and field.get("external_id") == field_name:
                return field
        return None

    @validar
    async def campo(
            self, campo_nome: str, valor: Any, is_multiple: bool = False
    ) -> List[ItemPodio]:
        """Realiza uma requisição HTTP POST para o endpoint de filtragem direta do Podio.

        Args:
            campo_nome (str): O `external_id` do campo no Podio que será filtrado.
            valor (Any): O valor do filtro a ser pesquisado.
            is_multiple (bool, optional): Se `True`, encapsula o valor em uma lista.
                                          Necessário para campos do tipo 'app', 'category', etc.
                                          Defaults to `False`.

        Returns:
            List[ItemPodio]: Lista contendo os dicionários dos itens encontrados no filtro.

        Raises:
            RuntimeError: Se houver falha na requisição HTTP ou erro retornado pelo Podio.
        """
        # Monta a URL dinâmica do endpoint de filtro do aplicativo
        url: str = f"/app/{self.app_id}/filter/"

        # Estrutura o filtro verificando se exige formato de lista
        filtros: Dict[str, Any] = {
            campo_nome: [valor] if is_multiple else valor
        }

        # Define o payload limitando a busca ao primeiro registro correspondente
        payload: Dict[str, Any] = {"filters": filtros, "limit": 1}

        # Cabeçalhos HTTP contendo o token de autenticação Bearer
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {buscar_token('ogx-token-podio')}",
            "Content-Type": "application/json",
        }

        # Dispara a requisição POST para a API do Podio
        response = await http.post(url, payload=payload, headers=headers)

        try:
            # Resolve a resposta assíncrona desestruturando a tupla (status_code, response_data)
            _, response_data = await resolve_response(response)
            return response_data.get("items", [])
        except Exception as e:
            # Captura o texto original da resposta de erro caso disponível
            texto_erro = getattr(response, 'text', str(response))
            raise RuntimeError(
                f'Erro ao consultar campo "{campo_nome}": {texto_erro}'
            ) from e

    @validar
    async def telefone(self, telefone_valor: str) -> List[ItemPodio]:
        """Consulta os itens do App e filtra manualmente buscando por correspondência de telefone.

        Como a API de filtro nativa do Podio possui limitações com campos de telefone complexos,
        este método busca a lista de itens do App e varre as estruturas em memória.

        Args:
            telefone_valor (str): O número de telefone a ser pesquisado.

        Returns:
            List[ItemPodio]: Lista de itens que possuem o número de telefone exato cadastrado.

        Raises:
            RuntimeError: Se houver falha na comunicação HTTP ou na leitura dos dados.
        """
        # Endpoint para obtenção dos itens do App
        url: str = f"/app/{self.app_id}/"

        # Cabeçalhos HTTP com autenticação Bearer
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {buscar_token('ogx-token-podio')}"
        }

        # Executa a chamada HTTP GET
        response = http.get(url, headers=headers)

        try:
            # Aguarda a resolução assíncrona da resposta HTTP
            _, response_data = await resolve_response(response)
            itens: List[ItemPodio] = response_data.get("items", [])

            itens_filtrados: List[ItemPodio] = []

            # Varre todos os itens retornado do aplicativo
            for item in itens:
                fields: List[CampoPodio] = item.get("fields", [])

                # Percorre cada campo do item verificando se é do tipo 'phone'
                for field in fields:
                    if field.get("type") == "phone":
                        valores: List[Dict[str, str]] = field.get("values", [])

                        # Verifica se o número informado bate com algum dos telefones do campo
                        if any(
                                v.get("value") == telefone_valor for v in valores
                        ):
                            itens_filtrados.append(item)
                            break  # Interrompe a varredura interna ao encontrar match no item

            return itens_filtrados
        except Exception as e:
            texto_erro = getattr(response, 'text', str(response))
            raise RuntimeError(
                f"Erro ao filtrar por telefone: {texto_erro}"
            ) from e

    @validar
    async def item_completo(self, data: LeadPreCadastroInput) -> Optional[ItemPodio]:
        """Executa um algoritmo de busca em funil com de duplicação e validação cruzada estrita.

        O algoritmo executa 3 etapas principais:
        1. **Povoamento:** Dispara buscas amplas no Podio por Nome, Sobrenome, E-mails e Telefones.
        2. **De duplicação:** Remove itens duplicados encontrados preservando a ordem pelo `item_id`.
        3. **Validação Cruzada Rígida (Filtro Fino):** Valida se o item retornado atende
           simultaneamente aos critérios: (E-mail MATCH OU Telefone MATCH) E Nome MATCH E Sobrenome MATCH.

        Args:
            data (LeadPreCadastroInput): Objeto de entrada contendo os dados do Lead a ser verificado.

        Returns:
            Optional[ItemPodio]: O item do Podio validado que corresponde perfeitamente ao Lead,
                                  ou `None` se nenhum item passar na validação estrita.
        """
        # Normaliza a entrada para dicionário, suportando Pydantic v2 (model_dump), v1 (dict) ou dict padrão
        if hasattr(data, "model_dump"):
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            data_dict = data.dict()
        else:
            data_dict = data

        # Extrai listas de e-mails e telefones em formato simples de string
        emails: List[str] = [e["email"] for e in data_dict.get("email", []) if "email" in e]
        telefones: List[str] = [t["numero"] for t in data_dict.get("telefone", []) if "numero" in t]
        resultados: List[ItemPodio] = []

        # -----------------------------------------------------------------
        # ETAPA 1: Povoamento (Consultas brutas no Podio)
        # -----------------------------------------------------------------
        # Busca por Nome (title) e Sobrenome (sobrenome-2)
        resultados.extend(await self.campo("title", data_dict.get("nome")))
        resultados.extend(await self.campo("sobrenome-2", data_dict.get("sobrenome")))

        # Busca por cada E-mail cadastrado
        for e in emails:
            resultados.extend(await self.campo("email", e, is_multiple=True))

        # Busca por cada Telefone cadastrado
        for t in telefones:
            resultados.extend(await self.telefone(t))

        # -----------------------------------------------------------------
        # ETAPA 2: Deduplicação (Remove repetições mantendo a ordem)
        # -----------------------------------------------------------------
        vistos = set()
        resultados_unicos: List[ItemPodio] = []
        for item in resultados:
            if item and "item_id" in item:
                if item["item_id"] not in vistos:
                    vistos.add(item["item_id"])
                    resultados_unicos.append(item)

        # -----------------------------------------------------------------
        # ETAPA 3: Validação Cruzada Rígida (Filtro Fino de Segurança)
        # -----------------------------------------------------------------
        for item in resultados_unicos:
            if not item or "fields" not in item:
                continue

            # Extrai os campos do item do Podio usando get_field
            campo_titulo: Optional[CampoPodio] = self.get_field(item, "title")
            campo_sobrenome: Optional[CampoPodio] = self.get_field(item, "sobrenome-2")
            campo_email: Optional[CampoPodio] = self.get_field(item, "email")
            campo_telefone: Optional[CampoPodio] = self.get_field(item, "telefone")

            # Extrai com segurança o valor do Nome
            try:
                titulo: str = campo_titulo["values"][0]["value"] if campo_titulo else ""
            except (KeyError, IndexError):
                titulo = ""

            # Extrai com segurança o valor do Sobrenome
            try:
                sobrenome_title: str = (
                    campo_sobrenome["values"][0]["value"]
                    if campo_sobrenome
                    else ""
                )
            except (KeyError, IndexError):
                sobrenome_title = ""

            # Extrai a lista de e-mails presentes no item do Podio
            item_emails: List[str] = (
                [v["value"] for v in campo_email.get("values", []) if "value" in v]
                if campo_email
                else []
            )

            # Extrai a lista de telefones presentes no item do Podio
            item_telefones: List[str] = (
                [v["value"] for v in campo_telefone.get("values", []) if "value" in v]
                if campo_telefone
                else []
            )

            # Avalia as regras booleanas de correspondência (Match)
            email_match: bool = any(e in item_emails for e in emails)
            telefone_match: bool = any(t in item_telefones for t in telefones)
            nome_match: bool = titulo == data_dict.get("nome")
            sobrenome_match: bool = sobrenome_title == data_dict.get("sobrenome")

            # Regra de ouro: Deve bater (E-mail OU Telefone) E Nome E Sobrenome simultaneamente
            if (email_match or telefone_match) and nome_match and sobrenome_match:
                return item  # Retorna imediatamente o primeiro registro totalmente validado

        return None  # Nenhum item atendeu todos os critérios cruzados


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["Buscar"]