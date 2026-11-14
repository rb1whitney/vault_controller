import os
from unittest.mock import MagicMock, patch

import pytest
from projects.vault_controller.lib.auth.base import BaseAuthStrategy
from projects.vault_controller.lib.auth.factory import AuthStrategyFactory


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.base_uri = "http://localhost:8200"
    adapter.hvac_client = MagicMock()
    adapter.hvac_client.client = MagicMock()
    adapter.auth = adapter.hvac_client.client.auth
    return adapter


def test_token_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'token' authentication:
    Should simply set the token on the adapter without making any API calls.
    """
    with patch.dict(
        os.environ,
        {
            "VAULT_AUTH_TYPE": "token",
            "VAULT_AUTH_SECRET": "test-token",
        },
    ):
        strategy = AuthStrategyFactory.get_strategy("token", mock_logger)
        strategy.authenticate(mock_adapter)

        assert mock_adapter.token == "test-token"
        mock_adapter.hvac_client.client.auth.assert_not_called()


def test_ldap_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'ldap' authentication using hvac.
    """
    with patch.dict(
        os.environ,
        {
            "VAULT_AUTH_TYPE": "ldap",
            "VAULT_AUTH_PRINCIPAL": "test-user",
            "VAULT_AUTH_SECRET": "test-password",
        },
    ):
        strategy = AuthStrategyFactory.get_strategy("ldap", mock_logger)
        strategy.authenticate(mock_adapter, mount_point="ldap")

        mock_adapter.hvac_client.client.auth.ldap.login.assert_called_once_with(
            username="test-user",
            password="test-password",
            mount_point="ldap",
        )


def test_approle_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'approle' authentication using hvac.
    """
    with patch.dict(
        os.environ,
        {
            "VAULT_AUTH_TYPE": "approle",
            "VAULT_AUTH_PRINCIPAL": "role-id-123",
            "VAULT_AUTH_SECRET": "secret-id-456",
        },
    ):
        strategy = AuthStrategyFactory.get_strategy("approle", mock_logger)
        strategy.authenticate(mock_adapter, mount_point="approle")

        mock_adapter.hvac_client.client.auth.approle.login.assert_called_once_with(
            role_id="role-id-123",
            secret_id="secret-id-456",
            mount_point="approle",
        )


def test_aws_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'aws' authentication using hvac.
    """
    with patch.dict(
        os.environ,
        {
            "VAULT_AUTH_TYPE": "aws",
            "VAULT_AUTH_PRINCIPAL": "test-role",
        },
    ):
        strategy = AuthStrategyFactory.get_strategy("aws", mock_logger)
        strategy.authenticate(mock_adapter, mount_point="aws")

        mock_adapter.hvac_client.client.auth.aws.iam_login.assert_called_once_with(
            role="test-role",
            mount_point="aws",
        )


def test_gcp_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'gcp' authentication using hvac.
    """
    with patch("projects.vault_controller.lib.auth.cloud.GCPAuthStrategy.get_gcp_jwt") as mock_jwt:
        mock_jwt.return_value = "signed-jwt-token"

        with patch.dict(
            os.environ,
            {
                "VAULT_AUTH_TYPE": "gcp",
                "VAULT_AUTH_PRINCIPAL": "test-role",
            },
        ):
            strategy = AuthStrategyFactory.get_strategy("gcp", mock_logger)
            strategy.authenticate(mock_adapter, mount_point="gcp")

            mock_adapter.hvac_client.client.auth.gcp.login.assert_called_once_with(
                role="test-role",
                jwt="signed-jwt-token",
                mount_point="gcp",
            )
            mock_jwt.assert_called_once_with("vault/test-role")


def test_factory_invalid_type(mock_logger):
    with pytest.raises(ValueError, match="Unsupported auth type: unknown"):
        AuthStrategyFactory.get_strategy("unknown", mock_logger)


def test_missing_env_variables(mock_adapter, mock_logger):
    with patch.dict(os.environ, {"VAULT_AUTH_TYPE": "ldap"}, clear=True):
        # Missing PRINCIPAL and SECRET
        strategy = AuthStrategyFactory.get_strategy("ldap", mock_logger)
        with pytest.raises(ValueError, match="Missing required environment variables"):
            strategy.authenticate(mock_adapter)


def test_base_auth_strategy_not_implemented(mock_adapter, mock_logger):
    base = BaseAuthStrategy(mock_logger)
    with pytest.raises(NotImplementedError):
        base.authenticate(mock_adapter)
