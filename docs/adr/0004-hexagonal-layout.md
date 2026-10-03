# ADR 0004: Hexagonal (Ports & Adapters) Architecture

## Status
Accepted

## Context
SAATH must run reliably both in local production environments (SQLite, Ollama, faster-whisper, WebPush) and in fast, isolated automated tests (in-memory SQLite, fake LLM, fake STT, fake Clock).
Coupling business rules (like commitment state machines or Hindi relative date math) to FastAPI or SQLAlchemy leads to slow test suites and high fragility.

## Decision
Adopt a strict Hexagonal dependency rule:
1. `domain/`: Pure Python dataclasses and functions. Zero third-party IO libraries. No SQLAlchemy, no FastAPI, no disk/network calls. 100% unit-testable in milliseconds.
2. `ports/`: Abstract Python `typing.Protocol` definitions for IO boundaries (`Clock`, `LLMProvider`, `STTProvider`, `EventStore`, `ProjectionRepo`, `Notifier`, `Outbox`).
3. `adapters/`: Concrete implementations of ports (`store_sqlite.py`, `clock_system.py`, `clock_sim.py`, `llm_ollama.py`, `llm_fake.py`, etc.).
4. `application/`: Orchestrates domain entities and ports for user commands (`ingest_message`, `confirm_event`, `undo`, etc.).
5. `api/`: Presentation layer using FastAPI routers, dependency injection (`Depends`), and RFC 7807 problem details.

## Consequences
- Testing without mocking frameworks: domain and state machine unit tests run purely with in-memory value objects and fake clocks.
- Swappable infrastructure: LLM can easily switch from Ollama Gemma to any local OpenAI-compatible endpoint or lightweight rule parser.
