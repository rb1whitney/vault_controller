import os
import re


def convert_pgp_key(pgp_key):
    """Strips PGP headers/footers for Vault API compatibility."""
    cleaned = re.sub("-----BEGIN PGP PUBLIC KEY BLOCK-----.*\n\n", "", pgp_key, flags=re.S)
    cleaned = re.sub("=.*\n-----END PGP PUBLIC KEY BLOCK-----", "", cleaned, re.S)
    return cleaned


def gather_pgp_keys(key_holders):
    """Loads and cleans PGP keys from the filesystem."""
    base64_pgp_keys = []
    current_dir = os.path.dirname(__file__)
    for holder in key_holders:
        path = os.path.join(current_dir, "../../config/pgp_keys/", f"{holder}.asc")
        with open(path, "r") as f:
            content = f.read()
        base64_pgp_keys.append(convert_pgp_key(content))
    return base64_pgp_keys


def format_key_response(key_response, key_holders, key_encrypt):
    """Standardizes the display of initialization/rekey shards."""
    key_output = {}
    key_suffix = "_base64" if key_encrypt else ""
    for index, vault_key in enumerate(key_response.get("keys" + key_suffix, [])):
        key = f"Keyholder #{index + 1}"
        key_output[key] = {
            "key" + key_suffix: vault_key,
            "email_address": key_holders[index],
        }
    return key_output
