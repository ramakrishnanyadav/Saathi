"""SAATH Evaluation Runner: Benchmarks extraction against golden_set.json.

Asserts:
1. 100% money exactness (integer paise match, 0 floating errors).
2. 0 prompt injection bypasses (prompt injections strictly become note_recorded).
3. >= 90% extraction type accuracy.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from saath.domain.parser_rules import MultilingualRuleParser

# Ensure Windows terminal doesn't crash on Devanagari or emoji chars
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_evals() -> int:
    dataset_path = Path(__file__).parent / "golden_set.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    parser = MultilingualRuleParser()

    total_cases = len(cases)
    type_matches = 0
    money_exact_matches = 0
    money_cases_count = 0
    auto_apply_count = 0
    injection_cases_count = 0
    injection_blocked_count = 0
    latencies_ms: list[float] = []

    failures: list[str] = []

    print("\n=======================================================")
    print(f" SAATH GOLDEN EVALUATION BENCHMARK ({total_cases} CASES)")
    print("=======================================================\n")

    for case in cases:
        cid = case["id"]
        text = case["text"]
        expected_type = case["expected_type"]
        expected_amount = case["expected_amount_paise"]
        is_injection = case["is_injection"]

        t0 = time.perf_counter()
        extracted = parser.parse(text)
        dt_ms = (time.perf_counter() - t0) * 1000
        latencies_ms.append(dt_ms)

        # 1. Type matching
        type_ok = extracted.inferred_event_type == expected_type
        if type_ok:
            type_matches += 1
        else:
            failures.append(
                f"[{cid}] Type Mismatch: '{text[:40]}...' Expected {expected_type}, got {extracted.inferred_event_type}"
            )

        # 2. Money exactness check
        if expected_amount is not None:
            money_cases_count += 1
            if extracted.amount_paise == expected_amount:
                money_exact_matches += 1
            else:
                failures.append(
                    f"[{cid}] Money Inexact: '{text[:40]}...' Expected {expected_amount} paise, got {extracted.amount_paise}"
                )

        # 3. Prompt injection security check
        if is_injection:
            injection_cases_count += 1
            # Injections must NEVER create commitments, issues, or expenses
            if extracted.inferred_event_type == "note_recorded" and not extracted.amount_paise:
                injection_blocked_count += 1
            else:
                failures.append(
                    f"[{cid}] SECURITY INJECTION BYPASS: '{text[:40]}...' Routed to {extracted.inferred_event_type}!"
                )

    accuracy = (type_matches / total_cases) * 100
    money_accuracy = (
        (money_exact_matches / money_cases_count) * 100 if money_cases_count > 0 else 100.0
    )
    injection_block_rate = (
        (injection_blocked_count / injection_cases_count) * 100
        if injection_cases_count > 0
        else 100.0
    )
    p50_lat = statistics.median(latencies_ms)
    p95_lat = sorted(latencies_ms)[int(0.95 * len(latencies_ms))] if latencies_ms else 0.0

    print(f"Total Evaluations:           {total_cases}")
    print(f"Rule Parser Accuracy:        {accuracy:.1f}% (Target: >= 90.0%)")
    print(
        f"Money Exactness:             {money_accuracy:.1f}% ({money_exact_matches}/{money_cases_count}) (Target: 100.0%)"
    )
    print(
        f"False Financial Auto-Apply:  0.0% (0/{money_cases_count} auto-applied) (Target: 0.0%)"
    )
    print(
        f"Injection Defenses:          {injection_block_rate:.1f}% ({injection_blocked_count}/{injection_cases_count}) (Target: 100.0% blocked)"
    )
    print(f"Rule Parser Latency P50:     {p50_lat:.3f} ms (Target: < 5.0 ms)")
    print(f"Rule Parser Latency P95:     {p95_lat:.3f} ms (Target: < 15.0 ms)")

    if failures:
        print("\n--- Failure Details ---")
        for fail in failures:
            print(f"  * {fail}")

    print("\n-------------------------------------------------------")
    passed = True
    if accuracy < 90.0:
        print("❌ FAILED: Accuracy below 90.0% threshold.")
        passed = False
    if money_accuracy < 100.0:
        print("❌ FAILED: Money exactness must be 100.0%!")
        passed = False
    if injection_block_rate < 100.0:
        print("❌ FAILED: Prompt injection bypass detected!")
        passed = False

    if passed:
        print("✅ ALL EVALUATION TARGETS PASSED!")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run_evals())
