"""Pure escalation ladder engine for SAATH follow-up progression."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from enum import Enum
from saath.domain.commitments import Commitment
from saath.domain.followup import FollowupDraft, FollowupStatus, Language


class EscalationRung(int, Enum):
    POLITE_NUDGE = 1
    FIRM_REMINDER = 2
    PRACTICAL_ALTERNATIVE = 3


def calculate_escalation_rung(
    reschedule_count: int = 0,
    hours_overdue: float = 0.0,
    prior_followups_sent: int = 0,
) -> EscalationRung:
    """
    Pure function computing escalation rung (1, 2, or 3) from context:
    - Rung 1 (Polite Nudge): 0-1 reschedules, < 24h overdue, 0 prior follow-ups.
    - Rung 2 (Firm Reminder): >= 2 reschedules OR >= 24h overdue OR 1 prior follow-up.
    - Rung 3 (Practical Alternative): >= 3 reschedules OR >= 72h overdue OR >= 2 prior follow-ups.
    """
    if reschedule_count >= 3 or hours_overdue >= 72.0 or prior_followups_sent >= 2:
        return EscalationRung.PRACTICAL_ALTERNATIVE
    if reschedule_count >= 2 or hours_overdue >= 24.0 or prior_followups_sent >= 1:
        return EscalationRung.FIRM_REMINDER
    return EscalationRung.POLITE_NUDGE


RUNG_TEMPLATES = {
    EscalationRung.POLITE_NUDGE: {
        Language.HINGLISH: "Hi {responsible}, {title} ke baare me puchna tha. Aapne bola tha ye ho jayega, bas update chahiye tha kab tak expect karein? Thanks!",
        Language.HI: "नमस्ते {responsible}, {title} के बारे में पूछना था। आपने कहा था यह हो जाएगा, क्या आप बता सकते हैं कब तक हो पाएगा? धन्यवाद।",
        Language.EN: "Hi {responsible}, following up regarding {title}. Could you please share a quick update on when we can expect this to be resolved? Thanks!",
    },
    EscalationRung.FIRM_REMINDER: {
        Language.HINGLISH: "Hi {responsible}, {title} abhi tak pending hai ({history_str}). Baar baar delay ho raha hai, please aaj confirm kar do kab tak final hoga.",
        Language.HI: "नमस्ते {responsible}, {title} अभी तक अटका हुआ है ({history_str})। कृपया आज स्पष्ट बता दें कि यह कब पूरा होगा।",
        Language.EN: "Hi {responsible}, regarding {title}, this is still pending ({history_str}). Could you please confirm the definitive timeline today?",
    },
    EscalationRung.PRACTICAL_ALTERNATIVE: {
        Language.HINGLISH: "Hi {responsible}, {title} me kaafi delay ho chuka hai. Agar aap nahi dekh pa rahe toh bata do, hum alternative arrange kar lete hain. Please kal tak batayein.",
        Language.HI: "नमस्ते {responsible}, {title} में काफ़ी देरी हो चुकी है। यदि आप नहीं कर पा रहे हैं तो बताएं, हम दूसरा विकल्प देखते हैं। कृपया कल तक सूचित करें।",
        Language.EN: "Hi {responsible}, {title} has been pending for a while. If you are unable to manage this, please let us know so we can arrange an alternative. Please confirm by tomorrow.",
    },
}


def draft_escalated_followup(
    commitment: Commitment,
    rung: EscalationRung = EscalationRung.POLITE_NUDGE,
    lang: Language = Language.HINGLISH,
    phone_number: str | None = None,
    promise_history: list[str] | None = None,
    now_ms: int = 0,
) -> FollowupDraft:
    """Generates an escalated follow-up draft preserving entity names and dates."""
    templates = RUNG_TEMPLATES.get(rung, RUNG_TEMPLATES[EscalationRung.POLITE_NUDGE])
    template = templates.get(lang, templates[Language.HINGLISH])

    history_str = "earlier promised"
    if promise_history and len(promise_history) >= 2:
        history_str = f"promised {', then '.join(promise_history)}"

    text = template.format(
        responsible=commitment.responsible_party or "there",
        title=commitment.title or "household item",
        history_str=history_str,
    )

    wa_url = None
    if phone_number:
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        if digits:
            encoded_text = urllib.parse.quote(text)
            wa_url = f"https://wa.me/{digits}?text={encoded_text}"

    return FollowupDraft(
        commitment_id=commitment.id,
        status=FollowupStatus.DRAFT_READY,
        draft_text=text,
        lang=lang,
        whatsapp_url=wa_url,
        created_at=now_ms,
        sent_at=None,
    )
