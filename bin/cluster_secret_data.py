import argparse
import os
import re
import sys

import urllib3
import yaml

# Don't write byte code for imported libraries
sys.dont_write_bytecode = True

# Import Ruthlessly Refactored Libraries
from projects.vault.lib.core.client import LocalVaultClient
from projects.vault.lib.engines.payload_processor import PayloadProcessor
from projects.vault.lib.utils import config as vault_config
from projects.vault.lib.validation.manager import ValidationManager

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def validate_input(cluster_name, validation_type, file_filter, yaml_files, logger):
    """Business logic validation before execution."""
    validator = ValidationManager(validation_type, logger)
    files_to_check = list(filter(re.compile(file_filter).match, yaml_files))
    if files_to_check:
        errors = validator.validate(cluster_name, files=files_to_check)
        if errors:
            raise ValueError(f"Validation failed for {validation_type}: {errors}")


def main():
    parser = argparse.ArgumentParser(description="Vault Secret Data Manager")
    parser.add_argument("--name", required=True, help="Vault Cluster Name")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", help="Path to YAML config files")
    group.add_argument("--wrapped-token", help="Wrapped token for secret delivery")

    parser.add_argument("--namespace", help="Target Vault namespace", default=None)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--auth-method", default="ldap")
    parser.add_argument("--mount-path", dest="mount_point", default="ldap")
    parser.add_argument("--auth-namespace", default="False")
    args = parser.parse_args()

    # Get Config and Initialize Client
    config = vault_config.get_cluster_config(args.name)
    from projects.vault.lib.core.logger import get_logger

    logger = get_logger("SecretData", args.log_level)

    client = LocalVaultClient(config["api_endpoint"], logger)
    if args.auth_namespace == "False":
        client.login(auth_method=args.auth_method, mount_point=args.mount_point)

    processor = PayloadProcessor(client)

    if args.wrapped_token:
        # Handle wrapped payload
        res = client.post("/v1/sys/wrapping/unwrap", {"token": args.wrapped_token})
        payload = res["data"]
        
        # In-line processing and submission
        for obj in payload.get("api_paths", []):
            processor.process(obj)
        client.submit(payload["api_paths"])
    else:
        # Batch process YAML files
        yaml_files = []
        if os.path.isdir(args.path):
            for root, _, files in os.walk(args.path):
                for f in files:
                    if f.endswith((".yaml", ".yml")):
                        yaml_files.append(os.path.join(root, f))
        else:
            yaml_files.append(args.path)
        yaml_files.sort()

        # Validate
        validate_input(args.name, "namespaces", ".*/namespaces/.*", yaml_files, logger)
        validate_input(args.name, "admin", ".*/admin/.*", yaml_files, logger)

        for f_path in yaml_files:
            logger.info(f"Processing payload: {f_path}")
            with open(f_path, "r") as f:
                data = yaml.safe_load(f)

            # Resolve namespace
            target_ns = data.get("_namespace") or args.namespace
            exec_client = client
            if target_ns:
                exec_client = LocalVaultClient(config["api_endpoint"], logger, namespace=target_ns)
                if args.auth_namespace == "True":
                    exec_client.login(auth_method=args.auth_method, mount_point=args.mount_point)
                else:
                    exec_client.adapter.token = client.adapter.token

            # Transform and Submit
            for obj in data.get("api_paths", []):
                processor.process(obj)
            exec_client.submit(data["api_paths"])

    if args.auth_method != "token":
        client.logout()


if __name__ == "__main__":
    main()
