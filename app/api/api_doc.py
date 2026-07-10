"""
API Router
----------
Ponto central de agregação de rotas.
Responsável por versionar a API e organizar os prefixos de URL.
"""

# ==============================
# Importações (Dependencies)
# ==============================
import os  # Manipulação de variáveis de ambiente e sistema operacional

from flask import render_template_string, request
from app.controller.router import Router
from ..dto import HttpStatus
from ..storage import storage
# =================================================================
# CONFIGURAÇÃO DE ROTEAMENTO GLOBAL
# =================================================================

# Inicializa o roteador principal com o prefixo global '/api'.
api = Router(name="api", url_prefix="/api")


@api.get("/docs",description="Página HTML da Documentação",responses={200:None})
def documentacao() -> str:
    """
    Página de documentação estilizada com a identidade AIESEC.
    """

    # Rotas organizadas por tipo - Completo com extensões YAML e Assets
    rotas = {
        "Swagger & OAuth": [
            "/openapi/swagger",
            "/openapi/swagger/<path:filename>",
            "/openapi/oauth2-redirect.html",
        ],
        "Scalar, Redoc & Elements": [
            "/openapi/scalar",
            "/openapi/redoc",
            "/openapi/elements",
            "/openapi/elements/<path:filename>",
            "/openapi/redoc/<path:filename>",
            "/openapi/scalar/<path:filename>"
        ],
        "RapiDoc & RapiPDF": [
            "/openapi/rapidoc",
            "/openapi/rapidoc/<path:filename>",
            "/openapi/rapipdf",
            "/openapi/rapipdf/<path:filename>"
        ],
        "Especificações (JSON/GERAL)": [
            "/openapi/openapi.json",
            "/openapi",  # Root da spec
        ],
        "Arquivos Estáticos & Assets": [
            "/static/<path:filename>",
            "/openapi/static/<path:filename>",
        ]
    }

    template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Documentation | AIESEC Hub</title>
        <style>
            :root {
                --aiesec-blue: #037EF3;
                --aiesec-dark-blue: #0056b3;
                --aiesec-light-grey: #F3F4F6;
                --text-color: #52565E;
                --success-green: #00C16E;
            }
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: var(--aiesec-light-grey);
                color: var(--text-color);
                margin: 0;
                padding: 0;
            }
            header {
                background: white;
                padding: 40px 20px;
                text-align: center;
                border-bottom: 4px solid var(--aiesec-blue);
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            .logo {
                font-weight: bold;
                font-size: 28px;
                color: var(--aiesec-blue);
                letter-spacing: -1px;
                margin-bottom: 10px;
                display: block;
            }
            .tagline {
                font-style: italic;
                color: #888;
                margin-bottom: 20px;
            }
            .container {
                max-width: 1100px;
                margin: 40px auto;
                padding: 0 20px;
            }
            .intro-text {
                text-align: center;
                margin-bottom: 40px;
            }
            .intro-text p {
                font-size: 1.1em;
                line-height: 1.6;
            }
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 25px;
            }
            .card {
                background: white;
                border-radius: 8px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                border-top: 1px solid #eee;
            }
            .card h2 {
                font-size: 19px;
                color: var(--aiesec-blue);
                margin-top: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .card h2::before {
                content: '◈';
                font-size: 12px;
            }
            .card ul {
                list-style: none;
                padding: 0;
                margin: 15px 0;
            }
            .card li {
                margin: 8px 0;
            }
            .card a {
                color: var(--text-color);
                text-decoration: none;
                font-size: 13px;
                word-break: break-all;
                padding: 10px;
                border-radius: 6px;
                display: block;
                background: #fdfdfd;
                border: 1px solid #f0f0f0;
                transition: all 0.2s ease;
            }
            .card a:hover {
                background: var(--aiesec-blue);
                color: white;
                transform: translateX(5px);
                box-shadow: 2px 2px 8px rgba(3, 126, 243, 0.2);
            }
            .badge {
                display: inline-block;
                padding: 2px 8px;
                background: var(--aiesec-blue);
                color: white;
                border-radius: 12px;
                font-size: 10px;
                text-transform: uppercase;
                margin-bottom: 10px;
            }
            footer {
                text-align: center;
                padding: 60px 40px;
                color: #aaa;
                font-size: 0.9em;
            }
            .highlight { color: var(--aiesec-blue); font-weight: bold; }
        </style>
    </head>
    <body>
        <header>
            <span class="logo">AIESEC API Gateway</span>
            <div class="tagline">"Empowering young leaders through technology."</div>
        </header>

        <div class="container">
            <div class="intro-text">
                <h1>Seja bem-vindo, <span class="highlight">Leader Developer!</span></h1>
                <p>Nossa API é o motor que conecta projetos nacionais da AIESEC no Brasil. <br>
                Abaixo você encontra todas as interfaces de documentação técnica disponíveis.</p>
            </div>

            <div class="cards">
                {% for categoria, links in rotas.items() %}
                    <div class="card">
                        <span class="badge">AIESEC Dev Tools</span>
                        <h2>{{ categoria }}</h2>
                        <p style="font-size: 0.85em; color: #888; margin-bottom: 15px;">Acesse e teste os recursos da V1.</p>
                        <ul>
                            {% for rota in links %}
                                <li><a href="{{ rota }}">➔ {{ rota }}</a></li>
                            {% endfor %}
                        </ul>
                    </div>
                {% endfor %}
            </div>
        </div>

        <footer>
            <strong>AIESEC No Brasil | Documentação de Código</strong><br>
            Desenvolvido para causar impacto e conectar jovens ao redor do mundo. <br>
            &copy; 2026 Todos os direitos reservados.
        </footer>
    </body>
    </html>
    """

    return render_template_string(template, rotas=rotas)

@api.get("/register",responses={204:None})
def registro():
    """
    Responsável por fazer o registro do IPV6 de quem tem autorização para acessar a documentação.
    """
    storage.add_ip(request.headers.get("X-Forwarded-For"))
    return "",HttpStatus.NO_CONTENT

# ==============================
# Exportações do Módulo
# ==============================
__all__ = ["api"]