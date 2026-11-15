from unittest.mock import MagicMock, patch

import pytest

from lib.core.client import LocalVaultClient


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def vault_client(mock_logger):
    with patch("lib.core.client.VaultClientAdapter") as mock_adapter:
        client = LocalVaultClient("http://localhost:8200", mock_logger)
        client.adapter = mock_adapter.return_value
        return client


def test_submit_success(vault_client):
    payload = [
        {"api_path": "v1/test", "api_action": "post", "api_payload": {"data": "test"}}
    ]
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"status": "ok"}'
    mock_response.json.return_value = {"status": "ok"}
    vault_client.adapter.request.return_value = mock_response

    responses = vault_client.submit(payload)
    assert responses == [{"status": "ok"}]
    vault_client.adapter.request.assert_called_with(
        "post", "v1/test", json={"data": "test"}, timeout=30
    )


def test_submit_ignore_error(vault_client):
    payload = [{"api_path": "v1/test", "api_action": "post"}]
    vault_client.adapter.request.side_effect = Exception("User already exists")
    responses = vault_client.submit(payload)
    assert responses == [{}]


def test_wrapper_methods(vault_client):
    with patch.object(vault_client, "submit") as mock_submit:
        mock_submit.return_value = [{"res": "ok"}]

        assert vault_client.get("v1/test") == {"res": "ok"}
        assert vault_client.post("v1/test", {"a": 1}) == {"res": "ok"}
        assert vault_client.put("v1/test", {"a": 1}) == {"res": "ok"}
        assert vault_client.delete("v1/test") == {"res": "ok"}
        assert vault_client.list("v1/test") == {"res": "ok"}


def test_logout(vault_client):
    vault_client.adapter.token = "my-token"
    with patch.object(vault_client, "post") as mock_post:
        vault_client.logout()
        mock_post.assert_called_with("/v1/auth/token/revoke-self", None)
        assert vault_client.adapter.token is None
