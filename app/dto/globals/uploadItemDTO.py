"""
Submódulo de DTO para Upload e Validação de Arquivos PDF.

Fornece o modelo `UploadItem` para recepção de arquivos enviados em Base64,
garantindo a integridade da extensão do arquivo (.pdf) e da assinatura digital (%PDF).
"""

# =================================================================
# 1. IMPORTAÇÕES E MÓDULOS NATIVOS
# =================================================================

# Módulo nativo do Python para suporte a anotações de tipos
from typing import Optional

# Importações do Pydantic (versão 2) utilizadas na construção e validação da estrutura de dados:
from pydantic import (
    BaseModel,        # Classe base para a criação de modelos de dados estruturados
    Base64Bytes,      # Tipo do Pydantic que valida a string Base64 e a converte automaticamente para o tipo 'bytes'
    Field,            # Função para definir metadados (alias, exemplos, descrição, limites) e regras específicas do campo
    ConfigDict,       # Dicionário de configuração para personalizar o comportamento global do modelo
    field_validator   # Decorador utilizado para criar funções auxiliares/validadores customizados para campos específicos
)

# =================================================================
# 2. CONSTANTES E CONFIGURAÇÕES GLOBAIS
# =================================================================

# Constante global que define o limite máximo do arquivo: 10 Megabytes (10 * 1024 * 1024 bytes)
# 1 MB = 1024 * 1024 bytes
# 2 MB = 2 * 1024 * 1024 bytes
# ......
# 10 MB = 10 * 1024 * 1024 bytes
TAMANHO_MAXIMO_10MB = 10 * 1024 * 1024


# =================================================================
# 3. ESTRUTURA DO MODELO (DTO)
# =================================================================

class UploadItem(BaseModel):
    """
    Modelo Pydantic para validação e recepção de upload de arquivos PDF via Base64.

    Atributos:
        nome (str): Nome do arquivo recebido (obrigatoriamente com extensão .pdf).
        base64 (bytes): Conteúdo do arquivo decodificado em bytes brutos e validado como PDF.
    """

    # Configuração global do modelo no Pydantic v2
    model_config = ConfigDict(
        # Permite instanciar o modelo aceitando tanto 'fileName' (alias do JS) quanto 'nome' (convenção Python)
        populate_by_name=True,
        # Lança erro de validação se forem enviados campos extras no JSON que não estejam mapeados neste modelo
        extra="forbid"
    )

    # 1. Campo para o nome do arquivo (Mapeia a chave 'fileName' enviada pelo front-end)
    nome: str = Field(
        ...,  # Os três pontos (...) indicam que este campo é estritamente obrigatório (não aceita None)
        alias="fileName",  # Chave esperada no payload JSON vindo do JavaScript
        description="Nome do arquivo enviado. Deve possuir obrigatoriamente a extensão .pdf.",
        json_schema_extra={"example": "curriculo_joao.pdf"}  # Exemplos exibidos na documentação automática (Swagger/OpenAPI)
    )

    # 2. Campo para o conteúdo do arquivo em Base64 (O Pydantic converte automaticamente a string para bytes)
    base64: Base64Bytes = Field(
        ...,  # Campo obrigatório
        max_length=TAMANHO_MAXIMO_10MB,  # Limite máximo de tamanho do arquivo em bytes após ser decodificado
        description="String formatada em Base64 do arquivo. O Pydantic valida e converte para bytes brutos.",
        json_schema_extra={"example": "JVBERi0xLjQKJ..."}  # Exemplo de string Base64 iniciando com a codificação do cabeçalho PDF (%PDF)
    )

    # =================================================================
    # 4. FUNÇÕES AUXILIARES / VALIDADORAS DE CAMPO
    # =================================================================

    @field_validator("nome")
    @classmethod
    def validar_extensao_pdf(cls, v: str) -> str:
        """
        Função auxiliar para validar o nome do arquivo.

        Parâmetros:
            v (str): O valor do nome do arquivo fornecido na requisição.

        Retorna:
            str: O próprio nome do arquivo caso a validação seja bem-sucedida.

        Exceções:
            ValueError: Se o nome do arquivo não terminar com a extensão '.pdf'.
        """
        # Converte o nome para letras minúsculas (.lower()) para aceitar tanto '.pdf' quanto '.PDF' ou '.Pdf'
        if not v.lower().endswith(".pdf"):
            # Lança exceção de valor inválido que o Pydantic captura e formata no erro HTTP 422
            raise ValueError("O nome do arquivo deve ter a extensão '.pdf'.")

        # Retorna o valor limpo e validado
        return v

    @field_validator("base64")
    @classmethod
    def validar_conteudo_pdf(cls, v: bytes) -> bytes:
        """
        Função auxiliar para validar a assinatura interna do arquivo (Magic Bytes).

        Parâmetros:
            v (bytes): O conteúdo do arquivo já decodificado pelo Pydantic de Base64 para bytes.

        Retorna:
            bytes: Os bytes originais do arquivo caso seja um PDF válido.

        Exceções:
            ValueError: Se os primeiros bytes do arquivo não corresponderem à assinatura padrão de PDFs (b'%PDF').
        """
        # Checa se os primeiros 4 bytes do arquivo começam com 'b"%PDF"' (Assinatura oficial de arquivos PDF)
        if not v.startswith(b"%PDF"):
            # Lança erro caso o usuário tente enviar uma imagem ou arquivo renomeado falsamente como PDF
            raise ValueError("O conteúdo enviado não é um arquivo PDF válido ou está corrompido.")

        # Retorna os bytes do arquivo validados e prontos para uso/armazenamento
        return v


# =================================================================
# 5. EXPORTAÇÃO CONSOLIDADA DO MÓDULO
# =================================================================

__all__ = ["UploadItem"]