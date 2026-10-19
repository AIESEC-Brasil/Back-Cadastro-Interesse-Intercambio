"""Modelo base compartilhado pelos payloads de cadastro de leads."""

from typing import List, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..common import (
    Autorizacao,
    Comite,
    ContatoEmail,
    ContatoTelefone,
    DataNascimento,
    Meio,
    Origem,
    ProdutoLead,
    Tag,
    Universidade,
)
from ..common.lead import validar_opcao_cache


class LeadPreCadastroBase(BaseModel):
    """Campos comuns do pré-cadastro de um lead."""

    model_config = ConfigDict(extra="ignore")

    nome: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
        description="Nome do lead",
    )
    sobrenome: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[A-Za-zÀ-ÿ\s]+$",
        description="Sobrenome do lead",
    )
    dataNascimento: DataNascimento = Field(description="Data de nascimento")
    telefone: List[ContatoTelefone] = Field(description="Telefones para contato")
    email: List[ContatoEmail] = Field(description="E-mails para contato")
    universidade: Optional[Universidade] = Field(
        default=None, description="Instituição de ensino, quando informada"
    )
    produto: ProdutoLead = Field(description="Produto ou programa de interesse")
    comite: Optional[Comite] = Field(
        default=None, description="Comitê responsável, quando informado"
    )
    autorizacao: Autorizacao = Field(description="Consentimento do lead")
    origem: Origem = Field(description="Origem do contato")
    meio: Optional[Meio] = Field(
        default=None, description="Meio de contato, quando informado"
    )
    tag: Optional[List[Tag]] = Field(
        default=None, description="Tags de campanha ou evento"
    )

    @field_validator("autorizacao")
    @classmethod
    def validar_autorizacao_metadados(cls, valor: Autorizacao) -> Autorizacao:
        """Confere o ID e o rótulo do consentimento com `termo_privacidade`."""
        texto: str = "sim" if valor is Autorizacao.SIM else "não"
        validar_opcao_cache("termo_privacidade", int(valor), texto)
        return valor

    @model_validator(mode="after")
    def validar_universidade_ou_comite(self) -> Self:
        """Exige uma referência de universidade ou comitê."""
        if self.universidade is None and self.comite is None:
            raise ValueError("Informe ao menos um dos campos: universidade ou comite.")
        return self


__all__ = ["LeadPreCadastroBase"]
