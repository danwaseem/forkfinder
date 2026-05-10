#!/usr/bin/env python3
"""
Seed all users from users.csv into the ForkFinder database via the signup API.
Run once before any load test. Safe to re-run — 409 (already exists) is skipped.

Usage:
    cd jmeter
    python3 seed_users.py
"""
import csv
import sys
import requests

BASE = "http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com"

def main():
    with open("users.csv") as f:
        rows = list(csv.DictReader(f))

    print(f"Seeding {len(rows)} users to {BASE} ...")
    ok = skipped = failed = 0

    for i, row in enumerate(rows):
        email    = row["email"]
        password = row["password"]
        name     = email.split("@")[0].replace(".", " ").title()

        try:
            r = requests.post(
                f"{BASE}/auth/user/signup",
                json={"name": name, "email": email, "password": password},
                timeout=10,
            )
        except requests.RequestException as e:
            print(f"[ERROR] {email}: {e}", file=sys.stderr)
            failed += 1
            continue

        if r.status_code in (200, 201):
            ok += 1
        elif r.status_code == 409:
            skipped += 1
        else:
            print(f"[WARN]  {email}: HTTP {r.status_code} — {r.text[:120]}", file=sys.stderr)
            failed += 1

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(rows)} processed (created={ok}, skipped={skipped}, failed={failed})")

    print(f"\nDone. created={ok}  already_existed={skipped}  failed={failed}")

if __name__ == "__main__":
    main()
