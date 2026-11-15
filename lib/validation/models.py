import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class ApiObject(BaseModel):
    api_path: str
    api_action: str
    api_payload: Optional[Dict[str, Any]] = None
    wrapped_token: Optional[str] = None
    transit_encoded_keys: Optional[List[str]] = None
    transit_secret_engine: Optional[str] = "transit"
    transit_engine: Optional[str] = None
    transit_key: Optional[str] = "namespace-encryption"
    transit_context: Optional[str] = None
    decode_base64_keys: Optional[List[str]] = None

    @validator("api_path")
    def validate_path(cls, v):
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        return v

class VaultPayload(BaseModel):
    namespace: Optional[str] = Field(None, alias="_namespace")
    api_paths: List[ApiObject]

    @root_validator(pre=False)
    def validate_ttl(cls, values):
        api_paths = values.get("api_paths", [])
        for obj in api_paths:
            if "sys/mounts" in obj.api_path:
                payload = obj.api_payload or {}
                config = payload.get("config", {})
                ttl_str = config.get("default_lease_ttl", "0s")
                ttl_seconds = cls.normalize_time(ttl_str)
                if ttl_seconds > 3600:
                    raise ValueError(f"Default TTL {ttl_str} exceeds 1h limit")
        return values

    @staticmethod
    def normalize_time(time_str):
        """Converts Vault time strings (e.g. 1h, 30d, or raw seconds) to integer seconds."""
        if isinstance(time_str, int):
            return time_str
        if not isinstance(time_str, str):
            return -1
        cleaned = time_str.strip().lower()
        if cleaned.isdigit():
            return int(cleaned)
        match = re.match(r"^(\d+)([hmsd])$", cleaned)
        if not match:
            return -1
        value, unit = match.groups()
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return int(value) * multipliers[unit]


def validate_cluster_name(value: str) -> str:
    """Validate Vault cluster name."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise ValueError(f"Invalid cluster name format: {value}")
    return value


def validate_namespace(value: Optional[str]) -> Optional[str]:
    """Validate Vault namespace."""
    if value and not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise ValueError(f"Invalid namespace format: {value}")
    return value


def validate_path(value: str) -> str:
    """Validate Vault path to prevent traversal."""
    if ".." in value:
        raise ValueError(f"Path traversal not allowed: {value}")
    if not re.match(r"^/?([a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+/?$", value):
        raise ValueError(f"Invalid Vault path format: {value}")
    return value
