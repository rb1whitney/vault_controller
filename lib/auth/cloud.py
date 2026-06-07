import os
from .base import BaseAuthStrategy


class AWSAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL"])
        mount_point = kwargs.get("mount_point", "aws")
        role = os.environ["VAULT_AUTH_PRINCIPAL"]

        payload = self.generate_aws_login_payload(role)
        
        # Enforce Vault Server ID Header to prevent IAM replay attacks
        if "X-Vault-AWS-IAM-Server-ID" not in payload.get("iam_request_headers", ""):
             self.logger.warning("X-Vault-AWS-IAM-Server-ID is missing from the IAM headers. This is a security risk.")

        api_path = f"v1/auth/{mount_point}/login"
        response = adapter.request("post", api_path, json=payload)
        adapter.token = response.json()["auth"]["client_token"]
        self.logger.info(f"Authenticated AWS role {role} using unified AWS strategy")

    def generate_aws_login_payload(self, role):
        import base64
        import json
        try:
            import boto3
        except ImportError:
            self.logger.error("boto3 is required for AWS auth. Run: pip install boto3")
            exit(1)

        session = boto3.Session()
        client = session.client("sts", region_name="us-east-1", endpoint_url="https://sts.us-east-1.amazonaws.com/")
        request = client._endpoint.create_request({}, client._service_model.operation_model("GetCallerIdentity"))
        request.headers["X-Vault-AWS-IAM-Server-ID"] = "vault"
        client._endpoint.auth.add_auth(request)
        prepared = request.prepare()

        body = prepared.body.encode("utf-8") if isinstance(prepared.body, str) else prepared.body
        headers = json.dumps(dict(prepared.headers)).encode("utf-8")
        url = prepared.url.encode("utf-8")

        return {
            "role": role,
            "iam_http_request_method": prepared.method,
            "iam_request_url": base64.b64encode(url).decode("utf-8"),
            "iam_request_headers": base64.b64encode(headers).decode("utf-8"),
            "iam_request_body": base64.b64encode(body).decode("utf-8"),
        }


class GCPAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL"])
        mount_point = kwargs.get("mount_point", "gcp")
        role = os.environ["VAULT_AUTH_PRINCIPAL"]

        # Audience parameter is required for Vault to trust the GCP metadata JWT
        audience = f"vault/{role}" 
        jwt = self.get_gcp_jwt(audience)

        api_path = f"v1/auth/{mount_point}/login"
        payload = {"role": role, "jwt": jwt}

        response = adapter.request("post", api_path, json=payload)
        adapter.token = response.json()["auth"]["client_token"]
        self.logger.info(f"Authenticated GCP role {role} using unified GCP strategy")

    def get_gcp_jwt(self, audience):
        try:
            import google.auth.transport.requests
            import google.oauth2.id_token
        except ImportError:
            self.logger.error("google-auth is required for GCP auth. Run: pip install google-auth")
            exit(1)
            
        request = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(request, audience)
