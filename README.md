# Metadados B2C

Este serviço disponibiliza os metadados do formulário B2C obtidos pelo Apps Script.

## Rota

`GET /new-lead-ogx/metadados`

A resposta mantém o formato `{"data":{"fields":[]}}`. Os dados ficam em cache pelo período definido em `CACHE_TTL`.

## Divisão de mercado

`GET /divisao-mercado/escritorios/metadados` e
`GET /divisao-mercado/universidades/metadados` retornam os dados do Apps Script
no formato `{"recurso":"...","path":"...","aba":"...","total":0,"dados":[]}`.

## Configuração

O serviço usa `AMBIENTE`, `CACHE_TTL`, `APPSCRIPT_B2C`,
`APPSCRIPT_DIVISAO_MERCADO`, definidos no ambiente de execução. O endpoint
único recebe `recurso=escritorios` ou `recurso=universidades` na query string.
O Apps Script deve selecionar a aba usando `e.parameter.recurso`. O arquivo
`.env.example` documenta as configurações disponíveis.

## Execução local

```bash
python server.py
```
