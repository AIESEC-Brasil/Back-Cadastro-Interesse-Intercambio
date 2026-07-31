"""Módulo para geração automatizada de scripts SQL de seed a partir de JSON.

Lê as definições de universidades e escritórios (CLs) no arquivo JSON
de divisão de mercado e gera as instruções SQL `INSERT` em um arquivo texto,
removendo duplicatas por nome e tratando aspas simples para segurança contra SQL Injection simples.
"""

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
import json  # Biblioteca nativa para parsing e manipulação de arquivos JSON
import os  # Utilitário para manipulação de rotas e caminhos de arquivos


# =================================================================
# 2. FUNÇÃO DE GERAÇÃO DO SEED SQL
# =================================================================

def gerar_sql_seed(raiz_projeto: str) -> None:
    """Gera um arquivo de script SQL de seed contendo os INSERTs de mercado.

    Lê os dados do arquivo 'doc/divisaoMercado.json' e escreve
    os comandos SQL sanitizados no arquivo 'doc/seed_mercado.txt'.

    Args:
        raiz_projeto (str): O caminho absoluto para o diretório raiz da aplicação.
    """
    # Mapeia os caminhos absolutos dos arquivos de entrada (JSON) e saída (TXT/SQL)
    caminho_json = os.path.join(raiz_projeto, "doc", "divisaoMercado.json")
    caminho_sql = os.path.join(raiz_projeto, "doc", "seed_mercado.txt")

    # Realiza a leitura e parsing do arquivo JSON de origem
    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Abre o arquivo de saída para escrita das instruções SQL
    with open(caminho_sql, "w", encoding="utf-8") as f:

        # -------------------------------------------------------------
        # 1. Processamento de Universidades / Instituições
        # -------------------------------------------------------------
        processados_univ = set()  # Conjunto hash para controle e remoção de duplicatas

        for item in dados.get("Universidades", []):
            # Normaliza o nome removendo espaços extras e ajustando capitalização (Title Case)
            nome = item.get("nome", "").strip().title()

            # Descarta registros vazios ou já processados anteriormente
            if not nome or nome in processados_univ:
                continue

            gv = item.get("gv", "")
            gt = item.get("gt", "")

            # Escapa aspas simples no nome para evitar erros de sintaxe no SQL
            nome_sanitizado = nome.replace("'", "''")

            # Escreve a instrução de INSERT no arquivo de saída
            f.write(
                f"INSERT INTO instituicoes_mercado (nome, gv, gt) "
                f"VALUES ('{nome_sanitizado}', '{gv}', '{gt}');\n"
            )

            # Adiciona o nome normalizado ao conjunto de controle
            processados_univ.add(nome)

        # -------------------------------------------------------------
        # 2. Processamento de Escritórios (CLs)
        # -------------------------------------------------------------
        processados_cl = set()  # Conjunto hash para controle e remoção de duplicatas

        for item in dados.get("Escritorios", []):
            # Normaliza o nome removendo espaços extras e ajustando capitalização (Title Case)
            nome = item.get("nome", "").strip().title()

            # Descarta registros vazios ou já processados anteriormente
            if not nome or nome in processados_cl:
                continue

            gv = item.get("gv", "")
            gt = item.get("gt", "")

            # Escapa aspas simples no nome para evitar erros de sintaxe no SQL
            nome_sanitizado = nome.replace("'", "''")

            # Escreve a instrução de INSERT no arquivo de saída
            f.write(
                f"INSERT INTO cl_mercado (nome, gv, gt) "
                f"VALUES ('{nome_sanitizado}', '{gv}', '{gt}');\n"
            )

            # Adiciona o nome normalizado ao conjunto de controle
            processados_cl.add(nome)

    # Exibe métricas do processamento executado no terminal
    print(f"Arquivo gerado com sucesso em: {caminho_sql}")
    print(f"Total de universidades únicas: {len(processados_univ)}")
    print(f"Total de CLs únicos: {len(processados_cl)}")


# =================================================================
# 3. EXPORTAÇÃO DO MÓDULO
# =================================================================
__all__ = ["gerar_sql_seed"]