"""Estratégias de montagem dos contratos de pré-cadastro."""

from abc import ABC, abstractmethod
from typing import Any

from ..dto.output import (
    LeadPersistencia,
    LeadPreCadastroB2CPersistencia,
)
from ..dto.types import LeadPreCadastroBase


class LeadPersistenceStrategy(ABC):
    """Define como um fluxo converte os dados do formulário em persistência."""

    @abstractmethod
    def montar(
        self,
        dados: LeadPreCadastroBase,
        dados_com_contatos: dict[str, Any],
        *,
        id_escritorio: int,
        lead_id: int | None = None,
    ) -> LeadPersistencia | LeadPreCadastroB2CPersistencia:
        """Monta o DTO específico para a estratégia de cadastro."""

    def dados_comuns(
        self,
        dados: LeadPreCadastroBase,
        dados_com_contatos: dict[str, Any],
        id_escritorio: int,
    ) -> dict[str, Any]:
        """Prepara os campos e contatos compartilhados pelos fluxos."""
        payload = {
            campo: dados_com_contatos[campo]
            for campo in ("telefone", "email", "tag")
            if campo in dados_com_contatos
        }
        payload.update(
            id_produto=dados.produto.id,
            id_status=1,
            id_escritorio=id_escritorio,
            id_origem=dados.origem.id,
            autorizacao=dados.autorizacao,
            nome=dados.nome,
            sobrenome=dados.sobrenome,
            universidade=dados.universidade,
            dataNascimento=dados.dataNascimento,
        )
        return payload


class ExpaLeadPersistenceStrategy(LeadPersistenceStrategy):
    """Monta a persistência completa após a criação do lead no EXPA."""

    def montar(
        self,
        dados: LeadPreCadastroBase,
        dados_com_contatos: dict[str, Any],
        *,
        id_escritorio: int,
        lead_id: int | None = None,
    ) -> LeadPersistencia:
        """Inclui ID do EXPA e meio de atração no DTO completo."""
        if lead_id is None:
            raise ValueError("A estratégia EXPA exige o identificador do lead.")
        payload = self.dados_comuns(dados, dados_com_contatos, id_escritorio)
        payload.update(
            id=lead_id,
            id_meio=dados.meio.id if dados.meio else None,
        )
        return LeadPersistencia.model_validate(payload)


class B2CLeadPersistenceStrategy(LeadPersistenceStrategy):
    """Monta o payload reduzido do cadastro direto B2C."""

    def montar(
        self,
        dados: LeadPreCadastroBase,
        dados_com_contatos: dict[str, Any],
        *,
        id_escritorio: int,
        lead_id: int | None = None,
    ) -> LeadPreCadastroB2CPersistencia:
        """Omite ID EXPA e meio de atração do contrato B2C."""
        if lead_id is not None:
            raise ValueError("A estratégia B2C não recebe identificador EXPA.")
        payload = self.dados_comuns(dados, dados_com_contatos, id_escritorio)
        payload["status"] = "pré-cadastro b2c"
        return LeadPreCadastroB2CPersistencia.model_validate(payload)


__all__ = [
    "B2CLeadPersistenceStrategy",
    "ExpaLeadPersistenceStrategy",
    "LeadPersistenceStrategy",
]
