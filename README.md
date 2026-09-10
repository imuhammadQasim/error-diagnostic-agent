# Production Incident Investigation Agent

A LangChain tool-using agent that investigates production incidents (e.g.
"Payment API started returning 500 errors around 10:30 AM") by calling
tools that read logs, metrics, database state, deployments, traces, and git
history - plus two real external APIs - and returns a structured,
evidence-backed root-cause report.

```
POST /api/v1/incidents/investigate
{"description": "Payment API started returning 500 errors around 10:30 AM."}
```

## What it does

The bundled dataset (`data/*.json`) encodes one coherent, realistic
incident: a `payment-api` deploy leaks a database connection on every retry,
the connection pool exhausts, and requests start failing with HTTP 500. Two
deliberate red herrings are included (an unrelated deploy to a different
service at almost the same time; a mild, non-causal CPU bump) so the agent
has to actually distinguish causation from correlation rather than pattern-match
on timing. Full ground truth: [`docs/incident_scenario.md`](docs/incident_scenario.md).

Given the incident description above, the agent should conclude something
close to: root cause = the `v2.4.1` deploy's connection leak; contributing
factor = client-side retry storm; not the notification-service deploy or
CPU load - with high but not absolute confidence, since the evidence is
strong correlation across five sources, not a smoking-gun stack trace.

## Architecture

```
FastAPI route (thin)
  -> app/services/incident_service.py   (invokes the agent, maps errors)
    -> app/agents/investigation_agent.py  (one LangChain agent, one system prompt)
      -> app/tools/*                       (what the LLM can call)
        -> app/repositories/*              (what each tool reads)
          -> data/*.json  |  live HTTP APIs
```

Each layer only knows about the one below it. A tool never reads a JSON
file directly - it calls a repository method. This is what makes "swap
static data for Datadog/Prometheus/etc. later" a repository-level change,
not a rewrite: the tool's function signature and docstring (what the LLM
sees) don't have to change at all. See **Swapping in real infrastructure**
below.

One agent, no LangGraph multi-agent graph, no human-in-the-loop yet - by
design, per the project's incremental scope. Those are documented as future
work, not implemented, so there's nothing speculative to maintain.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements-dev.txt   # includes requirements.txt + test tools
cp .env.example .env
```

Edit `.env`: set `LLM_PROVIDER` to `anthropic`, `groq`, or `gemini`, and fill
in the matching `*_API_KEY` (Groq and Gemini both have free-tier keys - get
one at console.groq.com/keys or aistudio.google.com/apikey; Anthropic keys
are at console.anthropic.com). Everything else has a working default.

## Running it

```bash
uvicorn app.main:app --reload
```

Then either:
- open **http://127.0.0.1:8000/docs** (interactive Swagger UI - "Try it out" on `/api/v1/incidents/investigate`), or
- `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/incidents/investigate \
  -H "Content-Type: application/json" \
  -d '{"description": "Payment API started returning 500 errors around 10:30 AM."}'
```

```bash
curl http://127.0.0.1:8000/api/v1/health
```

### Example response shape

```json
{
  "incident_summary": "payment-api began returning HTTP 500 on /api/payments/charge starting ~10:29 UTC.",
  "affected_service": "payment-api",
  "affected_endpoint": "/api/payments/charge",
  "root_cause": "The v2.4.1 deploy (commit abc123f, 'Add retry logic...') leaks a DB connection on each retry, exhausting the postgres-payments pool (20/20 connections in use by 10:26 UTC).",
  "confidence": 0.9,
  "evidence": [
    {"source": "deployments", "finding": "payment-api deployed v2.4.1 at 10:15:32Z, commit abc123f", "timestamp": "2026-09-09T10:15:32Z"},
    {"source": "database_metrics", "finding": "postgres-payments active_connections reached max_connections (20) by 10:26Z", "timestamp": "2026-09-09T10:26:00Z"},
    {"source": "traces", "finding": "trace-6659: db.acquire_connection took the full 30000ms timeout; the query itself never ran", "timestamp": "2026-09-09T10:29:02Z"}
  ],
  "contributing_factors": ["Client-side retries roughly tripled request volume once errors began (122/min -> 410/min)"],
  "recommended_actions": ["Roll back to v2.4.0", "Fix connection release in the gateway_client retry path before redeploying"],
  "requires_human_review": false
}
```

(Illustrative - the model produces its own wording each run; only the schema shape is fixed.)

## Running tests

```bash
pytest
```

Tests never call a real LLM provider API or make real network requests -
external HTTP calls are mocked with `respx`, and the agent/service tests
stub the LangGraph agent object directly. See `tests/`.

## LangSmith setup (optional)

LangSmith gives you a trace of every agent run: which tools it called, in
what order, with what arguments, how long each step took, and where a tool
failed.

1. Get an API key at smith.langchain.com.
2. In `.env`: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=<your key>`.
3. Run the app normally. Every `/investigate` call now shows up as a trace
   in your LangSmith project (`incident-investigation-agent` by default -
   change via `LANGSMITH_PROJECT`).

`app/main.py` is the only place this is wired: it copies the relevant
`Settings` fields into `os.environ` at startup, because LangSmith reads its
config from the environment rather than accepting it as a parameter.

## Real API integrations

Two tools call live public APIs (no auth, free, reliable) instead of
static JSON - `check_github_status` and `convert_time_to_utc`. Why these
two, and why not the more on-theme Stripe status API: [`docs/real_apis.md`](docs/real_apis.md).

## Swapping in real infrastructure later

Because tools depend on repositories and never touch `data/*.json`
directly, moving off static data is a repository-layer change:

| Static file | Real replacement | What changes |
|---|---|---|
| `logs.json` | Datadog / OpenTelemetry logs | New `LogsRepository` hitting the Datadog Logs API; same `get_logs(...)` signature |
| `metrics.json` | Prometheus / Datadog metrics | New `MetricsRepository` running a PromQL query; same `get_metrics(...)` signature |
| `database_metrics.json` | Live Postgres (`pg_stat_activity`) | New `DatabaseRepository` querying Postgres directly |
| `deployments.json` | Kubernetes / your CD tool | New `DeploymentsRepository` calling the k8s API or your CD provider's API |
| `traces.json` | OpenTelemetry / Jaeger | New `TracesRepository` querying your tracing backend |
| `git_commits.json` | GitHub API | New `GitRepository` calling `GET /repos/{owner}/{repo}/commits` |

In every case, the corresponding file in `app/tools/` and the agent's
system prompt stay the same (maybe update a docstring that describes valid
service names). That boundary is the point of the repository layer.

## What's not built yet (documented, not implemented)

- LangGraph multi-agent investigation, parallel tool calls, human-in-the-loop approval.
- Advanced state management / persisted conversation threads (`checkpointer` exists in LangChain 1.x and is trivial to add later - not wired in).
- A LangSmith evaluation dataset/run (`docs/` will hold this once built).
- Retry/backoff tuning on the two real API tools beyond the single request each currently makes.

## Project structure

```
app/
  api/v1/         FastAPI routes (thin - validate, call service, map errors to HTTP)
  agents/         The one LangChain agent + its system prompt
  tools/          What the LLM can call - one per data source, plus 2 real-API tools
  services/       Orchestrates the agent; owns error translation
  repositories/   Data access - the only layer that knows about data/*.json or HTTP
  schemas/        Pydantic request/response/report models
  config/         Typed settings, loaded from .env
data/             Six static JSON datasets, one coherent incident (see docs/incident_scenario.md)
tests/            Repository, tool, API, and service-layer tests
docs/             Design-decision notes
```
