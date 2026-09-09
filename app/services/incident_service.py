import anthropic
from langgraph.errors import GraphRecursionError

from app.agents import get_agent
from app.config import get_settings
from app.schemas import IncidentReport


class IncidentInvestigationError(Exception):
    """Base class for investigation failures the API layer maps to HTTP responses."""


class InvestigationTimedOutError(IncidentInvestigationError):
    """The agent used its full tool-call budget without reaching a conclusion."""


class LLMProviderError(IncidentInvestigationError):
    """The call to Anthropic itself failed (auth, rate limit, connectivity, ...)."""


class InvalidReportError(IncidentInvestigationError):
    """The agent finished but did not produce a schema-valid incident report."""


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
    except anthropic.AuthenticationError as exc:
        raise LLMProviderError("Anthropic rejected the API key - check ANTHROPIC_API_KEY.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMProviderError("Anthropic rate limit exceeded - try again shortly.") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMProviderError("Could not reach the Anthropic API.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMProviderError(f"Anthropic API error: {exc}") from exc

    report = result.get("structured_response")
    if report is None:
        raise InvalidReportError("The agent did not produce a structured incident report.")
    return report
