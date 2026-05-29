"""
Output Guardrail
================
Checks LLM response BEFORE sending it to the user.

3 things it checks:
  1. Toxicity   - harmful or dangerous content
  2. Min Length - response is too short to be useful
  3. JSON valid - if JSON output is required by policy

If any check fails → response is BLOCKED.
User never sees the bad response.
Gateway auto-retries with a corrected prompt.
"""

import re
import json
from app.guardrails.policy_engine import PolicyEngine


# ── Toxic Content Patterns ────────────────────────────────
TOXIC_PATTERNS = [
    r"\bhow\s+to\s+(make|build|create)\s+(a\s+)?(bomb|weapon|poison|explosive)\b",
    r"\bstep[\s-]by[\s-]step\s+(guide|instructions?)\s+(to|for)\s+(harm|hurt|attack)\b",
    r"\b(kill|murder)\s+(yourself|himself|herself|themselves)\b",
]


class OutputGuardrail:

    def __init__(self, policy_engine: PolicyEngine):
        self.policy = policy_engine

    async def check(self, response: str) -> dict:
        """
        Run all active checks on the LLM response.

        Returns a dict:
        {
            "blocked": True or False,
            "reason":  "Why it was blocked" or None,
            "checks":  ["list of checks performed"]
        }
        """
        checks = []

        # ── Check 1: Toxicity ─────────────────────────────
        if self.policy.is_active("block_toxic_output"):
            if self._detect_toxicity(response):
                return {
                    "blocked": True,
                    "reason": "Response contains harmful content.",
                    "checks": checks + ["toxicity_check: BLOCKED"]
                }
            checks.append("toxicity_check: pass")

        # ── Check 2: Minimum Length ───────────────────────
        if self.policy.is_active("min_output_length"):
            min_len = self.policy.get_value("min_output_length", 10)
            if len(response.strip()) < min_len:
                return {
                    "blocked": True,
                    "reason": "Response is too short to be useful.",
                    "checks": checks + ["length_check: BLOCKED (too short)"]
                }
            checks.append(f"length_check: pass ({len(response)} chars)")

        # ── Check 3: JSON Validation ──────────────────────
        if self.policy.is_active("require_json_output"):
            is_valid, error = self._validate_json(response)
            if not is_valid:
                return {
                    "blocked": True,
                    "reason": f"Response is not valid JSON: {error}",
                    "checks": checks + [f"json_check: BLOCKED ({error})"]
                }
            checks.append("json_check: pass")

        # ── All checks passed ─────────────────────────────
        return {
            "blocked": False,
            "reason": None,
            "checks": checks
        }

    # ── Helper Methods ────────────────────────────────────

    def _detect_toxicity(self, text: str) -> bool:
        """Returns True if toxic pattern found."""
        for pattern in TOXIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _validate_json(self, text: str):
        """Returns (True, None) if valid JSON, else (False, error)."""
        try:
            json.loads(text)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)