"""
Módulo de Persistência em Memória (Storage).

Este módulo gerencia o armazenamento temporário de endereços IP autorizados,
utilizando o padrão Singleton para garantir que a lista seja consistente
durante todo o ciclo de vida da aplicação.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import logging  # Sistema de logging nativo
from dataclasses import dataclass  # Facilita a criação de classes de dados
from typing import List, Literal  # Tipagens estáticas
from app.dto.output import HttpStatus  # Constantes de status HTTP

# ==============================
# Configurações Globais
# ==============================

# logger: Instanciado no nível do módulo.
# Isso permite que o nome do módulo apareça corretamente nos logs (ex: 'app.core.storage').
logger = logging.getLogger(__name__)


# ==============================
# Classe de Armazenamento
# ==============================

@dataclass
class Storage:
    """
    Controla o acesso e armazenamento de IPs permitidos em memória.

    Attributes:
        __ip (List[str]): Lista privada de endereços IP autorizados.
    """

    def __init__(self):
        """
        Inicializa o container de IPs como uma lista privada vazia.
        """
        # self.__ip: Atributo privado para evitar manipulação externa direta.
        self.__ip: List[str] = []

    def add_ip(self, ip: str) -> tuple[str, Literal[HttpStatus.CONFLICT]] | None:
        """
        Tenta registrar um IP na lista de permissões.

        Caso o IP já exista, a operação é abortada para evitar duplicidade.

        Args:
            ip (str): O endereço IP que deseja-se autorizar.

        Returns:
            tuple: Mensagem de erro e Status Conflict caso o IP já exista.
            None: Caso o IP seja adicionado com sucesso.
        """
        # Log de tentativa: Útil para monitorar quem está tentando se registrar
        logger.info(f"AIESEC Security | Iniciando tentativa de liberação para o IP: {ip}")

        # Verificação de existência (Prevenção de Duplicidade)
        if ip in self.__ip:
            logger.warning(f"AIESEC Security | Falha ao adicionar: O IP {ip} já consta na lista de liberados.")
            return "IP já existe", HttpStatus.CONFLICT

        # Inserção e confirmação
        self.__ip.append(ip)
        logger.info(f"AIESEC Security | Sucesso: IP {ip} foi adicionado à lista de permissões.")

        return None

    def get_ip(self) -> List[str]:
        """
        Retorna a lista atualizada de todos os IPs que possuem acesso.

        Returns:
            List[str]: Cópia ou referência da lista de IPs.
        """
        return self.__ip


# ==============================
# Instanciação (Singleton)
# ==============================

# storage: Objeto global utilizado para compartilhar os IPs entre diferentes middlewares/rotas.
storage = Storage()

# ==============================
# Exportações
# ==============================
__all__ = ['storage']