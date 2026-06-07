import json

from ..auth.factory import AuthStrategyFactory
from .adapter import VaultClientAdapter


class LocalVaultClient:
    """
    High-level Vault Client for performing REST API operations.
    Utilizes a Strategy pattern for authentication and an Adapter for HTTP.
    """

    def __init__(
        self,
        api_endpoint,
        logger,
        api_verify=True,
        namespace=None,
        allow_api_redirect=True,
        api_timeout=15,
        cert=None,
    ):
        self.logger = logger
        self.adapter = VaultClientAdapter(
            api_endpoint,
            verify=api_verify,
            namespace=namespace,
            allow_redirects=allow_api_redirect,
            timeout=api_timeout,
            cert=cert,
        )
        self.namespace = namespace

    def login(self, auth_method=None, mount_point=None, payload=None):
        """
        Authenticates the client using the specified strategy.
        Delegates to AuthStrategyFactory for implementation.
        """
        import os

        auth_type = auth_method or os.environ.get("VAULT_AUTH_TYPE")
        if not auth_type:
            self.logger.error("Authentication failed: VAULT_AUTH_TYPE not set.")
            exit(1)

        mount_point = mount_point or auth_type

        try:
            strategy = AuthStrategyFactory.get_strategy(auth_type, self.logger)
            strategy.authenticate(self.adapter, mount_point=mount_point, payload=payload)
        except Exception as e:
            self.logger.error(f"Authentication error with strategy '{auth_type}': {e}")
            exit(1)

        if self.adapter.token:
            self._lookup_self()

    def _lookup_self(self):
        """Verifies token validity and logs assigned policies."""
        try:
            res = self.get("/v1/auth/token/lookup-self")
            policies = res.get("data", {}).get("policies", [])
            self.logger.info(f"Authorized successfully against {self.adapter.base_uri}")
            self.logger.debug(f"Assigned Policies: {policies}")
        except Exception:
            self.logger.info(f"Authorized successfully (policy lookup skipped)")

    def submit(self, payload_paths):
        """
        Executes a batch of API actions defined in the payload.
        :param payload_paths: List of dicts with api_path, api_action, and api_payload.
        """
        responses = []
        for obj in payload_paths:
            path = obj["api_path"]
            action = obj["api_action"]
            data = obj.get("api_payload")

            ns_msg = f" (Namespace: {self.namespace})" if self.namespace else ""
            self.logger.info(f"Executing {action.upper()} on {path}{ns_msg}")

            try:
                if data:
                    # Mask potential secrets in debug logs
                    self.logger.debug(f"Payload (Masked): <REDACTED_SENSITIVE_DATA>")

                res = self.adapter.request(action, path, json=data, timeout=30)

                if res.status_code != 204 and res.content:
                    resp_json = res.json()
                    self.logger.debug(f"Response: {json.dumps(resp_json, indent=2)}")
                    responses.append(resp_json)
                else:
                    responses.append({})

            except Exception as e:
                # Idiomatic Vault behavior: ignore 'already exists' for idempotency
                msg = str(e).lower()
                if "already in use" in msg or "already exists" in msg:
                    self.logger.warning(f"Resource already exists at {path}. Skipping.")
                    responses.append({})
                else:
                    raise e

        return responses

    def get(self, path):
        return self.submit([{"api_path": path, "api_action": "get"}])[0]

    def post(self, path, payload):
        return self.submit([{"api_path": path, "api_action": "post", "api_payload": payload}])[0]

    def put(self, path, payload):
        return self.submit([{"api_path": path, "api_action": "put", "api_payload": payload}])[0]

    def delete(self, path):
        return self.submit([{"api_path": path, "api_action": "delete"}])[0]

    def list(self, path):
        return self.submit([{"api_path": path, "api_action": "list"}])[0]

    def logout(self):
        """Revokes the current token."""
        if self.adapter.token:
            self.post("/v1/auth/token/revoke-self", None)
            self.adapter.token = None
