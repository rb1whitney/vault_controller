from ..auth.factory import AuthStrategyFactory
from .adapter import VaultClientAdapter
from .errors import VaultError


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

    @property
    def hvac_client(self):
        """Returns the underlying hvac.Client instance."""
        return self.adapter.hvac_client.client

    def login(self, auth_method=None, mount_point=None, payload=None):
        """
        Authenticates the client using the specified strategy.
        Delegates to AuthStrategyFactory for implementation.
        """
        import os

        auth_type = auth_method or os.environ.get("VAULT_AUTH_TYPE")
        if not auth_type:
            msg = "Authentication failed: VAULT_AUTH_TYPE not set."
            self.logger.error(msg)
            raise VaultError(message=msg)

        mount_point = mount_point or auth_type

        try:
            strategy = AuthStrategyFactory.get_strategy(auth_type, self.logger)
            strategy.authenticate(self.adapter, mount_point=mount_point, payload=payload)
        except Exception as e:
            msg = f"Authentication error with strategy '{auth_type}': {e}"
            self.logger.error(msg)
            raise VaultError(message=msg) from e

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
            self.logger.info("Authorized successfully (policy lookup skipped)")

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
                    self.logger.debug("Payload (Masked): <REDACTED_SENSITIVE_DATA>")

                res = self.adapter.request(action, path, json=data, timeout=30)

                # Handle both requests.Response and dict (some adapters return JSON directly)
                status_code = getattr(res, "status_code", 200)
                content = getattr(res, "content", None)

                if status_code != 204 and (content or isinstance(res, dict)):
                    if isinstance(res, dict):
                        resp_json = res
                    else:
                        try:
                            resp_json = res.json()
                        except ValueError:
                            self.logger.debug("Response content is not JSON")
                            resp_json = {"content": content.decode("utf-8") if content else ""}

                    self.logger.debug(
                        f"Response (Masked): status={status_code}, keys={list(resp_json.keys())}"
                    )
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
                    raise

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
        """Revokes the current token and clears it from memory."""
        if self.adapter.token:
            try:
                self.post("/v1/auth/token/revoke-self", None)
            finally:
                self.adapter.token = None
