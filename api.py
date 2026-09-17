from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.db import init_db, run_query
from src.llm_engine import process_nl_query
from src.anomaly_detector import fetch_anomalies_summary

app = FastAPI(
    title="Support Ticket AI Engine API",
    description="REST API for natural language querying and operational anomaly detection on support tickets."
)

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup():
    """Ensure database is loaded and up-to-date on boot."""
    init_db()

@app.get("/health")
def health():
    """Endpoint 1: Health check verifying service status and data volume."""
    try:
        res = run_query("SELECT COUNT(*) AS total FROM tickets;")
        total_rows = res[0]["total"]
        return {
            "status": "healthy",
            "total_records": total_rows,
            "database": "tickets.db connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database check failed: {str(e)}")

@app.post("/query")
def handle_query(payload: QueryRequest):
    """Endpoint 2: Handles natural language queries."""
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="The 'question' field cannot be empty.")
    try:
        result = process_nl_query(payload.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")

@app.get("/anomalies")
def handle_anomalies():
    """Endpoint 3: Returns SLA breaches and statistical resolution outliers."""
    try:
        anomalies = fetch_anomalies_summary()
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection error: {str(e)}")