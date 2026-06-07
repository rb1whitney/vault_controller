import os
from .base import BaseAuthStrategy


class TokenAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_SECRET"])
        adapter.token = os.environ["VAULT_AUTH_SECRET"]
        self.logger.info("Authenticated using unified Token strategy")


class LDAPAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL", "VAULT_AUTH_SECRET"])
        mount_point = kwargs.get("mount_point", "ldap")
        username = os.environ["VAULT_AUTH_PRINCIPAL"]
        password = os.environ["VAULT_AUTH_SECRET"]

        api_path = f"v1/auth/{mount_point}/login/{username}"
        payload = {"password": password}

        response = adapter.request("post", api_path, json=payload)
        adapter.token = response.json()["auth"]["client_token"]
        self.logger.info(f"Authenticated as {username} using unified LDAP strategy")


class AppRoleAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL", "VAULT_AUTH_SECRET"])
        mount_point = kwargs.get("mount_point", "approle")
        role_id = os.environ["VAULT_AUTH_PRINCIPAL"]
        secret_id = os.environ["VAULT_AUTH_SECRET"]

        api_path = f"v1/auth/{mount_point}/login"
        payload = {"role_id": role_id, "secret_id": secret_id}

        response = adapter.request("post", api_path, json=payload)
        adapter.token = response.json()["auth"]["client_token"]
        self.logger.info(f"Authenticated role {role_id} using unified AppRole strategy")
