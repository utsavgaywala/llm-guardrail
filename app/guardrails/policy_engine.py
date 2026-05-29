"""
Policy Engine
=============
Reads policies.yaml and answers two questions:
  1. Is this policy enabled?
  2. What is this policy's value?

This means non-engineers can change gateway
behaviour just by editing the YAML file.
"""

import yaml
from pathlib import Path


class PolicyEngine:

    def __init__(self, config_path: str = "config/policies.yaml"):
        self.config_path = Path(config_path)
        self.policies = {}
        self._system_prompt = ""
        self.load()

    def load(self):
        """Read the YAML file and store policies in memory."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Policy file not found: {self.config_path}"
            )

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        self.policies = config.get("policies", {})
        self._system_prompt = config.get(
            "system_prompt",
            "You are a helpful assistant."
        )
        print(f"[PolicyEngine] Loaded {len(self.policies)} policies")

    def is_active(self, policy_name: str) -> bool:
        """Returns True if the policy is enabled in YAML."""
        policy = self.policies.get(policy_name, {})
        return policy.get("enabled", False)

    def get_value(self, policy_name: str, default=None):
        """Returns the value field of a policy."""
        policy = self.policies.get(policy_name, {})
        return policy.get("value", default)

    def get_system_prompt(self) -> str:
        """Returns the system prompt to send to LLM."""
        return self._system_prompt