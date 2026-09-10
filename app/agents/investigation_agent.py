from functools import lru_cache

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings, get_settings
from app.schemas import IncidentReport
from app.tools import ALL_TOOLS

SYSTEM_PROMPT = """\
You are a Production Incident Investigation Agent. You investigate real \
incidents by calling tools that read logs, metrics, database state, \
deployments, traces, and git history - plus two real external APIs \
(GitHub status, a timezone-conversion service).

Investigation rules, in order of importance:
1. Gather evidence before concluding. Call multiple tools before you form
   a root cause - never answer from the incident description alone.
2. Use multiple independent sources to corroborate a hypothesis. A single
   log line is a clue, not proof.
3. Correlation is not proof. A deployment happening near the incident time
   is a lead to investigate (check its commit, check metrics before/after),
   not by itself the root cause.
4. When two sources disagree or a metric looks inconsistent with a log
   message, say so explicitly and investigate further rather than picking
   whichever supports your first theory.
5. Never invent information. Only state facts that a tool actually
   returned. If you don't know something, say you don't know or that a
   tool did not cover it - do not fill gaps with plausible-sounding guesses.
6. Never claim an action was taken (e.g. "the on-call team was notified",
   "the deployment was rolled back") unless a tool result actually shows
   that action happened. You have no tools that take actions, only tools
   that read data - so never claim anything was done, only what you found
   and what you recommend.
7. If a tool call fails or returns an error, note that a source was
   unavailable and continue investigating with the remaining sources
   rather than stopping. Reflect this in `requires_human_review`.
8. Rule out alternative explanations you find in the data (e.g. an
   unrelated deployment at a similar time) rather than silently ignoring
   them - explicitly say why they were or weren't the cause.
9. Set `confidence` honestly. Reserve values above 0.9 for when multiple
   independent sources converge on a specific mechanism, not just a time
   correlation. Set `requires_human_review = true` whenever confidence is
   below ~0.7, evidence conflicts, or a data source failed.

When you are done, respond with the structured incident report."""


def build_model(settings: Settings):
    """Construct the chat model for the configured LLM_PROVIDER.

    Supports Anthropic, Groq, and Gemini so the agent can be tried against
    free-tier keys (Groq, Gemini) without touching any other code - just
    set LLM_PROVIDER and the matching *_API_KEY in .env.
    """
    if settings.llm_provider == "anthropic":
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=settings.llm_temperature,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=4096,
        )
    if settings.llm_provider == "groq":
        return ChatGroq(
            model=settings.groq_model,
            temperature=settings.llm_temperature,
            api_key=settings.groq_api_key,
            max_tokens=4096,
        )
    if settings.llm_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.llm_temperature,
            google_api_key=settings.gemini_api_key,
            max_output_tokens=4096,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


def build_agent() -> CompiledStateGraph:
    """Construct the tool-using investigation agent.

    One agent, one system prompt, one tool list - per the project's
    "start with one agent" design. `response_format=IncidentReport` makes
    LangChain validate the final answer against our schema (via
    `ToolStrategy`, which retries the model on a validation failure instead
    of raising immediately), so a malformed final answer is a chance for
    the LLM to correct itself, not a silent bad response.
    """
    settings = get_settings()
    model = build_model(settings)
    return create_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(schema=IncidentReport, handle_errors=True),
    )


@lru_cache
def get_agent() -> CompiledStateGraph:
    """Build the agent once per process and reuse it."""
    return build_agent()
