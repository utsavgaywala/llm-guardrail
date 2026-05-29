"""
Input Guardrail
===============
Checks every user message BEFORE it reaches the LLM.

3 things it checks:
  1. PII - personal information like credit cards, emails
  2. Prompt Injection - "ignore previous instructions..."
  3. Jailbreak - "act as DAN with no restrictions..."

If any check fails → message is BLOCKED.
LLM never sees it.
"""

import re
from app.guardrails.policy_engine import PolicyEngine


# ── PII Patterns ──────────────────────────────────────────
# These are regex patterns that match personal information

PII_PATTERNS = {
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
    "email":       r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone_india": r"\b[6-9]\d{9}\b",
    "aadhaar":     r"\b\d{4}\s\d{4}\s\d{4}\b",
    "pan_card":    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "password":    r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+",
}

# ── Prompt Injection Patterns ─────────────────────────────
# These are phrases attackers use to override instructions

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|rules)",
    r"forget\s+(everything|all|prior|previous)",
    r"your\s+new\s+(instructions|rules)\s+are",
    r"override\s+(safety|guidelines|rules|instructions)",
    r"system\s*prompt\s*[:=]",
]

# ── Jailbreak Patterns ────────────────────────────────────
# These are phrases used to remove AI safety restrictions

JAILBREAK_PATTERNS = [
    r"act\s+as\s+(an?\s+)?(unrestricted|unfiltered|evil|jailbroken)",
    r"you\s+have\s+no\s+(rules|restrictions|guidelines|ethics)",
    r"pretend\s+(you\s+are|to\s+be)\s+(evil|uncensored|unfiltered)",
    r"developer\s+mode",
    r"\bjailbreak\b",
    r"do\s+anything\s+now",
    r"\bdan\b.*\bno\s+restrictions\b",
]


class InputGuardrail:

    def __init__(self, policy_engine: PolicyEngine):
        self.policy = policy_engine

    async def check(self, message: str) -> dict:
        """
        Run all active checks on the user message.

        Returns a dict:
        {
            "blocked": True or False,
            "reason":  "Why it was blocked" or None,
            "checks":  ["list of checks performed"]
        }
        """
        checks = []

        # ── Check 1: PII Detection ────────────────────────
        if self.policy.is_active("block_pii"):
            pii_found = self._detect_pii(message)
            if pii_found:
                return {
                    "blocked": True,
                    "reason": f"PII detected: {pii_found}. Please do not share personal information.",
                    "checks": checks + [f"pii_check: BLOCKED ({pii_found})"]
                }
            checks.append("pii_check: pass")

        # ── Check 2: Prompt Injection ─────────────────────
        if self.policy.is_active("block_prompt_injection"):
            if self._detect_injection(message):
                return {
                    "blocked": True,
                    "reason": "Prompt injection attempt detected.",
                    "checks": checks + ["injection_check: BLOCKED"]
                }
            checks.append("injection_check: pass")

        # ── Check 3: Jailbreak ────────────────────────────
        if self.policy.is_active("block_jailbreak"):
            if self._detect_jailbreak(message):
                return {
                    "blocked": True,
                    "reason": "Jailbreak attempt detected.",
                    "checks": checks + ["jailbreak_check: BLOCKED"]
                }
            checks.append("jailbreak_check: pass")

        # ── Check 4: Message Length ───────────────────────
        max_len = self.policy.get_value("max_input_length", 2000)
        if len(message) > max_len:
            return {
                "blocked": True,
                "reason": f"Message too long. Max allowed: {max_len} characters.",
                "checks": checks + [f"length_check: BLOCKED ({len(message)} chars)"]
            }
        checks.append(f"length_check: pass ({len(message)} chars)")

        # ── All checks passed ─────────────────────────────
        return {
            "blocked": False,
            "reason": None,
            "checks": checks
        }

    # ── Helper Methods ────────────────────────────────────

    def _detect_pii(self, text: str):
        """Returns the PII type found, or None."""
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return pii_type
        return None

    def _detect_injection(self, text: str) -> bool:
        """Returns True if injection pattern found."""
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _detect_jailbreak(self, text: str) -> bool:
        """Returns True if jailbreak pattern found."""
        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False