"""Follow-up draft generation and WhatsApp deep-link generation."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from enum import Enum

from saath.domain.commitments import Commitment


class FollowupStatus(str, Enum):
    NONE = "none"
    DRAFT_READY = "draft_ready"
    SENT = "sent"


class Language(str, Enum):
    EN = "en"
    HI = "hi"
    HINGLISH = "hinglish"


@dataclass(frozen=True, slots=True)
class FollowupDraft:
    commitment_id: str
    status: FollowupStatus
    draft_text: str
    lang: Language
    whatsapp_url: str | None = None
    created_at: int = 0
    sent_at: int | None = None


# Polite, contextual message templates by language
TEMPLATES = {
    Language.HINGLISH: (
        "Hi {responsible}, {title} ke baare me puchna tha. "
        "Aapne bola tha ye ho jayega, bas update chahiye tha kab tak expect karein? Thanks!"
    ),
    Language.HI: (
        "नमस्ते {responsible}, {title} के बारे में पूछना था। "
        "आपने कहा था यह हो जाएगा, क्या आप बता सकते हैं कब तक हो पाएगा? धन्यवाद।"
    ),
    Language.EN: (
        "Hi {responsible}, following up regarding {title}. "
        "Could you please share a quick update on when we can expect this to be resolved? Thanks!"
    ),
}


def draft_followup(
    commitment: Commitment,
    lang: Language = Language.HINGLISH,
    phone_number: str | None = None,
    now_ms: int = 0,
) -> FollowupDraft:
    """
    Creates a polite, contextual follow-up draft for an overdue commitment.
    Generates a validated wa.me deep-link if phone_number is supplied.
    """
    template = TEMPLATES.get(lang, TEMPLATES[Language.HINGLISH])
    text = template.format(
        responsible=commitment.responsible_party or "there",
        title=commitment.title or "household item",
    )

    wa_url = None
    if phone_number:
        # Sanitize phone digits
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
