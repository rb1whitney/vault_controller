import os

from .base import BaseAuthStrategy


class AWSAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL"])
        mount_point = kwargs.get("mount_point", "aws")
        role = os.environ["VAULT_AUTH_PRINCIPAL"]

        self.logger.info(f"Authenticating AWS role {role} using hvac AWS IAM strategy")
        # hvac handles IAM payload generation internally if boto3 is available
        adapter.auth.aws.iam_login(
            role=role,
            mount_point=mount_point,
        )


class GCPAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL"])
        mount_point = kwargs.get("mount_point", "gcp")
        role = os.environ["VAULT_AUTH_PRINCIPAL"]

        # Audience parameter is required for Vault to trust the GCP metadata JWT
        audience = f"vault/{role}" 
        jwt = self.get_gcp_jwt(audience)

        self.logger.info(f"Authenticating GCP role {role} using hvac GCP strategy")
        adapter.auth.gcp.login(
            role=role,
            jwt=jwt,
            mount_point=mount_point,
        )

    def get_gcp_jwt(self, audience):
        try:
            import google.auth.transport.requests
            import google.oauth2.id_token
        except ImportError as e:
            msg = "google-auth is required for GCP auth. Run: pip install google-auth"
            self.logger.error(msg)
            raise ImportError(msg) from e

        request = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(request, audience)
