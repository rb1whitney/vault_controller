import pytest
from unittest.mock import MagicMock, patch
from lib.validation.manager import ValidationManager

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
        # Mocking namespace dir check
        with patch.object(validator, "_validate_namespace_dir", return_value=[]):
            errors = validator.validate("dev", files=["test.yaml"])
    assert len(errors) > 0
    assert any("mixes Read/Write" in e for e in errors)

@patch("yaml.safe_load")
def test_prohibit_long_lived_tokens(mock_yaml_load, mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    mock_yaml_load.return_value = {
        "api_paths": [{
            "api_path": "v1/sys/mounts/test",
            "api_action": "post",
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
        with patch.object(validator, "_validate_namespace_dir", return_value=[]):
            errors = validator.validate("dev", files=["test.yaml"])
    assert len(errors) > 0
    assert any("exceeds 1h limit" in e for e in errors)


def test_prohibit_raw_seconds_ttl_bypass(mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    payload = {
        "_namespace": "test",
        "api_paths": [{
            "api_path": "v1/sys/mounts/test",
            "api_action": "post",
            "api_payload": {"config": {"default_lease_ttl": "7200"}},
        }],
    }
    errors = validator.validate("dev", payload=payload)
    assert any("exceeds 1h limit" in e for e in errors)


def test_prohibit_modern_acl_put_read_write_policy(mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    payload = {
        "_namespace": "test",
        "api_paths": [{
            "api_path": "v1/sys/policies/acl/test",
            "api_action": "put",
            "api_payload": {"path": {"secret/*": {"capabilities": ["read", "update"]}}},
        }],
    }
    errors = validator.validate("dev", payload=payload)
    assert any("mixes Read/Write" in e for e in errors)

def test_validate_dispatch(mock_logger):
    validator = ValidationManager("namespaces", mock_logger)
    # Testing that it actually calls Pydantic and finds errors
    payload = {
        "_namespace": "test",
        "api_paths": [
            {"api_path": "v1/sys/policy/test", "api_action": "post", "api_payload": {"path": {"*": {"capabilities": ["read", "update"]}}}}
        ]
    }
    errors = validator.validate("dev", payload=payload)
    assert any("mixes Read/Write" in e for e in errors)
