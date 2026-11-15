import hvac

from .logger import get_logger

logger = get_logger("hvac_client")

class HvacClient:
    """
    Core Vault Client using the hvac library.
    Provides a cleaner interface and better stability.
    """
    def __init__(
        self,
        url,
        token=None,
        cert=None,
        verify=True,
        timeout=30,
        namespace=None,
    ):
        self.client = hvac.Client(
            url=url,
            token=token,
            cert=cert,
            verify=verify,
            timeout=timeout,
            namespace=namespace,
        )

    @property
    def token(self):
        return self.client.token

    @token.setter
    def token(self, value):
        self.client.token = value

    def is_authenticated(self):
        return self.client.is_authenticated()

    def request(self, method, url, **kwargs):
        """
        Proxies raw requests using the hvac adapter.
        Ensures a requests.Response object is returned.
        """
        # hvac adapter request handles prefixing and headers
        return self.client.adapter.request(method, url, **kwargs)
