from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Evidence, IncidentReport
from app.services import InvestigationTimedOutError, LLMProviderError

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_investigate_endpoint_rejects_short_description():
    response = client.post("/api/v1/incidents/investigate", json={"description": "500s"})
    assert response.status_code == 422


def test_investigate_endpoint_returns_report(mocker):
    fake_report = IncidentReport(
        incident_summary="Payment API returned 500s due to DB pool exhaustion.",
        affected_service="payment-api",
        affected_endpoint="/api/payments/charge",
        root_cause="Connection pool exhaustion after the v2.4.1 deploy.",
        confidence=0.9,
        evidence=[Evidence(source="logs", finding="Pool exhausted error at 10:26:19Z", timestamp="2026-09-09T10:26:19Z")],
        contributing_factors=["Client-side retry storm"],
        recommended_actions=["Roll back v2.4.1", "Fix connection release in gateway_client retry path"],
        requires_human_review=False,
    )
    mocker.patch("app.api.v1.incidents.investigate", return_value=fake_report)

    response = client.post(
        "/api/v1/incidents/investigate",
        json={"description": "Payment API started returning 500 errors around 10:30 AM."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["affected_service"] == "payment-api"
    assert body["confidence"] == 0.9


def test_investigate_endpoint_maps_timeout_to_504(mocker):
    mocker.patch(
        "app.api.v1.incidents.investigate",
        side_effect=InvestigationTimedOutError("hit tool-call limit"),
    )
    response = client.post(
        "/api/v1/incidents/investigate",
        json={"description": "Payment API started returning 500 errors around 10:30 AM."},
    )
    assert response.status_code == 504


def test_investigate_endpoint_maps_llm_provider_error_to_502(mocker):
    mocker.patch(
        "app.api.v1.incidents.investigate",
        side_effect=LLMProviderError("bad key"),
    )
    response = client.post(
        "/api/v1/incidents/investigate",
        json={"description": "Payment API started returning 500 errors around 10:30 AM."},
    )
    assert response.status_code == 502
