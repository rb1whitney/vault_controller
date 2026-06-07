#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Don't write byte code
sys.dont_write_bytecode = True

# Import standard library components
from projects.vault.lib.core.logger import get_logger
from projects.vault.lib.utils import config as vault_config


class SecretGenerator:
    """
    Orchestrates secret generation based on an external rules engine.
    """

    def __init__(self, rules_path, logger):
        with open(rules_path, "r") as f:
            self.rules_config = yaml.safe_load(f)
        self.logger = logger

    def generate(self, rule_name, **kwargs):
        """Executes a specific generation rule."""
        rule = self.rules_config.get("rules", {}).get(rule_name)
        if not rule:
            raise ValueError(f"Rule '{rule_name}' not found in rules engine.")

        # Ensure all required params are present
        for p in rule.get("params", []):
            if p not in kwargs:
                raise ValueError(
                    f"Missing required parameter '{p}' for rule '{rule_name}'."
                )

        cmd_str = rule["command"].format(**kwargs)
        self.logger.info(f"Executing generation rule: {rule_name}")

        try:
            result = subprocess.run(
                cmd_str,
                shell=True,  # Required for complex commands defined in yaml
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Generation failed: {e.stderr}")
            raise e

    def process_template(self, template_path, output_path):
        """Parses a template and replaces placeholders with generated secrets."""
        with open(template_path, "r") as f:
            content = f.read()

        # Regex for {{ rule_name(param1=val1, ...) }}
        pattern = re.compile(r"\{\{\s*(\w+)\((.*?)\)\s*\}\}")

        def replacer(match):
            rule_name = match.group(1)
            params_str = match.group(2)

            # Simple param parsing
            kwargs = {}
            if params_str:
                for pair in params_str.split(","):
                    k, v = pair.split("=")
                    kwargs[k.strip()] = v.strip().strip("'").strip('"')

            return self.generate(rule_name, **kwargs)

        processed_content = pattern.sub(replacer, content)

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            f.write(processed_content)
        self.logger.info(f"Successfully generated payload: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Vault Secret Generation Engine")
    parser.add_argument("--name", required=True, help="Vault Cluster Name")
    parser.add_argument(
        "--rules",
        default="projects/vault_controller/config/generation_rules.yaml",
        help="Path to rules engine",
    )
    parser.add_argument("--template", required=True, help="Input template YAML")
    parser.add_argument("--output", required=True, help="Target output YAML path")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    # Get Config and Initialize Logger
    try:
        vault_config.get_cluster_config(args.name)
    except NameError as e:
        print(f"Error: {e}")
        sys.exit(1)

    logger = get_logger("SecretGen", args.log_level)

    # Determine absolute path to rules if relative
    rules_path = Path(args.rules)
    if not rules_path.is_absolute():
        # Find repo root
        current_dir = Path(__file__).resolve().parent
        repo_root = current_dir.parent.parent.parent
        rules_path = repo_root / args.rules

    generator = SecretGenerator(rules_path, logger)
    generator.process_template(args.template, args.output)


if __name__ == "__main__":
    main()
