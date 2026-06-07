import glob
import os
import shutil
import subprocess
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


def run_cluster_secret_data(args, env):
    """
    Helper to run bin/cluster_secret_data.py with proper pythonpath and environment
    """
    repo_root = os.getcwd()
    script_path = os.path.join(repo_root, "projects/vault/bin/cluster_secret_data.py")
    cmd = ["python3", script_path, "--name", "example_vault", "--auth-method", "token"] + args
    # Ensure we run from projects/vault so relative config paths in tests work
    vault_root = os.path.join(repo_root, "projects/vault")
    return subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=vault_root)


def test_spinning_up_cluster_admin_config(vault_server):
    env = vault_server
    result = run_cluster_secret_data(["--path", "./config/example_vault/admin"], env)
    assert result.returncode == 0, f"Setup failed: {result.stderr}"

def test_spinning_up_cluster_app1_config(vault_server):
    env = vault_server
    repo_root = os.getcwd()
    # 1. Admin config
    res1 = run_cluster_secret_data(["--path", "./config/example_vault/admin"], env)
    assert res1.returncode == 0

    # 2. App1 specific config files
    # Instead of find, we just iterate or run on the specific YAML files
    app1_configs = glob.glob("./projects/vault/config/example_vault/app1/*.yaml")
    for f in app1_configs:
        # We need to strip the projects/vault prefix because run_cluster_secret_data sets cwd to projects/vault
        rel_f = os.path.relpath(f, "projects/vault")
        res2 = run_cluster_secret_data(["--path", rel_f], env)
        assert res2.returncode == 0

    # 2.1 Mount engines for new projects
    res_mount1 = run_cluster_secret_data(["--path", "./config/example_vault/cloud-boot-app/_secret_engines.yaml"], env)
    assert res_mount1.returncode == 0
    res_mount2 = run_cluster_secret_data(["--path", "./config/example_vault/nit-fabric/_secret_engines.yaml"], env)
    assert res_mount2.returncode == 0

    # 3. Vault transit write
    fixture_path = os.path.join(repo_root, "projects/vault/tests/fixtures/app1-transit-key")

    with open(fixture_path, "r") as f:
        backup_val = f.read().strip()

    cmd_transit = [
        "vault",
        "write",
        "/transit/restore/app1-transit-key",
        f"backup={backup_val}",
        "force=true",
    ]
    res3 = subprocess.run(cmd_transit, env=env, capture_output=True, text=True)
    assert res3.returncode == 0

    # 4. App1 kv
    res4 = run_cluster_secret_data(["--path", "./config/example_vault/app1/kv/"], env)
    assert res4.returncode == 0

    # 5. Cloud Boot App kv
    res5 = run_cluster_secret_data(["--path", "./config/example_vault/cloud-boot-app/kv/"], env)
    assert res5.returncode == 0

    # 6. NIT-Fabric kv
    res6 = run_cluster_secret_data(["--path", "./config/example_vault/nit-fabric/kv/"], env)
    assert res6.returncode == 0


def test_spinning_up_improperly_written_yaml(vault_server):
    env = vault_server
    result = run_cluster_secret_data(
        ["--path", "./tests/fixtures/invalid-file.yaml"], env
    )
    assert result.returncode != 0


def test_spinning_up_invalid_yaml_file(vault_server):
    env = vault_server
    result = run_cluster_secret_data(
        ["--path", "./tests/fixtures/invalid-payload.yaml"], env
    )
    assert result.returncode != 0


def test_logging_into_cluster(vault_server):
    env = vault_server
    repo_root = os.getcwd()
    res1 = run_cluster_secret_data(["--path", "./config/example_vault/admin"], env)
    assert res1.returncode == 0

    username = "vaultdeveloper1"
    # Parse password from tests/fixtures/ldap.ldif
    password = None
    ldap_fixture = os.path.join(repo_root, "projects/vault/tests/fixtures/ldap.ldif")
    with open(ldap_fixture, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"uid: {username}"):
                for check_line in lines[i : i + 4]:
                    if "userpassword:" in check_line.lower():
                        password = check_line.split(" ")[1].strip()
                        break
                break
    assert password is not None
