# Backend

API da aplicação de cadastro de interesse em intercâmbio, desenvolvida em Python com Flask. O serviço valida os dados recebidos, disponibiliza metadados para os formulários e integra cadastros com Google Apps Script e EXPA.

## Visão geral

O frontend encaminha as chamadas para a API por meio do proxy Next.js. O backend valida os dados com modelos Pydantic, monta os payloads esperados pelas integrações e converte falhas de validação ou de serviços externos em respostas HTTP.

Os metadados de formulários e de divisão de mercado são carregados das fontes configuradas e mantidos em cache em memória pelo período definido em `CACHE_TTL`.

## Tecnologias

- Python e Flask
- Flask-OpenAPI3 e Pydantic
- Cliente HTTP assíncrono para integrações
- Google Apps Script e EXPA
- pytest para testes automatizados

## Funcionalidades

- Fornecimento de metadados dos formulários B2C.
- Fornecimento de metadados de escritórios e universidades por divisão de mercado.
- Validação de pré-cadastros e qualificações.
- Montagem e envio de dados para os serviços configurados.
- Documentação OpenAPI e respostas de erro padronizadas.
- Cache dos metadados para reduzir chamadas externas repetidas.

## Estrutura do projeto

```text
.
├── app/
│   ├── api/                 # configuração da documentação OpenAPI
│   ├── cache/               # cache em memória
│   ├── clients/             # clientes HTTP e integrações externas
│   ├── config/              # leitura das configurações
│   ├── controller/          # endpoints da API
│   ├── dto/                 # modelos de entrada, saída e erros
│   ├── middlewares/         # autorização, logs e documentação
│   ├── router/              # registro e serialização das rotas
│   ├── strategies/          # estratégias de cadastro
│   └── utils/               # montagem de payloads e metadados
├── tests/                   # testes automatizados
├── .github/
│   ├── scripts/             # deploy e notificações
│   └── workflows/           # pipeline de deploy
├── .env.example
├── Dockerfile
├── requirements.txt
├── server.py
└── README.md
```

## Requisitos

- Python compatível com o workflow de deploy.
- pip.
- Credenciais e URLs das integrações externas para executar fluxos completos.

## Instalação e execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha no `.env` as configurações exigidas para o ambiente e inicie a aplicação:

```bash
python server.py
```

## Configuração do ambiente

`server.py` carrega o arquivo `.env` localizado no diretório `backend/` antes de iniciar a aplicação. Use `.env.example` como modelo. As principais variáveis são:

| Variável | Uso |
| --- | --- |
| `AMBIENTE` | Define o ambiente da aplicação (`DEV`, `TEST` ou `PRODUCTION`). |
| `CACHE_TTL` | Tempo de validade do cache de metadados, em segundos. |
| `DOMINIOS_PERMITIDOS` | Hosts permitidos pelas regras de acesso e CORS, separados por vírgula. |
| `API_KEYS_PERMITIDAS` | Chaves autorizadas para chamadas internas, separadas por vírgula. |
| `TOKEN_EXPA` | Token usado na integração com EXPA. |
| `APPSCRIPT_EXPA` | Endpoint do Apps Script relacionado a leads. |
| `APPSCRIPT_B2C` | Endpoint do Apps Script que fornece metadados B2C. |
| `APPSCRIPT_DIVISAO_MERCADO` | Endpoint de metadados de escritórios e universidades. |

O deploy usa os GitHub Actions Secrets para montar o `.env` enviado ao PythonAnywhere. Não versione o arquivo `.env` nem registre tokens nos logs.

## Endpoints principais

- `GET /new-lead-ogx/metadados`: metadados usados pelo formulário B2C.
- `POST /new-lead-ogx/cadastro`: cria pré-cadastro de lead.
- `PUT /new-lead-ogx/cadastro`: atualiza ou qualifica cadastro de lead.
- `POST /new-lead-ogx/cadastro-b2c`: cria cadastro B2C.
- `PUT /new-lead-ogx/cadastro-b2c`: atualiza cadastro B2C.
- `GET /divisao-mercado/escritorios/metadados`: escritórios e divisões de mercado.
- `GET /divisao-mercado/universidades/metadados`: universidades e divisões de mercado.

O portal OpenAPI fica em `/api/docs`, sujeito às regras de autorização configuradas para o ambiente. As respostas de divisão de mercado contêm `recurso`, `path`, `aba`, `total` e `dados`.

## Testes

```bash
python -m pytest
```

## Deploy

O workflow em `.github/workflows/deploy.yml` executa o deploy no PythonAnywhere. O script de deploy gera um `.env` remoto a partir do modelo e dos secrets configurados no GitHub Actions e recarrega a aplicação.
