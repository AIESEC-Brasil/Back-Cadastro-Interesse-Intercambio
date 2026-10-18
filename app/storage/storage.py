"""Módulo de Persistência em Memória (Storage).

Este módulo gerencia o armazenamento temporário de endereços IP autorizados,
utilizando o padrão Singleton para garantir que a lista seja consistente
durante todo o ciclo de vida da aplicação.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
from dataclasses import dataclass, field  # Decorador e utilitários para classes de dados
import logging  # Sistema de logging nativo do Python
from typing import List, Literal, Optional, Tuple  # Tipagens estáticas

from app.dto.output import HttpStatus  # Constantes de status HTTP da aplicação

# =================================================================
# 2. CONFIGURAÇÕES GLOBAIS E LOGGING
# =================================================================

# Instanciação do logger no nível do módulo (ex: 'app.core.storage')
logger = logging.getLogger(__name__)


# =================================================================
# 3. CLASSE DE ARMAZENAMENTO (STORAGE)
# =================================================================

@dataclass
class Storage:
    """Controla o acesso e armazenamento de IPs permitidos em memória.

    Attributes:
        _Storage__ip (List[str]): Lista privada de endereços IP autorizados.
    """

    # Atributo privado inicializado via field para evitar mutabilidade padrão
    __ip: List[str] = field(default_factory=list, init=False)

    def __init__(self) -> None:
        """Inicializa o container de IPs como uma lista privada vazia."""
        self.__ip: List[str] = []

    def add_ip(
            self, ip: str
    ) -> Optional[Tuple[str, Literal[HttpStatus.CONFLICT]]]:
        """Tenta registrar um endereço IP na lista de permissões em memória.

        Caso o IP já exista, a operação é abortada para evitar duplicidade.

        Args:
            ip (str): O endereço IP que se deseja autorizar.

        Returns:
            Optional[Tuple[str, Literal[HttpStatus.CONFLICT]]]:
                Retorna uma tupla contendo (mensagem_erro, HttpStatus.CONFLICT)
                caso o IP já esteja cadastrado. Retorna None em caso de sucesso.
        """
        # Log de auditoria: Monitora solicitações de adição de IP
        logger.info(
            f"AIESEC Security | Iniciando tentativa de liberação para o IP: {ip}"
        )

        # Verificação de existência para prevenção de duplicidade
        if ip in self.__ip:
            logger.warning(
                f"AIESEC Security | Falha ao adicionar: O IP {ip} já consta na lista de liberados."
            )
            return "IP já existe", HttpStatus.CONFLICT

        # Inserção e confirmação no storage em memória
        self.__ip.append(ip)
        logger.info(
            f"AIESEC Security | Sucesso: IP {ip} foi adicionado à lista de permissões."
        )

        return None

    def get_ip(self) -> List[str]:
        """Retorna uma cópia atualizada da lista de todos os IPs que possuem acesso.

        Returns:
            List[str]: Cópia da lista contendo os endereços IP autorizados.
        """
        # Retorna uma cópia (.copy()) para proteger o atributo privado contra mutação externa
        return self.__ip.copy()


# =================================================================
# 4. INSTANCIAÇÃO SINGLETON
# =================================================================

# Objeto global compartilhado entre diferentes middlewares e rotas
storage = Storage()


# =================================================================
# 5. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["storage"]