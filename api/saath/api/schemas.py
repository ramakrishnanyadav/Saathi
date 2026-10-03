"""Pydantic API request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    author_id: str = Field(default="m-1")
    dedupe_key: str | None = None
    source: str = "text"

    def model_post_init(self, __context: Any) -> None:
        if not self.text.strip():
            raise ValueError("Message text cannot be empty or whitespace only")
        self.text = self.text.strip()



class AdvanceClockRequest(BaseModel):
    delta_hours: float = Field(default=24.0, ge=0.0)
    hours: float | None = None
    target_ms: int | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.hours is not None:
            self.delta_hours = self.hours


class ReplyRequest(BaseModel):
    text: str = Field(..., min_length=1)
    author_id: str = Field(default="m-1")


class CommitmentReplyRequest(BaseModel):
    intent: str  # "not_yet" | "rescheduled" | "done" | "cancelled"
    new_due: int | str | None = None
    actor_id: str | None = None


class ConfirmEventRequest(BaseModel):
    author_id: str = Field(default="m-1")


class ConfirmExpenseRequest(BaseModel):
    expense_id: str
    confirmation_id: str | None = None
    title: str = Field(default="Shared Expense", min_length=1)
    amount_paise: int = Field(ge=1, le=10000000000)
    paid_by: str
    participant_ids: list[str] = Field(default_factory=list)
    shares: dict[str, int]

    def model_post_init(self, __context: Any) -> None:
        if not self.participant_ids and self.shares:
            self.participant_ids = list(self.shares.keys())


class OutboxItem(BaseModel):
    client_uuid: str
    text: str
    author_id: str = "m-1"
    occurred_at: int | None = None


class OutboxSyncRequest(BaseModel):
    items: list[OutboxItem]


class StandardResponse(BaseModel):
    success: bool
    data: dict[str, Any]
