import os

import yaml
from pydantic import ValidationError

from .models import VaultPayload


class ValidationManager:
    """
    Orchestrates complex business logic validation for Vault payloads.
    Uses Pydantic for structural validation and custom methods for domain logic.
    """

    def __init__(self, scheme, logger):
        self.scheme = scheme
        self.logger = logger

    def validate(self, cluster_name, files=None, payload=None):
        """Dispatches to the correct validator based on the scheme."""
        errors = []
        
        if files:
            for f in files:
                try:
                    with open(f) as stream:
                        data = yaml.safe_load(stream)
                    model = VaultPayload(**data)
                    errors.extend(self._run_logic_checks(f, model))
                except ValidationError as e:
                    for error in e.errors():
                        msg = f"{f}: {error['loc']} - {error['msg']}"
                        errors.append(msg)
                except Exception as e:
                    errors.append(f"Error processing {f}: {e}")

        if payload:
            try:
                model = VaultPayload(**payload)
                errors.extend(self._run_logic_checks("Payload", model))
            except ValidationError as e:
                for error in e.errors():
                    errors.append(f"Payload: {error['loc']} - {error['msg']}")

        return errors

    def _run_logic_checks(self, source, model):
        """Runs domain-specific logic checks based on the validation scheme."""
        errors = []
        if self.scheme == "namespaces":
            if source != "Payload":
                errors.extend(self._validate_namespace_dir(source, model))
            errors.extend(self._prohibit_read_write_policy(source, model))
        elif self.scheme == "admin":
            if model.namespace == "root":
                errors.append(
                    f"Root namespace is strictly prohibited in payload: {source}"
                )
        elif self.scheme == "secret":
            errors.extend(self._prohibit_configurations(model))
        return errors

    def _validate_namespace_dir(self, file_path, model):
        """Ensures files under a namespaces/ directory match their folder name."""
        errors = []
        abs_path = os.path.abspath(file_path)
        actual = model.namespace

        if actual == "root":
            errors.append(f"Root namespace is strictly prohibited in payload: {file_path}")
            return errors

        if "namespaces/" in abs_path:
            expected = abs_path.split("namespaces/")[-1].split("/")[0]
            if not actual:
                errors.append(f"Namespace missing in {file_path}")
            elif actual != expected:
                errors.append(
                    f"Namespace mismatch in {file_path}: expected {expected}, got {actual}"
                )
        return errors

    def _prohibit_read_write_policy(self, source, model):
        """Ensures policies do not mix read and write capabilities on the same path."""
        errors = []
        for obj in model.api_paths:
            is_policy_path = "sys/policy" in obj.api_path or "sys/policies/acl" in obj.api_path
            if is_policy_path and obj.api_action.lower() in ("post", "put"):
                payload = obj.api_payload or {}
                policy_data = payload.get("path", {})
                for path, caps in policy_data.items():
                    c = caps.get("capabilities", [])
                    is_read = "read" in c or "list" in c
                    is_write = "create" in c or "update" in c or "delete" in c
                    if is_read and is_write:
                        errors.append(f"Policy {obj.api_path} in {source} mixes Read/Write on path: {path}")
        return errors

    def _prohibit_configurations(self, model):
        """Prevents sensitive system re-configuration via wrapped tokens."""
        errors = []
        forbidden_prefixes = (
            "sys/policy",
            "sys/policies/acl",
            "sys/auth",
            "sys/audit",
            "sys/mounts",
            "sys/generate-root",
        )
        for obj in model.api_paths:
            if any(p in obj.api_path for p in forbidden_prefixes):
                errors.append(f"Forbidden: System/policy modification via wrapped token: {obj.api_path}")
            if obj.api_action.lower() in ["delete", "list"]:
                errors.append(f"Forbidden: Action '{obj.api_action}' not allowed in secrets deployment")
        return errors
