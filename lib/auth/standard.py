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

        self.logger.info(f"Authenticating as {username} using hvac LDAP strategy")
        adapter.auth.ldap.login(
            username=username,
            password=password,
            mount_point=mount_point,
        )


class AppRoleAuthStrategy(BaseAuthStrategy):
    def authenticate(self, adapter, **kwargs):
        self.validate_env(["VAULT_AUTH_PRINCIPAL", "VAULT_AUTH_SECRET"])
        mount_point = kwargs.get("mount_point", "approle")
        role_id = os.environ["VAULT_AUTH_PRINCIPAL"]
        secret_id = os.environ["VAULT_AUTH_SECRET"]

        self.logger.info(f"Authenticating role {role_id} using hvac AppRole strategy")
        adapter.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id,
            mount_point=mount_point,
        )
