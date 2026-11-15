class VaultError(Exception):
    """Base exception for all Vault-related errors."""

    def __init__(self, status_code="", message="", method="", url=""):
        self.status_code = status_code
        self.message = message
        self.method = method
        self.url = url
        err_msg = f" Error is: {message}" if message else ""
        exception_err = (
            f"Vault Client received a {status_code} status code "
            f"after making a {method} to {url}.{err_msg}"
        )
        super().__init__(exception_err)


class VaultClientError(VaultError):
    """Specific error for Vault HTTP client failures."""
