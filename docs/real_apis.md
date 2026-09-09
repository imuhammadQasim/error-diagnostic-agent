# Real API Integrations

Two tools call live public APIs instead of static JSON, to demonstrate the
full `Agent -> Tool -> HTTP API -> Response -> Agent` path for real.

## 1. GitHub status - `check_github_status` (`app/tools/external_tools.py`)

`GET https://www.githubstatus.com/api/v2/status.json` - free, no auth,
Atlassian Statuspage-backed, effectively never down.

**Why this instead of Stripe**, which would fit the "payment" theme better:
I checked `https://status.stripe.com/api/v2/status.json` before building
this and it now 404s - Stripe moved off the public Statuspage JSON feed.
Rather than build a tool against an API that doesn't actually exist,
I substituted GitHub's status API, which is the same kind of check (is an
external dependency the incident could plausibly be blamed on actually
having an outage) and is verified reliable. Framed narratively: our
deploys go through GitHub, so a GitHub-wide incident is a legitimate
alternative hypothesis worth ruling out.

**Real-world equivalent later:** the status API of whatever payment
gateway / cloud provider / CI platform you actually depend on.

## 2. Timezone conversion - `convert_time_to_utc` (`app/tools/external_tools.py`)

`POST https://timeapi.io/api/conversion/converttimezone` - free, no auth.

All of this project's static data (logs, metrics, traces, ...) is
timestamped in UTC. A real incident report ("around 10:30 AM") rarely says
which timezone. This tool lets the agent convert a stated local time to UTC
before it uses `since`/`until` filters on the other tools, instead of
guessing or silently assuming UTC.

One format quirk worth knowing if you touch this tool: the API's `dateTime`
field must be `"YYYY-MM-DD HH:MM:SS"` (space separator) - an ISO 8601 `T`
separator is silently rejected with `"Invalid DateTime format."`. Verified
by hand against the live API before writing this tool, not guessed.

**Real-world equivalent later:** you would likely drop this entirely once
your logging/metrics stack normalizes to UTC everywhere (most do), or
replace it with whatever locale library your team standardizes on.

## Failure handling

Both tools catch their own exceptions (`httpx.HTTPError`, bad/missing JSON
fields) and return a JSON string describing the failure instead of raising.
This matters for two reasons:

- LangGraph's `ToolNode` already converts an uncaught exception into an
  error message the agent can see - but a raw stack trace is a worse signal
  than a clean `{"error": "..."}` the agent can reason about and mention in
  `requires_human_review`.
- The system prompt explicitly tells the agent to treat a failed source as
  "unknown", not as "healthy" - see `app/agents/investigation_agent.py`.
