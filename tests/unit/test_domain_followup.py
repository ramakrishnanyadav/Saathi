"""Unit tests for follow-up message drafts and WhatsApp deep-links."""

from saath.domain.commitments import Commitment, CommitmentState
from saath.domain.followup import FollowupStatus, Language, draft_followup


def test_followup_draft_hinglish_and_whatsapp_link():
    c = Commitment(
        id="c-1",
        house_id="h-1",
        title="Tap repair",
        promise_made_by="Landlord",
        responsible_party="Landlord",
        tracked_by="m-1",
        due_at=1000,
        state=CommitmentState.WAITING,
    )

    draft = draft_followup(
        commitment=c,
        lang=Language.HINGLISH,
        phone_number="+91 98765-43210",
        now_ms=2000,
    )

    assert draft.status == FollowupStatus.DRAFT_READY
    assert "Landlord" in draft.draft_text
    assert "Tap repair" in draft.draft_text
    assert draft.whatsapp_url is not None
    assert "https://wa.me/919876543210?text=" in draft.whatsapp_url


def test_followup_draft_hindi_and_english():
    c = Commitment(
        id="c-2",
        house_id="h-1",
        title="AC service",
        promise_made_by="Technician",
        responsible_party="Technician",
        tracked_by="m-2",
        due_at=1000,
        state=CommitmentState.WAITING,
    )

    draft_hi = draft_followup(c, lang=Language.HI, now_ms=2000)
    assert "नमस्ते Technician" in draft_hi.draft_text
    assert "AC service" in draft_hi.draft_text

    draft_en = draft_followup(c, lang=Language.EN, now_ms=2000)
    assert "Hi Technician" in draft_en.draft_text
    assert "AC service" in draft_en.draft_text
