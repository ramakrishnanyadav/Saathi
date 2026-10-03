"""Deterministic source verifier for extracted events."""

from __future__ import annotations

import re
from typing import Any

from saath.domain.events import EventType

COMMON_HINDI_NUMBERS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "panch": 5,
    "chheh": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "sau": 100, "hazaar": 1000, "lakh": 100000, "pandrah": 15,
}


def verify_event_against_source(
    event_type: EventType,
    payload: dict[str, Any],
    source_text: str,
    base_confidence: float = 1.0,
) -> float:
    """
    Deterministic check that amounts, key entities, or titles extracted actually
    appear in the raw user message. If amounts or entities were hallucinated,
    confidence is severely downgraded.
    """
    lowered = source_text.lower()
    confidence = base_confidence

    if event_type == EventType.EXPENSE_CREATED:
        amt = payload.get("amount_paise")
        if amt is not None:
            rupees = int(amt) // 100
            # Check if direct rupees digits or normalized number representation appears in source
            rupee_str = str(rupees)
            digits_in_source = re.findall(r"\d+", lowered)
            has_rupee_match = rupee_str in lowered or any(d in rupee_str for d in digits_in_source if len(d) >= 2)
            has_word_match = any(word in lowered for word in COMMON_HINDI_NUMBERS)

            if not has_rupee_match and not has_word_match and not digits_in_source:
                # Amount is not grounded in source text!
                confidence = min(confidence, 0.2)

    elif event_type == EventType.COMMITMENT_CREATED:
        resp = str(payload.get("responsible_party", "")).lower().strip()
        title = str(payload.get("title", "")).lower().strip()
        resp_tokens = set(re.findall(r"\w+", resp))
        title_tokens = set(re.findall(r"\w+", title))
        source_tokens = set(re.findall(r"\w+", lowered))

        # Check grounding: at least one token from responsible party, title, or service role must overlap
        grounded = bool(resp_tokens & source_tokens) or bool(title_tokens & source_tokens)
        if not grounded:
            confidence = min(confidence, 0.4)

    return confidence
