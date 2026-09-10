import anthropic
import groq
import pytest
from google.genai import errors as gemini_errors
from langgraph.errors import GraphRecursionError

from app.config import Settings
from app.schemas import IncidentReport
from app.services import incident_service


class _StubAgent:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def invoke(self, *args, **kwargs):
        if self._exc:
            raise self._exc
        return self._result


def _fake_report() -> IncidentReport:
    return IncidentReport(
        incident_summary="summary",
        root_cause="cause",
        confidence=0.8,
        requires_human_review=False,
    )


def test_investigate_returns_structured_response(mocker):
    mocker.patch.object(incident_service, "get_agent", return_value=_StubAgent(result={"structured_response": _fake_report()}))
    report = incident_service.investigate("Payment API started returning 500 errors around 10:30 AM.")
    assert report.root_cause == "cause"


def test_investigate_raises_invalid_report_when_missing_structured_response(mocker):
    mocker.patch.object(incident_service, "get_agent", return_value=_StubAgent(result={"messages": []}))
    with pytest.raises(incident_service.InvalidReportError):
        incident_service.investigate("Payment API started returning 500 errors around 10:30 AM.")


def test_investigate_wraps_recursion_error(mocker):
    mocker.patch.object(incident_service, "get_agent", return_value=_StubAgent(exc=GraphRecursionError()))
    with pytest.raises(incident_service.InvestigationTimedOutError):
        incident_service.investigate("Payment API started returning 500 errors around 10:30 AM.")


@pytest.mark.parametrize(
    "provider, make_exc",
    [
        (
            "anthropic",
            lambda mocker: anthropic.AuthenticationError(
                "invalid key", response=mocker.Mock(status_code=401, headers={}), body=None
            ),
        ),
        (
            "groq",
            lambda mocker: groq.AuthenticationError(
                "invalid key", response=mocker.Mock(status_code=401, headers={}), body=None
            ),
        ),
        (
            "gemini",
            lambda mocker: gemini_errors.ClientError(401, {"message": "invalid key"}),
        ),
    ],
)
def test_investigate_wraps_authentication_error(mocker, provider, make_exc):
    exc = make_exc(mocker)
    mocker.patch.object(incident_service, "get_settings", return_value=Settings(llm_provider=provider))
    mocker.patch.object(incident_service, "get_agent", return_value=_StubAgent(exc=exc))
    with pytest.raises(incident_service.LLMProviderError):
        incident_service.investigate("Payment API started returning 500 errors around 10:30 AM.")
