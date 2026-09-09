# Reference Incident: Ground Truth

The datasets in `data/` are not random sample data — they encode one coherent,
realistic incident. This file is the answer key: use it to judge whether the
agent's future investigation is actually correct, and to write assertions in
repository/agent tests later.

## The story

`payment-api` depends on a Postgres pool (`postgres-payments`, `max_connections: 20`).

1. **09:50 - 10:12** — Unrelated prep: engineer J. Chen's `notification-service`
   commit (`77e410d`) and engineer R. Kapoor's `payment-api` commit `abc123f`
   ("Add retry logic with exponential backoff for gateway timeouts", PR #482)
   land around the same time.
2. **10:15:32** — `payment-api` deploys `v2.4.1` (commit `abc123f`).
3. **10:18:03** — `notification-service` deploys `v1.8.0` (commit `77e410d`).
   This is a **red herring**: same time window, unrelated service, no
   downstream effect (its metrics/logs stay flat the whole incident).
4. **10:20 - 10:26** — The new retry logic acquires a new DB connection on
   each retry attempt but does not reliably release the previous one
   (`logs.json` 10:33:00 WARN is the closest thing to a smoking-gun log line,
   deliberately logged *after* the outage starts, the way a real leak is
   often only noticed in hindsight). `postgres-payments` active connections
   climb from 9 -> 20 (`database_metrics.json`), and pool wait time climbs
   with it.
5. **10:26:19 - 10:27:10** — Pool exhausted; requests start timing out
   waiting for a free connection (`traces.json` `trace-6659`:
   `db.acquire_connection` = 30000ms, the query itself never runs).
6. **10:29:45 onward** — `payment-api` returns HTTP 500 on
   `/api/payments/charge` and `/api/payments/refund`. Error rate peaks at
   ~44% (`metrics.json`). Client-side retries roughly triple request volume
   (122/min -> 410/min), which is a **contributing factor** that worsens the
   exhaustion but is not the root cause.
7. `checkout-api` and `notification-service` stay healthy throughout — this
   is the evidence that rules out a platform-wide or infrastructure-wide
   cause.

## Root cause (what a correct investigation should conclude)

**Primary cause:** the `v2.4.1` deploy (commit `abc123f`) introduced a
connection-pool leak in the gateway retry path: retries acquire a new
connection without releasing the one from the failed attempt.

**Contributing factor:** client-side retry storms roughly tripled request
volume once errors started, accelerating pool exhaustion.

**Not the cause (red herrings a good agent should rule out, not just ignore):**
- `notification-service` deploy at 10:18:03 — different service, unaffected metrics.
- CPU/memory on `payment-api` — rises only mildly (34% -> 48%), not
  resource-exhaustion territory.
- Any Postgres-wide or third-party-gateway outage — `postgres-notifications`
  and `checkout-api` stay healthy, and (once the real API tools exist) the
  Stripe status check should come back green.

## Confidence and evidence expectations

A reasonable agent should reach **high confidence (~0.85-0.95)**, because:
- the timing correlation (deploy -> pool climb -> errors) is tight,
- the pool metrics show the specific mechanism (connections not idling back down),
- the trace data confirms *where* time is lost (waiting for a connection, not the query),
- and the commit diff area (`gateway_client.py`) matches the failure mode.

It should **not** claim 1.0 confidence: nothing in the data is a direct
"here is the leaked-connection stack trace" proof — it's strong correlated
evidence across five independent sources, not a certainty. This is
deliberate, so later evaluation can check that the agent doesn't overstate
confidence from correlation alone.
