from marshmallow import Schema, fields

class DivisaoCLSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    gv = fields.Str(required=True)
    gt = fields.Str(required=True)

# Instâncias para uso
divisao_CL_schema = DivisaoCLSchema() # Para um único objeto
divisoes_CL_schema = DivisaoCLSchema(many=True) # Para listas


class DivisaoUniversidadesSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    gv = fields.Str(required=True)
    gt = fields.Str(required=True)

# Instâncias para uso
divisao_Universidades_schema = DivisaoUniversidadesSchema() # Para um único objeto
divisoes_Universidades_schema = DivisaoUniversidadesSchema(many=True) # Para listas

__all__ = [
    "divisao_CL_schema",
    "divisoes_CL_schema",
    "divisao_Universidades_schema",
    "divisoes_Universidades_schema"
]