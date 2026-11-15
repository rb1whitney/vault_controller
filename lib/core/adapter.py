from .errors import VaultClientError
from .hvac_client import HvacClient
from .logger import get_logger

logger = get_logger("vault_client_adapter")

class VaultClientAdapter:
    """
    Legacy Adapter refactored to use hvac under the hood.
    Maintains compatibility with existing LocalVaultClient and Auth strategies.
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
        self.hvac_client = HvacClient(
            url=base_uri,
            token=token,
            cert=cert,
            verify=verify,
            timeout=timeout,
            namespace=namespace,
        )
        self.base_uri = base_uri.strip("/")
        self.namespace = namespace

    @property
    def token(self):
        return self.hvac_client.token

    @token.setter
    def token(self, value):
        self.hvac_client.token = value

    @property
    def auth(self):
        """Exposes hvac auth methods without multi-hop chaining."""
        return self.hvac_client.client.auth

    def close(self):
        """Closes the underlying HTTP adapter session."""
        self.hvac_client.client.adapter.close()

    def request(self, method, url, headers=None, **kwargs):
        try:
            # Ensure path is clean for hvac (it expects paths like 'v1/sys/health' or '/v1/sys/health')
            # hvac handles prepending base_uri
            response = self.hvac_client.request(method, url, headers=headers, **kwargs)
            return response
        except Exception as e:
            status_code = 500
            error_msg = str(e)
            
            # hvac exceptions often have the response attached
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_msg = e.response.json().get('errors', error_msg)
                except (ValueError, KeyError, AttributeError):
                    error_msg = e.response.text or error_msg
            
            raise VaultClientError(status_code, error_msg, method, url)
