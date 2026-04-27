"""
ForkFinder Load Test — replicates forkfinder_load_test.jmx
Three flows per virtual user:
  1. POST /auth/user/login
  2. GET  /restaurants
  3. POST /restaurants/{id}/reviews  (triggers Kafka)

Outputs JTL (CSV) to results/results_{N}.jtl  (compatible with JMeter reports)
Usage:
  python3 run_load_test.py --threads 100 --rampup 30
  python3 run_load_test.py --all   # runs 100/200/300/400/500
"""

import argparse
import asyncio
import csv
import os
import time
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

BASE_URL = "http://localhost:8000"
RESTAURANT_IDS = list(range(1, 14))  # restaurants 1–13

import subprocess

def _clear_reviews():
    """Drop all reviews from MongoDB before each run (avoids duplicate-review errors)."""
    try:
        subprocess.run(
            ["docker", "exec", "forkfinder-mongodb", "mongosh",
             "restaurant_platform", "--quiet", "--eval",
             "db.reviews.deleteMany({}); db.restaurants.updateMany({}, {$set: {avg_rating: 0, review_count: 0}})"],
            capture_output=True, timeout=15
        )
    except Exception:
        pass
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Load users from CSV
USERS_CSV = Path(__file__).parent / "users.csv"
with open(USERS_CSV) as f:
    ALL_USERS = [r for r in csv.DictReader(f)]


def _jtl_row(label, start_ms, elapsed_ms, status_code, success, response_bytes=0, thread_name=""):
    """Return a JTL (CSV) row dict."""
    return {
        "timeStamp": int(start_ms),
        "elapsed": int(elapsed_ms),
        "label": label,
        "responseCode": status_code,
        "responseMessage": "OK" if success else "FAILED",
        "threadName": thread_name,
        "dataType": "text",
        "success": str(success).lower(),
        "failureMessage": "" if success else f"HTTP {status_code}",
        "bytes": response_bytes,
        "sentBytes": 0,
        "grpThreads": 1,
        "allThreads": 1,
        "URL": "",
        "Latency": int(elapsed_ms),
        "IdleTime": 0,
        "Connect": 0,
    }


JTL_FIELDS = [
    "timeStamp", "elapsed", "label", "responseCode", "responseMessage",
    "threadName", "dataType", "success", "failureMessage", "bytes",
    "sentBytes", "grpThreads", "allThreads", "URL", "Latency", "IdleTime", "Connect",
]


async def virtual_user(session: aiohttp.ClientSession, user: dict, thread_id: int, results: list):
    thread_name = f"ThreadGroup 1-{thread_id}"

    # ── 1. Login ──────────────────────────────────────────────────────────────
    t0 = time.time()
    ts0 = t0 * 1000
    token = None
    try:
        async with session.post(
            f"{BASE_URL}/auth/user/login",
            json={"email": user["email"], "password": user["password"]},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            elapsed = (time.time() - t0) * 1000
            body = await resp.read()
            ok = resp.status == 200
            if ok:
                data = await asyncio.to_thread(lambda: __import__("json").loads(body))
                token = data.get("access_token")
            results.append(_jtl_row("POST /auth/user/login", ts0, elapsed,
                                    resp.status, ok, len(body), thread_name))
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        results.append(_jtl_row("POST /auth/user/login", ts0, elapsed,
                                 0, False, 0, thread_name))
        return  # can't proceed without token

    # ── 2. Restaurant search ──────────────────────────────────────────────────
    headers = {"Authorization": f"Bearer {token}"}
    t0 = time.time()
    ts0 = t0 * 1000
    try:
        async with session.get(
            f"{BASE_URL}/restaurants",
            params={"page": 1, "limit": 10},
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            elapsed = (time.time() - t0) * 1000
            body = await resp.read()
            ok = resp.status == 200
            results.append(_jtl_row("GET /restaurants", ts0, elapsed,
                                    resp.status, ok, len(body), thread_name))
    except Exception:
        elapsed = (time.time() - t0) * 1000
        results.append(_jtl_row("GET /restaurants", ts0, elapsed, 0, False, 0, thread_name))

    # ── 3. Submit review (triggers Kafka) ─────────────────────────────────────
    rid = RESTAURANT_IDS[(thread_id - 1) % len(RESTAURANT_IDS)]
    t0 = time.time()
    ts0 = t0 * 1000
    try:
        async with session.post(
            f"{BASE_URL}/restaurants/{rid}/reviews",
            json={
                "rating": random.randint(3, 5),
                "comment": f"Load test review from {user['email']} — great place!",
            },
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            elapsed = (time.time() - t0) * 1000
            body = await resp.read()
            ok = resp.status in (200, 201)
            results.append(_jtl_row("POST /restaurants/{id}/reviews", ts0, elapsed,
                                    resp.status, ok, len(body), thread_name))
    except Exception:
        elapsed = (time.time() - t0) * 1000
        results.append(_jtl_row("POST /restaurants/{id}/reviews", ts0, elapsed,
                                 0, False, 0, thread_name))


async def run_test(num_threads: int, rampup_seconds: int) -> list:
    """Spawn `num_threads` virtual users with linear ramp-up."""
    users = (ALL_USERS * ((num_threads // len(ALL_USERS)) + 1))[:num_threads]
    results = []
    delay_between = rampup_seconds / num_threads if num_threads > 1 else 0

    connector = aiohttp.TCPConnector(limit=num_threads + 50, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, user in enumerate(users):
            await asyncio.sleep(delay_between)
            tasks.append(asyncio.create_task(
                virtual_user(session, user, i + 1, results)
            ))
        await asyncio.gather(*tasks, return_exceptions=True)

    return results


def write_jtl(results: list, path: Path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=JTL_FIELDS)
        writer.writeheader()
        writer.writerows(results)


def summarize(results: list, num_threads: int) -> dict:
    by_label: dict[str, list] = {}
    for r in results:
        by_label.setdefault(r["label"], []).append(r)

    print(f"\n{'='*70}")
    print(f"  Load Test Summary — {num_threads} concurrent users")
    print(f"{'='*70}")
    print(f"{'Endpoint':<40} {'Reqs':>5} {'Err%':>6} {'Avg':>7} {'Min':>7} {'Max':>7} {'p90':>7} {'p99':>7}")
    print(f"{'-'*70}")

    summary = {}
    for label, rows in by_label.items():
        elaps = [r["elapsed"] for r in rows]
        errors = sum(1 for r in rows if r["success"] == "false")
        avg = statistics.mean(elaps)
        mn = min(elaps)
        mx = max(elaps)
        sorted_e = sorted(elaps)
        p90 = sorted_e[int(len(sorted_e) * 0.9)]
        p99 = sorted_e[int(len(sorted_e) * 0.99)]
        err_pct = errors / len(rows) * 100
        print(f"{label:<40} {len(rows):>5} {err_pct:>5.1f}% {avg:>6.0f}ms {mn:>6.0f}ms {mx:>6.0f}ms {p90:>6.0f}ms {p99:>6.0f}ms")
        summary[label] = {
            "requests": len(rows),
            "errors": errors,
            "error_pct": round(err_pct, 2),
            "avg_ms": round(avg, 1),
            "min_ms": mn,
            "max_ms": mx,
            "p90_ms": p90,
            "p99_ms": p99,
        }

    all_elaps = [r["elapsed"] for r in results]
    all_errors = sum(1 for r in results if r["success"] == "false")
    total = len(results)
    print(f"{'-'*70}")
    print(f"{'TOTAL':<40} {total:>5} {all_errors/total*100:>5.1f}% {statistics.mean(all_elaps):>6.0f}ms")
    print(f"{'='*70}\n")

    return summary


def write_aggregate_csv(all_summaries: list, path: Path):
    """Write aggregate_results.csv with one row per (threads, endpoint)."""
    fields = ["threads", "endpoint", "requests", "errors", "error_pct",
              "avg_ms", "min_ms", "max_ms", "p90_ms", "p99_ms"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for threads, summary in all_summaries:
            for label, stats in summary.items():
                w.writerow({"threads": threads, "endpoint": label, **stats})
    print(f"Aggregate CSV saved → {path}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=100)
    parser.add_argument("--rampup", type=int, default=30)
    parser.add_argument("--all", action="store_true",
                        help="Run all 5 levels: 100/200/300/400/500")
    args = parser.parse_args()

    levels = [100, 200, 300, 400, 500] if args.all else [args.threads]
    all_summaries = []

    for n in levels:
        rampup = max(10, n // 5)  # scale ramp-up with load
        print(f"\n>>> Clearing previous reviews …")
        _clear_reviews()
        print(f">>> Starting load test: {n} users, {rampup}s ramp-up …")
        wall_start = time.time()
        results = await run_test(n, rampup)
        wall_elapsed = time.time() - wall_start

        jtl_path = RESULTS_DIR / f"results_{n}.jtl"
        write_jtl(results, jtl_path)
        print(f"JTL saved → {jtl_path}  ({len(results)} samples, {wall_elapsed:.1f}s wall time)")

        summary = summarize(results, n)
        all_summaries.append((n, summary))

    if len(all_summaries) > 1:
        write_aggregate_csv(all_summaries, RESULTS_DIR / "aggregate_results.csv")


if __name__ == "__main__":
    asyncio.run(main())
