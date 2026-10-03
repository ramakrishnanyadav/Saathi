#!/usr/bin/env python3
"""
SAATH Privacy Audit Script

Tests that:
- LLM requests go ONLY to localhost (never external)
- Whisper is local (no cloud API)
- Household data stays in SQLite (no external DB)
- No accidental external telemetry
- No raw sensitive content in logs
- Audio is not permanently retained

Run: python scripts/privacy_audit.py
"""
from __future__ import annotations

import importlib
import inspect
import os
import pathlib
import re
import sys

# Add api/ to path
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "api"))

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def check(label: str, condition: bool, critical: bool = True) -> bool:
    status = PASS if condition else (FAIL if critical else WARN)
    print(f"  {status}  {label}")
    return condition


def audit_llm_endpoint() -> bool:
    """LLM must only call localhost or environment-configured local URLs."""
    from saath.adapters.llm_ollama import OllamaLLMProvider

    # Inspect the source code for any hardcoded external URLs
    source = inspect.getsource(OllamaLLMProvider)
    forbidden = re.findall(r'https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)\S+', source)
    allowed = "base_url" in source and "localhost" in source

    ok = len(forbidden) == 0
    return check("LLM adapter has no hardcoded external URLs", ok) and \
           check("LLM adapter uses configurable local base_url", allowed, critical=False)


def audit_whisper_local() -> bool:
    """Whisper must be running locally, not calling any cloud API."""
    from saath.adapters.stt_whisper import WhisperSTTAdapter
    source = inspect.getsource(WhisperSTTAdapter)

    has_cloud = any(cloud in source.lower() for cloud in [
        "openai.com", "api.openai", "assemblyai", "deepgram", "rev.ai", "google.com/speech"
    ])
    ok = not has_cloud
    return check("Whisper adapter makes no cloud API calls", ok)


def audit_sqlite_only() -> bool:
    """Verify no external DB clients are imported in the store adapter."""
    from saath.adapters import store_sqlite
    source = inspect.getsource(store_sqlite)

    forbidden_dbs = ["psycopg", "pymongo", "redis", "elasticsearch", "boto3", "firebase"]
    found = [db for db in forbidden_dbs if db in source.lower()]
    ok = len(found) == 0
    return check(f"Store adapter uses only SQLite (no {', '.join(forbidden_dbs[:3])} etc.)", ok)


def audit_no_external_telemetry() -> bool:
    """No sentry, datadog, mixpanel, or analytics libraries in the codebase."""
    api_path = ROOT / "api"
    telemetry_libs = ["sentry_sdk", "datadog", "mixpanel", "amplitude", "analytics.write_key", "ga4", "gtag"]

    found_any = False
    for py_file in api_path.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for lib in telemetry_libs:
            if lib in content:
                print(f"    Found '{lib}' in {py_file.relative_to(ROOT)}")
                found_any = True
                break

    ok = not found_any
    return check("No external telemetry/analytics libraries", ok)


def audit_no_sensitive_content_in_logs() -> bool:
    """Log statements must not log raw text content verbatim with sensitive patterns."""
    api_path = ROOT / "api"
    sensitive_patterns = [
        r'logger\.[a-z]+\(.*amount_paise',
        r'logger\.[a-z]+\(.*password',
        r'logger\.[a-z]+\(.*phone',
        r'logger\.[a-z]+\(.*secret',
    ]

    violations = []
    for py_file in api_path.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pat in sensitive_patterns:
            if re.search(pat, content, re.IGNORECASE):
                violations.append(f"{py_file.name}: {pat}")

    ok = len(violations) == 0
    if not ok:
        for v in violations:
            print(f"    {WARN} {v}")
    return check("Logs contain no raw sensitive content patterns", ok, critical=False)


def audit_audio_not_retained() -> bool:
    """Audio files must not be stored persistently on disk."""
    from saath.adapters.stt_whisper import WhisperSTTAdapter
    source = inspect.getsource(WhisperSTTAdapter)

    # Check for any file.write or open(..., 'wb') that would persist audio
    persistent_write = re.search(r'open\([^)]+["\']wb["\']\)', source)
    shutil_copy = "shutil.copy" in source and "audio" in source

    ok = not persistent_write and not shutil_copy
    return check("Audio bytes not written to permanent disk storage", ok)


def audit_cors_restricted() -> bool:
    """CORS must not allow wildcard origins in production."""
    from saath.api import main
    source = inspect.getsource(main)

    # Look for allow_origins=["*"] which would be dangerously open
    wildcard = re.search(r'allow_origins\s*=\s*\["\*"\]', source)
    ok = not wildcard
    return check("CORS does not allow wildcard origins", ok)


def audit_no_hardcoded_secrets() -> bool:
    """No hardcoded API keys or tokens in Python sources."""
    api_path = ROOT / "api"
    secret_patterns = [
        r'sk-[A-Za-z0-9]{32}',             # OpenAI API key
        r'Bearer [A-Za-z0-9]{32,}',        # Generic bearer token
        r'password\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']{8,}["\']',
    ]

    violations = []
    for py_file in api_path.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pat in secret_patterns:
            matches = re.findall(pat, content)
            if matches:
                violations.append(f"{py_file.name}: {len(matches)} match(es) of '{pat[:30]}'")

    ok = len(violations) == 0
    return check("No hardcoded API keys or secrets found", ok)


def main() -> int:
    print("\n" + "=" * 60)
    print("SAATH PRIVACY AUDIT")
    print("=" * 60 + "\n")

    results = [
        audit_llm_endpoint(),
        audit_whisper_local(),
        audit_sqlite_only(),
        audit_no_external_telemetry(),
        audit_no_sensitive_content_in_logs(),
        audit_audio_not_retained(),
        audit_cors_restricted(),
        audit_no_hardcoded_secrets(),
    ]

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"Privacy Audit: {passed}/{total} checks passed")
    if passed == total:
        print("[PASS] All privacy checks PASSED — SAATH is local-first clean")
    else:
        print(f"[FAIL] {total - passed} privacy check(s) FAILED — review above")
    print("=" * 60 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
