from typing import Any, Dict, List, Optional, Tuple, Union
from app.dto import LeadPreCadastroInput
from .podio import buscarToken
from ..http_request import HttpClient
from app.utils import resolve_response

# Inicializa o cliente HTTP apontando para o endpoint base do Podio focado em itens
http = HttpClient(base_url="https://api.podio.com", prefix="/item")

# Dicionários de tipos (Type Aliases) para simplificar a leitura e manutenção das assinaturas de funções
ItemPodio = Dict[str, Any]
CampoPodio = Dict[str, Any]


class Buscar:
    """Classe PodioUtils.

    Centraliza e encapsula os métodos de consulta, busca por filtros e validação
    cruzada de leads dentro de um aplicativo específico do Podio.
    """

    def __init__(self, app_id: Union[str, int]) -> None:
        """Inicializa o buscador vinculando-o a um App ID específico do Podio.

        Args:
            app_id: O identificador único do aplicativo Podio alvo.
        """
        self.app_id: Union[str, int] = app_id

    def get_field(
            self, item: Optional[ItemPodio], field_name: str
    ) -> Optional[CampoPodio]:
        """Varre a estrutura de um item do Podio para encontrar um campo específico
        utilizando o seu identificador externo (external_id).
        """
        if not item or "fields" not in item or not isinstance(item["fields"], list):
            return None

        for field in item["fields"]:
            if isinstance(field, dict) and field.get("external_id") == field_name:
                return field
        return None

    async def campo(
            self, campo_nome: str, valor: Any, is_multiple: bool = False
    ) -> List[ItemPodio]:
        """Realiza uma requisição HTTP POST para o endpoint de filtragem do Podio.

        Método alterado para ASYNC para poder aguardar o resolve_response.
        """
        url: str = f"/app/{self.app_id}/filter/"

        filtros: Dict[str, Any] = {
            campo_nome: [valor] if is_multiple else valor
        }
        payload: Dict[str, Any] = {"filters": filtros, "limit": 1}

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {buscarToken('ogx-token-podio')}",
            "Content-Type": "application/json",
        }

        response = http.post(url, payload=payload, headers=headers)

        try:
            # ATUALIZADO: Usando await e desestruturando a Tupla (status, data) que o resolve_response retorna
            _, response_data = await resolve_response(response)
            return response_data.get("items", [])
        except Exception as e:
            texto_erro = getattr(response, 'text', str(response))
            raise RuntimeError(
                f'Erro ao consultar campo "{campo_nome}": {texto_erro}'
            ) from e

    async def telefone(self, telefone_valor: str) -> List[ItemPodio]:
        """Consulta os itens do App e filtra manualmente pelo número de telefone interno.

        Método alterado para ASYNC para poder aguardar o resolve_response.
        """
        url: str = f"/app/{self.app_id}/"

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {buscarToken('ogx-token-podio')}"
        }

        response = http.get(url, headers=headers)

        try:
            # ATUALIZADO: Usando await e desestruturando a Tupla (status, data)
            _, response_data = await resolve_response(response)
            itens: List[ItemPodio] = response_data.get("items", [])

            itens_filtrados: List[ItemPodio] = []
            for item in itens:
                fields: List[CampoPodio] = item.get("fields", [])
                for field in fields:
                    if field.get("type") == "phone":
                        valores: List[Dict[str, str]] = field.get("values", [])
                        if any(
                                v.get("value") == telefone_valor for v in valores
                        ):
                            itens_filtrados.append(item)
                            break

            return itens_filtrados
        except Exception as e:
            texto_erro = getattr(response, 'text', str(response))
            raise RuntimeError(
                f"Erro ao filtrar por telefone: {texto_erro}"
            ) from e

    async def item_completo(self, data: LeadPreCadastroInput) -> Optional[ItemPodio]:
        """Método mestre que executa uma estratégia de funil e cruzamento de dados.

        Método alterado para ASYNC porque chama sub-métodos que agora são assíncronos.
        """
        if hasattr(data, "model_dump"):
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            data_dict = data.dict()
        else:
            data_dict = data

        emails: List[str] = [e["email"] for e in data_dict.get("email", []) if "email" in e]
        telefones: List[str] = [t["numero"] for t in data_dict.get("telefone", []) if "numero" in t]
        resultados: List[ItemPodio] = []

        # ETAPA 1: Povoamento. Adicionado 'await' nas chamadas dos métodos assíncronos
        resultados.extend(await self.campo("title", data_dict.get("nome")))
        resultados.extend(await self.campo("sobrenome-2", data_dict.get("sobrenome")))

        for e in emails:
            resultados.extend(await self.campo("email", e, is_multiple=True))

        for t in telefones:
            resultados.extend(await self.telefone(t))

        # ETAPA 2: Dedup. Remove duplicados mantendo a ordem original de busca usando o 'item_id'
        vistos = set()
        resultados_unicos: List[ItemPodio] = []
        for item in resultados:
            if item and "item_id" in item:
                if item["item_id"] not in vistos:
                    vistos.add(item["item_id"])
                    resultados_unicos.append(item)

        # ETAPA 3: Validação Cruzada Rígida (Filtro Fino)
        for item in resultados_unicos:
            if not item or "fields" not in item:
                continue

            campo_titulo: Optional[CampoPodio] = self.get_field(item, "title")
            campo_sobrenome: Optional[CampoPodio] = self.get_field(item, "sobrenome-2")
            campo_email: Optional[CampoPodio] = self.get_field(item, "email")
            campo_telefone: Optional[CampoPodio] = self.get_field(item, "telefone")

            try:
                titulo: str = campo_titulo["values"][0]["value"] if campo_titulo else ""
            except (KeyError, IndexError):
                titulo = ""

            try:
                sobrenome_title: str = (
                    campo_sobrenome["values"][0]["value"]
                    if campo_sobrenome
                    else ""
                )
            except (KeyError, IndexError):
                sobrenome_title = ""

            item_emails: List[str] = (
                [v["value"] for v in campo_email.get("values", []) if "value" in v]
                if campo_email
                else []
            )
            item_telefones: List[str] = (
                [v["value"] for v in campo_telefone.get("values", []) if "value" in v]
                if campo_telefone
                else []
            )

            email_match: bool = any(e in item_emails for e in emails)
            telefone_match: bool = any(t in item_telefones for t in telefones)
            nome_match: bool = titulo == data_dict.get("nome")
            sobrenome_match: bool = sobrenome_title == data_dict.get("sobrenome")

            if (email_match or telefone_match) and nome_match and sobrenome_match:
                return item

        return None


__all__ = ["Buscar"]