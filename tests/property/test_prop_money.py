"""Property-based tests for money math using Hypothesis."""

from hypothesis import given
from hypothesis import strategies as st
from saath.domain.money import MAX_PAISE, MIN_PAISE, split_equally


@given(
    total_paise=st.integers(min_value=MIN_PAISE, max_value=MAX_PAISE),
    participant_count=st.integers(min_value=1, max_value=20),
)
def test_hare_niemeyer_sum_invariant(total_paise: int, participant_count: int):
    """
    Property: For any valid paise amount and any number of participants (1..20),
    the sum of shares strictly equals the total paise.
    The maximum difference between any two shares is at most 1 paisa.
    All shares are integers (no floats).
    """
    participants = [f"user_{i}" for i in range(participant_count)]
    result = split_equally(total_paise, participants)

    # 1. Conservation of money invariant
    total_shares = sum(result.shares.values())
    assert total_shares == total_paise

    # 2. Integer types strictly preserved
    for share in result.shares.values():
        assert isinstance(share, int)
        assert not isinstance(share, float)

    # 3. Hare-Niemeyer difference bound (at most 1 paisa delta between any two shares)
    shares_list = list(result.shares.values())
    assert max(shares_list) - min(shares_list) <= 1
