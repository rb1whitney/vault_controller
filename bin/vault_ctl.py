import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging
import sys
import os
from typing import Optional
import yaml
import json
import glob

# Ensure repo root is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.core.client import LocalVaultClient
from lib.utils import (
    crypto as vault_crypto,
    ops,
    settings,
)
from lib.engines.payload_processor import PayloadProcessor
from lib.validation.manager import ValidationManager

app = typer.Typer(
    name="vault-ctl",
    help="Modern Vault Controller CLI",
    add_completion=False,
    no_args_is_help=True,
)

cluster_app = typer.Typer(help="Manage Vault Clusters")
app.add_typer(cluster_app, name="cluster")

rekey_app = typer.Typer(help="Manage Shamir Key Rotations")
cluster_app.add_typer(rekey_app, name="rekey")

secrets_app = typer.Typer(help="Manage Vault Secrets and Engines")
app.add_typer(secrets_app, name="secrets")

console = Console()

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )
    return logging.getLogger("vault-ctl")

@cluster_app.command("status")
def cluster_status(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name from contexts.yaml"),
):
    """Check health and seal status of nodes."""
    try:
        config = settings.get_cluster(name)
        table = Table(title=f"Vault Cluster Status: {name}")
        table.add_column("Node", style="cyan")
        table.add_column("Address", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Version", style="green")

        for endpoint in config.server_endpoints:
            client = LocalVaultClient(endpoint, logging.getLogger("health"))
            try:
                health = client.hvac_client.sys.read_health_status(method="GET")
                status = "ALIVE" if not health.get("sealed") else "SEALED"
                color = "green" if status == "ALIVE" else "yellow"
                table.add_row(
                     endpoint.split("//")[-1],
                     endpoint,
                     f"[{color}]{status}[/{color}]",
                     health.get("version", "N/A")
                )
            except Exception:
                table.add_row(endpoint.split("//")[-1], endpoint, "[red]DOWN[/red]", "N/A")
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)

@cluster_app.command("unseal")
def cluster_unseal(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    keys: str = typer.Option(
        ...,
        "--keys",
        prompt="Comma-separated unseal keys",
        hide_input=True,
        envvar="VAULT_UNSEAL_KEYS",
        help="Comma-separated unseal keys (prompted or via VAULT_UNSEAL_KEYS)",
    ),
):
    """Unseal all nodes in the cluster."""
    logger = logging.getLogger("vault-ctl")
    try:
        key_list = [k.strip() for k in keys.split(",") if k.strip()]
        config = settings.get_cluster(name)
        for endpoint in config.server_endpoints:
            console.print(f"Unsealing [cyan]{endpoint}[/]...")
            ops.unseal_host(logger, endpoint, key_list)
            console.print("  [green]Unseal command executed successfully.[/]")
    except Exception as e:
        console.print(f"[bold red]Unseal Failed:[/] {e}")
        raise typer.Exit(code=1)

@cluster_app.command("init")
def cluster_init(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    shares: int = typer.Option(5, help="Number of Shamir shares"),
    threshold: int = typer.Option(3, help="Shamir threshold"),
    rekey_cluster: bool = typer.Option(False, "--rekey", help="Rekey cluster post-initialization"),
    auto_unseal: bool = typer.Option(False, "--auto-unseal", help="Enable auto unseal recovery key mode"),
    deploy_admin: bool = typer.Option(True, "--deploy-admin/--no-deploy-admin", help="Deploy admin configuration post-init"),
    revoke_root: bool = typer.Option(True, "--revoke-root/--no-revoke-root", help="Revoke initial root token after admin bootstrap"),
):
    """Bootstrap a new Vault cluster."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Bootstrapping Vault...", total=None)
            root_token, key_output = ops.init_cluster(
                cluster_name=name,
                server_endpoints=config.server_endpoints,
                logger=logger,
                key_holders=config.key_holders,
                secret_shares=shares,
                secret_threshold=threshold,
                rekey_cluster=rekey_cluster,
                auto_unseal_enabled=auto_unseal,
            )
            console.print(f"[bold green]Initialized![/] Root Token: [bold yellow]{root_token[:4]}...{root_token[-4:]}[/]")
            if key_output:
                console.print_json(data=key_output)

        if deploy_admin:
            console.print("[yellow]Deploying admin configuration...[/]")
            client = LocalVaultClient(config.server_endpoints[0], logger)
            client.adapter.token = root_token
            try:
                processor = PayloadProcessor(client)
                admin_path = os.path.join(os.path.dirname(__file__), "../config/example_vault/admin/")
                if os.path.exists(admin_path):
                    yaml_files = []
                    for root, _, files in os.walk(admin_path):
                        for f in files:
                            if f.endswith((".yaml", ".yml")):
                                yaml_files.append(os.path.join(root, f))
                    yaml_files.sort()
                    for f_path in yaml_files:
                        with open(f_path, "r") as f:
                            data = yaml.safe_load(f)
                        target_client = client
                        if "_namespace" in data:
                            target_client = LocalVaultClient(config.api_endpoint, logger, namespace=data["_namespace"])
                            target_client.adapter.token = client.adapter.token
                        for obj in data.get("api_paths", []):
                            processor.process(obj)
                        target_client.submit(data["api_paths"])
                    console.print("[bold green]Admin configuration deployed successfully![/]")
            finally:
                if revoke_root:
                    client.logout()
                    console.print("[bold green]Initial root token revoked.[/]")

        console.print(Panel(f"Cluster [bold cyan]{name}[/] is now [bold green]INITIALIZED[/]"))
    except Exception as e:
        console.print(f"[bold red]Initialization Failed:[/] {e}")
        raise typer.Exit(code=1)

@rekey_app.command("init")
def rekey_init(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within namespace"),
):
    """Initialize a Shamir rekey attempt."""
    logger = logging.getLogger("vault-ctl")
    client = None
    try:
        config = settings.get_cluster(name)
        ns = None if not auth_namespace else config.config_env
        client = LocalVaultClient(config.api_endpoint, logger, namespace=ns)
        client.login(auth_method=auth_method, mount_point=mount_path)

        base64_pgp_keys = (
            vault_crypto.gather_pgp_keys(config.key_holders)
            if config.key_encrypt
            else None
        )
        ops.cancel_rekey(client, recovery_key=config.recovery_key)
        res = ops.start_rekey(
            client,
            secret_shares=len(config.key_holders) if config.key_encrypt else config.key_threshold,
            secret_threshold=config.key_threshold,
            pgp_keys=base64_pgp_keys,
            backup=bool(base64_pgp_keys),
            recovery_key=config.recovery_key,
        )
        console.print(f"[bold green]Rekey initiated successfully![/] Nonce: [bold yellow]{res['nonce']}[/]")
    except Exception as e:
        console.print(f"[bold red]Rekey Initialization Failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if client and auth_method != "token":
            client.logout()

@rekey_app.command("update")
def rekey_update_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    key: str = typer.Option(..., "--key", prompt="Shamir key share", hide_input=True, envvar="VAULT_KEY", help="A single Shamir key/unseal share"),
    nonce: str = typer.Option(..., "--nonce", envvar="NONCE", help="Rekey attempt nonce"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within namespace"),
):
    """Submit a Shamir key/unseal share to progress rekeying."""
    logger = logging.getLogger("vault-ctl")
    client = None
    try:
        config = settings.get_cluster(name)
        ns = None if not auth_namespace else config.config_env
        client = LocalVaultClient(config.api_endpoint, logger, namespace=ns)
        client.login(auth_method=auth_method, mount_point=mount_path)

        res = ops.rekey_update(client, key=key, nonce=nonce, recovery_key=config.recovery_key)
        console.print(f"Update response: {res}")
        if res.get("complete"):
            key_output = vault_crypto.format_key_response(res, config.key_holders, config.key_encrypt)
            console.print("[bold green]Rekey complete![/] New keys generated:")
            console.print_json(data=key_output)
    except Exception as e:
        console.print(f"[bold red]Rekey Update Failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if client and auth_method != "token":
            client.logout()

@rekey_app.command("cancel")
def rekey_cancel(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within namespace"),
):
    """Cancel any in-progress Shamir rekey attempt."""
    logger = logging.getLogger("vault-ctl")
    client = None
    try:
        config = settings.get_cluster(name)
        ns = None if not auth_namespace else config.config_env
        client = LocalVaultClient(config.api_endpoint, logger, namespace=ns)
        client.login(auth_method=auth_method, mount_point=mount_path)
        ops.cancel_rekey(client, recovery_key=config.recovery_key)
        console.print("[bold green]In-progress rekey cancelled successfully.[/]")
    except Exception as e:
        console.print(f"[bold red]Rekey Cancel Failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if client and auth_method != "token":
            client.logout()

@secrets_app.command("deploy")
def secrets_deploy(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to YAML configs"),
    wrapped_token: Optional[str] = typer.Option(None, "--wrapped-token", help="Wrapped token for secret delivery"),
    namespace: Optional[str] = typer.Option(None, help="Target Vault namespace"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within target namespace"),
):
    """Deploy secrets/config from YAML files or unwrapped tokens."""
    logger = logging.getLogger("vault-ctl")
    client = None
    try:
        if not wrapped_token and not path:
            console.print("[bold red]Error:[/] Either --path or --wrapped-token must be specified.")
            raise typer.Exit(code=1)

        yaml_files = []
        if path:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        if f.endswith((".yaml", ".yml")):
                            yaml_files.append(os.path.join(root, f))
            else:
                yaml_files.append(path)
            yaml_files.sort()

            # Shift-left offline validation gate BEFORE authenticating
            is_admin_path = "admin" in os.path.normpath(path).split(os.sep)
            scheme = "admin" if is_admin_path else "namespaces"
            validator = ValidationManager(scheme, logger)
            errors = validator.validate(name, files=yaml_files)
            if errors:
                console.print("[bold red]Validation Failed:[/]")
                for err in errors:
                    console.print(f"  - {err}")
                raise typer.Exit(code=1)

        config = settings.get_cluster(name)
        client = LocalVaultClient(config.api_endpoint, logger)
        if not auth_namespace:
            client.login(auth_method=auth_method, mount_point=mount_path)

        processor = PayloadProcessor(client)

        if wrapped_token:
            console.print("[yellow]Unwrapping token...[/]")
            res = client.post("/v1/sys/wrapping/unwrap", {"token": wrapped_token})
            payload = res["data"]
            errors = ValidationManager("secret", logger).validate(name, payload=payload)
            if errors:
                console.print("[bold red]Wrapped Payload Validation Failed:[/]")
                for err in errors:
                    console.print(f"  - {err}")
                raise typer.Exit(code=1)
            target_ns = payload.get("_namespace") or namespace
            exec_client = client
            try:
                if target_ns:
                    exec_client = LocalVaultClient(config.api_endpoint, logger, namespace=target_ns)
                    if auth_namespace:
                        exec_client.login(auth_method=auth_method, mount_point=mount_path)
                    else:
                        exec_client.adapter.token = client.adapter.token
                for obj in payload.get("api_paths", []):
                    processor.process(obj)
                exec_client.submit(payload["api_paths"])
            finally:
                if auth_namespace and auth_method != "token" and exec_client is not client:
                    exec_client.logout()
            console.print("[bold green]Wrapped configuration deployed successfully![/]")
        elif path:
            with Progress(console=console) as progress:
                task = progress.add_task("Deploying configuration...", total=len(yaml_files))
                for f_path in yaml_files:
                    progress.update(task, description=f"Processing {os.path.basename(f_path)}")
                    with open(f_path, "r") as f:
                        data = yaml.safe_load(f)

                    target_ns = data.get("_namespace") or namespace
                    exec_client = client
                    try:
                        if target_ns:
                            exec_client = LocalVaultClient(config.api_endpoint, logger, namespace=target_ns)
                            if auth_namespace:
                                exec_client.login(auth_method=auth_method, mount_point=mount_path)
                            else:
                                exec_client.adapter.token = client.adapter.token

                        if "api_paths" not in data:
                            raise KeyError(f"Missing required 'api_paths' key in payload: {f_path}")

                        for obj in data["api_paths"]:
                            processor.process(obj)
                        exec_client.submit(data["api_paths"])
                    finally:
                        if auth_namespace and auth_method != "token" and exec_client is not client:
                            exec_client.logout()
                    progress.advance(task)
            console.print("[bold green]Deployment complete![/]")
    except Exception as e:
        console.print(f"[bold red]Deployment Failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if client and auth_method != "token" and not auth_namespace:
            client.logout()

@secrets_app.command("list")
def secrets_list(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    mount: str = typer.Option(..., "--mount", "-m", help="KV engine mount name"),
    path: str = typer.Option("/", "--path", "-p", help="Vault secret search sub-path"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within namespace"),
    namespace: Optional[str] = typer.Option(None, help="Target Vault namespace"),
):
    """List all secrets at target mount path recursively."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        ns = namespace if namespace else (config.config_env if auth_namespace else None)
        client = LocalVaultClient(config.api_endpoint, logger, namespace=ns)
        client.login(auth_method=auth_method, mount_point=mount_path)

        secret_paths = ops.list_secrets_func(client, mount, path)
        secret_paths.sort()
        for s_path in secret_paths:
            console.print(s_path)

        if auth_method != "token":
            client.logout()
    except Exception as e:
        console.print(f"[bold red]List Failed:[/] {e}")
        raise typer.Exit(code=1)

@secrets_app.command("sync")
def secrets_sync(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    source_namespace: str = typer.Option("", help="Source Vault namespace"),
    source_kv: str = typer.Option(..., help="Source KV engine mount name"),
    source_path: str = typer.Option("/", help="Source path to sync"),
    transit_engine: str = typer.Option("namespace-encryption", help="Transit secret engine name"),
    file_path: str = typer.Option(..., help="Output filepath for encrypted YAML"),
    enable_plaintext: bool = typer.Option(False, help="Enable jasypt plaintext decryption mapping"),
    encrypt_password: str = typer.Option("", envvar="JASYPT_PASSWORD", help="Jasypt decrypt password (prefer JASYPT_PASSWORD envvar)"),
    decrypt_command_path: str = typer.Option("", envvar="DECRYPT_CMD_PATH", help="Path containing decrypt scripts"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    auth_namespace: bool = typer.Option(False, help="Authenticate within namespace"),
):
    """Sync remote secrets into local transit-encrypted YAML configuration."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        auth_ns = source_namespace if not auth_namespace else None
        auth_client = LocalVaultClient(config.api_endpoint, logger, namespace=auth_ns)
        auth_client.login(auth_method=auth_method, mount_point=mount_path)

        client = LocalVaultClient(config.api_endpoint, logger, namespace=source_namespace)
        client.adapter.token = auth_client.adapter.token

        secret_paths = ops.list_secrets_func(client, source_kv, source_path)
        for s_path in secret_paths:
            api_object = {}
            api_path = "v1/{0}{1}".format(source_kv, s_path)
            api_payload = client.get(api_path)['data']

            api_object['api_action'] = 'post'
            api_object['api_path'] = api_path
            api_object['transit_encoded_keys'] = ops.get_transit_encoded_keys(api_payload)
            api_object['transit_key'] = transit_engine
            api_object['transit_secret_engine'] = 'transit'

            transit_encrypt_api_path = f"v1/transit/encrypt/{transit_engine}"
            transit_decrypt_api_path = f"v1/transit/decrypt/{transit_engine}"
            json_file = f"{file_path}/secrets/{source_kv}{s_path}.json"

            older_json_payload = {}
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        older_json_payload = json.load(f)["api_paths"][0]['api_payload']
                except (OSError, json.JSONDecodeError, KeyError, IndexError):
                    pass

            api_object['api_payload'] = ops.encrypt_api_payload(
                client, api_payload, older_json_payload,
                transit_encrypt_api_path, transit_decrypt_api_path, api_path,
                str(enable_plaintext), encrypt_password, decrypt_command_path
            )

            json_payload = {
                '_namespace': source_namespace,
                'api_paths': [api_object]
            }
            console.print(f"Writing synced secrets to [cyan]{json_file}[/]")
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, "w") as f:
                json.dump(json_payload, f, indent=2, sort_keys=True)

        if auth_method != "token":
            auth_client.logout()
        console.print("[bold green]Synchronization Complete![/]")
    except Exception as e:
        console.print(f"[bold red]Sync Failed:[/] {e}")
        raise typer.Exit(code=1)

@secrets_app.command("validate")
def secrets_validate(
    directory: str = typer.Option("./config/json_workspaces", help="Directory containing JSON/YAML files"),
    allow_file_regex: str = typer.Option("**/*.json", help="Glob pattern of files to scan"),
    scheme: str = typer.Option("namespaces", help="Validation scheme for YAML payloads (namespaces, admin, secret)"),
):
    """Validate JSON syntax or Vault YAML payloads against Pydantic and policy guardrails."""
    logger = logging.getLogger("vault-ctl")
    invalid_files = []
    yaml_files = []
    path_pattern = os.path.join(directory, allow_file_regex)
    for filepath in glob.iglob(path_pattern, recursive=True):
        if os.path.isdir(filepath):
            continue
        if filepath.endswith((".yaml", ".yml")):
            yaml_files.append(filepath)
        else:
            try:
                with open(filepath, 'r') as f:
                    json.load(f)
            except (OSError, json.JSONDecodeError):
                invalid_files.append(filepath)

    yaml_errors = []
    if yaml_files:
        yaml_files.sort()
        yaml_errors = ValidationManager(scheme, logger).validate("validate", files=yaml_files)

    if invalid_files or yaml_errors:
        if invalid_files:
            console.print("[bold red]Invalid JSON Files Found:[/]")
            for f in invalid_files:
                console.print(f"  - {f}")
        if yaml_errors:
            console.print("[bold red]YAML Validation Errors Found:[/]")
            for err in yaml_errors:
                console.print(f"  - {err}")
        raise typer.Exit(code=1)
    else:
        console.print("[bold green]All files in the directory are valid.[/]")

@secrets_app.command("encrypt")
def secrets_encrypt(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    path: str = typer.Option(..., "--path", "-p", help="Path to plaintext YAML file or directory"),
    transit_engine: str = typer.Option("transit", help="Transit secret engine name"),
    transit_key: str = typer.Option("namespace-encryption", help="Transit key name"),
    transit_context: str = typer.Option("", help="Transit cryptographic context context"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    namespace: str = typer.Option("", help="Vault namespace"),
):
    """Encrypt YAML fields using Vault Transit secrets engine."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        client = LocalVaultClient(config.api_endpoint, logger, namespace=namespace)
        client.login(auth_method=auth_method, mount_point=mount_path)
        ops.handle_encrypt(client, path, transit_engine, transit_key, transit_context)
        if auth_method != "token":
            client.logout()
        console.print("[bold green]Encryption operation completed successfully![/]")
    except Exception as e:
        console.print(f"[bold red]Encryption Failed:[/] {e}")
        raise typer.Exit(code=1)

@secrets_app.command("decrypt")
def secrets_decrypt(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    path: str = typer.Option(..., "--path", "-p", help="Path to encrypted YAML file or directory"),
    transit_engine: str = typer.Option("transit", help="Transit secret engine name"),
    transit_key: str = typer.Option("namespace-encryption", help="Transit key name"),
    transit_context: str = typer.Option("", help="Transit cryptographic context context"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    namespace: str = typer.Option("", help="Vault namespace"),
):
    """Decrypt Vault Transit ciphertext fields inside YAML files."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        client = LocalVaultClient(config.api_endpoint, logger, namespace=namespace)
        client.login(auth_method=auth_method, mount_point=mount_path)
        ops.handle_decrypt(client, path, transit_engine, transit_key, transit_context)
        if auth_method != "token":
            client.logout()
        console.print("[bold green]Decryption operation completed successfully![/]")
    except Exception as e:
        console.print(f"[bold red]Decryption Failed:[/] {e}")
        raise typer.Exit(code=1)

@secrets_app.command("decode")
def secrets_decode(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    path: str = typer.Option(..., "--path", "-p", help="Path to YAML file or directory"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    namespace: str = typer.Option("", help="Vault namespace"),
):
    """Base64-decode fields in YAML payload files."""
    logger = logging.getLogger("vault-ctl")
    try:
        config = settings.get_cluster(name)
        client = LocalVaultClient(config.api_endpoint, logger, namespace=namespace)
        client.login(auth_method=auth_method, mount_point=mount_path)
        ops.handle_decode(client, path)
        if auth_method != "token":
            client.logout()
        console.print("[bold green]Decode operation completed successfully![/]")
    except Exception as e:
        console.print(f"[bold red]Decode Failed:[/] {e}")
        raise typer.Exit(code=1)

@secrets_app.command("encrypt-string")
def secrets_encrypt_string(
    name: str = typer.Option(..., "--name", "-n", help="Cluster name"),
    string: str = typer.Option(
        ...,
        prompt="Plaintext string to encrypt",
        hide_input=True,
        envvar="VAULT_PLAINTEXT_STRING",
        help="Plaintext string to encrypt (prompted or via VAULT_PLAINTEXT_STRING)",
    ),
    encode_string: bool = typer.Option(True, help="Encode string into base64 before encryption"),
    transit_engine: str = typer.Option("transit", help="Transit secret engine name"),
    transit_key: str = typer.Option("namespace-encryption", help="Transit key name"),
    transit_context: str = typer.Option("", help="Transit cryptographic context context"),
    auth_method: str = typer.Option("ldap", help="Vault auth method"),
    mount_path: str = typer.Option("ldap", help="Vault auth mount path"),
    namespace: str = typer.Option("", help="Vault namespace"),
):
    """Encrypt a single plaintext string via Vault Transit."""
    logger = logging.getLogger("vault-ctl")
    client = None
    try:
        config = settings.get_cluster(name)
        client = LocalVaultClient(config.api_endpoint, logger, namespace=namespace)
        client.login(auth_method=auth_method, mount_point=mount_path)
        cipher = ops.handle_encrypt_string(
            client, string, str(encode_string), transit_engine, transit_key, transit_context
        )
        console.print(f"[bold green]Resulting Ciphertext:[/] {cipher}")
    except Exception as e:
        console.print(f"[bold red]Encrypt String Failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if client and auth_method != "token":
            client.logout()

@app.command("backup")
def backup_cmd(
    mode: str = typer.Argument(..., help="Mode: backup or restore"),
    vault_path: str = typer.Argument(..., help="Path within Vault to back up"),
    vault_cluster: str = typer.Argument(..., help="Vault Cluster name"),
    vault_ldap: str = typer.Option("ldap", help="LDAP path"),
    vault_namespace: str = typer.Option("puppet", help="Target namespace"),
):
    """Perform Vault path backup or restoration."""
    try:
        cluster_config = settings.get_cluster(vault_cluster)
        ops.login(cluster_config, vault_ldap, vault_namespace)

        if mode == "backup":
            json_out = ops.backup(vault_path, vault_cluster)
            console.print(f"[bold green]Backup saved to {json_out}[/]")
        elif mode == "restore":
            ops.restore(vault_path, vault_cluster)
            console.print("[bold green]Restored successfully![/]")
    except Exception as e:
        console.print(f"[bold red]Backup/Restore Operation Failed:[/] {e}")
        raise typer.Exit(code=1)

@app.command("generate")
def generate_secrets(
    name: str = typer.Option(..., "--name", "-n", help="Vault Cluster name"),
    rules: str = typer.Option("config/generation_rules.yaml", help="Path to rules engine"),
    template: str = typer.Option(..., help="Input template YAML file path"),
    output: str = typer.Option(..., help="Target output YAML file path"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Orchestrate secret generation based on external rules engine."""
    logger = logging.getLogger("vault-ctl")
    try:
        # Validate cluster exists
        settings.get_cluster(name)
        rules_path = rules
        if not os.path.isabs(rules_path):
            rules_path = os.path.abspath(rules_path)

        generator = ops.SecretGenerator(rules_path, logger)
        generator.process_template(template, output)
        console.print(f"[bold green]Template {template} successfully generated to {output}[/]")
    except Exception as e:
        console.print(f"[bold red]Generation Failed:[/] {e}")
        raise typer.Exit(code=1)

@app.callback()
def main_callback(
    log_level: str = typer.Option("INFO", help="Logging level"),
):
    """Modern Vault Controller CLI."""
    setup_logging(log_level)

if __name__ == "__main__":
    app()
