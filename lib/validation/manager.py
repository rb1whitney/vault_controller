import os
import re

import yaml

from .rules import normalize_time


class ValidationManager:
    """
    Orchestrates complex business logic validation for Vault payloads.
    Decoupled from script execution.
    """

    def __init__(self, scheme, logger):
        self.scheme = scheme
        self.logger = logger

    def validate(self, cluster_name, files=None, payload=None):
        """Dispatches to the correct validator based on the scheme."""
        errors = []
        if self.scheme == "namespaces":
            errors.extend(self._validate_namespaces(files))
            errors.extend(self._prohibit_read_write_policy(files))
            errors.extend(self._prohibit_long_lived_tokens(files))
        elif self.scheme == "admin":
            # Admin-specific logic (currently permissive)
            pass
        elif self.scheme == "secret":
            errors.extend(self._prohibit_configurations(payload))
        else:
            raise ValueError(f"Unknown validation scheme: {self.scheme}")

        return errors

    def _validate_namespaces(self, files):
        """Ensures files are in the correct namespace directory."""
        errors = []
        for f in files or []:
            with open(f, "r") as stream:
                data = yaml.safe_load(stream)
            
            # Extract expected namespace from file path
            expected = os.path.abspath(f).split("namespaces/")[-1].split("/")[0]
            actual = data.get("_namespace")

            if not actual:
                errors.append(f"Namespace missing in {f}")
            elif actual != expected:
                errors.append(f"Namespace mismatch in {f}: expected {expected}, got {actual}")
            elif actual == "root":
                errors.append(f"Root namespace is strictly prohibited in payload: {f}")
        return errors

    def _prohibit_read_write_policy(self, files):
        """Ensures policies do not mix read and write capabilities on the same path."""
        errors = []
        for f in files or []:
            with open(f, "r") as stream:
                data = yaml.safe_load(stream)
            
            for obj in data.get("api_paths", []):
                if "sys/policy" in obj["api_path"]:
                    policy_data = obj.get("api_payload", {}).get("path", {})
                    for path, caps in policy_data.items():
                        c = caps.get("capabilities", [])
                        if ("read" in c or "list" in c) and ("create" in c or "update" in c or "delete" in c):
                            errors.append(f"Policy {obj['api_path']} in {f} mixes Read/Write on path: {path}")
        return errors

    def _prohibit_long_lived_tokens(self, files):
        """Enforces TTL limits on mounts and roles."""
        errors = []
        for f in files or []:
            with open(f, "r") as stream:
                data = yaml.safe_load(stream)
            
            for obj in data.get("api_paths", []):
                if "sys/mounts" in obj["api_path"]:
                    config = obj.get("api_payload", {}).get("config", {})
                    ttl = normalize_time(config.get("default_lease_ttl", "0s"))
                    # 2026 SRE Standard: Default TTL must not exceed 1 hour
                    if ttl > 3600:
                        errors.append(f"Default TTL in {f} exceeds 1h limit")
        return errors

    def _prohibit_configurations(self, payload):
        """Prevents sensitive system re-configuration via wrapped tokens."""
        errors = []
        for obj in payload.get("api_paths", []):
            if "sys/policy" in obj["api_path"]:
                errors.append(f"Forbidden: Policy modification via wrapped token: {obj['api_path']}")
            if obj["api_action"] in ["delete", "list"]:
                errors.append(f"Forbidden: Action '{obj['api_action']}' not allowed in secrets deployment")
        return errors
