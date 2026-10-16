# Metadados B2C

Este serviço disponibiliza os metadados do formulário B2C obtidos pelo Apps Script.

## Rota

`GET /new-lead-ogx/metadados`

A resposta mantém o formato `{"data":{"fields":[]}}`. Os dados ficam em cache pelo período definido em `CACHE_TTL`.

## Configuração

O serviço usa `AMBIENTE`, `CACHE_TTL` e `APPSCRIPT_B2C`, definidos no ambiente de execução. O arquivo `.env.example` documenta as configurações disponíveis.

## Execução local

```bash
python server.py
```
