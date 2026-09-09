"""The LangChain investigation agent: decides which tools to call and why."""

from app.agents.investigation_agent import build_agent, get_agent

__all__ = ["build_agent", "get_agent"]
