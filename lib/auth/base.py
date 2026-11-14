import os


class BaseAuthStrategy:
    def __init__(self, logger):
        self.logger = logger

    def validate_env(self, required_vars):
        missing = [v for v in required_vars if v not in os.environ or not os.environ[v]]
        if missing:
            msg = f"Missing required environment variables for authentication: {missing}"
            self.logger.error(msg)
            raise ValueError(msg)

    def authenticate(self, adapter, **kwargs):
        raise NotImplementedError("Subclasses must implement authenticate()")
