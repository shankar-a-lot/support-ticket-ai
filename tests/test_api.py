import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_health_endpoint():
    """Verify system readiness and correct record loading."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_records"] == 500

def test_anomalies_endpoint():
    """Verify anomaly detection engine returns both SLA and outlier data."""
    response = client.get("/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "sla_breaches" in data
    assert "resolution_outliers" in data
    assert isinstance(data["sla_breaches"], list)
    assert isinstance(data["resolution_outliers"], list)

def test_nl_query_execution():
    """Verify that a sample natural language query executes through the LLM pipeline."""
    sample_payload = {"question": "How many tickets are currently open?"}
    response = client.post("/query", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "SELECT" in data["sql"].upper()
    assert "data" in data
    assert "answer" in data