from unittest.mock import MagicMock

import pytest

from lib.engines.payload_processor import PayloadProcessor


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.logger = MagicMock()
    # Mock hvac_client structure
    client.hvac_client = MagicMock()
    return client

def test_inline_unwrap(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {"wrapped_token": "test-token"}
    mock_client.hvac_client.sys.unwrap.return_value = {"data": {"secret": "unwrapped"}}
    
    processor.process(api_object)
    
    mock_client.hvac_client.sys.unwrap.assert_called_with(token="test-token")
    assert api_object["api_payload"] == {"secret": "unwrapped"}

def test_inline_transit(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {
        "transit_encoded_keys": ["secret.data"],
        "api_payload": {"secret": {"data": "ciphertext"}},
        "transit_secret_engine": "my-transit",
        "transit_key": "my-key"
    }
    # base64 encoded "plaintext"
    mock_client.hvac_client.secrets.transit.decrypt_data.return_value = {"data": {"plaintext": "cGxhaW50ZXh0"}} 
    
    processor.process(api_object)
    
    mock_client.hvac_client.secrets.transit.decrypt_data.assert_called_with(
        name="my-key",
        ciphertext="ciphertext",
        context=None,
        mount_point="my-transit"
    )
    assert api_object["api_payload"]["secret"]["data"] == "plaintext"
    assert "transit_encoded_keys" not in api_object

def test_inline_base64(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {
        "decode_base64_keys": ["secret"],
        "api_payload": {"secret": "cGxhaW50ZXh0"}
    }
    
    processor.process(api_object)
    
    assert api_object["api_payload"]["secret"] == "plaintext"
    assert "decode_base64_keys" not in api_object

def test_inline_transform_policy(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {
        "api_path": "v1/sys/policy/test",
        "api_action": "post",
        "api_payload": {"path": {}}
    }
    
    processor.process(api_object)
    
    assert isinstance(api_object["api_payload"]["policy"], str)


def test_inline_transit_auto_detect_nested(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {
        "api_path": "v1/cloud-boot-app/data/mysql",
        "api_action": "post",
        "api_payload": {
            "data": {
                "username": "boot_admin",
                "password": "vault:v1:ciphertext123",
            }
        },
        "transit_engine": "transit",
        "transit_key": "vault-admin-transit-key",
    }
    mock_client.hvac_client.secrets.transit.decrypt_data.return_value = {
        "data": {"plaintext": "cGxhaW50ZXh0"}
    }

    processor.process(api_object)

    mock_client.hvac_client.secrets.transit.decrypt_data.assert_called_once_with(
        name="vault-admin-transit-key",
        ciphertext="vault:v1:ciphertext123",
        context=None,
        mount_point="transit",
    )
    assert api_object["api_payload"]["data"]["username"] == "boot_admin"
    assert api_object["api_payload"]["data"]["password"] == "plaintext"
    assert "transit_engine" not in api_object
    assert "transit_key" not in api_object
