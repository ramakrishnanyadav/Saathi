"""Unit tests for money domain calculations and formatting."""

import pytest
from saath.domain.money import (
    InvalidAmountError,
    InvalidParticipantError,
    format_rupees,
    split_equally,
    validate_paise_amount,
)


def test_electricity_bill_three_way_split():
    """Test ₹1,450 split 3 ways: 145000 paise -> 48334, 48333, 48333."""
    total_paise = 145_000
    participants = ["member_a", "member_b", "member_c"]
    result = split_equally(total_paise, participants)

    assert result.total_paise == 145_000
    assert sum(result.shares.values()) == 145_000
    assert result.shares["member_a"] == 48334
    assert result.shares["member_b"] == 48333
    assert result.shares["member_c"] == 48333


def test_money_validation_bounds():
    """Amounts outside [1, 10_000_000] paise are rejected."""
    validate_paise_amount(1)
    validate_paise_amount(10_000_000)

    with pytest.raises(InvalidAmountError):
        validate_paise_amount(0)

    with pytest.raises(InvalidAmountError):
        validate_paise_amount(-100)

    with pytest.raises(InvalidAmountError):
        validate_paise_amount(10_000_001)

    # Floats strictly rejected
    with pytest.raises(InvalidAmountError):
        validate_paise_amount(1450.50)  # type: ignore


def test_invalid_participants():
    """Empty or empty-unique participant list is rejected."""
    with pytest.raises(InvalidParticipantError):
        split_equally(1000, [])


def test_rupee_formatting_indian_digit_grouping():
    """Test format_rupees without floating point errors."""
    assert format_rupees(145000) == "₹1,450.00"
    assert format_rupees(48333) == "₹483.33"
    assert format_rupees(5) == "₹0.05"
    assert format_rupees(10000000) == "₹1,00,000.00"
    assert format_rupees(50000000) == "₹5,00,000.00"
    assert format_rupees(-500) == "-₹5.00"
    assert format_rupees(100, include_symbol=False) == "1.00"
