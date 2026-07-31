from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    EmailStr,        # Tipo de campo especializado que valida se a string segue o formato de e-mail (RFC 5322).
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
    field_serializer,# Decorador que permite customizar como um campo específico é convertido para JSON (ex: formatar datas).
    field_validator, # Decorador que permite definir funções de validação customizadas para campos específicos, garantindo integridade dos dados.
    TypeAdapter,     # Permite criar adaptadores de tipo para conversão e validação de dados complexos.
    model_validator  # Decorador para aplicar regras de validação no nível do modelo completo (múltiplos campos).
)

class Universidade(BaseModel):
    id: int = Field(...,description="Id da Universidade no Banco de Dados",json_schema_extra={"exemple":1})
    nome:str = Field(...,description="Nome da Universidade no Banco de Dados",json_schema_extra={"exemple":"Universidade Federal de Pernambuco"})

    model_config = ConfigDict(extra='ignore')

__all__ = ["Universidade"]