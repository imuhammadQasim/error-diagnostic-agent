from typing import Callable

from langgraph.errors import GraphRecursionError

from app.agents import get_agent
from app.config import get_settings
from app.schemas import IncidentReport


class IncidentInvestigationError(Exception):
    """Base class for investigation failures the API layer maps to HTTP responses."""


class InvestigationTimedOutError(IncidentInvestigationError):
    """The agent used its full tool-call budget without reaching a conclusion."""


class LLMProviderError(IncidentInvestigationError):
    """The call to the configured LLM provider itself failed (auth, rate limit, connectivity, ...)."""


class InvalidReportError(IncidentInvestigationError):
    """The agent finished but did not produce a schema-valid incident report."""


def _provider_error_handlers(provider: str) -> list[tuple[Callable[[Exception], bool], str]]:
    """Map the active provider SDK's exceptions to a user-facing message.

    Each provider (Anthropic, Groq, Gemini) raises its own exception
    hierarchy, so this is looked up based on the active LLM_PROVIDER rather
    than imported unconditionally - keeps a missing provider package from
    breaking the other two. List order matters: more specific predicates
    must come before the broad catch-all for that provider, since
    `investigate()` below raises on the first match.
    """
    if provider == "anthropic":
        import anthropic

        return [
            (lambda exc: isinstance(exc, anthropic.AuthenticationError), "Anthropic rejected the API key - check ANTHROPIC_API_KEY."),
            (lambda exc: isinstance(exc, anthropic.RateLimitError), "Anthropic rate limit exceeded - try again shortly."),
            (lambda exc: isinstance(exc, anthropic.APIConnectionError), "Could not reach the Anthropic API."),
            (lambda exc: isinstance(exc, anthropic.APIStatusError), "Anthropic API error: {exc}"),
        ]
    if provider == "groq":
        import groq

        return [
            (lambda exc: isinstance(exc, groq.AuthenticationError), "Groq rejected the API key - check GROQ_API_KEY."),
            (lambda exc: isinstance(exc, groq.RateLimitError), "Groq rate limit exceeded - try again shortly."),
            (lambda exc: isinstance(exc, groq.APIConnectionError), "Could not reach the Groq API."),
            (lambda exc: isinstance(exc, groq.APIStatusError), "Groq API error: {exc}"),
        ]
    if provider == "gemini":
        # google-genai reports errors as ClientError/ServerError, both
        # carrying the HTTP status in `.code` rather than distinct
        # exception types per status - so auth/rate-limit are distinguished
        # by code, not by isinstance.
        from google.genai import errors as gemini_errors

        return [
            (lambda exc: isinstance(exc, gemini_errors.APIError) and exc.code in (401, 403), "Gemini rejected the API key - check GEMINI_API_KEY."),
            (lambda exc: isinstance(exc, gemini_errors.APIError) and exc.code == 429, "Gemini rate limit exceeded - try again shortly."),
            (lambda exc: isinstance(exc, gemini_errors.ServerError), "Could not reach the Gemini API."),
            (lambda exc: isinstance(exc, gemini_errors.APIError), "Gemini API error: {exc}"),
        ]
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")


def investigate(description: str) -> IncidentReport:
    """Run the investigation agent on one incident description and return its report.

    This is the one place that knows how to invoke the agent - the API
    route only calls this function. It exists so error handling (a bad API
    key, a runaway agent, a malformed final answer) lives in one spot
    instead of being duplicated in every route that might someday call
    the agent.
    """
    settings = get_settings()
    agent = get_agent()

    # LangGraph's recursion_limit counts graph steps, not tool calls: each
    # tool call round-trip is a model step plus a tool step. Double the
    # configured tool-call budget and add headroom for the model's final
    # (non-tool-call) response.
    recursion_limit = settings.agent_max_iterations * 2 + 2

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": description}]},
            config={"recursion_limit": recursion_limit},
        )
    except GraphRecursionError as exc:
        raise InvestigationTimedOutError(
            f"Investigation did not conclude within {settings.agent_max_iterations} tool-call steps."
        ) from exc
    except Exception as exc:
        for matches, message in _provider_error_handlers(settings.llm_provider):
            if matches(exc):
                raise LLMProviderError(message.format(exc=exc)) from exc
        raise

    report = result.get("structured_response")
    if report is None:
        raise InvalidReportError("The agent did not produce a structured incident report.")
    return report
