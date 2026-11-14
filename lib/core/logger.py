import logging
import sys


def get_logger(name="vault_automation", log_level="INFO"):
    """Returns a pre-configured logger with file and console handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # File Handler
        # fh = logging.FileHandler("vault_automation.log")
        # fh.setFormatter(formatter)
        # logger.addHandler(fh)

        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


# Default logger instance for quick imports
logger = get_logger()
