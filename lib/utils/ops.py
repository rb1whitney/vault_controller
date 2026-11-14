import base64
import json
import logging
import os
import re
import shlex
import subprocess
import time
import yaml

from lib.core import command as secure_cmd
from lib.core.client import LocalVaultClient
from lib.core.errors import VaultError
from lib.utils import crypto as vault_crypto
from lib.validation.models import validate_cluster_name, validate_path

SAFE_PARAM_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")

class SecretGenerator:
    """
    Orchestrates secret generation based on an external rules engine.
    """
    def __init__(self, rules_path, logger):
        with open(rules_path, "r") as f:
            self.rules_config = yaml.safe_load(f)
        self.logger = logger

    def generate(self, rule_name, **kwargs):
        """Executes a specific generation rule securely."""
        rule = self.rules_config.get("rules", {}).get(rule_name)
        if not rule:
            raise ValueError(f"Rule '{rule_name}' not found in rules engine.")

        for p in rule.get("params", []):
            if p not in kwargs:
                raise ValueError(
                    f"Missing required parameter '{p}' for rule '{rule_name}'."
                )
        for k, v in kwargs.items():
            if not SAFE_PARAM_RE.match(str(v)):
                raise ValueError(
                    f"Unsafe characters in parameter '{k}' for rule '{rule_name}'."
                )

        # Secure split and format execution (prevents shell injection)
        cmd_tokens = shlex.split(rule["command"])
        formatted_cmd = [token.format(**kwargs) for token in cmd_tokens]
        self.logger.info(f"Executing generation rule securely: {rule_name}")

        try:
            result = subprocess.run(
                formatted_cmd,
                shell=False,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Generation failed: {e.stderr}")
            raise e

    def process_template(self, template_path, output_path):
        """Parses a template and replaces placeholders with generated secrets."""
        if ".." in os.path.normpath(output_path).split(os.sep):
            raise ValueError(f"Path traversal not allowed in output path: {output_path}")
        with open(template_path, "r") as f:
            content = f.read()

        pattern = re.compile(r"\{\{\s*(\w+)\((.*?)\)\s*\}\}")

        def replacer(match):
            rule_name = match.group(1)
            params_str = match.group(2)

            kwargs = {}
            if params_str:
                for pair in params_str.split(","):
                    k, v = pair.split("=")
                    kwargs[k.strip()] = v.strip().strip("'").strip('"')

            return self.generate(rule_name, **kwargs)

        processed_content = pattern.sub(replacer, content)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            f.write(processed_content)
        self.logger.info(f"Successfully generated payload: {output_path}")

# Initialize and Unseal Logic
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
    init_res = initialize(
        client,
        secret_shares=kwargs.get("secret_shares", 5),
        secret_threshold=kwargs.get("secret_threshold", 3),
        auto_unseal_enabled=kwargs.get("auto_unseal_enabled", False),
    )
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

    logger.info(f"Cluster keys generated. Root token: {root_token[:4]}...{root_token[-4:]}")
    return root_token, key_output

# Backup / Restore Logic
def login(cluster_config, vault_ldap, vault_namespace):
    api_endpoint = (
        cluster_config.api_endpoint
        if hasattr(cluster_config, "api_endpoint")
        else cluster_config["api_endpoint"]
    )
    os.environ["VAULT_ADDR"] = api_endpoint
    os.environ["VAULT_NAMESPACE"] = vault_namespace
    ldap_user = os.environ.get("LDAP_USERNAME")
    if not ldap_user:
        msg = "LDAP_USERNAME environment variable must be set"
        logging.error(msg)
        raise VaultError(message=msg)

    cmd = [
        "vault",
        "login",
        "-method=ldap",
        f"-path={vault_ldap}",
        f"username={ldap_user}",
    ]
    secure_cmd.run(cmd)

def backup(vault_path, vault_cluster):
    validate_path(vault_path)
    validate_cluster_name(vault_cluster)
    basename = os.path.basename(vault_path.rstrip("/"))
    if not basename:
        raise ValueError(f"Invalid vault_path for backup: {vault_path}")
    bkup_marker = f"backup-{basename}-{vault_cluster}.bkup"
    json_out = f"{basename}-{vault_cluster}.json"

    fd_marker = os.open(bkup_marker, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.close(fd_marker)

    cmd = ["vault", "read", "-format=json", vault_path]
    result = secure_cmd.run(cmd)

    data = json.loads(result.stdout).get("data", {})
    fd_out = os.open(json_out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd_out, "w") as f:
        json.dump(data, f, indent=2)
    return json_out

def restore(vault_path, vault_cluster):
    validate_path(vault_path)
    validate_cluster_name(vault_cluster)
    basename = os.path.basename(vault_path.rstrip("/"))
    if not basename:
        raise ValueError(f"Invalid vault_path for restore: {vault_path}")
    bkup_marker = f"backup-{basename}-{vault_cluster}.bkup"
    json_in = f"{basename}-{vault_cluster}.json"

    if not os.path.exists(bkup_marker):
        raise FileNotFoundError(f"Backup marker {bkup_marker} not found. Aborting.")

    cmd = ["vault", "write", vault_path, f"@{json_in}"]
    secure_cmd.run(cmd)

    os.remove(bkup_marker)

# Rekey Specific Logic
def start_rekey(client, secret_shares, secret_threshold, pgp_keys=None, backup=True, recovery_key=False):
    api_payload = {
        'secret_shares': secret_shares,
        'secret_threshold': secret_threshold,
    }
    if pgp_keys:
        api_payload['pgp_keys'] = pgp_keys
        api_payload['backup'] = backup

    api_path = 'v1/sys/rekey/init'
    if recovery_key:
        api_path = 'v1/sys/rekey-recovery-key/init'
    return client.put(api_path, api_payload)

def rekey_update(client, key, nonce=None, recovery_key=False):
    api_payload = { 'key': key }
    if nonce is not None:
        api_payload['nonce'] = nonce

    api_path = 'v1/sys/rekey/update'
    if recovery_key:
        api_path = 'v1/sys/rekey-recovery-key/update'
    return client.put(api_path, api_payload)

def cancel_rekey(client, recovery_key=False):
    api_path = 'v1/sys/rekey/init'
    if recovery_key:
        api_path = 'v1/sys/rekey-recovery-key/init'
    return client.delete(api_path)

# Secrets list, validate, sync and encryption logic
def list_secrets_func(client, mount_name, mount_path):
    mount_secrets = []
    mount_path = mount_path.replace('//','')    
    if mount_path.endswith('/'):
        api_path = "/v1/{0}/{1}".format(mount_name, mount_path)
        secret_paths = client.list(api_path)['data']['keys']
        for secret_path in secret_paths:
            if '/' in secret_path:
                new_mount_path = "{0}{1}".format(mount_path, secret_path)
                results = list_secrets_func(client, mount_name, new_mount_path)
                mount_secrets.extend(results)
            else:
                path_suffix = mount_path if mount_path.startswith('/') else "/{0}".format(mount_path)
                mount_secrets.append("{0}{1}".format(path_suffix, secret_path))
    else:
        mount_secrets.append(mount_path)
    return mount_secrets

def encrypt_api_payload(client, payload, older_json_payload, transit_encrypt_api_path, transit_decrypt_api_path, api_path, enable_plaintext_secrets, decrypt_password, decrypt_cmd_path):
    encrypted_payload = {}
    for key, value in list(payload.items()):
        if isinstance(value, dict):
            older_value = older_json_payload[key] if older_json_payload and key in older_json_payload else {}
            encrypted_payload[key] = encrypt_api_payload(
                client, value, older_value, transit_encrypt_api_path, 
                transit_decrypt_api_path, api_path, enable_plaintext_secrets, decrypt_password, decrypt_cmd_path)
        else:
            value_list = [value]
            if isinstance(value, list):
                value_list = value
                encrypted_payload[key] = []
            for index, current_value in enumerate(value_list):
                older_value = ''
                older_encrypted_value = ''
                if older_json_payload and key in older_json_payload:
                    older_json_payload_value = older_json_payload[key]
                    older_json_payload_value_list = older_json_payload_value if isinstance(older_json_payload_value, list) else [older_json_payload_value]
                    older_encrypted_value = older_json_payload_value_list[index] if index < len(older_json_payload_value_list) else ''
                    
                    if older_encrypted_value:
                        decrypt_payload = { 'ciphertext': older_encrypted_value }
                        try:
                            decrypted_payload = client.post(transit_decrypt_api_path, decrypt_payload)
                            try:
                                older_value = str(base64.b64decode(decrypted_payload['data']['plaintext']), 'UTF-8')
                            except ValueError:
                                older_value = str(base64.b64decode(decrypted_payload['data']['plaintext']))
                        except (VaultError, KeyError, ValueError):
                            older_value = ''

                encrypted_payload_value = None
                if older_value != current_value:
                    base64_value = str(base64.b64encode(str(current_value).encode('UTF-8')), 'UTF-8')
                    transit_payload = {'plaintext': base64_value}
                    encrypted_data = client.post(transit_encrypt_api_path, transit_payload)
                    if 'error' in encrypted_data:
                        msg = "Vault unable to parse {0} at api_path: {2} with error: {1}".format(
                            key, encrypted_data['error'], api_path
                        )
                        client.logger.error(msg)
                        raise VaultError(message=msg)
                    
                    encrypted_payload_value = encrypted_data['data']['ciphertext']
                else:
                    encrypted_payload_value = older_encrypted_value
                    
                if isinstance(value, list):
                    encrypted_payload[key].append(encrypted_payload_value)
                else:
                    encrypted_payload[key] = encrypted_payload_value
                
                if(enable_plaintext_secrets == 'True' and "ENC(" in str(older_value)) and not current_value == 'changeme':
                    cleaned_jasypt_value = str(older_value).replace('ENC(','').replace(')','')
                    
                    # Safe isolated subprocess environment execution (no parent process environment pollution)
                    sub_env = os.environ.copy()
                    sub_env["encrypt_password"] = decrypt_password
                    sub_env["encrypt_secret"] = cleaned_jasypt_value
                    
                    decrypted_secret = secure_cmd.run(['sh', 'decrypt_env.sh'], cwd=decrypt_cmd_path, env=sub_env).stdout
                    base64_value = str(base64.b64encode(decrypted_secret.encode('UTF-8')), 'UTF-8')
                    transit_payload = {'plaintext': base64_value}
                    encrypted_data = client.post(transit_encrypt_api_path, transit_payload)
                    plaintext_key = "{}_plaintext".format(key)
                    encrypted_payload[plaintext_key] = encrypted_data['data']['ciphertext']

    return encrypted_payload

def get_transit_encoded_keys(value, key_path=""):
    transit_encoded_keys = []
    for k, v in value.items():
        full_key = f"{key_path}.{k}" if key_path else k
        if isinstance(v, dict):
            transit_encoded_keys.extend(get_transit_encoded_keys(v, full_key))
        else:
            transit_encoded_keys.append(full_key)
    return transit_encoded_keys

# Private helper to unify handle_encrypt and handle_decrypt YAML walk/rewrite logic
def _process_yaml_payloads(path, client, callback):
    yaml_files = get_yaml_files(path)
    for yaml_file in yaml_files:
        client.logger.debug("Processing {0}".format(yaml_file))
        with open(yaml_file, "r") as f:
            yaml_payload = yaml.safe_load(f)

        modified = False
        for api_object in yaml_payload.get("api_paths", []):
            if callback(api_object):
                modified = True

        if modified:
            with open(yaml_file, "w") as f:
                yaml.dump(yaml_payload, f, default_flow_style=False, sort_keys=True)

# Encryption / Decryption / Decode
def validate_batch_result(client, batch_result, key, path):
    if "error" in batch_result:
        msg = "Vault unable to parse {0} at api_path: {1} with error: {2}".format(
            key, path, batch_result["error"]
        )
        client.logger.error(msg)
        raise VaultError(message=msg)

def get_yaml_files(path):
    yaml_files = []
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    yaml_files.append(os.path.join(root, file))
    else:
        yaml_files.append(path)
    yaml_files.sort()
    return yaml_files

def handle_decode(client, path):
    def decode_callback(api_object):
        if "decode_base64_keys" in api_object and api_object["decode_base64_keys"]:
            api_payload = api_object["api_payload"]
            for key_name in api_object["decode_base64_keys"]:
                decrypt_value = _get_nested_value(api_payload, key_name)
                decrypt_value_list = (
                    decrypt_value if isinstance(decrypt_value, list) else [decrypt_value]
                )
                for index, decrypt_value_item in enumerate(decrypt_value_list):
                    decrypt_value_list[index] = str(
                        base64.b64decode(decrypt_value_item), "UTF-8"
                    )
                decoded = (
                    decrypt_value_list
                    if isinstance(decrypt_value, list)
                    else decrypt_value_list[0]
                )
                _set_nested_value(api_payload, key_name, decoded)
            api_object["decode_base64_keys"] = []
            return True
        return False

    _process_yaml_payloads(path, client, decode_callback)

def _get_nested_value(data, dot_path):
    """Retrieve a value from a nested dict using a dot-separated key path."""
    cur = data
    for part in dot_path.split("."):
        cur = cur[part]
    return cur


def _set_nested_value(data, dot_path, value):
    """Set a value in a nested dict using a dot-separated key path."""
    parts = dot_path.split(".")
    cur = data
    for part in parts[:-1]:
        cur = cur[part]
    cur[parts[-1]] = value


def _collect_leaf_paths(data, prefix=""):
    """Collect dot-separated paths for all non-dict leaf values in api_payload."""
    paths = []
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            paths.extend(_collect_leaf_paths(v, full_key))
        else:
            paths.append(full_key)
    return paths


def handle_decrypt(client, path, transit_engine="transit", transit_key="namespace-encryption", transit_context=""):
    def decrypt_callback(api_object):
        if "transit_encoded_keys" in api_object and api_object["transit_encoded_keys"]:
            transit_secret_engine = (
                api_object.get("transit_secret_engine")
                or api_object.get("transit_engine")
                or transit_engine
            )
            tk = api_object.get("transit_key", transit_key)
            transit_api_path = "v1/{0}/decrypt/{1}".format(
                transit_secret_engine, tk
            )
            for key_name in api_object["transit_encoded_keys"]:
                val = _get_nested_value(api_object["api_payload"], key_name)
                ctx = api_object.get("transit_context", transit_context) if ("transit_context" in api_object or transit_context != "") else None
                if isinstance(val, list):
                    decrypted_list = []
                    for item in val:
                        tp = {"ciphertext": item}
                        if ctx is not None:
                            tp["context"] = ctx
                        res = client.post(transit_api_path, tp)
                        decrypted_list.append(str(base64.b64decode(res["data"]["plaintext"]), "UTF-8"))
                    _set_nested_value(api_object["api_payload"], key_name, decrypted_list)
                else:
                    tp = {"ciphertext": val}
                    if ctx is not None:
                        tp["context"] = ctx
                    res = client.post(transit_api_path, tp)
                    _set_nested_value(
                        api_object["api_payload"],
                        key_name,
                        str(base64.b64decode(res["data"]["plaintext"]), "UTF-8"),
                    )
            api_object["transit_encoded_keys"] = []
            return True
        return False

    _process_yaml_payloads(path, client, decrypt_callback)

def handle_encrypt(client, path, transit_engine="transit", transit_key="namespace-encryption", transit_context=""):
    def encrypt_callback(api_object):
        if "transit_encoded_keys" in api_object and api_object["transit_encoded_keys"]:
            # Perform decrypt check first as in legacy logic
            transit_secret_engine = (
                api_object.get("transit_secret_engine")
                or api_object.get("transit_engine")
                or transit_engine
            )
            tk = api_object.get("transit_key", transit_key)
            transit_api_path = "v1/{0}/decrypt/{1}".format(
                transit_secret_engine, tk
            )
            for key_name in api_object["transit_encoded_keys"]:
                val = _get_nested_value(api_object["api_payload"], key_name)
                ctx = api_object.get("transit_context", transit_context) if ("transit_context" in api_object or transit_context != "") else None
                if isinstance(val, list):
                    decrypted_list = []
                    for item in val:
                        tp = {"ciphertext": item}
                        if ctx is not None:
                            tp["context"] = ctx
                        res = client.post(transit_api_path, tp)
                        decrypted_list.append(str(base64.b64decode(res["data"]["plaintext"]), "UTF-8"))
                    _set_nested_value(api_object["api_payload"], key_name, decrypted_list)
                else:
                    tp = {"ciphertext": val}
                    if ctx is not None:
                        tp["context"] = ctx
                    res = client.post(transit_api_path, tp)
                    _set_nested_value(
                        api_object["api_payload"],
                        key_name,
                        str(base64.b64decode(res["data"]["plaintext"]), "UTF-8"),
                    )

        api_payload = api_object["api_payload"]
        base64_encoded_keys = api_object.get("decode_base64_keys", [])
        leaf_keys = _collect_leaf_paths(api_payload)

        api_object["transit_secret_engine"] = transit_engine
        api_object["transit_key"] = transit_key
        api_object["transit_encoded_keys"] = leaf_keys

        if "decode_base64_keys" in api_object:
            api_object.pop("decode_base64_keys")
        if transit_context != "":
            api_object["transit_context"] = transit_context

        data_to_encrypt = []
        for key_name in leaf_keys:
            encrypt_value = _get_nested_value(api_payload, key_name)
            encrypt_value_list = (
                encrypt_value if isinstance(encrypt_value, list) else [encrypt_value]
            )
            for encrypt_value_item in encrypt_value_list:
                encrypt_payload = {}
                if key_name not in base64_encoded_keys:
                    encrypt_value_item = str(
                        base64.b64encode(str(encrypt_value_item).encode("UTF-8")),
                        "UTF-8",
                    )
                encrypt_payload["plaintext"] = encrypt_value_item
                if transit_context != "":
                    encrypt_payload["context"] = transit_context
                data_to_encrypt.append(encrypt_payload)

        transit_payload = {"batch_input": data_to_encrypt}
        transit_api_path = "v1/{0}/encrypt/{1}".format(
            transit_engine, transit_key
        )
        encrypted_payload = client.post(transit_api_path, transit_payload)

        batch_results = encrypted_payload["data"]["batch_results"]
        for key_name in leaf_keys:
            current_val = _get_nested_value(api_payload, key_name)
            if isinstance(current_val, list):
                array_length = len(current_val)
                batch_result_list = batch_results[:array_length]
                for batch_result in batch_result_list:
                    validate_batch_result(
                        client, batch_result, key_name, api_object["api_path"]
                    )
                _set_nested_value(
                    api_payload,
                    key_name,
                    [b["ciphertext"] for b in batch_result_list],
                )
                batch_results = batch_results[array_length:]
            else:
                batch_result = batch_results.pop(0)
                validate_batch_result(
                    client, batch_result, key_name, api_object["api_path"]
                )
                _set_nested_value(api_payload, key_name, batch_result["ciphertext"])
        return True

    _process_yaml_payloads(path, client, encrypt_callback)

def handle_encrypt_string(client, string, encode_string="True", transit_engine="transit", transit_key="namespace-encryption", transit_context=""):
    encrypt_payload = {}
    encrypt_value = string
    if "True" == encode_string:
        client.logger.debug("Encoding string into base64 value")
        encrypt_value = str(base64.b64encode(encrypt_value.encode("UTF-8")), "UTF-8")
    encrypt_payload["plaintext"] = encrypt_value
    if transit_context != "":
        encrypt_payload["context"] = transit_context

    transit_payload = {"batch_input": [encrypt_payload]}
    transit_api_path = "v1/{0}/encrypt/{1}".format(transit_engine, transit_key)
    encrypted_payload = client.post(transit_api_path, transit_payload)
    cipher = encrypted_payload["data"]["batch_results"][0]["ciphertext"]
    client.logger.info("Encrypted String: {0}".format(cipher))
    return cipher
