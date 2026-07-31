from pydantic import (
    BaseModel,       # Classe base para criação de modelos de dados com validação automática.
    Field,           # Utilizado para definir metadados dos campos, como descrições, aliases e exemplos para o JSON Schema.
    ConfigDict,      # Objeto de configuração para definir comportamentos do modelo (ex: permitir aliases, proibir campos extras).
    model_validator  # Decorador para aplicar regras de validação no nível do modelo completo (múltiplos campos).
)
from typing import (
    Union,  # Hint de tipo que permite que um campo aceite mais de um tipo de dado (ex: datetime OU string).
    Self  # Hint de tipo para representar listas/arrays de elementos de um tipo específico.
)
def validar_dados_produto(nome: str, id_podio: int, id_expa: int) -> Union[bool, str]:
    """
    Valida as chaves de identificação e regras de negócio de um produto de intercâmbio.

    Garante de forma integrada que o título e o ID do Podio façam correspondência estrutural
    no cache de metadados sob a tag 'status' e que o ID correspondente da plataforma internacional
    EXPA esteja listado dentro das categorias oficiais aceitas de intercâmbios ativos.

    Args:
        nome (str): Nome descritivo ou título comercial do programa (Ex: Voluntário Global).
        id_podio (int): Código numérico indexador atribuído ao campo de seleção do Podio.
        id_expa (int): Código internacional mapeado na plataforma global da AIESEC (EXPA).

    Returns:
        bool | str: True se todos os parâmetros passarem nas regras de negócio cruzadas;
                   String com o motivo do erro caso contrário.
    """
    from app.cache import cache
    # Lista de IDs internacionais permitidos e aceitos pelas regras globais (Ex: GV, GT, GE)
    list_id_expa = [7, 8, 9]

    # Variáveis de controle para rastrear onde a validação travou
    tem_produto = False
    tem_id_podio = False
    tem_nome_correto = False

    try:
        # Puxa o estado atualizado dos metadados extraídos da API do Podio
        cache_metadados = cache.store["metadados_card-ogx"]["data"]
        for item in cache_metadados:
            # Localiza o campo chave que gerencia os estados/produtos do formulário
            if item.get("external_id") == "produto":
                tem_produto = True  # Encontrou o bloco de produto

                for opcao in item.get("options", []):
                    # Verifica se o identificador local corresponde ao enviado
                    if opcao.get("id") == id_podio:
                        tem_id_podio = True  # Encontrou o ID do Podio dentro das opções

                        # Valida se o título do produto corresponde ao texto configurado no backend
                        if opcao.get("text", "").strip() == nome.strip():
                            tem_nome_correto = True  # O texto bateu com o ID do Podio

                            # Confirma se o programa está contido na matriz de IDs internacionais permitidos
                            if id_expa in list_id_expa:
                                return True # Todas as 3 pontas de checagem batem com as definições
        # --- Retornos de erro após sair de todos os loops ---
        if not tem_produto:
            return "Não possui o extern_id produto"

        if not tem_id_podio:
            return "ID do Podio informado não foi encontrado nas opções do produto"

        if not tem_nome_correto:
            return "O nome não corresponde ao ID do Podio informado"

        # Se encontrou o produto, o ID e o nome correto, mas o ID EXPA falhou na lista [7, 8, 9]
        if id_expa not in list_id_expa:
            return "ID EXPA inválido!"

    except (NameError, KeyError, TypeError):
        # Trata exceções estruturais defensivamente para evitar quebras abruptas na API
        return "erro"

    return False

class Produto(BaseModel):
    """
    Representa estruturalmente os programas e produtos de intercâmbio comercializados pela AIESEC (GV, GT, GE).

    Esta classe consolida os vínculos de indexação exigidos pelo ecossistema do sistema, possuindo o título do produto,
    o ID numérico interno associado às tabelas de campos do Podio e o identificador global da plataforma internacional EXPA.

    Attributes:
        titulo (str): Nome descritivo comercial do produto de interesse (Ex: voluntario global).
        id_podio (int): ID identificador configurado e mapeado nas opções do campo do Podio.
        id_expa (int): ID de mapeamento internacional da oportunidade na plataforma EXPA.
    """
    model_config = ConfigDict(extra='forbid')
    titulo: str = Field(
        description="Título de identificação do produto",
        json_schema_extra={"example": "voluntario global"}
    )
    id_podio: int = Field(
        description="ID interno do produto indexado no Podio",
        json_schema_extra={"example": 1}
    )
    id_expa: int = Field(
        description="ID do programa correspondente no sistema EXPA",
        json_schema_extra={"example": 7}
    )

    @model_validator(mode="after")
    def verificar_produto_no_cache(self) -> Self | None:
        """
        Validador de negócio executado após a higienização que audita o produto em relação ao cache.

        Garante que o ID do Podio faça correspondência ao título do programa e que o ID EXPA
        seja um produto internacional corporativamente aceito nas regras vigentes.

        Returns:
            Produto: Retorna a instância limpa e autorizada do modelo de Produto.

        Raises:
            ValueError: Caso haja divergência cadastral entre os códigos Podio, EXPA ou nome do programa.
        """
        # Encaminha os três eixos de dados consolidados do modelo para auditoria contra os metadados ativos
        valido = validar_dados_produto(self.titulo, self.id_podio, self.id_expa)

        # Se for um booleano True, o produto está aprovado
        if valido is True:
            return self

        if valido == "Não possui o extern_id produto":
            raise ValueError("Dados Inválidos: Não foi achado a referencia de produto")

        elif valido == "ID do Podio informado não foi encontrado nas opções do produto":
            raise ValueError("Dados Inválidos: O id do podio informado não está presente nos dados")

        elif valido == "O nome não corresponde ao ID do Podio informado":
            raise ValueError("Dados Inválidos: O nome do produto está incoerente")

        elif valido == "ID EXPA inválido!":
            raise ValueError("Dados Inválidos: O id do expa está incoerente")

        elif valido == "erro":
            raise ValueError("Metadados do Podio Não foram baixados")
        return None

__all__ = ["Produto"]