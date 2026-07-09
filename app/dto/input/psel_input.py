"""
DTOs de entrada e transformação para o fluxo do Processo Seletivo (PSEL).

Inclui modelos Pydantic para validação dos dados recebidos e métodos auxiliares
para montar payloads aceitos pelo Podio, garantindo a integridade dos dados
desde a captura na API até a persistência no CRM.
"""

# =================================================================
# 1. IMPORTAÇÕES (DEPENDÊNCIAS)
# =================================================================
from datetime import datetime            # Manipulação de objetos de data e hora para registros cronológicos.
from typing import Dict, List, Any, Optional # Tipagem estática para estruturas de dados complexas e opcionais.
from pydantic import (                   # Biblioteca principal para análise, validação e gestão de esquemas de dados.
    BaseModel,                           # Classe base para a criação de modelos de dados validados.
    Field                                # Campo para definição de metadados, aliases e regras de validação.
)

# Importações de submodelos para composição e manutenção da paridade entre módulos.
from .padrao import Comite, EmailItem, TelefoneItem, Autorizacao, DataNascimento

# =================================================================
# 2. MODELOS DE ENTRADA (API -> FLASK)
# =================================================================

class LeadPselInput(BaseModel):
    """
    Representa os dados brutos de um candidato (Lead) recebidos via API externa.

    Este modelo atua como a primeira camada de defesa, validando tipos de dados,
    formatos de e-mail e regras de negócio para datas de nascimento.

    Attributes:
        nome (str): Nome completo ou identificador textual do candidato.
        data_nascimento (DataNascimento): Objeto de data validado para impedir datas futuras.
        emails (List[EmailItem]): Coleção de e-mails categorizados (casa, trabalho, etc).
        telefones (List[TelefoneItem]): Coleção de números telefônicos categorizados.
        comite (Comite): Identificador e nome da unidade AIESEC de destino.
        id_autorizacao (Autorizacao): Flag booleana/inteira de consentimento LGPD.
    """

    # Configuração centralizada para o comportamento do Pydantic
    model_config = {
        "populate_by_name": True, # Permite a criação do modelo usando nomes internos ou aliases (ex: dataNascimento).
        "from_attributes": True,  # Facilita a compatibilidade com instâncias de ORMs ou classes Python puras.
        "extra": "forbid"         # Impede a injeção de campos não mapeados, mitigando ataques de atribuição em massa.
    }

    # Definição dos Campos
    nome: str = Field(
        min_length=3,
        max_length=255,
        description="Nome completo do candidato",
        json_schema_extra={"example": "João Silva"}
    )

    data_nascimento: DataNascimento = Field(
        alias="dataNascimento",
        description="Data de nascimento do candidato (validação contra datas futuras)",
        json_schema_extra={
            "example": "2000-06-23 00:00:00"
        }
    )

    emails: List[EmailItem] = Field(description="Lista de e-mails para contato")

    telefones: List[TelefoneItem] = Field(description="Lista de telefones para contato")

    comite: Comite = Field(description="Comitê Local responsável pelo atendimento")

    id_autorizacao: Autorizacao = Field(
        alias="idAutorizacao",
        description="Estado de autorização para tratamento de dados (LGPD)"
    )


class ParamsInput(BaseModel):
    """
    Validador para parâmetros de consulta (Query Params) em rotas de segurança.

    Utilizado para verificar a integridade de links de convite ou sessões
    de teste do Processo Seletivo.

    Attributes:
        id (int): Identificador numérico do registro.
        nome (str): Nome do candidato para verificação cruzada (checksum visual).
        token (str): Hash único de autenticação da sessão.
    """
    id: int = Field(description="ID único identificador do registro no CRM")
    nome: str = Field(description="Nome associado para conferência de integridade")
    token: str = Field(description="Token de segurança para validação da URL/Link")


# =================================================================
# 3. MODELOS DE SAÍDA / TRANSFORMAÇÃO (PODIO)
# =================================================================

class LeadPselPodio(LeadPselInput):
    """
    Extensão do modelo de entrada especializada na exportação para o CRM Podio.

    Herda todas as validações do LeadPselInput e adiciona lógica de mapeamento
    específica para os Slugs e IDs internos do Podio.
    """

    def to_podio_payload(self) -> dict:
        """
        Converte o objeto Pydantic em um dicionário compatível com a API do Podio.

        Realiza a normalização de listas para o formato de 'Fields' do Podio e
        converte objetos de data para strings formatadas.

        Returns:
            dict: Payload mapeado com Slugs internos do CRM.
        """
        return {
            "titulo": self.nome,
            "data-de-nascimento": self.data_nascimento.strftime("%Y-%m-%d %H:%M:%S"),
            "email": [
                {"type": email.tipo, "value": email.email} for email in self.emails
            ],
            "telefone": [
                {"type": telefone.tipo, "value": telefone.numero} for telefone in self.telefones
            ],
            "autorizo-receber-informacoes-sobre-os-projetos-de-inter": self.id_autorizacao,
            "aiesec-mais-proxima-digite-primeira-letra-para-filtrar": self.comite.id,
            "tem-fit-cultural": 3 # ID fixo que define o status inicial no fluxo do CRM
        }


class AtualizarPodioStatusFitCultural(BaseModel):
    """
    Modelo simplificado para atualização pontual de status no CRM.

    Attributes:
        status (int): Valor numérico representando o novo estado (ex: Aprovado, Reprovado).
    """
    status: int = Field(
        description="ID numérico da opção de status no Podio",
        json_schema_extra={"example": 203}
    )

    def to_podio_payload(self) -> Dict[str, int]:
        """
        Gera o payload de atualização de campo único.

        Returns:
            Dict[str, int]: Dicionário mapeando o slug 'status' ao ID fornecido.
        """
        return {"status": self.status}


# =================================================================
# 4. EXPORTAÇÕES DO MÓDULO
# =================================================================

# Lista explícita de componentes acessíveis para manter o namespace limpo.
__all__ = [
    "LeadPselInput",
    "LeadPselPodio",
    "AtualizarPodioStatusFitCultural",
    "ParamsInput"
]