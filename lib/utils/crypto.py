import os
import re


def convert_pgp_key(pgp_key):
    """Strips PGP headers/footers for Vault API compatibility."""
    cleaned = re.sub(
        r"-----BEGIN PGP PUBLIC KEY BLOCK-----.*?\r?\n\r?\n",
        "",
        pgp_key,
        flags=re.DOTALL,
    )
    cleaned = re.sub(
        r"\r?\n=[A-Za-z0-9+/=]{4}\r?\n-----END PGP PUBLIC KEY BLOCK-----.*",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    return cleaned.strip()


def gather_pgp_keys(key_holders):
    """Loads and cleans PGP keys from the filesystem."""
    base64_pgp_keys = []
    current_dir = os.path.dirname(__file__)
    pgp_dir = os.path.abspath(os.path.join(current_dir, "../../config/pgp_keys"))
    for holder in key_holders:
        safe_holder = os.path.basename(holder)
        if not safe_holder or safe_holder != holder or ".." in holder:
            raise ValueError(f"Invalid key holder name: {holder}")
        path = os.path.join(pgp_dir, f"{safe_holder}.asc")
        with open(path) as f:
            content = f.read()
        base64_pgp_keys.append(convert_pgp_key(content))
    return base64_pgp_keys


def format_key_response(key_response, key_holders, key_encrypt):
    """Standardizes the display of initialization/rekey shards."""
    key_output = {}
    key_suffix = "_base64" if key_encrypt else ""
    for index, vault_key in enumerate(key_response.get("keys" + key_suffix, [])):
        key = f"Keyholder #{index + 1}"
        email = (
            key_holders[index]
            if index < len(key_holders)
            else f"keyholder-{index + 1}@unassigned"
        )
        key_output[key] = {
            "key" + key_suffix: vault_key,
            "email_address": email,
        }
    return key_output
