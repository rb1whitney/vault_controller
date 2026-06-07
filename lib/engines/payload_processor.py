import base64
import json


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
            # Mask token in logs for security
            masked_token = f"{token[:4]}...{token[-4:]}"
            self.logger.info(f"Unwrapping token: {masked_token}")
            res = self.client.post("/v1/sys/wrapping/unwrap", {"token": token})
            api_object["api_payload"] = res["data"]

    def _inline_transit(self, api_object):
        """Performs in-line decryption via the Transit Secrets Engine."""
        if "transit_encoded_keys" not in api_object:
            return

        engine = api_object.get("transit_secret_engine", "transit")
        key = api_object.get("transit_key", "namespace-encryption")
        api_path = f"v1/{engine}/decrypt/{key}"

        self.logger.info(f"Decrypting keys via Transit ({engine}/{key})")

        for key_name in api_object["transit_encoded_keys"]:
            path_keys = key_name.split(".")
            ciphertext = self._get_nested(api_object["api_payload"], path_keys)

            payload = {"ciphertext": ciphertext}
            if "transit_context" in api_object:
                payload["context"] = api_object["transit_context"]

            res = self.client.post(api_path, payload)
            plaintext = base64.b64decode(res["data"]["plaintext"]).decode("utf-8")

            self._set_nested(
                api_object["api_payload"], path_keys, plaintext, ciphertext
            )

        # Cleanup metadata
        for k in ["transit_encoded_keys", "transit_secret_engine", "transit_key", "transit_context"]:
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

    def _set_nested(self, data, keys, value, search_val):
        """Helper to set nested dictionary values."""
        last_key = keys[-1]
        for k in keys[:-1]:
            data = data[k]

        if isinstance(data[last_key], list):
            data[last_key] = [value if x == search_val else x for x in data[last_key]]
        else:
            data[last_key] = value
