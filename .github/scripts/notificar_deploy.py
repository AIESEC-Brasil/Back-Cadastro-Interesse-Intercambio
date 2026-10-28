import datetime
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

payload = {
    "status": os.environ["STATUS"],
    "repositorio": os.environ["GITHUB_REPOSITORY"],
    "ref": os.environ["GITHUB_REF"],
    "autor": os.environ["GITHUB_ACTOR"],
    "mensagem_commit": os.environ.get("COMMIT_MESSAGE", ""),
    "run_url": (
        f'{os.environ["GITHUB_SERVER_URL"]}/'
        f'{os.environ["GITHUB_REPOSITORY"]}/actions/runs/'
        f'{os.environ["GITHUB_RUN_ID"]}'
    ),
    "ambiente": "Produção",
    "detalhe_erro": os.environ["DETAIL"],
    "timestamp": datetime.datetime.now(ZoneInfo("America/Sao_Paulo")).strftime(
        "%d/%m/%Y %H:%M:%S"
    ),
}

request = Request(
    os.environ["APPSCRIPT_URL"],
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urlopen(request, timeout=30) as response:
        print(f"Resposta do Apps Script: HTTP {response.status}")
except HTTPError as error:
    print(f"Resposta do Apps Script: HTTP {error.code}")
except (URLError, TimeoutError) as error:
    print(f"Falha ao enviar notificação ao Apps Script: {type(error).__name__}")
