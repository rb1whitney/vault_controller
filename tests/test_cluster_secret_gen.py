import subprocess
from unittest.mock import MagicMock, patch

import pytest
import yaml

from lib.utils.ops import SecretGenerator


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def rules_file(tmp_path):
    rules = {
        "rules": {
            "test_rule": {
                "command": "echo 'generated-{param}'",
                "params": ["param"],
            }
        }
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.dump(rules))
    return str(path)


def test_generator_init(rules_file, mock_logger):
    gen = SecretGenerator(rules_file, mock_logger)
    assert "test_rule" in gen.rules_config["rules"]


def test_generate_success(rules_file, mock_logger):
    gen = SecretGenerator(rules_file, mock_logger)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "generated-value"
        mock_run.return_value.returncode = 0
        
        res = gen.generate("test_rule", param="value")
        
        assert res == "generated-value"
        mock_run.assert_called_once()
        # Verify shell=False is used for security
        assert mock_run.call_args[1].get("shell", False) is False


def test_generate_missing_params(rules_file, mock_logger):
    gen = SecretGenerator(rules_file, mock_logger)
    with pytest.raises(ValueError, match="Missing required parameter"):
        gen.generate("test_rule")


def test_process_template(rules_file, mock_logger, tmp_path):
    gen = SecretGenerator(rules_file, mock_logger)
    template = tmp_path / "template.yaml"
    template.write_text("key: {{ test_rule(param=hello) }}")
    output = tmp_path / "output.yaml"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "live-secret"
        mock_run.return_value.returncode = 0

        gen.process_template(str(template), str(output))

        assert output.exists()
        assert output.read_text() == "key: live-secret"


def test_generate_failure(rules_file, mock_logger):
    gen = SecretGenerator(rules_file, mock_logger)
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error-msg")
        
        with pytest.raises(subprocess.CalledProcessError):
            gen.generate("test_rule", param="fail")
        
        mock_logger.error.assert_called()


def test_generate_unsafe_param(rules_file, mock_logger):
    gen = SecretGenerator(rules_file, mock_logger)
    with pytest.raises(ValueError, match="Unsafe characters"):
        gen.generate("test_rule", param="1)); __import__('os').system('id'")
