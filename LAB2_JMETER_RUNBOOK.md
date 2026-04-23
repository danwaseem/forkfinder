# Lab 2 Part 5 — JMeter Performance Testing Runbook

## Overview

This runbook covers running the ForkFinder load test at five concurrency levels (100 / 200 / 300 / 400 / 500 users), capturing results, building the response-time-vs-concurrency graph, and writing the analysis section for the report.

**Test plan file:** `jmeter/forkfinder_load_test.jmx`  
**User credentials CSV:** `jmeter/users.csv`  
**Results output dir:** `jmeter/results/`

---

## Endpoints Under Test

| # | Sampler label | Method | Path |
|---|--------------|--------|------|
| 1 | Login | POST | `/auth/user/login` |
| 2 | Search Restaurants | GET | `/restaurants?q=pizza&limit=12&sort=rating` |
| 3 | Submit Review | POST | `/restaurants/${RESTAURANT_ID}/reviews` |

Each thread executes all three requests in order once per loop. The JWT from the Login response is extracted and used as the Bearer token for the subsequent two requests.

---

## Prerequisites

### 1. Install JMeter

```bash
# macOS (Homebrew)
brew install jmeter

# Or download from https://jmeter.apache.org/download_jmeter.cgi
# Unzip to ~/jmeter and add bin/ to PATH
export PATH="$HOME/apache-jmeter-5.6.3/bin:$PATH"
```

Verify:

```bash
jmeter --version
# Apache JMeter 5.6.3
```

### 2. Start the backend

```bash
# Option A — local
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option B — Docker Compose (MongoDB + Kafka + all services)
docker compose --env-file .env.docker up --build
```

Verify the API is up:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### 3. Seed test users

All 520 users in `jmeter/users.csv` (user001@example.com … user500@example.com plus 20 named accounts) **must exist** in the database before running any load test. If running against a fresh database, seed them first:

```bash
cd jmeter
python3 seed_users.py        # see "Seeding script" section below
```

#### Seeding script (create once, run once per fresh DB)

Save as `jmeter/seed_users.py`:

```python
import csv, requests, sys

BASE = "http://localhost:8000"

with open("users.csv") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        email    = row["email"]
        password = row["password"]
        name     = email.split("@")[0].replace(".", " ").title()
        r = requests.post(f"{BASE}/auth/register", json={
            "name": name, "email": email, "password": password
        })
        if r.status_code not in (200, 201, 409):   # 409 = already exists
            print(f"[WARN] {email}: {r.status_code} {r.text}", file=sys.stderr)
        elif i % 50 == 0:
            print(f"  seeded row {i}: {email}")

print("Done.")
```

This is idempotent — re-running it when users already exist returns HTTP 409 (conflict), which is silently skipped.

### 4. Know your restaurant ID

The review sampler uses `RESTAURANT_ID`. Confirm a valid ID:

```bash
curl "http://localhost:8000/restaurants?limit=1" | python3 -m json.tool | grep '"id"'
```

Note the numeric `id` value (e.g., `1`). Pass it as `-JRESTAURANT_ID=1` when running tests (see below).

---

## Running the Tests

From the repo root, run each concurrency level with the JMeter CLI (non-GUI mode):

```bash
# Template — replace N with 100/200/300/400/500
jmeter -n \
  -t jmeter/forkfinder_load_test.jmx \
  -Jthreads=N \
  -Jrampup=30 \
  -JBASE_HOST=localhost \
  -JBASE_PORT=8000 \
  -JRESTAURANT_ID=1 \
  -l jmeter/results/raw_N.jtl \
  -e -o jmeter/results/html_N
```

### All five runs in sequence

```bash
for N in 100 200 300 400 500; do
  echo "=== Starting run: $N threads ==="
  jmeter -n \
    -t jmeter/forkfinder_load_test.jmx \
    -Jthreads=$N \
    -Jrampup=30 \
    -JBASE_HOST=localhost \
    -JBASE_PORT=8000 \
    -JRESTAURANT_ID=1 \
    -l jmeter/results/raw_${N}.jtl \
    -e -o jmeter/results/html_${N}
  echo "=== Done: $N threads. HTML report at jmeter/results/html_${N}/index.html ==="
  sleep 10   # let the server cool down between runs
done
```

**What each flag does:**

| Flag | Meaning |
|------|---------|
| `-n` | Non-GUI (headless) mode — required for load testing |
| `-t` | Path to the `.jmx` test plan |
| `-Jthreads=N` | Overrides `${__P(threads,100)}` — number of concurrent virtual users |
| `-Jrampup=30` | Overrides `${__P(rampup,30)}` — seconds to ramp up to full thread count |
| `-JBASE_HOST` | Target host (change to your server IP for remote runs) |
| `-JBASE_PORT` | Target port |
| `-JRESTAURANT_ID` | Restaurant used by the Submit Review sampler |
| `-l` | Raw results file (JTL format — CSV with timestamps, latencies, status codes) |
| `-e -o` | Generate HTML dashboard report into the specified directory |

---

## Verifying Results

After each run, check the Summary Report printed to the console. Look for:

```
summary +  1000 in  00:00:35 = 28.5/s  Avg:  3512  Min:   201  Max: 12045  Err:   3 (0.30%)
```

Key columns:

| Column | Meaning |
|--------|---------|
| `Avg` | Average response time (ms) — **primary metric** |
| `Min/Max` | Floor and ceiling latencies |
| `Err %` | Error rate — should stay < 5% for 100–300 users; < 10% acceptable at 400–500 |
| `/s` | Throughput (requests per second) |

Open the HTML dashboard:

```bash
open jmeter/results/html_100/index.html   # macOS
```

The dashboard shows response time percentiles (p50, p90, p95, p99), throughput over time, and error distribution.

---

## Building the Response-Time-vs-Concurrency Graph

### Step 1 — Extract average response times from JTL files

```bash
python3 - <<'EOF'
import csv, statistics, glob, os

for jtl in sorted(glob.glob("jmeter/results/raw_*.jtl")):
    n = os.path.basename(jtl).replace("raw_","").replace(".jtl","")
    times = []
    with open(jtl) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("success","true") == "true":
                times.append(int(row["elapsed"]))
    if times:
        print(f"Threads={n:>4}  avg={statistics.mean(times):.0f}ms  "
              f"p90={sorted(times)[int(len(times)*0.90)]:.0f}ms  "
              f"p99={sorted(times)[int(len(times)*0.99)]:.0f}ms  "
              f"n={len(times)}")
EOF
```

### Step 2 — Fill in the results table

Replace the placeholder values below with your actual measurements:

| Concurrent Users | Avg Response (ms) | p90 (ms) | p99 (ms) | Error % | Throughput (req/s) |
|-----------------|------------------|---------|---------|---------|-------------------|
| 100 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 200 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 300 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 400 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 500 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |

### Step 3 — Plot the graph

**Option A — Python/matplotlib (recommended):**

```python
import matplotlib.pyplot as plt

users    = [100, 200, 300, 400, 500]
avg_ms   = [XXX, XXX, XXX, XXX, XXX]   # replace with your values
p90_ms   = [XXX, XXX, XXX, XXX, XXX]
errors   = [X.X, X.X, X.X, X.X, X.X]  # percentages

fig, ax1 = plt.subplots(figsize=(9, 5))
ax1.plot(users, avg_ms, marker='o', label='Avg response (ms)', color='steelblue')
ax1.plot(users, p90_ms, marker='s', linestyle='--', label='p90 response (ms)', color='dodgerblue')
ax1.set_xlabel('Concurrent Users')
ax1.set_ylabel('Response Time (ms)')
ax1.set_title('ForkFinder API — Response Time vs Concurrency')

ax2 = ax1.twinx()
ax2.bar(users, errors, alpha=0.25, color='tomato', label='Error %', width=25)
ax2.set_ylabel('Error Rate (%)')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig('jmeter/results/response_time_vs_concurrency.png', dpi=150)
plt.show()
```

Run with: `python3 jmeter/plot_results.py`

**Option B — Google Sheets / Excel:**  
Copy the table from Step 2 into a spreadsheet. Insert Chart → Line chart with Users on X-axis and Avg/p90 response times on Y-axis. Add a secondary axis for Error %.

---

## Screenshots to Capture for the Report

1. **JMeter GUI — Test Plan overview**: Open `forkfinder_load_test.jmx` in JMeter GUI (`jmeter` with no `-n` flag), take a screenshot showing the Thread Group, samplers, CSV dataset, and listeners in the left tree.

2. **Summary Report (console output)**: Screenshot of the terminal showing the five-run output, one summary line per run.

3. **HTML Dashboard — Aggregate report table**: Open `jmeter/results/html_100/index.html` → Statistics table. Screenshot showing all three sampler rows with their latencies and error rates.

4. **Response Time Over Time chart**: From the HTML dashboard → "Response Time Over Time" chart for one run (e.g., 300 threads). Screenshot.

5. **Response-time-vs-concurrency graph**: The PNG produced in Step 3 above (`response_time_vs_concurrency.png`).

---

## Writing the Analysis

Address these four points in your report section:

### 1. Throughput saturation point
Identify the concurrency level at which throughput stops increasing (or starts falling). This is your saturation point. Example: "Throughput peaked at 42 req/s at 200 concurrent users and remained flat at 300+, indicating the server is CPU-bound at ~200 users."

### 2. Response time degradation
Note when average response time crosses a user-noticeable threshold (commonly 2 s). Example: "Average response time stayed under 500 ms at 100–200 users but rose sharply to 3.2 s at 400 users and 5.8 s at 500 users."

### 3. Error analysis
Classify errors by sampler:
- **Login errors (4xx)** — credential not found (missed seeding), or rate limiting.
- **Search errors** — unlikely unless DB is overwhelmed; 5xx indicates connection pool exhaustion.
- **Review errors (400)** — expected at higher concurrency due to the unique-per-user constraint (one review per user per restaurant). These are not server failures. Mention this explicitly: "400 errors on the review sampler reflect the application's unique-review constraint, not infrastructure failures."

### 4. Bottleneck identification
Based on where latency spikes — auth (bcrypt is CPU-intensive), MongoDB queries (check slow query logs: `db.setProfilingLevel(1, {slowms: 100})`), or Kafka publish latency.

---

## Environment Caveats

| Caveat | Detail |
|--------|--------|
| **Review uniqueness** | Each user can only review each restaurant once. At 500 concurrent users all hitting `RESTAURANT_ID=1`, only the first submitter per user succeeds; repeats return HTTP 400. Use a different `RESTAURANT_ID` per run, or create a restaurant per run, to get clean 201s. |
| **bcrypt CPU cost** | The Login sampler is CPU-bound due to bcrypt (work factor 12). Under high concurrency, login latency will dominate. This is expected and correct behavior — mention it in the analysis. |
| **Local machine limits** | Running backend + MongoDB + Kafka + JMeter on a laptop competes for CPU/RAM. Treat local results as indicative, not definitive. For accurate results, run the backend on a separate machine or EC2 instance and point `-JBASE_HOST` at it. |
| **Ramp-up period** | The default `rampup=30` seconds spreads thread starts over 30 s. For a sharper spike test, use `-Jrampup=5`. For a gradual load test, use `-Jrampup=60`. |
| **JMeter heap** | For 500 threads with listeners enabled, JMeter may need more heap. Set `JVM_ARGS="-Xms512m -Xmx2g"` before running. |
| **CSV sharing mode** | `users.csv` is configured with `shareMode.all` — all threads share one cursor cycling through rows. With 500 threads and 520 rows, every thread gets a unique user. If you add more than one loop, users will repeat. |

---

## File Structure After Testing

```
jmeter/
├── forkfinder_load_test.jmx     ← JMeter test plan
├── users.csv                    ← 520 test user credentials
├── seed_users.py                ← one-time DB seeding script
├── plot_results.py              ← graph generation script
└── results/
    ├── raw_100.jtl              ← raw JTL for 100 users
    ├── raw_200.jtl
    ├── raw_300.jtl
    ├── raw_400.jtl
    ├── raw_500.jtl
    ├── html_100/index.html      ← HTML dashboard
    ├── html_200/index.html
    ├── html_300/index.html
    ├── html_400/index.html
    ├── html_500/index.html
    └── response_time_vs_concurrency.png
```

---

## Quick Reference

```bash
# Single quick run at 100 users
jmeter -n -t jmeter/forkfinder_load_test.jmx -Jthreads=100 -Jrampup=30 \
  -JBASE_HOST=localhost -JBASE_PORT=8000 -JRESTAURANT_ID=1 \
  -l jmeter/results/raw_100.jtl -e -o jmeter/results/html_100

# Open HTML report (macOS)
open jmeter/results/html_100/index.html

# Check backend logs for slow queries
docker compose logs backend --tail 100 | grep -i "slow\|error\|timeout"

# MongoDB slow query profiling
docker compose exec mongodb mongosh restaurant_platform \
  --eval "db.setProfilingLevel(1, {slowms: 100})"
```
