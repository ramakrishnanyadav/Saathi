"""Integration tests for message and outbox sync idempotency."""

import pytest
from saath.adapters.store_sqlite import SQLiteEventStore


@pytest.mark.asyncio
async def test_message_deduplication():
    """Messages with identical dedupe_key are rejected on duplicate ingest."""
    store = SQLiteEventStore(":memory:")
    await store.record_house("h-1", "Test Flat", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-1", "Alice", "+919876543210", "flatmate", [], 1000)

    # First ingest
    ok1 = await store.record_message(
        message_id="msg-1",
        house_id="h-1",
        author_id="m-1",
        text="Gas Rahul mangayega kal tak",
        dedupe_key="client-uuid-12345",
        received_at=1000,
    )
    assert ok1 is True

    # Duplicate delivery with same dedupe_key
    ok2 = await store.record_message(
        message_id="msg-2",
        house_id="h-1",
        author_id="m-1",
        text="Gas Rahul mangayega kal tak",
        dedupe_key="client-uuid-12345",
        received_at=1001,
    )
    assert ok2 is False

    await store.close()


@pytest.mark.asyncio
async def test_outbox_batch_deduplication():
    """Outbox batch of 50 items with 10 duplicate client_uuids yields exactly 40 unique recorded receipts."""
    store = SQLiteEventStore(":memory:")
    await store.record_house("h-1", "Test Flat", "Asia/Kolkata", 1000)

    # 40 unique UUIDs + 10 repeated UUIDs = 50 total attempts
    uuids = [f"uuid-{i}" for i in range(40)]
    batch = uuids + uuids[:10]
    assert len(batch) == 50

    recorded_count = 0
    for idx, client_uuid in enumerate(batch):
        recorded = await store.record_outbox_receipt(
            client_uuid=client_uuid,
            house_id="h-1",
            message_id=f"msg-{idx}",
            now_ms=1000 + idx,
        )
        if recorded:
            recorded_count += 1

    assert recorded_count == 40
    await store.close()
