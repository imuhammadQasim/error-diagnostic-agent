from fastapi import APIRouter, HTTPException

from app.schemas import IncidentInvestigateRequest, IncidentReport
from app.services import (
    IncidentInvestigationError,
    InvalidReportError,
    InvestigationTimedOutError,
    LLMProviderError,
    investigate,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/investigate")
def investigate_incident(request: IncidentInvestigateRequest) -> IncidentReport:
    """Run the investigation agent on a free-text incident description.

    Route stays thin: validate the request (Pydantic already did that),
    call the service, translate known failure modes to HTTP responses.
    """
    try:
        return investigate(request.description)
    except InvestigationTimedOutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except InvalidReportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IncidentInvestigationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
