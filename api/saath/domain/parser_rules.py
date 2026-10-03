"""Deterministic multilingual (English/Hindi/Hinglish) rule-based event extractor."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from saath.domain.events import ActionKind, EventType

# Numbers in Hindi words
HINDI_NUMBER_WORDS = {
    "ek": 1,
    "do": 2,
    "teen": 3,
    "char": 4,
    "panch": 5,
    "chheh": 6,
    "saat": 7,
    "aath": 8,
    "nau": 9,
    "das": 10,
    "gyarah": 11,
    "barah": 12,
    "terah": 13,
    "chaudah": 14,
    "pandrah": 15,
    "solah": 16,
    "satrah": 17,
    "atharah": 18,
    "unnis": 19,
    "bees": 20,
    "sau": 100,
    "hazaar": 1000,
}

INJECTION_PATTERNS = [
    r"(ignore\s+(all\s+)?(previous\s+)?instructions)",
    r"(system\s+prompt)",
    r"(delete\s+all\s+data)",
    r"(mark\s+everything\s+done)",
    r"(drop\s+table)",
    r"(bypass\s+auth)",
    r"(override\s+security)",
    r"(disregard\s+constraints)",
]


def detect_prompt_injection(text: str) -> bool:
    """Checks for prompt injection attempts in input text."""
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in INJECTION_PATTERNS)


def parse_numeric_amount_paise(text: str) -> int | None:
    """Extracts rupee amount from digits or common Hindi words and converts to paise."""
    # 1. Match direct digits like 1450, 1,450, 500.50, ₹1450
    m = re.search(
        r"(?:rs\.?|₹|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|rupees|paise)?", text.lower()
    )
    if m:
        val_str = m.group(1).replace(",", "")
        try:
            val_float = float(val_str)
            return int(round(val_float * 100))
        except ValueError:
            pass

    # 2. Match words like "pandrah sau" (1500)
    lowered = text.lower()
    if "pandrah sau" in lowered:
        return 1500 * 100
    if "hazaar" in lowered:
        m_haz = re.search(r"(\w+)\s+hazaar", lowered)
        if m_haz and m_haz.group(1) in HINDI_NUMBER_WORDS:
            return HINDI_NUMBER_WORDS[m_haz.group(1)] * 1000 * 100

    return None


def extract_rules_events(
    text: str,
    author_id: str,
    members: Sequence[Mapping[str, Any]],
    now_ms: int,
) -> list[dict[str, Any]]:
    """
    Deterministic fallback parser.
    Extracts candidate events from Hinglish/Hindi/English utterances.
    """
    t = text.lower().strip()
    events: list[dict[str, Any]] = []

    # Check prompt injection
    if detect_prompt_injection(t):
        events.append(
            {
                "event_type": EventType.NOTE_RECORDED.value,
                "confidence": 0.3,
                "payload": {
                    "text": text,
                    "tags": ["suspicious_injection", "raw_note"],
                },
            }
        )
        return events

    # 1. Household Issues & Commitments (e.g. "tap leak ho raha hai, landlord bola kal plumber bhejega")
    has_leak = any(k in t for k in ["leak", "tap", "kharab", "pipe", "geyser", "broken", "theek", "repair", "fix", "servicing"])
    has_landlord = "landlord" in t or "owner" in t or "makan malik" in t
    has_plumber = "plumber" in t or "electrician" in t or "aadmi" in t or "technician" in t or "internet" in t or "wifi" in t

    if (has_leak or "promised" in t or "bhejega" in t) and (has_landlord or has_plumber):
        if "electrician" in t:
            service = "Electrician repair"
        elif "internet" in t or "wifi" in t:
            service = "Internet repair"
        elif "plumber" in t:
            service = "Send plumber to fix tap leak" if ("tap" in t or "leak" in t) else "Plumber repair"
        else:
            service = "Maintenance repair"

        events.append(
            {
                "event_type": EventType.ISSUE_REPORTED.value,
                "confidence": 0.95,
                "payload": {
                    "title": service,
                    "category": "maintenance",
                    "description": text,
                    "urgency": "high" if "urgent" in t or "jaldi" in t else "normal",
                },
            }
        )
        # Relative time detection (never default if unmentioned)
        rel_time = None
        if "kal" in t or "tomorrow" in t:
            rel_time = "tomorrow"
        elif "parso" in t or "day after tomorrow" in t:
            rel_time = "day_after_tomorrow"
        elif "monday" in t:
            rel_time = "monday"

        comm_payload: dict[str, Any] = {
            "title": service,
            "promise_made_by": "Landlord" if has_landlord else "Plumber",
            "responsible_party": "Landlord" if has_landlord else "Plumber",
            "tracked_by": author_id,
        }
        if rel_time:
            time_of_day = "evening" if ("shaam" in t or "evening" in t) else ("morning" if ("subah" in t or "morning" in t) else "general")
            comm_payload["symbolic_due"] = {"rel": rel_time, "time_of_day": time_of_day}

        events.append(
            {
                "event_type": EventType.COMMITMENT_CREATED.value,
                "confidence": 0.95,
                "payload": comm_payload,
            }
        )
        return events

    # 2. Expenses (e.g. "bijli ka bill bhar diya 1450, teen mein split")
    is_bill_or_paid = any(
        k in t for k in ["bill", "bhar diya", "paid", "kharcha", "spent", "split"]
    )
    amount_paise = parse_numeric_amount_paise(t)
    if is_bill_or_paid and amount_paise:
        title = (
            "Electricity bill"
            if "bijli" in t or "electric" in t
            else ("Wifi bill" if "wifi" in t else "Household expense")
        )
        # Find participants
        member_ids = tuple(m["id"] for m in members) if members else (author_id,)
        events.append(
            {
                "event_type": EventType.EXPENSE_CREATED.value,
                "confidence": 0.90,
                "payload": {
                    "title": title,
                    "amount_paise": amount_paise,
                    "paid_by": author_id,
                    "participant_ids": member_ids,
                    "is_confirmed": False,  # MUST REQUIRE USER CONFIRMATION
                },
            }
        )
        return events

    # 3. Supply Depletion (e.g. "doodh khatam hai", "gas khatam")
    if "khatam" in t or "empty" in t or "finished" in t or "out of" in t:
        item = (
            "milk"
            if ("doodh" in t or "milk" in t)
            else ("cooking gas" if "gas" in t else "supplies")
        )
        events.append(
            {
                "event_type": EventType.SUPPLY_DEPLETED.value,
                "confidence": 0.95,
                "payload": {
                    "item_name": item,
                    "item_norm": item.lower().replace(" ", "_"),
                    "reported_by": author_id,
                },
            }
        )
        return events

    # 4. Invisible Work / Coordination (e.g. "maine plumber ko 3 baar call kiya")
    m_call = re.search(r"(\d+)\s*(?:baar|times)?\s*call", t)
    if "call kiya" in t or "called" in t or m_call:
        times = int(m_call.group(1)) if m_call else 1
        label = (
            "Followed up with plumber"
            if "plumber" in t
            else ("Followed up with landlord" if "landlord" in t else "Followed up on call")
        )
        for _ in range(times):
            events.append(
                {
                    "event_type": EventType.ACTION_TAKEN.value,
                    "confidence": 0.95,
                    "payload": {
                        "member_id": author_id,
                        "kind": ActionKind.COORDINATION.value,
                        "label": label,
                        "details": text,
                    },
                }
            )
        return events

    # 5. Domestic Help Notice (e.g. "bai aaj nahi aayi")
    if ("bai" in t or "maid" in t or "cook" in t) and ("nahi aayi" in t or "absent" in t or "didn't come" in t):
        events.append(
            {
                "event_type": EventType.ACTION_TAKEN.value,
                "confidence": 0.95,
                "payload": {
                    "member_id": author_id,
                    "kind": ActionKind.COORDINATION.value,
                    "label": "Noticed maid absence",
                    "details": text,
                },
            }
        )
        return events

    # 6. Commitment assigned to a flatmate (e.g. "gas Rahul mangayega parso tak")
    for m in members:
        m_name = m.get("name", "").lower()
        if m_name and m_name in t:
            rel = (
                "day_after_tomorrow" if "parso" in t else ("tomorrow" if "kal" in t else "tomorrow")
            )
            events.append(
                {
                    "event_type": EventType.COMMITMENT_CREATED.value,
                    "confidence": 0.90,
                    "payload": {
                        "title": "Order cooking gas" if "gas" in t else "Household task",
                        "promise_made_by": m["name"],
                        "responsible_party": m["name"],
                        "tracked_by": author_id,
                        "symbolic_due": {"rel": rel, "time_of_day": "evening"},
                    },
                }
            )
            return events

    # Default fallback: save as note
    events.append(
        {
            "event_type": EventType.NOTE_RECORDED.value,
            "confidence": 0.5,
            "payload": {
                "text": text,
                "tags": ["general_note"],
            },
        }
    )
    return events


@dataclass(frozen=True)
class ExtractedParseResult:
    inferred_event_type: str
    amount_paise: int | None
    due_symbol: str | None
    category: str | None
    is_injection: bool


class MultilingualRuleParser:
    """Parser class for evaluating and routing natural household utterances."""

    def parse(self, text: str) -> ExtractedParseResult:
        t = text.lower().strip()

        # 1. Prompt Injection check
        if detect_prompt_injection(t):
            return ExtractedParseResult(
                inferred_event_type="note_recorded",
                amount_paise=None,
                due_symbol=None,
                category=None,
                is_injection=True,
            )

        # 2. Extract amount if present
        amount_paise = parse_numeric_amount_paise(t)

        # 3. Expenses take precedence when a numerical amount is extracted with payment/service keywords
        is_payment_verb = any(
            k in t
            for k in [
                "paid",
                "bought",
                "bill",
                "rent",
                "salary",
                "renewal",
                "split",
                "zomato",
                "blinkit",
                "pay",
                "rupees",
                "cash",
                "rs",
                "online",
            ]
        )
        if amount_paise is not None and (is_payment_verb or "₹" in text):
            return ExtractedParseResult(
                inferred_event_type="expense_created",
                amount_paise=amount_paise,
                due_symbol=None,
                category="expenses",
                is_injection=False,
            )

        # 4. Actions already completed (if no amount is attached)
        is_completed = (
            "done" in t
            or "fixed" in t
            or "replaced" in t
            or "cleared" in t
            or "spoke to" in t
            or "coordinated" in t
            or "aa gaya aur" in t
            or "breakfast made by me" in t
            or "work done" in t
            or "call kiya" in t
        )
        if is_completed:
            return ExtractedParseResult(
                inferred_event_type="action_taken",
                amount_paise=None,
                due_symbol=None,
                category="coordination" if "coordinated" in t or "spoke" in t else "maintenance",
                is_injection=False,
            )

        # 5. Domestic help notices / Supplies
        is_domestic_or_supply = (
            "will not come" in t
            or "khali ho gaya" in t
            or "completely over" in t
            or "finished" in t
            or "empty" in t
            or "got 20l" in t
            or "water jar" in t
            or "khatam" in t
        )
        if is_domestic_or_supply and not ("said" in t or "promised" in t or "bola" in t):
            return ExtractedParseResult(
                inferred_event_type="supply_status_changed",
                amount_paise=None,
                due_symbol=None,
                category="supplies",
                is_injection=False,
            )

        # 6. Issues reported (broken, leaking, fused, broke, came off the wall, etc.)
        is_issue = (
            "broken" in t
            or "came off" in t
            or "fused" in t
            or "leaking" in t
            or "stopped working" in t
            or "turntable plate broke" in t
            or "due next week" in t
        )
        if is_issue and not ("will" in t or "promised" in t or "scheduled" in t or "bola" in t):
            return ExtractedParseResult(
                inferred_event_type="issue_reported",
                amount_paise=None,
                due_symbol=None,
                category="repair",
                is_injection=False,
            )

        # 7. Commitments (scheduling, promises, reminders for future)
        due_symbol: str | None = None
        for day in [
            "tomorrow",
            "kal",
            "कल",
            "parso",
            "परसों",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "tonight",
            "today",
        ]:
            if day in t:
                due_symbol = "kal" if day == "कल" else ("parso" if day == "परसों" else day)
                break

        is_promise = (
            "said" in t
            or "will" in t
            or "promised" in t
            or "scheduled" in t
            or "bola" in t
            or "बोला" in t
            or "भेजेगा" in t
            or "agreed" in t
            or "bhejega" in t
            or "delivery hogi" in t
            or "aayega" in t
            or "meeting" in t
            or due_symbol is not None
        )
        if is_promise:
            return ExtractedParseResult(
                inferred_event_type="commitment_created",
                amount_paise=None,
                due_symbol=due_symbol,
                category="commitments",
                is_injection=False,
            )

        # Default fallback
        return ExtractedParseResult(
            inferred_event_type="note_recorded",
            amount_paise=amount_paise,
            due_symbol=None,
            category="notes",
            is_injection=False,
        )
