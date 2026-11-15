from unittest.mock import patch

import pytest

from lib.core import command as secure_cmd
from lib.core.errors import VaultError


def test_run_valid_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "success"
        
        result = secure_cmd.run(["echo", "success"])
        assert result.stdout == "success"
        mock_run.assert_called_once_with(["echo", "success"], capture_output=True, text=True, check=False, shell=False, cwd=None, env=None)

def test_run_invalid_command_type():
    with pytest.raises(ValueError, match="Command must be a list"):
        secure_cmd.run("echo shell injection")

def test_run_command_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 2
        mock_run.return_value.stderr = "error"
        
        with pytest.raises(VaultError) as e:
            secure_cmd.run(["ls", "/nonexistent"], check=True)
        assert e.value.status_code == 2
