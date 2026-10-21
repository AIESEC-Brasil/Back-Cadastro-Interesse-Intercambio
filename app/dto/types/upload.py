"""Tipo compartilhado para documentos PDF codificados em Base64."""

from typing import Self

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, field_validator

MAX_PDF_SIZE_BYTES: int = 5 * 1024 * 1024


# ==============================================================================
# VALIDAÇÃO DO ARQUIVO PDF
# ==============================================================================
class UploadItem(BaseModel):
    """Arquivo PDF enviado pelo formulário."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    nome: str = Field(alias="fileName", description="Nome do arquivo PDF")
    base64: Base64Bytes = Field(
        max_length=MAX_PDF_SIZE_BYTES,
        description="Conteúdo do PDF codificado em Base64 (máximo de 5 MiB)",
    )

    @field_validator("nome")
    @classmethod
    def validar_extensao_pdf(cls: type[Self], nome: str) -> str:
        """Exige extensão `.pdf` no nome enviado."""
        if not nome.lower().endswith(".pdf"):
            raise ValueError("O nome do arquivo deve ter a extensão '.pdf'.")
        return nome

    @field_validator("base64")
    @classmethod
    def validar_assinatura_pdf(cls: type[Self], conteudo: bytes) -> bytes:
        """Confere a assinatura do PDF após a decodificação Base64."""
        if not conteudo.startswith(b"%PDF"):
            raise ValueError("O conteúdo enviado não é um arquivo PDF válido.")
        return conteudo


__all__ = ["MAX_PDF_SIZE_BYTES", "UploadItem"]
