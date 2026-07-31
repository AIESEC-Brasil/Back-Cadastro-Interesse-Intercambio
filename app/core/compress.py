"""Módulo de Configuração do Flask-Compress.

Inicialização da extensão Flask-Compress para otimização de respostas HTTP.
Realiza a compactação automática (gzip/brotli) dos payloads para redução
de latência e consumo de banda.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
# A extensão Compress intercepta as respostas Flask e aplica compactação
from flask_compress import Compress

# =================================================================
# 2. INSTÂNCIA GLOBAL DO FLASK-COMPRESS
# =================================================================

# Instanciação do objeto central de compressão.
# Nota de arquitetura: No arquivo principal da aplicação (app.py ou Application Factory),
# ele deve ser vinculado ao app através do método `compress.init_app(app)`.
compress = Compress()


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = [
    "compress",  # Instância global do otimizador de compressão HTTP
]