from pydantic import BaseModel, Field


class IncidentInvestigateRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Payment API started returning 500 errors around 10:30 AM.",
    )


class Evidence(BaseModel):
    source: str = Field(..., description="Tool/data source this came from, e.g. 'logs', 'database_metrics', 'git_commits'.")
    finding: str = Field(..., description="The specific, concrete fact observed - not an inference.")
    timestamp: str | None = Field(None, description="ISO 8601 UTC timestamp this evidence relates to, if applicable.")


class IncidentReport(BaseModel):
    """The agent's final, structured output.

    This is passed to `create_agent(..., response_format=IncidentReport)`,
    so LangChain validates the model's final answer against this schema
    before it ever reaches the API layer - if the LLM's output doesn't fit,
    the service layer sees a validation error instead of silently shipping
    malformed data.
    """

    incident_summary: str = Field(..., description="One or two sentences describing what happened.")
    affected_service: str | None = Field(None, description="The service identified as affected, if any.")
    affected_endpoint: str | None = Field(None, description="The specific endpoint identified as affected, if any.")
    root_cause: str = Field(..., description="The most likely root cause, grounded in the gathered evidence.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the root cause, 0-1.")
    evidence: list[Evidence] = Field(default_factory=list, description="Concrete facts from tools that support the conclusion.")
    contributing_factors: list[str] = Field(default_factory=list, description="Secondary factors that worsened the incident but are not the root cause.")
    recommended_actions: list[str] = Field(default_factory=list, description="Concrete next steps for the on-call engineer.")
    requires_human_review: bool = Field(..., description="True if confidence is low, evidence is conflicting, or a tool failed in a way that could hide the real cause.")
