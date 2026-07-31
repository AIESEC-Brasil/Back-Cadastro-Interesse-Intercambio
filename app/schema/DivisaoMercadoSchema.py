"""Esquemas de serialização e desserialização Marshmallow.

Define as estruturas de validação e transformação de dados (Schemas) para
divisões de escritórios locais (CLs) e universidades da aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from marshmallow import Schema, fields  # Biblioteca de serialização e validação de dados


# =================================================================
# 2. ESQUEMA DE DIVISÃO DE CLs (ESCRITÓRIOS LOCAIS)
# =================================================================

class DivisaoCLSchema(Schema):
    """Esquema Marshmallow para serialização/validação de Divisão de CL."""

    id = fields.Int(dump_only=True)  # ID gerado no banco (apenas leitura/serialização)
    nome = fields.Str(required=True)  # Nome do escritório local (obrigatório)
    gv = fields.Str(required=True)    # Código/Sigla para a área de Global Volunteer (obrigatório)
    gt = fields.Str(required=True)    # Código/Sigla para a área de Global Talent (obrigatório)


# Instâncias reutilizáveis do esquema de CL
divisao_cl_schema = DivisaoCLSchema()          # Instância para um único objeto
divisoes_cl_schema = DivisaoCLSchema(many=True)  # Instância para coleções/listas de objetos


# =================================================================
# 3. ESQUEMA DE DIVISÃO DE UNIVERSIDADES
# =================================================================

class DivisaoUniversidadesSchema(Schema):
    """Esquema Marshmallow para serialização/validação de Divisão de Universidades."""

    id = fields.Int(dump_only=True)  # ID gerado no banco (apenas leitura/serialização)
    nome = fields.Str(required=True)  # Nome da instituição/universidade (obrigatório)
    gv = fields.Str(required=True)    # Código/Sigla para a área de Global Volunteer (obrigatório)
    gt = fields.Str(required=True)    # Código/Sigla para a área de Global Talent (obrigatório)


# Instâncias reutilizáveis do esquema de Universidades
divisao_universidades_schema = DivisaoUniversidadesSchema()          # Instância para um único objeto
divisoes_universidades_schema = DivisaoUniversidadesSchema(many=True)  # Instância para coleções/listas de objetos


# =================================================================
# 4. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "DivisaoCLSchema",
    "DivisaoUniversidadesSchema",
    "divisao_cl_schema",
    "divisoes_cl_schema",
    "divisao_universidades_schema",
    "divisoes_universidades_schema",
]