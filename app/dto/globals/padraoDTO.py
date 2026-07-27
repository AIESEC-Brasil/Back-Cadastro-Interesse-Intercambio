"""
Módulo de Submodelos de Apoio para DTOs (Data Transfer Objects).

Este arquivo define estruturas de dados compartilhadas que compõem múltiplos
objetos de transferência de dados no sistema, garantindo validação rigorosa
e formatação amigável para integração com APIs (ex: Podio) e interfaces de usuário.
"""

# =================================================================
# 1. IMPORTAÇÕES (DEPENDÊNCIAS)
# =================================================================
import re  # Módulo padrão para operações com expressões regulares (validações de string)
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
from pydantic_core import (
    core_schema      # Fornece acesso às estruturas de baixo nível do Pydantic para criar validadores customizados complexos.
)
from enum import (
    Enum,            # Classe base para criar enumeradores de strings, garantindo conjuntos fixos de opções.
    IntEnum          # Variante de enumerador onde os membros são comparáveis a inteiros, ideal para flags numéricas.
)
from typing import (
    Dict,  # Hint de tipo para representar dicionários (mapeamentos chave-valor) nas assinaturas de métodos.
    Any,  # Hint de tipo especial que indica que um valor pode ser de qualquer natureza (dinâmico).
    Union,  # Hint de tipo que permite que um campo aceite mais de um tipo de dado (ex: datetime OU string).
    List, Self  # Hint de tipo para representar listas/arrays de elementos de um tipo específico.
)
from datetime import (
    datetime,        # Objeto padrão para manipulação de carimbos de data e hora (timestamp).
    date             # Objeto padrão para manipulação de datas calendárias (dia, mês, ano).
)

# =================================================================
# 2. ENUMS E TIPOS CONSTANTES
# =================================================================

class CategoriaContato(str, Enum):
    """
    Categorias de contato aceitas, padronizadas para integração com o Podio.

    Herda de (str, Enum) para garantir a serialização correta como string no JSON
    e permitir comparações diretas com strings em estruturas condicionais.

    Attributes:
        HOME (str): Representa contatos residenciais ou de escopo puramente pessoal.
        WORK (str): Representa contatos corporativos ou de uso profissional.
        MOBILE (str): Representa linhas telefônicas móveis/celulares.
        MAIN (str): Indica o canal de contato principal do cliente.
        OTHER (str): Categoria genérica para cenários não previstos nas demais chaves.
        PRIVATE_FAX (str): Linha de fax privada de uso pessoal.
        WORK_FAX (str): Linha de fax corporativa de uso comercial.
    """
    HOME = "home"                 # Uso residencial/pessoal
    WORK = "work"                 # Uso profissional/corporativo
    MOBILE = "mobile"             # Dispositivo móvel/celular
    MAIN = "main"                 # Contato principal
    OTHER = "other"               # Outras categorias não listadas
    PRIVATE_FAX = "private_fax"   # Fax pessoal
    WORK_FAX = "work_fax"         # Fax profissional


class Autorizacao(IntEnum):
    """
    Enumeração para representação binária de estados de consentimento e autorização.

    Esta classe utiliza IntEnum para garantir que os valores internos sejam estritamente
    inteiros (0 ou 1), facilitando a persistência limpa e direta em APIs de terceiros
    (como o ecossistema do Podio) e em bancos de dados que interpretam flags numéricas.

    Members:
        SIM (int): Indica consentimento e autorização explicitamente concedidos (1).
        NAO (int): Indica consentimento ou autorização expressamente negados/revogados (0).
    """
    SIM = 1  # Valor inteiro representando autorização concedida
    NAO = 0  # Valor inteiro representando autorização negada


# =================================================================
# 3. FUNÇÕES AUXILIARES DE VALIDAÇÃO (PROJETADAS PARA O CACHE/REGEX)
# =================================================================

def validar_email(email: str) -> bool:
    """
    Valida se a string fornecida corresponde a um padrão estrutural sintático de e-mail válido.

    A expressão regular valida o formato local, a presença do caractere separador '@',
    a existência de um domínio base válido e extensões de topo (TLD) com no mínimo 2 letras.

    Args:
        email (str): O endereço de e-mail em formato textual que passará pela validação.

    Returns:
        bool: Retorna True se o e-mail possuir formato estrutural correto;
              Retorna False se estiver vazio, for nulo ou falhar no casamento com o Regex.
    """
    # Validação defensiva precoce: se a string estiver vazia ou nula, retorna falso
    if not email or email == "":
        return False

    # Expressão regular flexível: permite múltiplos subdomínios (ex: .org.br, .com.br)
    # e aceita TLDs longos de novas extensões de internet (ex: .online, .digital) através do {2,}
    regex_email: str = r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$'

    # Executa o casamento estrito da string inteira com o padrão configurado
    return bool(re.fullmatch(regex_email, email))


def validar_telefone(telefone: str) -> bool:
    """
    Valida se a string corresponde a um número de telefone celular brasileiro (DDD + 9 dígitos).

    Esta validação impõe regras nacionais restritas: a string deve conter exatamente 11 caracteres
    numéricos, ignorando os códigos do país (+55). O DDD não pode começar com zero e o dígito
    identificador de celular nacional deve ser obrigatoriamente 9.

    Args:
        telefone (str): String numérica do telefone que será submetida à validação.

    Returns:
        bool: True se o formato respeitar o padrão DD9XXXX-XXXX;
              False se estiver fora da especificação nacional ou vazio.
    """
    # Retorna falso se a entrada for vazia
    if not telefone or telefone == "":
        return False

    # Explicação detalhada do padrão Regex:
    # ^[1-9]{2} -> Garante 2 dígitos de DDD de 11 a 99 (evitando que iniciem com 0)
    # 9         -> Exige o nono dígito fixo obrigatório para telefones móveis do Brasil
    # [0-9]     -> Permite qualquer variação no primeiro dígito do bloco de numeração móvel
    # \d{7}$    -> Captura os 7 dígitos numéricos finais, selando o encerramento do padrão
    padrao: str = r'^[1-9]{2}9[0-9]\d{7}$'

    # Realiza a checagem posicional absoluta do início ao fim da string
    return bool(re.fullmatch(padrao, telefone))


def validar_dados_comite(id_comite: int, nome_comite: str) -> Union[bool, str]:
    """
    Varre a base de dados do cache local de metadados para confirmar a integridade de um comitê.

    Verifica de forma cruzada se o ID informado existe dentro do escopo do campo 'aiesec-mais-proxima'
    e se o nome correspondente naquele nó de dados é equivalente ao nome enviado pelo payload da API.

    Args:
        id_comite (int): Identificador numérico inteiro que descreve a unidade local.
        nome_comite (str): Nome descritivo da unidade fornecido pelo usuário ou formulário.

    Returns:
        bool | str: True se a chave e o valor coincidirem exatamente com os registros do cache;
                   String com a mensagem exata do erro caso contrário.
    """
    from app.cache import cache

    # Variáveis de controle para rastrear onde a validação falhou
    tem_comite = False
    tem_id_comite = False

    try:
        # Acessa profundamente a estrutura de dicionários aninhados salvos no repositório de cache
        cache_metadados = cache.store["metadados_card-ogx"]["data"]

        # Percorre os blocos de configuração contidos no JSON retornado
        for item in cache_metadados:
            # Filtra apenas o bloco de chaves mapeado para a seletora de comitês locais da AIESEC
            if item.get("external_id") == "aiesec-mais-proxima":
                tem_comite = True  # Encontrou o bloco do comitê no cache

                # Itera sobre o array de opções ativas configuradas no Podio para este campo
                for opcao in item.get("options", []):
                    # Localiza o nó cujo identificador seja idêntico ao ID que estamos validando
                    if opcao.get("id") == id_comite:
                        tem_id_comite = True  # O ID enviado existe nas opções

                        # Realiza o isolamento de strings limpando lacunas de espaçamento antes da igualdade
                        if opcao.get("text", "").strip() == nome_comite.strip():
                            return True  # Validação bem-sucedida: par ID e Nome é idêntico ao oficial

        # --- Retornos de erro exatos após sair de todos os loops ---
        if not tem_comite:
            return "Não possui o extern_id aiesec-mais-proxima"

        if not tem_id_comite:
            return "ID do comitê informado não foi encontrado nas opções"

        # Se encontrou o bloco e o ID, mas o fluxo não retornou True, o nome está errado
        return "O nome do comitê não corresponde ao ID informado"

    except (NameError, KeyError, TypeError):
        # Captura e neutraliza exceções de escopo ou de estrutura nula caso o cache não esteja carregado
        return "Erro interno ao processar a estrutura do cache do comitê"

    return False


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
        return "Erro interno ao processar a estrutura do cache"

    return False


# =================================================================
# 4. SUB-MODELOS DE APOIO (DTOs)
# =================================================================

class EmailItem(BaseModel):
    """
    Estrutura para itens de e-mail categorizados e validados.

    Esta classe gerencia pares contendo a categoria do canal de contato digital (tipo)
    e o endereço eletrônico correspondente, aplicando filtros estritos para impedir
    que e-mails utilizem marcações exclusivas de telefonia fixa ou móvel.

    Attributes:
        tipo (CategoriaContato): Classificação da etiqueta de contato (ex: 'home', 'work').
        email (EmailStr): O endereço de e-mail validado sintática e estruturalmente pelas RFCs.
    """
    tipo: CategoriaContato = Field(description="Categoria ou etiqueta do e-mail")
    email: EmailStr = Field(
        description="Endereço de e-mail em formato válido",
        json_schema_extra={
            "example": "teste@gmail.com"
        }
    )

    @field_validator('tipo', mode="before")
    @classmethod
    def tipo_valido(cls, tipo: CategoriaContato) -> CategoriaContato:
        """
        Validador que barra a atribuição de etiquetas de telefonia ou fax para instâncias de e-mail.

        Args:
            tipo (CategoriaContato): Categoria informada antes da consolidação do objeto.

        Returns:
            CategoriaContato: A categoria higienizada aprovada.

        Raises:
            ValueError: Se a categoria informada pertencer ao grupo exclusivo de mobile ou fax.
        """
        # Define o conjunto de chaves de enumeração cujo uso é restrito a canais de voz/telefonia
        lista_exclusivo_tipo_mobile = {
            CategoriaContato.MOBILE,
            CategoriaContato.MAIN,
            CategoriaContato.PRIVATE_FAX,
            CategoriaContato.WORK_FAX
        }

        # Bloqueia a criação do modelo caso o usuário tente associar uma etiqueta de celular a um e-mail
        if tipo in lista_exclusivo_tipo_mobile:
            raise ValueError(f"A categoria '{tipo}' não é permitida para endereços de e-mail.")
        return tipo

    @field_validator('email', mode="before")
    @classmethod
    def email_valido(cls, email: Any) -> Any:
        """
        Intercepta o e-mail bruto recebido no payload para fins de higienização de strings e pré-validação.

        Executa o isolamento e remoção de espaços em branco antes que o motor de tipos
        do Pydantic faça o processamento nativo do `EmailStr`.

        Args:
            email (Any): O valor do e-mail capturado na forma original em que foi transmitido.

        Returns:
            Any: String limpa se passar nos filtros regex customizados.

        Raises:
            ValueError: Se a entrada estiver nula, em branco ou possuir formato inválido.
        """
        # Converte o dado de entrada para string padrão e remove espaços invisíveis das bordas
        email_str = str(email).strip() if email else ""

        # Aciona o motor regex auxiliar para verificar se o e-mail possui corpo e formato válidos
        if validar_email(email_str):
            return email_str
        raise ValueError("O email não é um e-mail válido ou está em branco")


class TelefoneItem(BaseModel):
    """
    Estrutura para itens de telefone e celular compatível com as especificações da API do Podio.

    Mapeia os dados brutos de entrada para uma estrutura limpa e tipada contendo a etiqueta
    do telefone e o número formatado puramente como string numérica, incluindo obrigatoriamente o DDD.

    Attributes:
        tipo (CategoriaContato): Tipo de classificação do telefone (Ex: CategoriaContato.MOBILE).
        numero (str): String numérica contendo o DDD e o número telefônico limpos.
    """
    tipo: CategoriaContato = Field(description="Categoria do telefone")
    numero: str = Field(
        description="Número do telefone com DDD",
        json_schema_extra={
            "example": "81999999999"
        }
    )

    @field_validator('numero', mode="before")
    @classmethod
    def telefone_valido(cls, numero: Any) -> str:
        """
        Intercepta, limpa e valida a string de telefone recebida no payload bruto.

        Garante que espaços adicionais não quebrem a validação e aciona a regra
        de expressão regular do padrão celular nacional brasileiro.

        Args:
            numero (Any): O dado cru enviado no campo de número do telefone.

        Returns:
            str: O número telefônico higienizado contendo apenas dígitos numéricos válidos.

        Raises:
            ValueError: Se o telefone for nulo, vazio ou falhar no padrão nacional de 11 dígitos.
        """
        # Executa limpeza removendo espaços em branco extras que costumam vir de inputs de formulários
        num_str = str(numero).strip() if numero else ""

        # Consulta a função nacional de checagem para aprovar ou rejeitar o número de telefone móvel
        if validar_telefone(num_str):
            return num_str
        raise ValueError("O telefone não é um número válido ou está em branco")


class Comite(BaseModel):
    """
    Representa formalmente um Comitê Local (Unidade operacional da AIESEC) dentro do ecossistema.

    Esta classe realiza validação cruzada tardia (`mode="after"`) garantindo que nenhuma entidade
    seja criada se o ID numérico local e o Nome descritivo da filial não tiverem uma correspondência
    exata e idêntica na tabela de metadados ativa do cache do sistema.

    Attributes:
        id (int): Código numérico indexador único que identifica o comitê local.
        nome (str): Nome amigável de exibição da praça regional da unidade (Ex: Recife (PE)).
    """
    id: int = Field(
        description="ID interno numérico da entidade",
        json_schema_extra={"example": 32}
    )
    nome: str = Field(
        description="Nome amigável da unidade (Comitê Local)",
        json_schema_extra={"example": "Recife(PE)"}
    )

    @model_validator(mode="after")
    def verificar_comite_no_cache(self) -> "Comite":
        """
        Validador de negócio executado após a higienização que audita o comitê em relação ao cache.

        Garante de forma cruzada que o ID informado exista no escopo correto e que o nome
        corresponda exatamente à unidade cadastrada no cache de metadados do Podio.

        Returns:
            Comite: Retorna a instância limpa e autorizada do modelo de Comitê.

        Raises:
            ValueError: Caso haja divergência cadastral entre o ID do comitê e o nome informado.
        """
        # Encaminha as chaves consolidadas do modelo para auditoria contra os metadados ativos
        valido = validar_dados_comite(self.id_comite, self.nome_comite)

        if valido is True:
            return self

        # Comparação idêntica caractere por caractere
        if valido == "Não possui o extern_id aiesec-mais-proxima":
            raise ValueError("Dados Inválidos: Não foi achada a referência de comitê local")

        elif valido == "ID do comitê informado não foi encontrado nas opções":
            raise ValueError("Dados Inválidos: O id do comitê informado não está presente nos dados")

        elif valido == "O nome do comitê não corresponde ao ID informado":
            raise ValueError("Dados Inválidos: O nome do comitê está incoerente")

        elif valido == "Erro interno ao processar a estrutura do cache do comitê":
            raise ValueError("Dados Inválidos: Falha de comunicação com a estrutura de cache")

        return None


class DataNascimento:
    """
    Classe utilitária avançada para validação, normalização e parsing de datas de nascimento.

    Esta classe não herda de `BaseModel` por design estrutural; ela é configurada para injetar
    comportamentos diretamente no núcleo do Pydantic v2 (`CoreSchema`), agindo como um tipo de dado primitivo
    customizado que retorna uma instância pura de `datetime`, eliminando chaves aninhadas desnecessárias no JSON final.
    """
    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """
        Injeta a lógica de pré-validação customizada da classe dentro do fluxo de tipagem do Pydantic v2.

        Associa a função estática `cls.validar` para rodar imediatamente antes do interpretador consolidar
        a estrutura final baseada no esquema nativo de data e hora (`datetime_schema`).
        """
        return core_schema.no_info_before_validator_function(
            cls.validar,
            core_schema.datetime_schema(),
        )

    @staticmethod
    def validar(value: Any) -> datetime:
        """
        Executa a normalização cronológica de strings temporais, impedindo inclusive registros em datas futuras.

        Suporta múltiplos formatos de entrada de mercado, incluindo strings de data pura (YYYY-MM-DD),
        data e hora completas, e strings contendo marcação de fuso horário ISO 8601 (suportando o caractere de sufixo Z).

        Args:
            value (Any): O valor de data bruto oriundo da requisição ou do banco.

        Returns:
            datetime: Objeto padrão datetime nativo do Python após o parse com sucesso.

        Raises:
            ValueError: Se a string não casar com nenhum formato temporal suportado ou se a data for futura.
        """
        nascimento = value

        # Se a entrada recebida for uma string textual, inicia o ciclo de conversões experimentais
        if isinstance(value, str):
            # Varre os formatos tradicionais de tempo usados na comunicação interna da aplicação
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    nascimento = datetime.strptime(value, fmt)
                    break  # Converteu com sucesso: interrompe o laço de tentativas imediatamente
                except ValueError:
                    continue  # Falhou no formato atual: testa o próximo item do array

            # Caso os formatos tradicionais falhem, processa o dado usando as especificações da ISO 8601
            if isinstance(nascimento, str):
                try:
                    # Substitui o sufixo 'Z' (Zulu Time) pelo offset equivalente padrão (+00:00) exigido pelo fromisoformat
                    nascimento = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Formato de data inválido: {value}")

        # Se o dado foi convertido ou já veio originalmente como um objeto datetime
        if isinstance(nascimento, datetime):
            # Bloqueio de integridade cronológica: a data civil de nascimento nunca pode ser maior que o dia de hoje
            if nascimento.date() > date.today():
                raise ValueError("A data de nascimento não pode ser uma data futura.")
            return nascimento  # Retorna o objeto cronológico perfeitamente estabelecido

        raise ValueError("Tipo de dado inválido para data de nascimento.")


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

        return None


class DivisaoMercado(BaseModel):
    """
    Estrutura para representar o mapeamento e divisão de mercado por Comitê Local ou Instituição de Ensino.

    Utiliza aliases customizados para realizar o parse direto de chaves que contém caracteres especiais e espaços
    vinda de payloads externos estruturados (Ex: dicionários estruturados com a chave 'Voluntario Global').

    Attributes:
        id (int): Identificador interno sequencial da linha de divisão.
        nome (str): Nome amigável da divisão de captação (Ex: nome da universidade ou CL parceiro).
        gv (str): Nome da unidade responsável pelo roteamento de leads do programa Voluntariado Global.
        gt (str): Nome da unidade responsável pelo roteamento de leads do programa Talentos Globais.
    """
    id: int = Field(
        description="ID interno numérico da divisão de mercado",
        json_schema_extra={"example": 1}
    )
    nome: str = Field(
        description="Nome amigável da divisão (CL ou Instituição vinculada)",
        json_schema_extra={"example": "Recife(PE)"}
    )
    gv: str = Field(
        alias="Voluntario Global",  # Vincula a chave descritiva com espaços ao atributo compacto do Python
        description="Destino de routing para leads de Voluntariado Global",
        json_schema_extra={"example": "AIESEC em Recife"}
    )
    gt: str = Field(
        alias="Talento Global",     # Vincula a chave descritiva com espaços ao atributo compacto do Python
        description="Destino de routing para leads de Talentos Globais",
        json_schema_extra={"example": "AIESEC em Recife"}
    )

    # Injeta configurações globais no modelo Pydantic v2
    # populate_by_name=True permite preencher o modelo tanto passando o nome do atributo ('gv') quanto o alias ('Voluntario Global')
    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def processar_lista(cls, dados: Any) -> list:
        """
        Método de processamento dinâmico em lote para listas de dados de divisão de mercado.

        Instancia um adaptador de tipo dedicado para converter coleções, valida os dados e executa
        o dump convertendo as propriedades de volta para o formato esperado com aliases (chaves com espaços).

        Args:
            dados (Any): Coleção/Lista de dicionários contendo os dados brutos de mercado.

        Returns:
            list: Lista de dicionários reestruturada e serializada com os aliases oficiais aplicados.
        """
        # Cria em tempo de execução um adaptador especializado baseado no contexto dinâmico da classe (cls)
        adapter = TypeAdapter(List[cls])

        # Realiza a validação contra os esquemas da classe e exporta o JSON forçando o uso das chaves com aliases nativos
        return adapter.dump_python(adapter.validate_python(dados), by_alias=True)


# =================================================================
# 5. EXPORTAÇÕES DO MÓDULO
# =================================================================

# Define de forma estrita quais símbolos serão exportados ao utilizar padrões globais como 'from ... import *'
__all__ = [
    "Comite",
    "TelefoneItem",
    "EmailItem",
    "Autorizacao",
    "DataNascimento",
    "DivisaoMercado",
    "Produto"
]