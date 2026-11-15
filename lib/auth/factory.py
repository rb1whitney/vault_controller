from typing import ClassVar

from .cloud import AWSAuthStrategy, GCPAuthStrategy
from .standard import AppRoleAuthStrategy, LDAPAuthStrategy, TokenAuthStrategy


class AuthStrategyFactory:
    _strategies: ClassVar[dict] = {
        "token": TokenAuthStrategy,
        "ldap": LDAPAuthStrategy,
        "approle": AppRoleAuthStrategy,
        "aws": AWSAuthStrategy,
        "gcp": GCPAuthStrategy,
    }

    @classmethod
    def get_strategy(cls, auth_type, logger):
        strategy_class = cls._strategies.get(auth_type.lower())
        if not strategy_class:
            raise ValueError(f"Unsupported auth type: {auth_type}")
        return strategy_class(logger)
