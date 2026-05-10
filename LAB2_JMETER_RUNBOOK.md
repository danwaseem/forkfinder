# Lab 2 Part 5 — JMeter Performance Testing Runbook

## Overview

This runbook covers running the ForkFinder load test at five concurrency levels (100 / 200 / 300 / 400 / 500 users), capturing results, building the response-time-vs-concurrency graph, and writing the analysis section for the report.

**Target environment:** AWS EKS (deployed)  
**Ingress URL:** `http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com`  
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

### 2. Verify the AWS deployment is live

```bash
curl http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com/health
# {"status":"ok"}
```

Also confirm pods are running:

```bash
kubectl get pods -n forkfinder
```

All pods should show `1/1 Running`.

### 3. Seed test users

All 520 users in `jmeter/users.csv` must exist in the database before running any load test. Save the script below as `jmeter/seed_users.py` and run it once:

```python
import csv, requests, sys

BASE = "http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com"

with open("users.csv") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        email    = row["email"]
        password = row["password"]
        name     = email.split("@")[0].replace(".", " ").title()
        r = requests.post(f"{BASE}/auth/user/signup", json={
            "name": name, "email": email, "password": password
        })
        if r.status_code not in (200, 201, 409):   # 409 = already exists, skip silently
            print(f"[WARN] {email}: {r.status_code} {r.text}", file=sys.stderr)
        elif i % 50 == 0:
            print(f"  seeded row {i}: {email}")

print("Done.")
```

Run from the `jmeter/` directory:

```bash
cd jmeter
python3 seed_users.py
```

This is idempotent — re-running when users already exist returns HTTP 409 which is silently skipped.

### 4. Know your restaurant ID

The review sampler uses `RESTAURANT_ID`. Confirm a valid ID from the live cluster:

```bash
curl "http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com/restaurants?limit=1" \
  | python3 -m json.tool | grep '"id"'
```

After a full reseed, restaurant IDs are 1–40. Use any value in that range (e.g. `1`).

---

## Running the Tests

### Option A — JMeter CLI (`.jmx` test plan)

From the repo root, run each concurrency level with JMeter in non-GUI mode:

```bash
# Template — replace N with 100/200/300/400/500
jmeter -n \
  -t jmeter/forkfinder_load_test.jmx \
  -Jthreads=N \
  -Jrampup=30 \
  -JBASE_HOST=k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com \
  -JBASE_PORT=80 \
  -JRESTAURANT_ID=1 \
  -l jmeter/results/raw_N.jtl \
  -e -o jmeter/results/html_N
```

#### All five runs in sequence

```bash
for N in 100 200 300 400 500; do
  echo "=== Starting run: $N threads ==="
  jmeter -n \
    -t jmeter/forkfinder_load_test.jmx \
    -Jthreads=$N \
    -Jrampup=30 \
    -JBASE_HOST=k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com \
    -JBASE_PORT=80 \
    -JRESTAURANT_ID=$N \
    -l jmeter/results/raw_${N}.jtl \
    -e -o jmeter/results/html_${N}
  echo "=== Done: $N threads. HTML report → jmeter/results/html_${N}/index.html ==="
  sleep 15
done
```

> Note: `RESTAURANT_ID=$N` uses a different restaurant per run (IDs 100, 200, 300, 400, 500 don't exist — set to a valid ID like `1` through `40`, or rotate them: `RESTAURANT_IDS=(1 2 3 4 5)` and index by run number). The simplest correct approach is to use a different ID per run to avoid the unique-review-per-user constraint:

```bash
RIDS=(1 5 10 15 20)
LEVELS=(100 200 300 400 500)
for i in "${!LEVELS[@]}"; do
  N=${LEVELS[$i]}
  RID=${RIDS[$i]}
  echo "=== $N threads, restaurant $RID ==="
  jmeter -n \
    -t jmeter/forkfinder_load_test.jmx \
    -Jthreads=$N \
    -Jrampup=30 \
    -JBASE_HOST=k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com \
    -JBASE_PORT=80 \
    -JRESTAURANT_ID=$RID \
    -l jmeter/results/raw_${N}.jtl \
    -e -o jmeter/results/html_${N}
  sleep 15
done
```

### Option B — Python async runner (`run_load_test.py`)

The repo also includes a Python-based runner that outputs JTL-compatible files. Before using it, update the two hardcoded values at the top of `jmeter/run_load_test.py`:

```python
# Line 18 — change from localhost to the EKS ingress
BASE_URL = "http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com"

# Line 19 — use IDs 1–40 (post-reseed range)
RESTAURANT_IDS = list(range(1, 41))
```

Also update the `_clear_reviews()` function to use `kubectl exec` instead of `docker exec`:

```python
def _clear_reviews():
    try:
        pod = subprocess.check_output(
            ["kubectl", "get", "pod", "-n", "forkfinder",
             "-l", "app=restaurant-service",
             "-o", "jsonpath={.items[0].metadata.name}"],
            text=True
        ).strip()
        subprocess.run(
            ["kubectl", "exec", "-n", "forkfinder", pod, "--",
             "python", "-c",
             "from app.database import get_db; db=get_db(); "
             "db.reviews.delete_many({}); "
             "db.restaurants.update_many({}, {'$set': {'avg_rating': 0, 'review_count': 0}})"],
            capture_output=True, timeout=30
        )
    except Exception:
        pass
```

Then run:

```bash
cd jmeter
python3 run_load_test.py --all          # runs all 5 levels
python3 run_load_test.py --threads 100  # single run
```

**What each flag does (JMeter CLI):**

| Flag | Meaning |
|------|---------|
| `-n` | Non-GUI (headless) mode — required for load testing |
| `-t` | Path to the `.jmx` test plan |
| `-Jthreads=N` | Number of concurrent virtual users |
| `-Jrampup=30` | Seconds to ramp up to full thread count |
| `-JBASE_HOST` | EKS ingress hostname (no `http://`) |
| `-JBASE_PORT` | `80` for the EKS ingress |
| `-JRESTAURANT_ID` | Restaurant used by the Submit Review sampler |
| `-l` | Raw results file (JTL/CSV format) |
| `-e -o` | Generate HTML dashboard into the specified directory |

---

## Verifying Results

After each run, check the Summary Report printed to the console:

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

| Concurrent Users | Avg Response (ms) | p90 (ms) | p99 (ms) | Error % | Throughput (req/s) |
|-----------------|------------------|---------|---------|---------|-------------------|
| 100 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 200 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 300 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 400 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |
| 500 | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ | _(fill)_ |

### Step 3 — Plot the graph

Save as `jmeter/plot_results.py` and run `python3 jmeter/plot_results.py`:

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
ax1.set_title('ForkFinder API — Response Time vs Concurrency (AWS EKS)')

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

---

## Screenshots to Capture for the Report

1. **JMeter GUI — Test Plan overview**: Open `forkfinder_load_test.jmx` in JMeter GUI (`jmeter` with no `-n` flag), screenshot showing Thread Group, samplers, CSV dataset, and listeners in the left tree.

2. **Summary Report (console output)**: Screenshot of the terminal showing the five-run output, one summary line per run.

3. **HTML Dashboard — Aggregate report table**: Open `jmeter/results/html_100/index.html` → Statistics table. Screenshot showing all three sampler rows with their latencies and error rates.

4. **Response Time Over Time chart**: From the HTML dashboard → "Response Time Over Time" chart for one run (e.g., 300 threads).

5. **Response-time-vs-concurrency graph**: The PNG produced in Step 3 (`response_time_vs_concurrency.png`).

---

## Writing the Analysis

### 1. Throughput saturation point
Identify the concurrency level at which throughput stops increasing (or starts falling). Example: "Throughput peaked at 42 req/s at 200 concurrent users and remained flat at 300+, indicating the EKS pods are CPU-bound at ~200 users."

### 2. Response time degradation
Note when average response time crosses a user-noticeable threshold (commonly 2 s). Example: "Average response time stayed under 500 ms at 100–200 users but rose sharply to 3.2 s at 400 users and 5.8 s at 500 users."

### 3. Error analysis
Classify errors by sampler:
- **Login errors (4xx)** — credential not found (missed seeding), or rate limiting.
- **Search errors** — unlikely unless MongoDB is overwhelmed; 5xx indicates connection pool exhaustion.
- **Review errors (400)** — expected at higher concurrency due to the unique-per-user constraint (one review per user per restaurant). These are not infrastructure failures. Mention explicitly: "400 errors on the review sampler reflect the application's unique-review constraint, not server failures."

### 4. Bottleneck identification
Based on where latency spikes — auth (bcrypt is CPU-intensive), MongoDB queries, or Kafka publish latency. To profile MongoDB slow queries:

```bash
kubectl exec -n forkfinder deploy/restaurant-service -- \
  python -c "from app.database import get_db; db=get_db(); db.command('profile', 1, slowms=100)"
```

---

## Environment Caveats

| Caveat | Detail |
|--------|--------|
| **Review uniqueness** | Each user can only review each restaurant once. Use a different `RESTAURANT_ID` per run (IDs 1–40 available after reseed) to avoid 400 errors dominating the results. |
| **bcrypt CPU cost** | The Login sampler is CPU-bound due to bcrypt (work factor 12). Under high concurrency, login latency will dominate. This is expected — mention it in the analysis. |
| **EKS node capacity** | Results reflect actual cloud infrastructure. If pods are on `t3.small`/`t3.medium` nodes, CPU throttling will appear at 300–400 users. Note the instance type in your report. |
| **Ramp-up period** | Default `rampup=30` spreads thread starts over 30 s. For a sharper spike test use `-Jrampup=5`. For a gradual test use `-Jrampup=60`. |
| **JMeter heap** | For 500 threads with listeners enabled, JMeter may need more heap. Set before running: `export JVM_ARGS="-Xms512m -Xmx2g"` |
| **CSV sharing mode** | `users.csv` is configured with `shareMode.all` — all threads share one cursor cycling through rows. With 500 threads and 520 rows, every thread gets a unique user. If you add more than one loop, users will repeat. |
| **Network latency** | Running JMeter from your laptop to an AWS EKS ingress adds ~10–30 ms of baseline network RTT. This is included in all measurements and is realistic for a deployed app. |

---

## Quick Reference

```bash
# Single quick run — 100 users against AWS
jmeter -n -t jmeter/forkfinder_load_test.jmx -Jthreads=100 -Jrampup=30 \
  -JBASE_HOST=k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com \
  -JBASE_PORT=80 -JRESTAURANT_ID=1 \
  -l jmeter/results/raw_100.jtl -e -o jmeter/results/html_100

# Open HTML report (macOS)
open jmeter/results/html_100/index.html

# Verify API health
curl http://k8s-forkfind-forkfind-8e65d48af1-1990260306.us-east-1.elb.amazonaws.com/health

# Check pod logs for errors during a test run
kubectl logs -n forkfinder deploy/restaurant-service --tail=50 -f

# MongoDB slow query profiling (run during a load test)
kubectl exec -n forkfinder deploy/restaurant-service -- \
  python -c "from app.database import get_db; db=get_db(); db.command('profile', 1, slowms=100)"
```

---

## File Structure After Testing

```
jmeter/
├── forkfinder_load_test.jmx     ← JMeter test plan
├── users.csv                    ← 520 test user credentials
├── seed_users.py                ← one-time DB seeding script (points to AWS)
├── run_load_test.py             ← Python async runner alternative
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
