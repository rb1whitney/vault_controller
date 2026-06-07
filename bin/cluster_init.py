import argparse
import json
import os
import sys
import time

import urllib3
import yaml

# Don't write byte code for imported libraries
sys.dont_write_bytecode = True

# Import Ruthlessly Refactored Libraries
from projects.vault.lib.core.client import LocalVaultClient
from projects.vault.lib.core.logger import get_logger
from projects.vault.lib.engines.payload_processor import PayloadProcessor
from projects.vault.lib.utils import config as vault_config
from projects.vault.lib.utils import crypto as vault_crypto


def rekey(client, keys, secret_threshold, pgp_keys=None, backup=True, auto_unseal=False):
    """Orchestrates the rekeying of a Vault cluster."""
    api_payload = {"secret_shares": len(keys), "secret_threshold": secret_threshold}
    if pgp_keys:
        api_payload["pgp_keys"] = pgp_keys
        api_payload["backup"] = backup

    init_path = "v1/sys/rekey-recovery-key/init" if auto_unseal else "v1/sys/rekey/init"
    update_path = "v1/sys/rekey-recovery-key/update" if auto_unseal else "v1/sys/rekey/update"

    init_response = client.put(init_path, api_payload)

    for key in keys:
        payload = {"key": key, "nonce": init_response["nonce"]}
        res = client.put(update_path, payload)
        if res.get("complete"):
            return res
    return {}


def initialize(client, secret_shares=5, secret_threshold=3, auto_unseal_enabled=False):
    """Performs the initial bootstrap of a Vault cluster."""
    payload = {}
    if auto_unseal_enabled:
        payload = {
            "recovery_shares": secret_shares,
            "stored_shares": secret_shares,
            "recovery_threshold": secret_threshold,
        }
    else:
        payload = {"secret_shares": secret_shares, "secret_threshold": secret_threshold}

    return client.put("v1/sys/init", payload)


def unseal_host(logger, host, keys):
    """Unseals a specific Vault node."""
    unseal_client = LocalVaultClient(host, logger)
    for key in keys:
        res = unseal_client.put("v1/sys/unseal", {"key": key})
        if not res.get("sealed"):
            break


def init_cluster(cluster_name, server_endpoints, logger, key_holders, **kwargs):
    """High-level cluster bootstrap orchestrator."""
    client = LocalVaultClient(server_endpoints[0], logger)
    init_res = initialize(client, **kwargs)
    root_token = init_res["root_token"]
    keys = init_res.get("recovery_keys") if kwargs.get("auto_unseal_enabled") else init_res.get("keys")

    logger.info(f"Initialized {cluster_name} at {server_endpoints[0]}")

    if not kwargs.get("auto_unseal_enabled"):
        for endpoint in server_endpoints:
            unseal_host(logger, endpoint, keys)

    if kwargs.get("rekey_cluster"):
        time.sleep(10)
        pgp_keys = vault_crypto.gather_pgp_keys(key_holders)
        rekey_res = rekey(client, keys, kwargs.get("secret_threshold"), pgp_keys=pgp_keys)
        key_output = vault_crypto.format_key_response(rekey_res, key_holders, True)
    else:
        key_output = vault_crypto.format_key_response(init_res, key_holders, False)

    # Security Fix: Mask shards in logs
    logger.info(f"Cluster keys generated. Root token: {root_token[:4]}...{root_token[-4:]}")
    return root_token


def main():
    parser = argparse.ArgumentParser(description="Vault Cluster Bootstrapper")
    parser.add_argument("--name", required=True, help="Cluster name from contexts.yaml")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    if "DEBUG" not in args.log_level:
        sys.tracebacklimit = 0

    config = vault_config.get_cluster_config(args.name)
    logger = get_logger("VaultInit", args.log_level)

    # 1. Bootstrap Cluster
    root_token = init_cluster(
        cluster_name=args.name,
        server_endpoints=config["server_endpoints"],
        logger=logger,
        key_holders=config["key_holders"],
        secret_shares=len(config["key_holders"]),
        secret_threshold=config["key_threshold"],
        rekey_cluster=config["key_encrypt"],
        auto_unseal_enabled=config["recovery_key"],
    )

    # 2. Provision Admin State
    client = LocalVaultClient(config["server_endpoints"][0], logger)
    client.adapter.token = root_token
    processor = PayloadProcessor(client)

    admin_path = os.path.join(os.path.dirname(__file__), "../config/example_vault/admin/")
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
            target_client = LocalVaultClient(config["api_endpoint"], logger, namespace=data["_namespace"])
            target_client.adapter.token = client.adapter.token

        for obj in data.get("api_paths", []):
            processor.process(obj)
        target_client.submit(data["api_paths"])


if __name__ == "__main__":
    main()
