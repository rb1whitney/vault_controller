import os
import sys
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.core.logger import get_logger
from lib.engines.payload_processor import PayloadProcessor
from lib.utils.crypto import convert_pgp_key, format_key_response
from lib.utils.ops import backup, handle_encrypt, init_cluster


def test_handle_encrypt_import():
    assert callable(handle_encrypt)


def test_init_cluster_import():
    assert callable(init_cluster)


def test_backup_import():
    assert callable(backup)


def test_get_logger_returns_configured_logger():
    log = get_logger("test_vault_logger", "DEBUG")
    assert log.name == "test_vault_logger"
    assert len(log.handlers) >= 1


def test_convert_pgp_key_preserves_base64_equals():
    pgp = (
        "-----BEGIN PGP PUBLIC KEY BLOCK-----\n"
        "Version: GnuPG v2\n\n"
        "mQENBFxyz==\n"
        "abcd1234==\n"
        "=CRC4\n"
        "-----END PGP PUBLIC KEY BLOCK-----\n"
    )
    cleaned = convert_pgp_key(pgp)
    assert "mQENBFxyz==" in cleaned
    assert "abcd1234==" in cleaned
    assert "BEGIN PGP" not in cleaned
    assert "END PGP" not in cleaned


def test_handle_encrypt_nested_kv_v2(tmp_path):
    manifest = tmp_path / "secret.yaml"
    manifest.write_text(
        "api_paths:\n"
        "- api_path: v1/app/data/db\n"
        "  api_action: post\n"
        "  api_payload:\n"
        "    data:\n"
        "      password: secret123\n"
    )
    mock_client = MagicMock()
    mock_client.post.return_value = {
        "data": {"batch_results": [{"ciphertext": "vault:v1:encrypted"}]}
    }
    handle_encrypt(mock_client, str(manifest), transit_context="ctx")
    call_args = mock_client.post.call_args[0][1]
    assert call_args["batch_input"][0]["context"] == "ctx"
    assert "vault:v1:encrypted" in manifest.read_text()


def test_format_key_response_handles_fewer_key_holders():
    res = format_key_response({"keys": ["k1", "k2", "k3"]}, ["admin@example.com"], False)
    assert len(res) == 3
    assert res["Keyholder #1"]["email_address"] == "admin@example.com"
    assert res["Keyholder #3"]["email_address"] == "keyholder-3@unassigned"


def test_payload_processor_auto_detects_without_transit_meta():
    mock_client = MagicMock()
    mock_client.hvac_client.secrets.transit.decrypt_data.return_value = {
        "data": {"plaintext": "cGxhaW50ZXh0"}
    }
    processor = PayloadProcessor(mock_client)
    obj = {
        "api_path": "v1/app/data/db",
        "api_action": "post",
        "api_payload": {"data": {"password": "vault:v1:abc"}},
    }
    processor.process(obj)
    assert obj["api_payload"]["data"]["password"] == "plaintext"
