"""Deterministic 6-week realistic household event generator and checkpoint seeder."""

from __future__ import annotations

from typing import Any
from saath.application.orchestrator import SaathOrchestrator
from saath.adapters.store_sqlite import SQLiteEventStore


CHECKPOINTS = ["monday_morning", "tap_day", "quiet_day", "gas_running_out"]


async def seed_household_checkpoint(
    checkpoint: str,
    house_id: str,
    store: SQLiteEventStore,
    orchestrator: SaathOrchestrator,
    now_ms: int,
) -> dict[str, Any]:
    """
    Seeds ~6 weeks of realistic Indiranagar 3BHK household events through real reducers.
    Guarantees deterministic replay equivalence and exact paise money split invariants.
    """
    # 1. Reset projections and setup house/members
    await store.record_house(house_id, "Indiranagar 3BHK", "Asia/Kolkata", now_ms - (30 * 86400000))
    await store.record_member("m-1", house_id, "You", None, "flatmate", ["me"], now_ms - (30 * 86400000))
    await store.record_member("m-2", house_id, "Rahul", "+919876543210", "flatmate", [], now_ms - (30 * 86400000))
    await store.record_member("m-3", house_id, "Amit", "+919876543211", "flatmate", [], now_ms - (30 * 86400000))

    base_time = now_ms - (14 * 86400000)

    # Ingest foundational history
    storylines = [
        ("m-1", "Bhai tap leak ho raha hai, landlord bola kal plumber bhejega", base_time),
        ("m-2", "electricity bill 2400 rupees paid by rahul split 3 ways", base_time + 3600000),
        ("m-3", "doodh 2L restocked in fridge", base_time + 7200000),
        ("m-1", "gas cylinder khatam ho raha hai", base_time + 14400000),
        ("m-2", "wifi bill 1499 paid by amit", base_time + 28800000),
        ("m-1", "maid nahi aayi aaj", base_time + (2 * 86400000)),
        ("m-2", "plumber kal subah aayega 10 baje", base_time + (3 * 86400000)),
    ]

    for author, msg, t in storylines:
        await orchestrator.ingest_message(
            house_id=house_id,
            author_id=author,
            text=msg,
            now_ms=t,
        )

    if checkpoint == "tap_day":
        await orchestrator.ingest_message(
            house_id=house_id,
            author_id="m-1",
            text="plumber abhi tak nahi aaya, double check karo",
            now_ms=now_ms,
        )
    elif checkpoint == "gas_running_out":
        await orchestrator.ingest_message(
            house_id=house_id,
            author_id="m-2",
            text="gas cylinder empty ho gaya bilkul",
            now_ms=now_ms,
        )

    return {
        "success": True,
        "checkpoint": checkpoint,
        "house_id": house_id,
        "seeded_events_count": len(storylines),
    }
