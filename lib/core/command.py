import subprocess

from .errors import VaultError
from .logger import get_logger

logger = get_logger("secure_cmd")


def _redact_cmd(cmd):
    """Mask sensitive key=value arguments before logging."""
    sensitive_prefixes = ("password=", "token=", "secret=", "backup=", "key=")
    redacted = []
    for arg in cmd:
        lower = arg.lower()
        if any(lower.startswith(p) for p in sensitive_prefixes):
            prefix = arg.split("=", 1)[0]
            redacted.append(f"{prefix}=<REDACTED>")
        else:
            redacted.append(arg)
    return " ".join(redacted)


def run(cmd, check=True, cwd=None, capture_output=True, env=None):
    """
    Execute a subprocess command securely.
    Ensures that cmd is a list of arguments, preventing shell injection.
    """
    if not isinstance(cmd, list):
        msg = f"Command must be a list to prevent shell injection, got: {type(cmd)}"
        logger.error(msg)
        raise ValueError(msg)

    logger.info(f"Running secure command: {_redact_cmd(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False,  # We handle the check manually
            shell=False,  # Strictly forbidden
            cwd=cwd,
            env=env,
        )
    except Exception as e:
        msg = f"Failed to execute command: {e}"
        logger.error(msg)
        raise VaultError(message=msg) from e

    if check and result.returncode != 0:
        msg = f"Command failed with exit code {result.returncode}: {result.stderr}"
        logger.error(msg)
        raise VaultError(status_code=result.returncode, message=msg)

    return result
