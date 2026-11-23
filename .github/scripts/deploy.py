"""Publica os arquivos permitidos do backend e recarrega a webapp no PythonAnywhere.

O workflow fornece os segredos por variáveis de ambiente. O script materializa
essas configurações num `.env` temporário, envia apenas arquivos de aplicação
permitidos e nunca grava o arquivo gerado no checkout do Git.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote

import requests
from dotenv import set_key

class DeployConfig(TypedDict):
    """Configuração validada e compartilhada pelas etapas do deploy."""

    username: str
    domain: str
    project_dir: Path
    remote_dir: str
    app_env: dict[str, str]
    session: requests.Session


APP_ENV_NAMES: tuple[str, ...] = (
    "AMBIENTE", "CACHE_TTL", "DOMINIOS_PERMITIDOS", "API_KEYS_PERMITIDAS",
    "TOKEN_EXPA", "APPSCRIPT_EXPA",
    "APPSCRIPT_B2C", "APPSCRIPT_DIVISAO_MERCADO",
)
ALLOWED_DIRS: set[str] = {"app", "doc"}
ALLOWED_FILES: set[str] = {".env.example", "requirements.txt", "server.py"}
LEGACY_ENV_FILES: tuple[str, ...] = (".env.dev", ".env.test")
IGNORED_SUBDIRS: set[str] = {
    "__pycache__", ".pytest_cache", ".git", ".vscode", ".idea"
}
CREATED_DIRS: set[str] = set()


def required_env(name: str) -> str:
    """Lê uma variável de ambiente obrigatória do workflow.

    Args:
        name: Nome da variável ou do GitHub Actions Secret.

    Returns:
        Valor não vazio configurado no ambiente do processo.

    Raises:
        SystemExit: Se a variável não estiver configurada.
    """
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Configure o Actions secret obrigatório: {name}")
    return value

def load_config() -> DeployConfig:
    """Valida credenciais e prepara caminhos e sessão da API PythonAnywhere."""
    username = required_env("PYTHONANYWHERE_USERNAME")
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Token {required_env('PYTHONANYWHERE_API_TOKEN')}"
    })
    return {
        "username": username,
        "domain": required_env("PYTHONANYWHERE_DOMAIN"),
        "project_dir": Path.cwd(),
        "remote_dir": f"/home/{username}/Back-Cadastro-Interesse-Intercambio",
        "app_env": {name: required_env(name) for name in APP_ENV_NAMES},
        "session": session,
    }

def api_url(config: DeployConfig, path: str) -> str:
    """Monta uma URL da API PythonAnywhere para o usuário configurado.

    Args:
        config: Configuração do deploy com o usuário da conta.
        path: Caminho da API iniciado por `/`.

    Returns:
        URL absoluta e com o nome do usuário escapado.
    """
    api_user = quote(config["username"], safe="")
    return f"https://www.pythonanywhere.com/api/v0/user/{api_user}{path}"

def parse_null_bytes_file(file_path_str: str) -> set[str]:
    """Lê caminhos NUL-separated produzidos pelas opções `git diff -z`.

    Args:
        file_path_str: Caminho do arquivo temporário criado pelo workflow.

    Returns:
        Conjunto de caminhos relativos normalizados; vazio se o arquivo faltar.
    """
    path = Path(file_path_str)
    if not path.exists():
        return set()
    raw = path.read_bytes()
    if not raw:
        return set()
    return {
        Path(item.decode("utf-8", errors="ignore")).as_posix()
        for item in raw.split(b"\0")
        if item.strip()
    }

def delete_remote_path(config: DeployConfig, remote_path: str) -> bool:
    """Remove um caminho remoto, esvaziando diretórios quando necessário.

    Args:
        config: Configuração e sessão autenticada da API PythonAnywhere.
        remote_path: Caminho absoluto do arquivo ou diretório remoto.

    Returns:
        `True` quando removido ou ausente; `False` quando a API não consegue
        concluir a remoção.
    """
    url = api_url(config, f"/files/path{quote(remote_path, safe='/')}")
    response = config["session"].delete(url, timeout=60)

    if response.status_code in (204, 404):
        return True

    # Se falhar porque a pasta contém arquivos no servidor, limpa o diretório recursivamente
    tree_url = api_url(config, f"/files/tree/?path={quote(remote_path, safe='/')}")
    tree_res = config["session"].get(tree_url, timeout=60)

    if tree_res.status_code == 200:
        contents = tree_res.json()
        # Apaga itens internos ordenando dos caminhos mais profundos aos mais rasos
        for item_path in sorted(contents, key=lambda p: len(p.split('/')), reverse=True):
            item_url = api_url(config, f"/files/path{quote(item_path, safe='/')}")
            config["session"].delete(item_url, timeout=60)

        # Tenta deletar o diretório principal novamente após esvaziar
        retry_res = config["session"].delete(url, timeout=60)
        if retry_res.status_code in (204, 404):
            return True

    print(f"ERRO [{response.status_code}] ao deletar {remote_path}")
    return False

def ensure_remote_dir(config: DeployConfig, remote_path: str) -> None:
    """Garante que o diretório remoto exista, criando-o no máximo uma vez.

    Args:
        config: Configuração e sessão autenticada da API PythonAnywhere.
        remote_path: Caminho absoluto do diretório a preparar.

    Raises:
        SystemExit: Se a API não conseguir criar ou confirmar o diretório.
    """
    if remote_path in CREATED_DIRS:
        return
    url = api_url(config, f"/files/path{quote(remote_path, safe='/')}")
    response = config["session"].post(url, timeout=60)
    if response.status_code not in (200, 201, 204, 400, 409):
        raise SystemExit(
            f"Não foi possível preparar diretório remoto: HTTP {response.status_code}"
        )
    CREATED_DIRS.add(remote_path)
    time.sleep(2)

def upload_file(
    config: DeployConfig,
    local_path: Path,
    remote_path: str,
    max_retries: int = 3,
) -> bool:
    """Envia um arquivo e repete em falhas temporárias da API.

    Args:
        config: Configuração e sessão autenticada da API PythonAnywhere.
        local_path: Arquivo local a enviar.
        remote_path: Destino absoluto no servidor.
        max_retries: Número máximo de tentativas de envio.

    Returns:
        `True` quando o envio é concluído; `False` após falha definitiva.
    """
    remote_parent = str(Path(remote_path).parent).replace("\\", "/")
    ensure_remote_dir(config, remote_parent)
    url = api_url(config, f"/files/path{quote(remote_path, safe='/')}")

    for attempt in range(max_retries):
        try:
            with local_path.open("rb") as stream:
                response = config["session"].post(
                    url,
                    files={"content": (Path(remote_path).name, stream)},
                    timeout=60,
                )
            if response.status_code in (200, 201):
                time.sleep(2)
                return True
            if response.status_code == 429 and attempt < max_retries - 1:
                try:
                    wait = int(response.headers.get("Retry-After", "10"))
                except ValueError:
                    wait = 10
                time.sleep(max(wait, 1))
                continue
            if response.status_code >= 500 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"ERRO [{response.status_code}] ao enviar {Path(remote_path).name}")
            return False
        except requests.RequestException as error:
            if attempt == max_retries - 1:
                print(f"ERRO [{type(error).__name__}] ao enviar {Path(remote_path).name}")
                return False
            time.sleep(2 ** attempt)

    return False

def is_path_allowed(relative_path: str) -> bool:
    """Indica se o caminho pertence à lista de conteúdo implantável.

    Args:
        relative_path: Caminho do repositório relativo à raiz do backend.

    Returns:
        `True` para arquivos ou diretórios explicitamente permitidos.
    """
    parts = Path(relative_path).parts
    if not parts:
        return False
    if parts[0] in ALLOWED_DIRS:
        return True
    if len(parts) == 1 and parts[0] in ALLOWED_FILES:
        return True
    return False

def process_deletions(config: DeployConfig) -> int:
    """Aplica no servidor as exclusões permitidas reportadas pelo GitHub Actions.

    Args:
        config: Configuração e sessão autenticada da API PythonAnywhere.

    Returns:
        Quantidade de caminhos remotos removidos com sucesso.
    """
    deleted_paths = parse_null_bytes_file(required_env("DELETED_FILES_PATH"))
    total_deleted = 0

    # Ordena do caminho mais longo ao mais curto para apagar arquivos antes das pastas pai
    sorted_deletions = sorted(deleted_paths, key=lambda p: len(Path(p).parts), reverse=True)

    for relative_path in sorted_deletions:
        if is_path_allowed(relative_path):
            remote_path = f"{config['remote_dir']}/{relative_path}"
            print(f"Deletando do servidor: {relative_path} ...", end=" ", flush=True)
            if delete_remote_path(config, remote_path):
                print("OK")
                total_deleted += 1
            else:
                print("FALHA")

            # Tenta remover também o diretório pai caso a exclusão do arquivo tenha deixado a pasta vazia
            parent_rel = Path(relative_path).parent.as_posix()
            if parent_rel and parent_rel != "." and is_path_allowed(parent_rel):
                remote_parent = f"{config['remote_dir']}/{parent_rel}"
                delete_remote_path(config, remote_parent)

    return total_deleted

def upload_project(config: DeployConfig) -> bool:
    """Envia alterações permitidas, o `.env` gerado e limpa arquivos antigos.

    Args:
        config: Configuração do projeto, credenciais e sessão HTTP.

    Returns:
        `True` se houve implantação; `False` se não havia alterações aplicáveis
        ou se algum arquivo não pôde ser enviado.
    """
    project_dir = config["project_dir"]
    if not project_dir.is_dir():
        print(f"Erro local: pasta '{project_dir}' não encontrada")
        return False

    changed_paths = parse_null_bytes_file(required_env("CHANGED_FILES_PATH"))

    print(f"Pasta local: {project_dir}")
    print(f"Destino no servidor: {config['remote_dir']}")
    print(f"Arquivos detectados no Git: {len(changed_paths)}\n")
    CREATED_DIRS.clear()

    total_deleted = process_deletions(config)

    with tempfile.TemporaryDirectory() as temp_dir:
        template_file = project_dir / ".env.example"
        if not template_file.is_file():
            raise SystemExit(
                "O arquivo .env.example é necessário como modelo documentado"
            )

        env_file = Path(temp_dir) / ".env"
        shutil.copyfile(template_file, env_file)
        for name, value in config["app_env"].items():
            set_key(str(env_file), name, value, quote_mode="never")

        files = []
        for filename in sorted(ALLOWED_FILES):
            if filename in changed_paths:
                path = project_dir / filename
                if path.is_file():
                    files.append((path, filename))

        for dirname in sorted(ALLOWED_DIRS):
            base = project_dir / dirname
            if not base.is_dir():
                continue
            for root, dirs, filenames in os.walk(base):
                dirs[:] = sorted(d for d in dirs if d not in IGNORED_SUBDIRS)
                for filename in sorted(filenames):
                    path = Path(root) / filename
                    relative = path.relative_to(project_dir).as_posix()
                    if (
                        path.suffix not in {".pyc", ".pyo"}
                        and relative in changed_paths
                    ):
                        files.append((path, relative))

        if files or total_deleted > 0:
            files.append((env_file, ".env"))

        files.sort(key=lambda item: item[1])
        if not files and total_deleted == 0:
            print("Nenhum arquivo permitido foi alterado, criado ou deletado; deploy ignorado.")
            return False

        ensure_remote_dir(config, config["remote_dir"])
        total_uploaded = 0
        for path, relative_path in files:
            remote_path = f"{config['remote_dir']}/{relative_path}"
            print(f"Enviando: {relative_path} ...", end=" ", flush=True)
            if upload_file(config, path, remote_path):
                print("OK")
                total_uploaded += 1
            else:
                print()
                return False

        for filename in LEGACY_ENV_FILES:
            remote_path = f"{config['remote_dir']}/{filename}"
            print(f"Removendo arquivo legado: {filename} ...", end=" ", flush=True)
            if delete_remote_path(config, remote_path):
                print("OK")
            else:
                print("FALHA")
                return False

    print(f"\nConcluído! Total: {total_uploaded} enviados/atualizados, {total_deleted} deletados.")
    return True

def reload_webapp(config: DeployConfig) -> None:
    """Solicita à API PythonAnywhere o reload da aplicação publicada.

    Args:
        config: Configuração e sessão autenticada da API PythonAnywhere.

    Raises:
        SystemExit: Se a API responder com um status diferente de HTTP 200.
    """
    url = api_url(
        config,
        f"/webapps/{quote(config['domain'], safe='')}/reload/",
    )
    print("\nRecarregando a aplicação Web no PythonAnywhere...")
    response = config["session"].post(url, timeout=60)
    if response.status_code != 200:
        raise SystemExit(f"Erro ao recarregar a webapp: HTTP {response.status_code}")
    print("Aplicação Web recarregada com sucesso!")

if __name__ == "__main__":
    deploy_config = load_config()
    if upload_project(deploy_config):
        reload_webapp(deploy_config)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("deployed=true\n")
