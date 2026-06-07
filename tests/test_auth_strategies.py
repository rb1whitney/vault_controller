import os
from unittest.mock import MagicMock, patch

import pytest
from projects.vault.lib.auth.factory import AuthStrategyFactory


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.base_uri = "http://localhost:8200"
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
        mock_adapter.request.assert_not_called()


def test_ldap_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'ldap' authentication:
    Should perform a POST to v1/auth/ldap/login/username with password.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"auth": {"client_token": "ldap-token"}}
    mock_adapter.request.return_value = mock_response

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

        mock_adapter.request.assert_called_once_with(
            "post",
            "v1/auth/ldap/login/test-user",
            json={"password": "test-password"},
        )
        assert mock_adapter.token == "ldap-token"


def test_approle_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'approle' authentication:
    Should perform a POST to v1/auth/approle/login with role_id and secret_id.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"auth": {"client_token": "approle-token"}}
    mock_adapter.request.return_value = mock_response

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

        mock_adapter.request.assert_called_once_with(
            "post",
            "v1/auth/approle/login",
            json={"role_id": "role-id-123", "secret_id": "secret-id-456"},
        )
        assert mock_adapter.token == "approle-token"


def test_aws_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'aws' authentication:
    Should use boto3 to generate a signed request and POST to v1/auth/aws/login.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"auth": {"client_token": "aws-token"}}
    mock_adapter.request.return_value = mock_response

    # Mocking the complex AWS signed request generation
    with patch("projects.vault.lib.auth.cloud.AWSAuthStrategy.generate_aws_login_payload") as mock_gen:
        mock_gen.return_value = {"iam_http_request_method": "POST", "iam_request_url": "...", "role": "test-role"}

        with patch.dict(
            os.environ,
            {
                "VAULT_AUTH_TYPE": "aws",
                "VAULT_AUTH_PRINCIPAL": "test-role",
            },
        ):
            strategy = AuthStrategyFactory.get_strategy("aws", mock_logger)
            strategy.authenticate(mock_adapter, mount_point="aws")

            mock_adapter.request.assert_called_once()
            args, kwargs = mock_adapter.request.call_args
            assert args[0] == "post"
            assert args[1] == "v1/auth/aws/login"
            assert kwargs["json"]["role"] == "test-role"
            assert mock_adapter.token == "aws-token"


def test_gcp_auth_strategy(mock_adapter, mock_logger):
    """
    Characterize 'gcp' authentication:
    Should use google-auth to get a JWT and POST to v1/auth/gcp/login.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"auth": {"client_token": "gcp-token"}}
    mock_adapter.request.return_value = mock_response

    with patch("projects.vault.lib.auth.cloud.GCPAuthStrategy.get_gcp_jwt") as mock_jwt:
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

            mock_adapter.request.assert_called_once_with(
                "post",
                "v1/auth/gcp/login",
                json={"role": "test-role", "jwt": "signed-jwt-token"},
            )
            assert mock_adapter.token == "gcp-token"
            mock_jwt.assert_called_once_with("vault/test-role")


def test_factory_invalid_type(mock_logger):
    with pytest.raises(ValueError, match="Unsupported auth type: unknown"):
        AuthStrategyFactory.get_strategy("unknown", mock_logger)


def test_missing_env_variables(mock_adapter, mock_logger):
    with patch.dict(os.environ, {"VAULT_AUTH_TYPE": "ldap"}, clear=True):
        # Missing PRINCIPAL and SECRET
        strategy = AuthStrategyFactory.get_strategy("ldap", mock_logger)
        with pytest.raises(SystemExit):
            strategy.authenticate(mock_adapter)
