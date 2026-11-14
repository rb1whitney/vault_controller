import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch

from bin.vault_ctl import app

runner = CliRunner()

@pytest.fixture
def mock_settings():
    with patch("lib.utils.settings.get_cluster") as mock_get:
        mock_config = MagicMock()
        mock_config.api_endpoint = "http://localhost:8200"
        mock_config.server_endpoints = ["http://localhost:8200"]
        mock_config.key_holders = ["admin@example.com"]
        mock_config.key_threshold = 1
        mock_config.key_encrypt = False
        mock_config.recovery_key = False
        mock_get.return_value = mock_config
        yield mock_get

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Modern Vault Controller CLI" in result.output

@patch("bin.vault_ctl.LocalVaultClient")
def test_cluster_status_down(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.hvac_client.sys.read_health_status.side_effect = Exception("offline")
    mock_client_cls.return_value = mock_client

    result = runner.invoke(app, ["cluster", "status", "--name", "example_vault"])
    assert result.exit_code == 0
    assert "example_vault" in result.output
    assert "DOWN" in result.output

@patch("lib.utils.ops.unseal_host")
def test_cluster_unseal(mock_unseal, mock_settings):
    result = runner.invoke(
        app,
        ["cluster", "unseal", "--name", "example_vault"],
        input="key1\n",
    )
    assert result.exit_code == 0
    assert "Unsealing" in result.output
    mock_unseal.assert_called_once()

def test_secrets_validate_success(tmp_path):
    # Create valid JSON directory for test
    d = tmp_path / "json_workspace"
    d.mkdir()
    f = d / "secret.json"
    f.write_text('{"key": "value"}')

    result = runner.invoke(app, ["secrets", "validate", "--directory", str(d), "--allow-file-regex", "*.json"])
    assert result.exit_code == 0
    assert "valid" in result.output

def test_secrets_validate_failure(tmp_path):
    # Create invalid JSON directory for test
    d = tmp_path / "json_workspace"
    d.mkdir()
    f = d / "secret.json"
    f.write_text('{"key": invalid_json}')

    result = runner.invoke(app, ["secrets", "validate", "--directory", str(d), "--allow-file-regex", "*.json"])
    assert result.exit_code != 0
    assert "Invalid JSON" in result.output


@patch("bin.vault_ctl.LocalVaultClient")
def test_secrets_deploy_validation_gate_blocks_before_login(mock_client_cls, tmp_path):
    bad_yaml = tmp_path / "bad-policy.yaml"
    bad_yaml.write_text(
        "api_paths:\n"
        "- api_path: v1/sys/policy/bad\n"
        "  api_action: post\n"
        "  api_payload:\n"
        "    path:\n"
        "      secret/*:\n"
        "        capabilities: [read, update]\n"
    )
    result = runner.invoke(
        app,
        ["secrets", "deploy", "--name", "example_vault", "--path", str(bad_yaml)],
    )
    assert result.exit_code != 0
    assert "Validation Failed" in result.output
    mock_client_cls.assert_not_called()


@patch("bin.vault_ctl.LocalVaultClient")
def test_secrets_deploy_logout_on_failure(mock_client_cls, mock_settings, tmp_path):
    good_yaml = tmp_path / "good.yaml"
    good_yaml.write_text(
        "api_paths:\n"
        "- api_path: v1/app/data/db\n"
        "  api_action: post\n"
        "  api_payload:\n"
        "    data:\n"
        "      key: val\n"
    )
    mock_client = MagicMock()
    mock_client.submit.side_effect = RuntimeError("vault error")
    mock_client_cls.return_value = mock_client

    result = runner.invoke(
        app,
        ["secrets", "deploy", "--name", "example_vault", "--auth-method", "ldap", "--path", str(good_yaml)],
    )
    assert result.exit_code != 0
    mock_client.logout.assert_called_once()
