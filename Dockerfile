# Imagem base da API: Python 3.13 sobre Alpine Linux. O build context deste
# Dockerfile é a pasta backend/ (definida por build em docker-compose.yml).
FROM python:3.13.14-alpine

# Define o diretório de trabalho dentro da imagem. COPY, RUN e CMD passam a
# operar a partir de /app, salvo quando um caminho absoluto é informado.
WORKDIR /app

# Evita criar arquivos .pyc durante a execução, envia logs sem buffer para
# stdout/stderr do container e silencia o aviso do pip por instalar como root.
# Essa configuração do pip não troca o usuário que executa o processo.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore

# Copia primeiro a lista de dependências. O Docker pode reutilizar as camadas
# de instalação enquanto requirements.txt não mudar, mesmo que o código mude.
COPY requirements.txt .
# Atualiza o instalador e instala FastAPI, SQLAlchemy, drivers e demais
# dependências declaradas em requirements.txt sem guardar cache do pip na imagem.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# Copia o restante do contexto backend/ para /app. Arquivos que não devem entrar
# no contexto da imagem devem ser excluídos por um arquivo .dockerignore.
COPY . .

# Documenta a porta interna usada pelo Uvicorn. EXPOSE, sozinho, não publica a
# porta no host; docker-compose.yml faz o mapeamento 5000:5000.
EXPOSE 5000

# Inicia server.py. O script executa Uvicorn e carrega a factory create_app
# definida em app/main.py, escutando em 0.0.0.0:5000 dentro do container.
CMD ["python", "server.py"]