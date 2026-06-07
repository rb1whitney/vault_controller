import argparse
import re


def validate_cluster_name(value):
    """Validate Vault cluster name."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise argparse.ArgumentTypeError(f"Invalid cluster name format: {value}")
    return value


def validate_namespace(value):
    """Validate Vault namespace."""
    if value and not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise argparse.ArgumentTypeError(f"Invalid namespace format: {value}")
    return value


def validate_path(value):
    """Validate Vault path to prevent traversal."""
    if ".." in value:
        raise argparse.ArgumentTypeError(f"Path traversal not allowed: {value}")
    if not re.match(r"^/?([a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+/?$", value):
        raise argparse.ArgumentTypeError(f"Invalid Vault path format: {value}")
    return value


def normalize_time(time_str):
    """Converts Vault time strings (e.g. 1h, 30d) to integer seconds."""
    if not isinstance(time_str, str):
        return -1
    
    match = re.match(r"^(\d+)([hmsd])$", time_str.lower())
    if not match:
        return -1
    
    value, unit = match.groups()
    value = int(value)
    
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    
    return value * multipliers[unit]
