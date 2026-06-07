import json
import pytest
from unittest.mock import MagicMock, patch
from projects.vault.lib.engines.payload_processor import PayloadProcessor

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.logger = MagicMock()
    return client

def test_inline_unwrap(mock_client):
    processor = PayloadProcessor(mock_client)
    api_object = {"wrapped_token": "test-token"}
    mock_client.post.return_value = {"data": {"secret": "unwrapped"}}
    
    processor.process(api_object)
    
    mock_client.post.assert_called_with("/v1/sys/wrapping/unwrap", {"token": "test-token"})
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
    mock_client.post.return_value = {"data": {"plaintext": "cGxhaW50ZXh0"}} 
    
    processor.process(api_object)
    
    mock_client.post.assert_called_with("v1/my-transit/decrypt/my-key", {"ciphertext": "ciphertext"})
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
