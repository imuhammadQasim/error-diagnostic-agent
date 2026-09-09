import json

import httpx
from langchain.tools import tool

from app.config import get_settings


@tool
def check_github_status() -> str:
    """Check GitHub's real-time system status (api.githubstatus.com).

    Use this to rule out "the deploy pipeline's provider was down" as a
    contributing cause - our deployments are triggered through GitHub, so a
    GitHub-wide incident could plausibly explain a bad or stuck deploy.
    This only reports GitHub's *current* status, not history for a past
    timestamp, so it is only useful when the investigation is happening
    close to the incident time.
    """
    settings = get_settings()
    try:
        response = httpx.get(settings.github_status_url, timeout=settings.external_api_timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return json.dumps({
            "source": "githubstatus.com (real API)",
            "indicator": data["status"]["indicator"],
            "description": data["status"]["description"],
            "checked_at": data["page"]["updated_at"],
        })
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        return json.dumps({
            "source": "githubstatus.com (real API)",
            "error": f"Could not reach GitHub status API: {exc}",
            "note": "Treat GitHub's status as unknown, not as healthy - do not assume no issue.",
        })


@tool
def convert_time_to_utc(local_datetime: str, source_timezone: str) -> str:
    """Convert a local date/time to UTC using a real timezone-conversion API (timeapi.io).

    Use this when an incident report gives a time without saying it's
    already UTC (our logs/metrics/traces timestamps are all UTC), so you
    can correctly bound `since`/`until` filters on the other tools instead
    of guessing.

    Args:
        local_datetime: Local date and time as "YYYY-MM-DD HH:MM:SS", e.g. "2026-09-09 06:30:00".
        source_timezone: IANA timezone name, e.g. "America/New_York", "Asia/Karachi", "UTC".
    """
    settings = get_settings()
    try:
        response = httpx.post(
            f"{settings.time_api_base_url}/conversion/converttimezone",
            json={
                "fromTimeZone": source_timezone,
                "dateTime": local_datetime,
                "toTimeZone": "UTC",
                "dstAmbiguity": "",
            },
            timeout=settings.external_api_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        result = data["conversionResult"]
        return json.dumps({
            "source": "timeapi.io (real API)",
            "input": {"local_datetime": local_datetime, "source_timezone": source_timezone},
            "utc_datetime": result["dateTime"] + "Z",
        })
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        return json.dumps({
            "source": "timeapi.io (real API)",
            "error": f"Could not convert time: {exc}",
            "note": "Do not guess a UTC time - ask for clarification or proceed without a precise time bound.",
        })
