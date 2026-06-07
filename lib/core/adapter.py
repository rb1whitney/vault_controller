import requests

from .errors import VaultClientError
from .logger import get_logger

logger = get_logger("vault_client_adapter")


class VaultClientAdapter:
    """
    Handles raw HTTP communication with the Vault API.
    Decoupled from specific secret engine logic.
    """

    def __init__(
        self,
        base_uri,
        token=None,
        cert=None,
        verify=True,
        timeout=30,
        allow_redirects=True,
        namespace=None,
    ):
        self.base_uri = base_uri.strip("/")
        self.token = token
        self.namespace = namespace
        self.session = requests.Session()
        self.allow_redirects = allow_redirects
        self.default_kwargs = {
            "cert": cert,
            "verify": verify,
            "timeout": timeout,
        }

    def close(self):
        """Closes the underlying Requests session."""
        self.session.close()

    def _construct_url(self, api_url):
        """Standardizes URL construction for Vault API endpoints."""
        clean_api_path = api_url.strip("/").replace("//", "/")
        return f"{self.base_uri}/{clean_api_path}"

    def request(self, method, url, headers=None, **kwargs):
        """
        Executes an HTTP request against Vault.
        Raises VaultClientError for non-2xx responses.
        """
        full_url = self._construct_url(url)
        headers = headers or {}

        if self.token:
            headers["X-Vault-Token"] = self.token
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace

        # Merge default configs with request-specific overrides
        request_kwargs = self.default_kwargs.copy()
        request_kwargs.update(kwargs)

        response = self.session.request(
            method=method,
            url=full_url,
            headers=headers,
            allow_redirects=self.allow_redirects,
            **request_kwargs,
        )

        if not response.ok:
            self._handle_error(response, method, full_url)

        return response

    def _handle_error(self, response, method, url):
        """Parses Vault error responses and raises a structured Exception."""
        error = None
        if (
            response.headers.get("Content-Type") == "application/json"
            and response.content
        ):
            try:
                error = response.json().get("errors")
            except Exception as e:
                logger.error(f"Failed to parse JSON error response: {e}")

        if error is None:
            error = response.text

        raise VaultClientError(response.status_code, error, method, url)
