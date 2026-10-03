"""Unit tests for the SAATH Escalation Ladder Engine."""

import pytest
from saath.domain.commitments import Commitment, CommitmentState
from saath.domain.escalation import (
    EscalationRung,
    calculate_escalation_rung,
    draft_escalated_followup,
)
from saath.domain.followup import Language


def test_calculate_rung_polite_nudge():
    rung = calculate_escalation_rung(reschedule_count=0, hours_overdue=5.0, prior_followups_sent=0)
    assert rung == EscalationRung.POLITE_NUDGE


def test_calculate_rung_firm_reminder_via_reschedules():
    rung = calculate_escalation_rung(reschedule_count=2, hours_overdue=2.0, prior_followups_sent=0)
    assert rung == EscalationRung.FIRM_REMINDER


def test_calculate_rung_firm_reminder_via_overdue_hours():
    rung = calculate_escalation_rung(reschedule_count=0, hours_overdue=25.0, prior_followups_sent=0)
    assert rung == EscalationRung.FIRM_REMINDER


def test_calculate_rung_firm_reminder_via_prior_followup():
    rung = calculate_escalation_rung(reschedule_count=0, hours_overdue=5.0, prior_followups_sent=1)
    assert rung == EscalationRung.FIRM_REMINDER


def test_calculate_rung_practical_alternative_via_reschedules():
    rung = calculate_escalation_rung(reschedule_count=3, hours_overdue=10.0, prior_followups_sent=0)
    assert rung == EscalationRung.PRACTICAL_ALTERNATIVE


def test_calculate_rung_practical_alternative_via_overdue_hours():
    rung = calculate_escalation_rung(reschedule_count=0, hours_overdue=75.0, prior_followups_sent=0)
    assert rung == EscalationRung.PRACTICAL_ALTERNATIVE


def test_calculate_rung_practical_alternative_via_prior_followups():
    rung = calculate_escalation_rung(reschedule_count=0, hours_overdue=10.0, prior_followups_sent=2)
    assert rung == EscalationRung.PRACTICAL_ALTERNATIVE


def test_draft_polite_hinglish():
    c = Commitment("c1", "h1", "Tap repair", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.POLITE_NUDGE, Language.HINGLISH)
    assert "Landlord" in draft.draft_text
    assert "Tap repair" in draft.draft_text
    assert "baare me puchna tha" in draft.draft_text


def test_draft_polite_hindi():
    c = Commitment("c1", "h1", "Tap repair", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.POLITE_NUDGE, Language.HI)
    assert "Landlord" in draft.draft_text
    assert "Tap repair" in draft.draft_text
    assert "नमस्ते" in draft.draft_text


def test_draft_polite_english():
    c = Commitment("c1", "h1", "Tap repair", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.POLITE_NUDGE, Language.EN)
    assert "Landlord" in draft.draft_text
    assert "following up regarding Tap repair" in draft.draft_text


def test_draft_firm_reminder_with_history():
    c = Commitment("c1", "h1", "Geyser fix", "Rahul", "Rahul", "m1")
    history = ["Tuesday", "Thursday"]
    draft = draft_escalated_followup(
        c, EscalationRung.FIRM_REMINDER, Language.HINGLISH, promise_history=history
    )
    assert "promised Tuesday, then Thursday" in draft.draft_text
    assert "Rahul" in draft.draft_text
    assert "Geyser fix" in draft.draft_text


def test_draft_firm_reminder_english():
    c = Commitment("c1", "h1", "Geyser fix", "Rahul", "Rahul", "m1")
    draft = draft_escalated_followup(c, EscalationRung.FIRM_REMINDER, Language.EN)
    assert "this is still pending" in draft.draft_text


def test_draft_firm_reminder_hindi():
    c = Commitment("c1", "h1", "Geyser fix", "Rahul", "Rahul", "m1")
    draft = draft_escalated_followup(c, EscalationRung.FIRM_REMINDER, Language.HI)
    assert "अभी तक अटका हुआ है" in draft.draft_text


def test_draft_practical_alternative_hinglish():
    c = Commitment("c1", "h1", "Plumber visit", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.PRACTICAL_ALTERNATIVE, Language.HINGLISH)
    assert "alternative arrange kar lete hain" in draft.draft_text
    assert "Landlord" in draft.draft_text


def test_draft_practical_alternative_hindi():
    c = Commitment("c1", "h1", "Plumber visit", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.PRACTICAL_ALTERNATIVE, Language.HI)
    assert "दूसरा विकल्प देखते हैं" in draft.draft_text


def test_draft_practical_alternative_english():
    c = Commitment("c1", "h1", "Plumber visit", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.PRACTICAL_ALTERNATIVE, Language.EN)
    assert "arrange an alternative" in draft.draft_text


def test_whatsapp_url_generation_valid_phone():
    c = Commitment("c1", "h1", "Plumber visit", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(
        c, EscalationRung.POLITE_NUDGE, Language.EN, phone_number="+91 98765 43210"
    )
    assert draft.whatsapp_url is not None
    assert "wa.me/919876543210" in draft.whatsapp_url
    assert "Plumber+visit" in draft.whatsapp_url or "Plumber%20visit" in draft.whatsapp_url


def test_whatsapp_url_generation_no_phone():
    c = Commitment("c1", "h1", "Plumber visit", "Landlord", "Landlord", "m1")
    draft = draft_escalated_followup(c, EscalationRung.POLITE_NUDGE, Language.EN, phone_number=None)
    assert draft.whatsapp_url is None


def test_entity_preservation_validator():
    c = Commitment("comm-88", "h1", "WiFi Router Replacement", "Airtel Tech", "Airtel Tech", "m1")
    draft = draft_escalated_followup(c, EscalationRung.FIRM_REMINDER, Language.EN)
    assert "Airtel Tech" in draft.draft_text
    assert "WiFi Router Replacement" in draft.draft_text


def test_date_preservation_in_draft():
    c = Commitment("comm-89", "h1", "Broadband repair", "Airtel", "Airtel", "m1")
    history = ["Yesterday 4pm", "Today 10am"]
    draft = draft_escalated_followup(
        c, EscalationRung.FIRM_REMINDER, Language.EN, promise_history=history
    )
    assert "promised Yesterday 4pm, then Today 10am" in draft.draft_text
