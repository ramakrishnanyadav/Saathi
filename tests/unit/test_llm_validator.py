"""Unit tests for validator safety checks on LLM candidate outputs."""

import pytest
from saath.application.validator import ExtractionValidationError, validate_extracted_event
from saath.domain.events import EventType


def test_validator_rejects_unknown_roommate():
    valid_members = ["m-1", "m-2", "m-3"]
    payload = {
        "title": "Pizza Party",
        "amount_paise": 150000,
        "paid_by": "m-999_unknown_roommate",
        "participant_ids": ["m-1", "m-2"],
    }
    with pytest.raises(ExtractionValidationError, match="not a registered house member"):
        validate_extracted_event("expense_created", payload, valid_members)


def test_validator_rejects_unknown_participant():
    valid_members = ["m-1", "m-2"]
    payload = {
        "title": "Groceries",
        "amount_paise": 50000,
        "paid_by": "m-1",
        "participant_ids": ["m-1", "ghost_user"],
    }
    with pytest.raises(ExtractionValidationError, match="Participant 'ghost_user' is not a registered house member"):
        validate_extracted_event("expense_created", payload, valid_members)


def test_validator_rejects_extra_fields():
    valid_members = ["m-1"]
    payload = {
        "title": "Electrician",
        "responsible_party": "Landlord",
        "hallucinated_field": "injected_data",
    }
    with pytest.raises(ExtractionValidationError, match="Schema validation failed"):
        validate_extracted_event("commitment_created", payload, valid_members)


def test_validator_rejects_amount_out_of_range_negative():
    valid_members = ["m-1"]
    payload = {
        "title": "Refund",
        "amount_paise": -500,
        "paid_by": "m-1",
    }
    with pytest.raises(ExtractionValidationError, match="Schema validation failed"):
        validate_extracted_event("expense_created", payload, valid_members)


def test_validator_rejects_amount_out_of_range_excessive():
    valid_members = ["m-1"]
    payload = {
        "title": "Mansion Buy",
        "amount_paise": 99999999999999,
        "paid_by": "m-1",
    }
    with pytest.raises(ExtractionValidationError, match="Schema validation failed"):
        validate_extracted_event("expense_created", payload, valid_members)


def test_validator_rejects_invalid_event_type():
    valid_members = ["m-1"]
    payload = {"title": "Test"}
    with pytest.raises(ExtractionValidationError, match="Invalid event_type"):
        validate_extracted_event("non_existent_event", payload, valid_members)
