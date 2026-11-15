import glob
import os
import shutil
import subprocess
import sys
import time

import pytest

VAULT_DEV_LISTEN_ADDRESS = "localhost:8200"
VAULT_DEV_ROOT_TOKEN_ID = "ePTlEeggAGoYE1OMGiUas8du"


@pytest.fixture(scope="function")
def vault_server():
    """
    Spins up a dev vault server and cleans it up after the test completes.
    """
    env = os.environ.copy()
    env["VAULT_DEV_LISTEN_ADDRESS"] = VAULT_DEV_LISTEN_ADDRESS
    env["VAULT_DEV_ROOT_TOKEN_ID"] = VAULT_DEV_ROOT_TOKEN_ID
    env["VAULT_TOKEN"] = VAULT_DEV_ROOT_TOKEN_ID
    env["VAULT_ADDR"] = f"http://{VAULT_DEV_LISTEN_ADDRESS}"
    env["VAULT_AUTH_TYPE"] = "token"
    env["VAULT_AUTH_SECRET"] = VAULT_DEV_ROOT_TOKEN_ID

    # Start the vault server in the background
    if not shutil.which("vault"):
        pytest.skip("Vault binary not found in PATH")

    process = subprocess.Popen(
        ["vault", "server", "-dev", "-dev-no-store-token"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for vault to initialize
    time.sleep(2)

    yield env

    # Teardown
    process.terminate()
    process.wait()


def run_secrets_deploy(args, env):
    """
    Helper to run bin/vault_ctl.py secrets deploy with proper pythonpath and environment
    """
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(vault_root, "bin/vault_ctl.py")
    cmd = [sys.executable, script_path, "secrets", "deploy", "--name", "example_vault", "--auth-method", "token", *args]
    
    # Merge current environment to ensure PYTHONPATH and other settings are preserved
    full_env = os.environ.copy()
    full_env.update(env)
    # Ensure repo root is in PYTHONPATH
    full_env["PYTHONPATH"] = vault_root + (":" + full_env.get("PYTHONPATH", "") if full_env.get("PYTHONPATH") else "")
    
    return subprocess.run(cmd, env=full_env, capture_output=True, text=True, cwd=vault_root, check=False)


def test_spinning_up_cluster_admin_config(vault_server):
    env = vault_server
    result = run_secrets_deploy(["--path", "./config/example_vault/admin"], env)
    assert result.returncode == 0, f"Setup failed: {result.stderr}"

def test_spinning_up_cluster_app1_config(vault_server):
    env = vault_server
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # 1. Admin config
    res1 = run_secrets_deploy(["--path", "./config/example_vault/admin"], env)
    assert res1.returncode == 0, f"Admin deploy failed: {res1.stdout} {res1.stderr}"

    # 2. App1 specific config files
    app1_configs = sorted(glob.glob(os.path.join(vault_root, "config/example_vault/app1/*.yaml")))
    for f in app1_configs:
        rel_f = os.path.relpath(f, vault_root)
        res2 = run_secrets_deploy(["--path", rel_f], env)
        assert res2.returncode == 0, f"App1 config {rel_f} failed: {res2.stdout} {res2.stderr}"

    # 2.1 Mount engines for new projects
    res_mount1 = run_secrets_deploy(["--path", "./config/example_vault/cloud-boot-app/_secret_engines.yaml"], env)
    assert res_mount1.returncode == 0, res_mount1.stdout
    res_mount2 = run_secrets_deploy(["--path", "./config/example_vault/nit-fabric/_secret_engines.yaml"], env)
    assert res_mount2.returncode == 0, res_mount2.stdout

    # 3. Vault transit key restores
    for key_name in ("app1-transit-key", "vault-admin-transit-key"):
        fixture_path = os.path.join(vault_root, "tests/fixtures", key_name)
        with open(fixture_path) as f:
            backup_val = f.read().strip()

        cmd_transit = [
            "vault",
            "write",
            f"/transit/restore/{key_name}",
            f"backup={backup_val}",
            "force=true",
        ]
        res3 = subprocess.run(cmd_transit, env=env, capture_output=True, text=True, check=False)
        assert res3.returncode == 0, f"Transit restore failed for {key_name}: {res3.stderr}"

    # 4. App1 kv
    res4 = run_secrets_deploy(["--path", "./config/example_vault/app1/kv/"], env)
    assert res4.returncode == 0, res4.stdout

    # 5. Cloud Boot App kv
    res5 = run_secrets_deploy(["--path", "./config/example_vault/cloud-boot-app/kv/"], env)
    assert res5.returncode == 0, res5.stdout

    # 6. NIT-Fabric kv
    res6 = run_secrets_deploy(["--path", "./config/example_vault/nit-fabric/kv/"], env)
    assert res6.returncode == 0, res6.stdout

    # 7. Verify in-line Transit decryption actually wrote plaintext into Vault KV
    import hvac
    client = hvac.Client(url=env["VAULT_ADDR"], token=env["VAULT_TOKEN"])
    mysql_secret = client.secrets.kv.v2.read_secret_version(
        path="mysql",
        mount_point="cloud-boot-app",
        raise_on_deleted_version=True,
    )["data"]["data"]
    assert mysql_secret["password"] == "VaultPassword2026!"
    assert not mysql_secret["password"].startswith("vault:v1:")

    app1_token = client.read("app1-authenticator/access-token")["data"]
    assert not app1_token["access_key"].startswith("vault:v1:")
    assert not app1_token["secret_key"].startswith("vault:v1:")


def test_spinning_up_improperly_written_yaml(vault_server):
    env = vault_server
    result = run_secrets_deploy(
        ["--path", "./tests/fixtures/invalid-file.yaml"], env
    )
    assert result.returncode != 0


def test_spinning_up_invalid_yaml_file(vault_server):
    env = vault_server
    result = run_secrets_deploy(
        ["--path", "./tests/fixtures/invalid-payload.yaml"], env
    )
    assert result.returncode != 0


def test_logging_into_cluster(vault_server):
    env = vault_server
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res1 = run_secrets_deploy(["--path", "./config/example_vault/admin"], env)
    assert res1.returncode == 0

    username = "vaultdeveloper1"
    # Parse password from tests/fixtures/ldap.ldif
    password = None
    ldap_fixture = os.path.join(vault_root, "tests/fixtures/ldap.ldif")
    with open(ldap_fixture) as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"uid: {username}"):
                for check_line in lines[i : i + 4]:
                    if "userpassword:" in check_line.lower():
                        password = check_line.split(" ")[1].strip()
                        break
                break
    assert password is not None

    # Verify token login works against the ephemeral cluster via LocalVaultClient
    import logging
    from unittest.mock import patch

    from lib.core.client import LocalVaultClient
    with patch.dict(os.environ, {"VAULT_AUTH_TYPE": "token", "VAULT_AUTH_SECRET": env["VAULT_AUTH_SECRET"]}):
        client = LocalVaultClient(env["VAULT_ADDR"], logging.getLogger("test_login"))
        client.login(auth_method="token")
        assert client.hvac_client.is_authenticated()
