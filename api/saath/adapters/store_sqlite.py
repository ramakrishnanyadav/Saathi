"""SQLite asynchronous event store and projection adapter with WAL, STRICT tables, and triggers."""

from __future__ import annotations

import json
from typing import Any, Sequence

import aiosqlite
from saath.domain.commitments import Commitment
from saath.domain.events import ActionKind, CommitmentState, DomainEvent, EventType
from saath.domain.ids import generate_uuidv7
from saath.domain.insights import ActionRecord

SCHEMA_DDL = """
-- Core Household and Identity
CREATE TABLE IF NOT EXISTS house (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    created_at INTEGER NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS member (
    id TEXT PRIMARY KEY,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'flatmate',
    aliases_json TEXT NOT NULL DEFAULT '[]',
    created_at INTEGER NOT NULL,
    UNIQUE(house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS message (
    id TEXT PRIMARY KEY,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    author_id TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'text',
    text TEXT NOT NULL,
    dedupe_key TEXT NOT NULL,
    received_at INTEGER NOT NULL,
    UNIQUE(house_id, dedupe_key),
    FOREIGN KEY(house_id, author_id) REFERENCES member(house_id, id)
) STRICT;

-- Append-Only Event Store
CREATE TABLE IF NOT EXISTS event (
    id TEXT PRIMARY KEY,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    occurred_at INTEGER NOT NULL,
    message_id TEXT,
    causation_id TEXT,
    correlation_id TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    status TEXT NOT NULL DEFAULT 'applied',
    supersedes_id TEXT,
    schema_version INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(house_id, actor_id) REFERENCES member(house_id, id)
) STRICT;

-- Offline Idempotency Receipt
CREATE TABLE IF NOT EXISTS outbox_receipt (
    client_uuid TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    message_id TEXT,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(house_id, client_uuid)
) STRICT;

-- Projections
CREATE TABLE IF NOT EXISTS projection_commitment (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    promise_made_by TEXT NOT NULL,
    responsible_party TEXT NOT NULL,
    tracked_by TEXT NOT NULL,
    due_at INTEGER,
    state TEXT NOT NULL,
    issue_id TEXT,
    source_event_id TEXT,
    snoozed_until INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS projection_issue (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    urgency TEXT NOT NULL DEFAULT 'normal',
    status TEXT NOT NULL DEFAULT 'open',
    created_at INTEGER NOT NULL,
    PRIMARY KEY (house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS projection_expense (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    paid_by TEXT NOT NULL,
    is_confirmed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    PRIMARY KEY (house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS projection_expense_share (
    house_id TEXT NOT NULL,
    expense_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    share_paise INTEGER NOT NULL,
    PRIMARY KEY (house_id, expense_id, member_id),
    FOREIGN KEY (house_id, expense_id) REFERENCES projection_expense(house_id, id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS projection_supply (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    item_norm TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'available',
    reported_by TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS projection_action_log (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    occurred_at INTEGER NOT NULL,
    issue_id TEXT,
    commitment_id TEXT,
    PRIMARY KEY (house_id, id)
) STRICT;

CREATE TABLE IF NOT EXISTS projection_followup (
    id TEXT NOT NULL,
    house_id TEXT NOT NULL REFERENCES house(id) ON DELETE CASCADE,
    commitment_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'none',
    draft_text TEXT NOT NULL DEFAULT '',
    lang TEXT NOT NULL DEFAULT 'hinglish',
    whatsapp_url TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    sent_at INTEGER,
    PRIMARY KEY (house_id, id),
    UNIQUE (house_id, commitment_id),
    FOREIGN KEY (house_id, commitment_id) REFERENCES projection_commitment(house_id, id) ON DELETE CASCADE
) STRICT;

-- Indexes for O(log n + k) query efficiency
CREATE INDEX IF NOT EXISTS idx_commitment_attention 
    ON projection_commitment (house_id, state, due_at);

CREATE INDEX IF NOT EXISTS idx_event_history 
    ON event (house_id, occurred_at, id);

CREATE INDEX IF NOT EXISTS idx_action_log 
    ON projection_action_log (house_id, member_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_supply_norm 
    ON projection_supply (house_id, item_norm);
"""

TRIGGERS_DDL = """
CREATE TRIGGER IF NOT EXISTS event_no_update
BEFORE UPDATE ON event
BEGIN
    SELECT RAISE(ABORT, 'events are immutable');
END;

CREATE TRIGGER IF NOT EXISTS event_no_delete
BEFORE DELETE ON event
BEGIN
    SELECT RAISE(ABORT, 'events are immutable');
END;
"""


class SQLiteEventStore:
    """Async SQLite adapter for event store, triggers, and materialized projections."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path, timeout=30.0)
            await self._conn.execute("PRAGMA busy_timeout = 30000;")
            # Enable WAL mode and foreign keys
            await self._conn.execute("PRAGMA journal_mode = WAL;")
            await self._conn.execute("PRAGMA foreign_keys = ON;")
            await self._conn.executescript(SCHEMA_DDL)
            await self._conn.executescript(TRIGGERS_DDL)
            for col in ["message_id", "causation_id", "correlation_id", "supersedes_id"]:
                try:
                    await self._conn.execute(f"ALTER TABLE event ADD COLUMN {col} TEXT;")
                except Exception:
                    pass
            await self._conn.commit()
        return self._conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def record_house(
        self, house_id: str, name: str, timezone: str = "Asia/Kolkata", now_ms: int = 0
    ) -> None:
        conn = await self.connect()
        await conn.execute(
            """INSERT INTO house (id, name, timezone, created_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   name = excluded.name,
                   timezone = excluded.timezone""",
            (house_id, name, timezone, now_ms),
        )
        await conn.commit()

    async def get_house(self, house_id: str) -> dict[str, Any] | None:
        """Retrieves household by id."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM house WHERE id = ?", (house_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "timezone": row["timezone"],
                "created_at": row["created_at"],
            }

    async def record_member(
        self,
        member_id: str,
        house_id: str,
        name: str,
        phone: str | None = None,
        role: str = "flatmate",
        aliases: list[str] | None = None,
        now_ms: int = 0,
    ) -> None:
        conn = await self.connect()
        aliases_json = json.dumps(aliases or [])
        await conn.execute(
            """INSERT INTO member 
               (id, house_id, name, phone, role, aliases_json, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   name = excluded.name,
                   phone = excluded.phone,
                   role = excluded.role,
                   aliases_json = excluded.aliases_json""",
            (member_id, house_id, name, phone, role, aliases_json, now_ms),
        )
        await conn.commit()

    async def get_members(self, house_id: str) -> list[dict[str, Any]]:
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM member WHERE house_id = ? ORDER BY name ASC", (house_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "house_id": r["house_id"],
                    "name": r["name"],
                    "phone": r["phone"],
                    "role": r["role"],
                    "aliases": json.loads(r["aliases_json"]),
                }
                for r in rows
            ]

    async def record_message(
        self,
        message_id: str,
        house_id: str,
        author_id: str,
        text: str,
        dedupe_key: str,
        received_at: int,
        source: str = "text",
    ) -> bool:
        """Records an ingested message. Returns False if duplicate detected."""
        conn = await self.connect()
        try:
            await conn.execute(
                """INSERT INTO message (id, house_id, author_id, source, text, dedupe_key, received_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (message_id, house_id, author_id, source, text, dedupe_key, received_at),
            )
            await conn.commit()
            return True
        except aiosqlite.IntegrityError:
            # Duplicate dedupe_key
            return False

    async def record_outbox_receipt(
        self, client_uuid: str, house_id: str, message_id: str | None = None, now_ms: int = 0
    ) -> bool:
        """Records an outbox receipt for client UUID idempotency."""
        conn = await self.connect()
        try:
            await conn.execute(
                "INSERT INTO outbox_receipt (client_uuid, house_id, message_id, created_at) VALUES (?, ?, ?, ?)",
                (client_uuid, house_id, message_id, now_ms),
            )
            await conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def append_event_and_project(self, event: DomainEvent) -> None:
        """
        Appends an event and updates materialized projections within a single transaction.
        Guarantees O(1) amortized event insertion + projection maintenance.
        """
        conn = await self.connect()
        # 1. Insert Event into immutable log
        payload_str = json.dumps(dict(event.payload))
        await conn.execute(
            """INSERT INTO event (id, house_id, type, actor_id, payload, occurred_at, message_id, causation_id, correlation_id, confidence, status, supersedes_id, schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.id,
                event.house_id,
                event.event_type.value,
                event.actor_id,
                payload_str,
                event.occurred_at,
                event.message_id,
                getattr(event, "causation_id", None),
                getattr(event, "correlation_id", None),
                event.confidence,
                event.status,
                event.supersedes_id,
                getattr(event, "schema_version", 1),
            ),
        )

        # 2. Materialize projection incrementally
        await self._apply_projection_in_tx(conn, event)
        await conn.commit()

    async def _apply_projection_in_tx(self, conn: aiosqlite.Connection, event: DomainEvent) -> None:
        """Applies event logic to projection tables."""
        p = event.payload
        etype = event.event_type

        if etype == EventType.ISSUE_REPORTED:
            issue_id = str(p.get("issue_id", event.id))
            await conn.execute(
                """INSERT INTO projection_issue (id, house_id, title, description, category, urgency, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       title = excluded.title,
                       description = excluded.description,
                       category = excluded.category,
                       urgency = excluded.urgency""",
                (
                    issue_id,
                    event.house_id,
                    p["title"],
                    p.get("description", ""),
                    p.get("category", "general"),
                    p.get("urgency", "normal"),
                    event.occurred_at,
                ),
            )

        elif etype == EventType.COMMITMENT_CREATED:
            cid = str(p.get("commitment_id", event.id))
            due_at_val = int(p["due_at"]) if p.get("due_at") is not None else None
            await conn.execute(
                """INSERT INTO projection_commitment 
                   (id, house_id, title, promise_made_by, responsible_party, tracked_by, due_at, state, issue_id, source_event_id, snoozed_until, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'waiting', ?, ?, ?, ?, ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       title = excluded.title,
                       promise_made_by = excluded.promise_made_by,
                       responsible_party = excluded.responsible_party,
                       due_at = excluded.due_at,
                       updated_at = excluded.updated_at""",
                (
                    cid,
                    event.house_id,
                    p["title"],
                    p["promise_made_by"],
                    p["responsible_party"],
                    p["tracked_by"],
                    due_at_val,
                    p.get("issue_id"),
                    event.id,
                    p.get("snoozed_until"),
                    event.occurred_at,
                    event.occurred_at,
                ),
            )

        elif etype == EventType.COMMITMENT_UPDATED:
            cid = str(p["commitment_id"])
            new_state = str(p.get("new_state", "waiting"))
            new_due_at = p.get("new_due_at")
            snoozed_until = p.get("snoozed_until")

            if snoozed_until is not None:
                await conn.execute(
                    """UPDATE projection_commitment 
                       SET snoozed_until = ?, updated_at = ?
                       WHERE id = ? AND house_id = ?""",
                    (int(snoozed_until), event.occurred_at, cid, event.house_id),
                )
            elif new_state == "rescheduled" and new_due_at is not None:
                # Rescheduled resets to waiting with new due_at
                await conn.execute(
                    """UPDATE projection_commitment 
                       SET state = 'waiting', due_at = ?, snoozed_until = NULL, updated_at = ?
                       WHERE id = ? AND house_id = ?""",
                    (int(new_due_at), event.occurred_at, cid, event.house_id),
                )
            else:
                await conn.execute(
                    """UPDATE projection_commitment 
                       SET state = ?, updated_at = ?
                       WHERE id = ? AND house_id = ?""",
                    (new_state, event.occurred_at, cid, event.house_id),
                )

        elif etype == EventType.EXPENSE_CREATED:
            eid = str(p.get("expense_id", event.id))
            is_confirmed = 1 if p.get("is_confirmed", False) else 0
            await conn.execute(
                """INSERT INTO projection_expense (id, house_id, title, amount_paise, paid_by, is_confirmed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       title = excluded.title,
                       amount_paise = excluded.amount_paise,
                       paid_by = excluded.paid_by,
                       is_confirmed = excluded.is_confirmed""",
                (
                    eid,
                    event.house_id,
                    p["title"],
                    int(p["amount_paise"]),
                    p["paid_by"],
                    is_confirmed,
                    event.occurred_at,
                ),
            )
            # Record shares
            shares = p.get("shares", {})
            for mid, share_paise in shares.items():
                await conn.execute(
                    """INSERT INTO projection_expense_share (house_id, expense_id, member_id, share_paise)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(house_id, expense_id, member_id) DO UPDATE SET
                           share_paise = excluded.share_paise""",
                    (event.house_id, eid, mid, int(share_paise)),
                )

        elif etype == EventType.EXPENSE_CONFIRMED:
            eid = str(p["expense_id"])
            await conn.execute(
                "UPDATE projection_expense SET is_confirmed = 1 WHERE id = ? AND house_id = ?",
                (eid, event.house_id),
            )

        elif etype == EventType.SUPPLY_DEPLETED:
            sid = str(p.get("supply_id", event.id))
            await conn.execute(
                """INSERT INTO projection_supply (id, house_id, item_name, item_norm, status, reported_by, updated_at)
                   VALUES (?, ?, ?, ?, 'depleted', ?, ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       item_name = excluded.item_name,
                       item_norm = excluded.item_norm,
                       status = 'depleted',
                       reported_by = excluded.reported_by,
                       updated_at = excluded.updated_at""",
                (
                    sid,
                    event.house_id,
                    p["item_name"],
                    p["item_norm"],
                    p["reported_by"],
                    event.occurred_at,
                ),
            )

        elif etype == EventType.SUPPLY_RESTOCKED:
            item_norm = p["item_norm"]
            await conn.execute(
                """UPDATE projection_supply SET status = 'available', reported_by = ?, updated_at = ?
                   WHERE item_norm = ? AND house_id = ?""",
                (p["restocked_by"], event.occurred_at, item_norm, event.house_id),
            )

        elif etype == EventType.ACTION_TAKEN:
            aid = str(p.get("action_id", event.id))
            await conn.execute(
                """INSERT INTO projection_action_log (id, house_id, member_id, kind, label, details, occurred_at, issue_id, commitment_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       label = excluded.label,
                       details = excluded.details,
                       occurred_at = excluded.occurred_at""",
                (
                    aid,
                    event.house_id,
                    p["member_id"],
                    str(p["kind"]),
                    p["label"],
                    p.get("details", ""),
                    event.occurred_at,
                    p.get("issue_id"),
                    p.get("commitment_id"),
                ),
            )

        elif etype == EventType.FOLLOWUP_DRAFTED:
            fid = str(p.get("followup_id", event.id))
            cid = str(p["commitment_id"])
            draft_text = str(p.get("draft_text", ""))
            whatsapp_url = p.get("whatsapp_url", "")
            await conn.execute(
                """INSERT INTO projection_followup (id, house_id, commitment_id, status, draft_text, whatsapp_url, created_at, updated_at)
                   VALUES (?, ?, ?, 'draft_ready', ?, ?, ?, ?)
                   ON CONFLICT(house_id, id) DO UPDATE SET
                       draft_text = excluded.draft_text,
                       whatsapp_url = excluded.whatsapp_url,
                       updated_at = excluded.updated_at""",
                (fid, event.house_id, cid, draft_text, whatsapp_url, event.occurred_at, event.occurred_at),
            )

        elif etype == EventType.FOLLOWUP_OPENED:
            cid = str(p["commitment_id"])
            await conn.execute(
                "UPDATE projection_followup SET status = 'opened', updated_at = ? WHERE commitment_id = ? AND house_id = ?",
                (event.occurred_at, cid, event.house_id),
            )

        elif etype == EventType.FOLLOWUP_SENT:
            cid = str(p["commitment_id"])
            await conn.execute(
                "UPDATE projection_followup SET status = 'sent', updated_at = ? WHERE commitment_id = ? AND house_id = ?",
                (event.occurred_at, cid, event.house_id),
            )

    async def get_open_commitments(self, house_id: str) -> list[Commitment]:
        """Fetches all waiting commitments for the attention screen and reply matching."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """SELECT * FROM projection_commitment 
               WHERE house_id = ? AND state = 'waiting' 
               ORDER BY due_at ASC""",
            (house_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Commitment(
                    id=r["id"],
                    house_id=r["house_id"],
                    title=r["title"],
                    promise_made_by=r["promise_made_by"],
                    responsible_party=r["responsible_party"],
                    tracked_by=r["tracked_by"],
                    due_at=r["due_at"],
                    state=CommitmentState(r["state"]),
                    issue_id=r["issue_id"],
                    source_event_id=r["source_event_id"],
                    snoozed_until=r["snoozed_until"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    async def get_expenses(
        self, house_id: str, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetches expenses and their member shares for a given household."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row

        query = "SELECT id, title, amount_paise, paid_by, is_confirmed, created_at FROM projection_expense WHERE house_id = ?"
        params: list[Any] = [house_id]
        if status == "pending":
            query += " AND is_confirmed = 0"
        elif status == "confirmed":
            query += " AND is_confirmed = 1"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        expenses: list[dict[str, Any]] = []
        async with conn.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                exp_id = r["id"]
                # Fetch shares for this expense
                async with conn.execute(
                    "SELECT member_id, share_paise FROM projection_expense_share WHERE house_id = ? AND expense_id = ?",
                    (house_id, exp_id),
                ) as share_cursor:
                    share_rows = await share_cursor.fetchall()
                    shares = {s["member_id"]: s["share_paise"] for s in share_rows}

                expenses.append(
                    {
                        "id": exp_id,
                        "title": r["title"],
                        "amount_paise": r["amount_paise"],
                        "paid_by": r["paid_by"],
                        "is_confirmed": bool(r["is_confirmed"]),
                        "created_at": r["created_at"],
                        "shares": shares,
                    }
                )

        return expenses

    async def get_depleted_supplies(self, house_id: str) -> list[dict[str, Any]]:
        """Returns supplies currently marked as depleted for this household."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """SELECT id, item_name, status, reported_by, updated_at
               FROM projection_supply
               WHERE house_id = ? AND status = 'depleted'
               ORDER BY updated_at DESC""",
            (house_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "item_name": r["item_name"],
                    "status": r["status"],
                    "reported_by": r["reported_by"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ]

    async def get_commitment_by_id(
        self, commitment_id: str, house_id: str | None = None
    ) -> Commitment | None:
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        query = "SELECT * FROM projection_commitment WHERE id = ?"
        params: list[Any] = [commitment_id]
        if house_id:
            query += " AND house_id = ?"
            params.append(house_id)
        async with conn.execute(query, tuple(params)) as cursor:
            r = await cursor.fetchone()
            if not r:
                return None
            return Commitment(
                id=r["id"],
                house_id=r["house_id"],
                title=r["title"],
                promise_made_by=r["promise_made_by"],
                responsible_party=r["responsible_party"],
                tracked_by=r["tracked_by"],
                due_at=r["due_at"],
                state=CommitmentState(r["state"]),
                issue_id=r["issue_id"],
                source_event_id=r["source_event_id"],
                snoozed_until=r["snoozed_until"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def get_all_events(self, house_id: str | None = None) -> list[DomainEvent]:
        """Returns all events ordered by occurred_at ASC, id ASC."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        query = "SELECT * FROM event"
        params: list[Any] = []
        if house_id:
            query += " WHERE house_id = ?"
            params.append(house_id)
        query += " ORDER BY occurred_at ASC, id ASC"

        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                DomainEvent(
                    id=r["id"],
                    house_id=r["house_id"],
                    event_type=EventType(r["type"]),
                    actor_id=r["actor_id"],
                    occurred_at=r["occurred_at"],
                    payload=json.loads(r["payload"]),
                    message_id=r["message_id"],
                    causation_id=r["causation_id"] if "causation_id" in r.keys() else None,
                    correlation_id=r["correlation_id"] if "correlation_id" in r.keys() else None,
                    confidence=r["confidence"],
                    status=r["status"],
                    supersedes_id=r["supersedes_id"],
                    schema_version=r["schema_version"] if "schema_version" in r.keys() else 1,
                )
                for r in rows
            ]

    async def get_weekly_action_records(
        self, house_id: str, week_start_ms: int, week_end_ms: int
    ) -> list[ActionRecord]:
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """SELECT member_id, kind, label, occurred_at 
               FROM projection_action_log 
               WHERE house_id = ? AND occurred_at >= ? AND occurred_at < ?
               ORDER BY occurred_at ASC""",
            (house_id, week_start_ms, week_end_ms),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                ActionRecord(
                    member_id=r["member_id"],
                    kind=ActionKind(r["kind"]),
                    label=r["label"],
                    occurred_at=r["occurred_at"],
                )
                for r in rows
            ]

    async def rebuild_projections_from_events(self, house_id: str | None = None) -> None:
        """
        Deterministic Replay Engine.
        Clears projection tables (scoped to house_id if provided) and replays events from genesis in O(E).
        Guarantees Replay Equivalence without cross-house data loss.
        """
        conn = await self.connect()
        # 1. Clear projections (scoped to house_id if provided)
        if house_id:
            await conn.execute("DELETE FROM projection_commitment WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_issue WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_expense_share WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_expense WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_supply WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_action_log WHERE house_id = ?", (house_id,))
            await conn.execute("DELETE FROM projection_followup WHERE house_id = ?", (house_id,))
        else:
            await conn.execute("DELETE FROM projection_commitment")
            await conn.execute("DELETE FROM projection_issue")
            await conn.execute("DELETE FROM projection_expense_share")
            await conn.execute("DELETE FROM projection_expense")
            await conn.execute("DELETE FROM projection_supply")
            await conn.execute("DELETE FROM projection_action_log")
            await conn.execute("DELETE FROM projection_followup")

        # 2. Fetch events monotonically
        events = await self.get_all_events(house_id)

        # 3. Identify all superseded event IDs
        superseded_ids = {
            ev.supersedes_id for ev in events if ev.supersedes_id is not None
        }

        # 4. Stream and apply each active event (skipping superseded events and undo events)
        for ev in events:
            if ev.id in superseded_ids or ev.event_type == EventType.EVENT_SUPERSEDED:
                continue
            await self._apply_projection_in_tx(conn, ev)

        await conn.commit()

    async def append_events_and_project_batch(self, events: Sequence[DomainEvent]) -> None:
        """Appends a batch of events and updates their projections in a single atomic transaction."""
        if not events:
            return
        conn = await self.connect()
        try:
            for event in events:
                await conn.execute(
                    """INSERT INTO event 
                       (id, house_id, type, actor_id, payload, occurred_at, message_id, causation_id, correlation_id, confidence, status, supersedes_id, schema_version)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.id,
                        event.house_id,
                        event.event_type.value,
                        event.actor_id,
                        json.dumps(dict(event.payload)),
                        event.occurred_at,
                        event.message_id,
                        getattr(event, "causation_id", None),
                        getattr(event, "correlation_id", None),
                        event.confidence,
                        event.status,
                        event.supersedes_id,
                        getattr(event, "schema_version", 1),
                    ),
                )
                await self._apply_projection_in_tx(conn, event)
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

    async def undo_event(
        self, house_id: str, event_id: str, actor_id: str, now_ms: int
    ) -> DomainEvent:
        """
        Implements true Undo through a superseding event.
        Never mutates or deletes the original event (strict append-only).
        Appends EVENT_SUPERSEDED with supersedes_id, and rebuilds projections for the house.
        """
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM event WHERE id = ? AND house_id = ?",
            (event_id, house_id),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Event '{event_id}' not found in house '{house_id}'.")

        # Check if already superseded
        async with conn.execute(
            "SELECT id FROM event WHERE house_id = ? AND supersedes_id = ?",
            (house_id, event_id),
        ) as cursor:
            existing_superseder = await cursor.fetchone()
            if existing_superseder:
                raise ValueError(f"Event '{event_id}' is already superseded.")

        undo_ev_id = generate_uuidv7("ev")
        undo_ev = DomainEvent(
            id=undo_ev_id,
            house_id=house_id,
            event_type=EventType.EVENT_SUPERSEDED,
            actor_id=actor_id,
            occurred_at=now_ms,
            payload={
                "superseded_event_id": event_id,
                "original_type": row["type"],
            },
            supersedes_id=event_id,
            schema_version=1,
        )

        # Append the undo event without touching any existing row
        await conn.execute(
            """INSERT INTO event (id, house_id, type, actor_id, payload, occurred_at, message_id, causation_id, correlation_id, confidence, status, supersedes_id, schema_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                undo_ev.id,
                undo_ev.house_id,
                undo_ev.event_type.value,
                undo_ev.actor_id,
                json.dumps(dict(undo_ev.payload)),
                undo_ev.occurred_at,
                None,
                None,
                None,
                1.0,
                "applied",
                event_id,
                1,
            ),
        )
        await conn.commit()

        # Rebuild projections for this house to restore exact state before the superseded event
        await self.rebuild_projections_from_events(house_id=house_id)
        return undo_ev

    async def get_member(self, house_id: str, member_id: str) -> dict[str, Any] | None:
        """Retrieves a specific member scoped to house_id."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM member WHERE id = ? AND house_id = ?",
            (member_id, house_id),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "house_id": row["house_id"],
                "name": row["name"],
                "phone": row["phone"],
                "role": row["role"],
                "aliases": json.loads(row["aliases_json"]),
            }

    async def validate_member_belongs_to_house(self, house_id: str, member_id: str) -> bool:
        """Returns True if member belongs to house, False otherwise."""
        m = await self.get_member(house_id, member_id)
        return m is not None

    async def has_confirmed_expense(self, house_id: str, expense_id: str) -> bool:
        """Checks if an expense is already confirmed (for double-click idempotency)."""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT is_confirmed FROM projection_expense WHERE id = ? AND house_id = ?",
            (expense_id, house_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None and bool(row["is_confirmed"])
