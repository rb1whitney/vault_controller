from .standard import TokenAuthStrategy, LDAPAuthStrategy, AppRoleAuthStrategy
from .cloud import AWSAuthStrategy, GCPAuthStrategy


class AuthStrategyFactory:
    _strategies = {
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
