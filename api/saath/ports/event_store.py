"""Port protocols for Event Store and Projection Repository."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from saath.domain.commitments import Commitment
from saath.domain.events import DomainEvent


class EventStore(Protocol):
    """Protocol for append-only event store."""

    async def append(self, event: DomainEvent) -> None:
        """Appends an immutable domain event within an active transaction."""
        ...

    async def get_events(
        self,
        house_id: str,
        after_occurred_at: int | None = None,
        after_id: str | None = None,
        limit: int = 50,
    ) -> Sequence[DomainEvent]:
        """Reads events ordered by (occurred_at, id) for keyset pagination."""
        ...

    async def get_all_events_for_replay(self, house_id: str | None = None) -> Sequence[DomainEvent]:
        """Streams or returns all events ordered monotonically for projection rebuilding."""
        ...


class ProjectionRepo(Protocol):
    """Protocol for reading and mutating projections."""

    async def apply_event(self, event: DomainEvent) -> None:
        """Incrementally applies an event to materialize projections."""
        ...

    async def clear_projections(self, house_id: str | None = None) -> None:
        """Clears all materialized projections before a full replay."""
        ...

    async def get_open_commitments(self, house_id: str) -> Sequence[Commitment]:
        """Returns all waiting commitments for attention list and reply resolution."""
        ...

    async def get_commitment_by_id(self, commitment_id: str) -> Commitment | None:
        """Fetches a single commitment by ID."""
        ...

    async def get_attention_items(self, house_id: str, now_ms: int) -> dict[str, Sequence[Any]]:
        """Returns items grouped into overdue, waiting, and actions."""
        ...
