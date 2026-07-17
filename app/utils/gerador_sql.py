import json
import os

def gerar_sql_seed(raiz_projeto: str):
    caminho_json = os.path.join(raiz_projeto, 'doc', 'divisaoMercado.json')
    caminho_sql = os.path.join(raiz_projeto, 'doc', 'seed_mercado.txt')

    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    with open(caminho_sql, 'w', encoding='utf-8') as f:
        
        # 1. Conjunto para controlar duplicatas de Universidades
        processados_univ = set()
        for item in dados.get('Universidades', []):
            nome = item.get('nome', '').strip().title()  # Normaliza o nome para evitar duplicatas por capitalização
            if not nome or nome in processados_univ:
                continue
            
            gv = item.get('gv', '')
            gt = item.get('gt', '')
            
            f.write(f"INSERT INTO instituicoes_mercado (nome, gv, gt) VALUES ('{nome.replace("'", "''")}', '{gv}', '{gt}');\n")
            processados_univ.add(nome)
        
        # 2. Conjunto para controlar duplicatas de Escritórios (CL)
        processados_cl = set()
        for item in dados.get('Escritorios', []):
            nome = item.get('nome', '').strip().title()  # Normaliza o nome para evitar duplicatas por capitalização
            if not nome or nome in processados_cl:
                continue
                
            gv = item.get('gv', '')
            gt = item.get('gt', '')
            
            f.write(f"INSERT INTO cl_mercado (nome, gv, gt) VALUES ('{nome.replace("'", "''")}', '{gv}', '{gt}');\n")
            processados_cl.add(nome)

    print(f"Arquivo gerado com sucesso em: {caminho_sql}")
    print(f"Total de universidades únicas: {len(processados_univ)}")
    print(f"Total de CLs únicos: {len(processados_cl)}")

__all__ = ["gerar_sql_seed"]