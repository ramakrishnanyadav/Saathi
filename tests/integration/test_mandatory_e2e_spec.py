"""Mandatory End-to-End Tests (§33, §34, §35) for SAATH Core Loop."""

import pytest
from httpx import ASGITransport, AsyncClient
from saath.api.deps import get_store, reset_app_state
from saath.api.main import app
from saath.domain.events import EventType


@pytest.mark.asyncio
async def test_mandatory_spec_section_33_e2e_lifecycle():
    """§33 Mandatory E2E:
    1. Seed household members
    2. Enter: 'Landlord bola kal plumber bhejega.'
    3. Verify issue & commitment created, landlord responsible, tracked_by auth user, due tomorrow
    4. Advance demo clock -> Overdue -> Next action = follow-up
    5. Draft follow-up -> Open WhatsApp (OPENED) -> Explicitly mark Sent
    6. Enter: 'kal aayega' -> Safe reschedule
    7. Enter: 'plumber aa gaya' -> DONE
    8. Verify complete auditable history
    """
    reset_app_state(":memory:")
    store = await get_store()
    await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", 1_000_000)
    await store.record_member("m-1", "h-demo", "You", "+919876543210", "flatmate", ["me"], 1_000_000)
    await store.record_member("m-2", "h-demo", "Rahul", "+919876543211", "flatmate", [], 1_000_000)
    await store.record_member("m-3", "h-demo", "Amit", "+919876543212", "flatmate", [], 1_000_000)
    await store.record_member("m-landlord", "h-demo", "Landlord", "+919999988888", "landlord", ["owner"], 1_000_000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-House-Id": "h-demo", "X-Member-Id": "m-1"}

        # 2. Enter: 'Landlord bola kal plumber bhejega.'
        res_msg = await client.post(
            "/api/v1/messages",
            headers=headers,
            json={"text": "Landlord bola kal plumber bhejega.", "dedupe_key": "msg-e2e-1"},
        )
        assert res_msg.status_code == 200
        data_msg = res_msg.json()
        assert data_msg["success"] is True

        ev_types = [e["event_type"] for e in data_msg["applied_events"]]
        assert EventType.ISSUE_REPORTED.value in ev_types
        assert EventType.COMMITMENT_CREATED.value in ev_types

        comm_ev = next(e for e in data_msg["applied_events"] if e["event_type"] == EventType.COMMITMENT_CREATED.value)
        assert comm_ev["payload"]["responsible_party"] == "Landlord"
        assert comm_ev["payload"]["tracked_by"] == "m-1"
        assert comm_ev["payload"]["due_at"] is not None
        cid = comm_ev["payload"]["commitment_id"]

        # 3. Check attention (currently waiting, not yet overdue)
        res_att = await client.get("/api/v1/attention", headers=headers)
        assert res_att.status_code == 200
        data_att = res_att.json()
        assert len(data_att["overdue"]) == 0
        assert any(c["id"] == cid for c in data_att["waiting"])

        # 4. Advance demo clock by 48 hours to trigger overdue
        res_adv = await client.post("/api/v1/demo/clock/advance", headers=headers, json={"hours": 48})
        assert res_adv.status_code == 200

        # 5. Verify overdue & next action = follow-up
        res_att_after = await client.get("/api/v1/attention", headers=headers)
        data_att_after = res_att_after.json()
        assert len(data_att_after["overdue"]) >= 1
        overdue_item = next(c for c in data_att_after["overdue"] if c["id"] == cid)
        assert overdue_item["is_overdue"] is True
        assert overdue_item["next_action"]["kind"] == "followup"

        # 6. Generate draft & open WhatsApp
        res_draft = await client.post(f"/api/v1/commitments/{cid}/followup", headers=headers)
        assert res_draft.status_code == 200
        draft_data = res_draft.json()["draft"]
        assert "https://wa.me/" in draft_data["whatsapp_url"]

        # Record opened (opening WhatsApp is distinct from marked sent!)
        res_opened = await client.post(f"/api/v1/followups/{cid}/opened", headers=headers)
        assert res_opened.status_code == 200
        assert res_opened.json()["success"] is True

        # Explicitly mark sent
        res_sent = await client.post(f"/api/v1/followups/{cid}/sent", headers=headers)
        assert res_sent.status_code == 200
        assert res_sent.json()["success"] is True

        # 7. Enter: 'kal aayega' -> Safe reschedule
        res_resched = await client.post(
            "/api/v1/messages",
            headers=headers,
            json={"text": "kal aayega", "dedupe_key": "msg-e2e-2"},
        )
        assert res_resched.status_code == 200
        data_resched = res_resched.json()
        assert data_resched["reply_resolution"]["intent"] == "rescheduled"

        # Verify commitment is no longer overdue
        res_att_resched = await client.get("/api/v1/attention", headers=headers)
        assert not any(c["id"] == cid for c in res_att_resched.json()["overdue"])

        # 8. Enter: 'plumber aa gaya' -> DONE
        res_done = await client.post(
            "/api/v1/messages",
            headers=headers,
            json={"text": "plumber aa gaya", "dedupe_key": "msg-e2e-3"},
        )
        assert res_done.status_code == 200
        data_done = res_done.json()
        assert data_done["reply_resolution"]["intent"] == "done"

        # Verify commitment no longer in open attention
        res_att_final = await client.get("/api/v1/attention", headers=headers)
        assert not any(c["id"] == cid for c in res_att_final.json()["waiting"])
        assert not any(c["id"] == cid for c in res_att_final.json()["overdue"])

        # 9. Verify complete auditable history
        res_hist = await client.get("/api/v1/history", headers=headers)
        assert res_hist.status_code == 200
        hist_events = res_hist.json()["events"]
        assert len(hist_events) >= 4  # Issue, Created, Rescheduled, Done


@pytest.mark.asyncio
async def test_mandatory_spec_section_34_money_e2e():
    """§34 Mandatory Money E2E:
    Input: 'Rahul paid 1450 electricity bill for all three.'
    Verify:
      - Informational ₹1450 (145000 paise)
      - Payer Rahul (m-3)
      - Participants m-1, m-2, m-3
      - Largest remainder split: 48334, 48333, 48333
      - Before confirmation: NO expense created
      - After confirmation: exactly one expense
      - Double-click confirmation: idempotent, still exactly one expense
    """
    reset_app_state(":memory:")
    store = await get_store()
    await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", 1_000_000)
    await store.record_member("m-1", "h-demo", "You", "+919876543210", "flatmate", ["me"], 1_000_000)
    await store.record_member("m-2", "h-demo", "Amit", "+919876543211", "flatmate", [], 1_000_000)
    await store.record_member("m-3", "h-demo", "Rahul", "+919876543212", "flatmate", [], 1_000_000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-House-Id": "h-demo", "X-Member-Id": "m-3"}

        # 1. Ingest money message
        res_msg = await client.post(
            "/api/v1/messages",
            headers=headers,
            json={"text": "Rahul paid 1450 electricity bill for all three.", "dedupe_key": "msg-money-1"},
        )
        assert res_msg.status_code == 200
        data_msg = res_msg.json()

        # Must NOT auto-apply any financial mutation
        assert len(data_msg["applied_events"]) == 0
        assert len(data_msg["pending_confirmations"]) == 1

        conf_card = data_msg["pending_confirmations"][0]
        assert conf_card["amount_paise"] == 145000
        assert conf_card["paid_by"] == "m-3"
        assert set(conf_card["payload"]["participant_ids"]) == {"m-1", "m-2", "m-3"}

        # Largest remainder rule check: 145000 / 3 = 48333.33 -> 48334, 48333, 48333
        shares = conf_card["shares"]
        assert sum(shares.values()) == 145000
        assert sorted(shares.values()) == [48333, 48333, 48334]

        # Verify no expense in history before confirmation
        res_hist_before = await client.get("/api/v1/history", headers=headers)
        hist_before = [e for e in res_hist_before.json()["events"] if e["type"] == EventType.EXPENSE_CREATED.value]
        assert len(hist_before) == 0

        # 2. Confirm expense
        res_conf1 = await client.post(
            "/api/v1/expenses/confirm",
            headers=headers,
            json=conf_card["payload"],
        )
        assert res_conf1.status_code == 200
        assert res_conf1.json()["success"] is True

        # Verify exactly one expense in history
        res_hist_after = await client.get("/api/v1/history", headers=headers)
        hist_after = [e for e in res_hist_after.json()["events"] if e["type"] == EventType.EXPENSE_CREATED.value]
        assert len(hist_after) == 1

        # 3. Double-click confirmation (idempotency test)
        res_conf2 = await client.post(
            "/api/v1/expenses/confirm",
            headers=headers,
            json=conf_card["payload"],
        )
        assert res_conf2.status_code == 200
        assert res_conf2.json().get("already_confirmed") is True or res_conf2.json().get("success") is True

        # Still exactly one expense event in history!
        res_hist_after2 = await client.get("/api/v1/history", headers=headers)
        hist_after2 = [e for e in res_hist_after2.json()["events"] if e["type"] == EventType.EXPENSE_CREATED.value]
        assert len(hist_after2) == 1


@pytest.mark.asyncio
async def test_mandatory_spec_section_35_ambiguity_e2e():
    """§35 Mandatory Ambiguity E2E:
    Create:
      1. Plumber repair
      2. Electrician repair
      3. Internet repair
    Input: 'Ho gaya.'
    Expected: ASK WHICH. Never automatically resolve or guess.
    """
    reset_app_state(":memory:")
    store = await get_store()
    await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", 1_000_000)
    await store.record_member("m-1", "h-demo", "You", "+919876543210", "flatmate", ["me"], 1_000_000)
    await store.record_member("m-2", "h-demo", "Rahul", "+919876543211", "flatmate", [], 1_000_000)
    await store.record_member("m-3", "h-demo", "Amit", "+919876543212", "flatmate", [], 1_000_000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-House-Id": "h-demo", "X-Member-Id": "m-1"}

        # Create 3 open commitments
        titles = ["Plumber repair", "Electrician repair", "Internet repair"]
        for title in titles:
            res = await client.post(
                "/api/v1/messages",
                headers=headers,
                json={"text": f"Landlord promised {title} kal", "dedupe_key": f"seed-{title}"},
            )
            assert res.status_code == 200

        # Verify all 3 are open
        res_att = await client.get("/api/v1/attention", headers=headers)
        assert len(res_att.json()["waiting"]) >= 3

        # Ambiguous reply
        res_ambig = await client.post(
            "/api/v1/messages",
            headers=headers,
            json={"text": "Ho gaya.", "dedupe_key": "ambig-reply-1"},
        )
        assert res_ambig.status_code == 200
        data_ambig = res_ambig.json()

        # Must ask which candidate!
        assert data_ambig["reply_resolution"] is not None
        assert data_ambig["reply_resolution"]["intent"] == "ask_which"
        candidates = data_ambig["reply_resolution"]["ask_which"]
        assert len(candidates) >= 3

        # All 3 commitments must STILL be open (NONE were auto-marked done!)
        res_att_check = await client.get("/api/v1/attention", headers=headers)
        assert len(res_att_check.json()["waiting"]) >= 3
