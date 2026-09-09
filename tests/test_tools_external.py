import json

import httpx
import respx

from app.config import get_settings
from app.tools.external_tools import check_github_status, convert_time_to_utc

settings = get_settings()


@respx.mock
def test_check_github_status_success():
    respx.get(settings.github_status_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "page": {"updated_at": "2026-09-09T10:00:00Z"},
                "status": {"indicator": "none", "description": "All Systems Operational"},
            },
        )
    )
    raw = check_github_status.invoke({})
    data = json.loads(raw)
    assert data["indicator"] == "none"
    assert "error" not in data


@respx.mock
def test_check_github_status_handles_api_failure_without_raising():
    respx.get(settings.github_status_url).mock(return_value=httpx.Response(500))
    raw = check_github_status.invoke({})
    data = json.loads(raw)
    assert "error" in data


@respx.mock
def test_convert_time_to_utc_success():
    respx.post(f"{settings.time_api_base_url}/conversion/converttimezone").mock(
        return_value=httpx.Response(
            200,
            json={
                "fromTimezone": "America/New_York",
                "fromDateTime": "2026-09-09T06:30:00",
                "toTimeZone": "UTC",
                "conversionResult": {"dateTime": "2026-09-09T10:30:00"},
            },
        )
    )
    raw = convert_time_to_utc.invoke({
        "local_datetime": "2026-09-09 06:30:00",
        "source_timezone": "America/New_York",
    })
    data = json.loads(raw)
    assert data["utc_datetime"] == "2026-09-09T10:30:00Z"


@respx.mock
def test_convert_time_to_utc_handles_network_error_without_raising():
    respx.post(f"{settings.time_api_base_url}/conversion/converttimezone").mock(
        side_effect=httpx.ConnectTimeout
    )
    raw = convert_time_to_utc.invoke({
        "local_datetime": "2026-09-09 06:30:00",
        "source_timezone": "America/New_York",
    })
    data = json.loads(raw)
    assert "error" in data
