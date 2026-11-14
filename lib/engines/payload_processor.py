import base64
import json
import re

TRANSIT_CIPHERTEXT_RE = re.compile(r"^vault:v\d+:")


class PayloadProcessor:
    """
    Handles inline transformations of Vault payloads (Transit, Unwrapping, Base64).
    Decouples the core Client from engine-specific logic.
    """

    def __init__(self, client):
        self.client = client
        self.logger = client.logger

    def process(self, api_object):
        """Orchestrates all inline transformations for a single API object."""
        self._inline_unwrap(api_object)
        self._inline_transit(api_object)
        self._inline_base64(api_object)
        self._inline_transform(api_object)

    def _inline_unwrap(self, api_object):
        """Retrieves and injects payloads from wrapped tokens."""
        if "wrapped_token" in api_object:
            token = api_object["wrapped_token"]
            masked_token = f"{token[:4]}...{token[-4:]}"
            self.logger.info(f"Unwrapping token: {masked_token}")
            
            # Use hvac native unwrap
            res = self.client.hvac_client.sys.unwrap(token=token)
            api_object["api_payload"] = res["data"]

    def _decrypt_value(self, ciphertext, engine, key, context=None):
        """Decrypts a single Vault Transit ciphertext string."""
        res = self.client.hvac_client.secrets.transit.decrypt_data(
            name=key,
            ciphertext=ciphertext,
            context=context,
            mount_point=engine,
        )
        b64_plaintext = res["data"]["plaintext"]
        raw_bytes = base64.b64decode(b64_plaintext)
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return b64_plaintext

    def _decrypt_recursive(self, data, engine, key, context=None):
        """Recursively walks api_payload and decrypts any vault:vN: ciphertexts."""
        if isinstance(data, dict):
            return {
                k: self._decrypt_recursive(v, engine, key, context)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._decrypt_recursive(item, engine, key, context) for item in data]
        if isinstance(data, str) and TRANSIT_CIPHERTEXT_RE.match(data):
            return self._decrypt_value(data, engine, key, context)
        return data

    def _has_transit_ciphertext(self, data):
        """Returns True if any leaf string in data matches vault:vN: ciphertext."""
        if isinstance(data, dict):
            return any(self._has_transit_ciphertext(v) for v in data.values())
        if isinstance(data, list):
            return any(self._has_transit_ciphertext(item) for item in data)
        return isinstance(data, str) and bool(TRANSIT_CIPHERTEXT_RE.match(data))

    def _inline_transit(self, api_object):
        """Performs in-line decryption via the Transit Secrets Engine."""
        has_explicit_keys = bool(api_object.get("transit_encoded_keys"))
        has_transit_meta = any(
            k in api_object
            for k in ("transit_key", "transit_engine", "transit_secret_engine")
        )
        payload = api_object.get("api_payload")
        has_ciphertext = self._has_transit_ciphertext(payload) if payload is not None else False

        if not has_explicit_keys and not has_transit_meta and not has_ciphertext:
            return

        engine = (
            api_object.get("transit_secret_engine")
            or api_object.get("transit_engine")
            or "transit"
        )
        key = api_object.get("transit_key") or "namespace-encryption"
        context = api_object.get("transit_context")

        self.logger.info(f"Decrypting keys via hvac Transit ({engine}/{key})")

        if has_explicit_keys:
            for key_name in api_object["transit_encoded_keys"]:
                path_keys = key_name.split(".")
                val = self._get_nested(payload, path_keys)
                if isinstance(val, list):
                    decrypted_list = [
                        self._decrypt_value(item, engine, key, context)
                        for item in val
                    ]
                    self._set_nested(payload, path_keys, decrypted_list)
                else:
                    plaintext = self._decrypt_value(val, engine, key, context)
                    self._set_nested(payload, path_keys, plaintext)
        elif payload is not None:
            api_object["api_payload"] = self._decrypt_recursive(
                payload, engine, key, context
            )

        # Cleanup metadata
        for k in [
            "transit_encoded_keys",
            "transit_secret_engine",
            "transit_engine",
            "transit_key",
            "transit_context",
        ]:
            api_object.pop(k, None)

    def _inline_base64(self, api_object):
        """Decodes base64 fields in place."""
        if "decode_base64_keys" in api_object:
            payload = api_object["api_payload"]
            for key in api_object["decode_base64_keys"]:
                val = payload[key]
                if isinstance(val, list):
                    payload[key] = [base64.b64decode(v).decode("utf-8") for v in val]
                else:
                    payload[key] = base64.b64decode(val).decode("utf-8")
            api_object.pop("decode_base64_keys")

    def _inline_transform(self, api_object):
        """Handles special object transformations (e.g. Policies)."""
        path = api_object.get("api_path")
        action = api_object.get("api_action")

        if not path or not action:
            return

        if "sys/policy" in path and action == "post":
            api_object["api_payload"] = {"policy": json.dumps(api_object["api_payload"])}

        if "/roleset/" in path and action == "post":
            if "bindings" in api_object["api_payload"]:
                api_object["api_payload"]["bindings"] = json.dumps(
                    api_object["api_payload"]["bindings"]
                )

    def _get_nested(self, data, keys):
        """Helper to navigate nested dictionaries."""
        for k in keys:
            data = data[k]
        return data

    def _set_nested(self, data, keys, value, search_val=None):
        """Helper to set nested dictionary values."""
        last_key = keys[-1]
        for k in keys[:-1]:
            data = data[k]

        if search_val is not None and isinstance(data[last_key], list):
            for idx, item in enumerate(data[last_key]):
                if item == search_val:
                    data[last_key][idx] = value
                    break
        else:
            data[last_key] = value
