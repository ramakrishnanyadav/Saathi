"""Ollama and OpenAI-compatible LLM adapter with schema constraints and deterministic fallback."""

from __future__ import annotations

import json

import httpx
from saath.domain.parser_rules import extract_rules_events
from saath.ports.llm import ExtractionResult, HouseContext, RawExtractedEvent

SYSTEM_PROMPT = """You are SAATH, a household memory and follow-through parser.
Turn user messages into structured events. You are a parser, NOT an actor.
Output valid JSON only matching the schema.

Few-shot examples:
1. "bijli ka bill bhar diya 1450, teen mein split"
   {"events": [{"event_type": "expense_created", "payload": {"title": "Electricity bill", "amount_paise": 145000, "is_confirmed": false}}]}

2. "landlord bola kal tap theek karne aadmi bhejega"
   {"events": [
     {"event_type": "issue_reported", "payload": {"title": "Tap leak", "category": "maintenance"}},
     {"event_type": "commitment_created", "payload": {"title": "Tap repair", "responsible_party": "Landlord", "symbolic_due": {"rel": "tomorrow"}}}
   ]}

3. "bai aaj nahi aayi"
   {"events": [{"event_type": "action_taken", "payload": {"kind": "coordination", "label": "Noticed maid absence"}}]}

4. "doodh khatam hai"
   {"events": [{"event_type": "supply_depleted", "payload": {"item_name": "milk", "item_norm": "milk"}}]}

5. "maine plumber ko 3 baar call kiya"
   {"events": [{"event_type": "action_taken", "payload": {"kind": "coordination", "label": "Followed up with plumber", "times": 3}}]}
"""


import time


class OllamaLLMProvider:
    """Ollama LLM provider using Gemma or any local open-weights model."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma2:2b",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def warmup(self) -> bool:
        """Warms the model into RAM/VRAM on startup with a minimal dummy prompt."""
        payload = {
            "model": self.model,
            "prompt": "ping",
            "stream": False,
            "keep_alive": "30m",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                return resp.status_code == 200
        except Exception:
            return False

    async def extract_events(self, text: str, context: HouseContext) -> ExtractionResult:
        """
        Attempts schema-constrained extraction via Ollama.
        If unreachable, timed out, or returning malformed data, falls back to deterministic rule parser.
        """
        author_id = context.author_id
        payload = {
            "model": self.model,
            "system": SYSTEM_PROMPT,
            "prompt": f"House Context: members={context.members}\nMessage: {text}",
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
        }

        fallback_reason: str | None = None
        t0 = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                dt_ms = (time.perf_counter() - t0) * 1000
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("response", "{}")
                    parsed = json.loads(response_text)
                    raw_events = parsed.get("events", [])
                    extracted: list[RawExtractedEvent] = []
                    for ev in raw_events:
                        extracted.append(
                            RawExtractedEvent(
                                event_type=ev.get("event_type", "note_recorded"),
                                payload=ev.get("payload", {}),
                                confidence=float(ev.get("confidence", 0.9)),
                            )
                        )
                    if extracted:
                        return ExtractionResult(
                            events=tuple(extracted),
                            raw_response=response_text,
                            used_fallback=False,
                            parser="llm",
                            model=self.model,
                            latency_ms=dt_ms,
                            fallback_reason=None,
                        )
                    else:
                        fallback_reason = "LLM returned empty event list"
                else:
                    fallback_reason = f"Ollama HTTP {resp.status_code}"
        except httpx.TimeoutException:
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = f"Timeout after {self.timeout_seconds}s"
        except (httpx.ConnectError, httpx.NetworkError):
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = "Ollama connection refused (server offline)"
        except httpx.HTTPStatusError as e:
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = f"Ollama HTTP error {e.response.status_code}"
        except httpx.RequestError as e:
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = f"Ollama request failed: {type(e).__name__}"
        except (json.JSONDecodeError, KeyError) as e:
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = f"Malformed JSON from LLM: {type(e).__name__}"
        except Exception as e:
            dt_ms = (time.perf_counter() - t0) * 1000
            fallback_reason = f"Ollama request error: {type(e).__name__}"

        # Fallback path
        rule_events = extract_rules_events(text, author_id, context.members, context.now_ms)
        extracted_fallback = tuple(
            RawExtractedEvent(
                event_type=e["event_type"],
                payload=e["payload"],
                confidence=float(e.get("confidence", 0.85)),
            )
            for e in rule_events
        )
        return ExtractionResult(
            events=extracted_fallback,
            raw_response="fallback_rule_engine",
            used_fallback=True,
            parser="rules",
            model="rules_engine",
            latency_ms=dt_ms,
            fallback_reason=fallback_reason or "Ollama unavailable",
        )


