"""Port protocol for LLM providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class HouseContext:
    house_id: str
    author_id: str
    timezone: str
    members: Sequence[Mapping[str, Any]]
    open_commitments: Sequence[Mapping[str, Any]]
    recent_events: Sequence[Mapping[str, Any]]
    now_ms: int


@dataclass(frozen=True, slots=True)
class RawExtractedEvent:
    event_type: str
    payload: dict[str, Any]
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    events: tuple[RawExtractedEvent, ...]
    raw_response: str
    used_fallback: bool = False
    parser: str = "rules"
    model: str = "rules_engine"
    latency_ms: float = 0.0
    fallback_reason: str | None = None



class LLMProvider(Protocol):
    """Protocol for LLM structured extraction provider."""

    async def extract_events(self, text: str, context: HouseContext) -> ExtractionResult:
        """Extracts structured candidate events from unstructured text."""
        ...
