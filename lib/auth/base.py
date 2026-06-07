import os
import sys


class BaseAuthStrategy:
    def __init__(self, logger):
        self.logger = logger

    def validate_env(self, required_vars):
        missing = [v for v in required_vars if v not in os.environ or not os.environ[v]]
        if missing:
            self.logger.error(
                f"Missing required environment variables for authentication: {missing}"
            )
            sys.exit(1)

    def authenticate(self, adapter, **kwargs):
        raise NotImplementedError("Subclasses must implement authenticate()")
