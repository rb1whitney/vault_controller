import pytest
from unittest.mock import MagicMock, patch
from projects.vault.lib.validation.manager import ValidationManager

@pytest.fixture
def mock_logger():
    return MagicMock()

def test_validator_init(mock_logger):
    validator = ValidationManager("admin", mock_logger)
    assert validator.scheme == "admin"

@patch("yaml.safe_load")
def test_prohibit_configurations(mock_yaml_load, mock_logger):
    validator = ValidationManager("secret", mock_logger)
    payload = {
        "api_paths": [{"api_path": "v1/sys/config", "api_action": "delete"}]
    }
    errors = validator.validate("dev", payload=payload)
    assert len(errors) == 1
    assert "delete" in errors[0]

@patch("yaml.safe_load")
def test_prohibit_read_write_policy(mock_yaml_load, mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    mock_yaml_load.return_value = {
        "api_paths": [{
            "api_path": "v1/sys/policy/test",
            "api_action": "post",
            "api_payload": {
                "path": {
                    "secret/*": {"capabilities": ["read", "update", "delete"]}
                }
            }
        }]
    }
    with patch("builtins.open", MagicMock()):
        # Mocking the namespace check to avoid path parsing complexity
        with patch.object(validator, "_validate_namespaces", return_value=[]):
            errors = validator.validate("dev", files=["test.yaml"])
    assert len(errors) == 1
    assert "v1/sys/policy/test" in errors[0]

@patch("yaml.safe_load")
def test_prohibit_long_lived_tokens(mock_yaml_load, mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    mock_yaml_load.return_value = {
        "api_paths": [{
            "api_path": "v1/sys/mounts/test",
            "api_payload": {
                "type": "kv",
                "config": {
                    "default_lease_ttl": "800h",
                    "max_lease_ttl": "900h"
                }
            }
        }]
    }
    with patch("builtins.open", MagicMock()):
        with patch.object(validator, "_validate_namespaces", return_value=[]):
            with patch.object(validator, "_prohibit_read_write_policy", return_value=[]):
                errors = validator.validate("dev", files=["test.yaml"])
    assert len(errors) == 1
    assert "800h" in str(errors) or "Default TTL" in errors[0]

def test_validate_dispatch(mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    with patch.object(validator, "_validate_namespaces") as mock_val_ns:
        with patch.object(validator, "_prohibit_read_write_policy") as mock_prohibit_rw:
            with patch.object(validator, "_prohibit_long_lived_tokens") as mock_prohibit_ll:
                mock_val_ns.return_value = ["error1"]
                mock_prohibit_rw.return_value = []
                mock_prohibit_ll.return_value = []
                errors = validator.validate("dev", files=["test.yaml"])
                assert "error1" in errors
