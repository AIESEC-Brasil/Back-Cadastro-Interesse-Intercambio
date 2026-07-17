"""
Modelos ORM para Mapeamento de Divisão de Mercado.

Define as entidades persistidas na base de dados para o roteamento e controle
de mercado, estruturando a distribuição de Vendas e Talentos.
"""

# ==============================
# Importações (Dependencies)
# ==============================
from app.core import db  # Instância do SQLAlchemy vinculada à aplicação


# ==============================
# Entidade Principal
# ==============================

class Universidades(db.Model):
    """
    Representa uma Instituição Mapeada e o escritório que atende a essa instituição de acordo com o modelo
    de Voluntariado Global (GV) ou Talentos Globais (GT).

    Attributes:
        id (int): Chave primária interna do sistema.
        nome (str): Nome completo ou formatado da instituição.
        gv (str): Destino de roteamento para a área de Voluntariado Global.
        gt (str): Destino de roteamento para a área de Talentos Globais.
    """
    __tablename__ = "instituicoes_mercado"  # Tabela de mapeamento de instituições e seus respectivos escritórios responsáveis

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_as_ci"
    } # Define a codificação e collation para compatibilidade com caracteres especiais e emojis.

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)
    gv = db.Column(db.String(255), nullable=False)
    gt = db.Column(db.String(255), nullable=False)


# ==============================
# Entidades de Contato
# ==============================

class DivisaoCL(db.Model):
    """
    Modelo de configuração de divisão por Comitê Local (CL).

    Armazena as definições de mercado específicas para cada CL,
    mapeando as responsabilidades de GT e GV.
    """
    __tablename__ = "cl_mercado"  # Tabela de configurações globais por Comitê Local

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_as_ci"
    } # Configurações de charset e collation para compatibilidade com caracteres especiais e emojis

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)
    gv = db.Column(db.String(255), nullable=False)
    gt = db.Column(db.String(255), nullable=False)


# ==============================
# Exportações
# ==============================
__all__ = [
    "db",
    "Universidades",
    "DivisaoCL",
]