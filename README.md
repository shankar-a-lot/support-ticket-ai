# Support Ticket AI Intelligence Engine

An end-to-end, LLM-powered support ticket analytics and anomaly detection system built with FastAPI, SQLite, Streamlit, and Groq Cloud.

---

## Overview

This project implements the technical assessment requirements for the AI Engineer role at DOTMappers IT Pvt. Ltd. It provides an automated system capable of ingesting customer support ticket records, executing natural language queries via text-to-SQL, performing operational anomaly detection, and exposing interactive interfaces through a REST API and a web dashboard.

---

## Key Engineering Decisions

* **In-Memory / Local SQLite**: Rather than executing raw Python eval() calls on Pandas (a severe security risk), user questions are compiled into standardized SQL and executed within a read-only database layer.
* **SQL Guardrails**: The engine validates that every generated statement begins strictly with SELECT or WITH, actively blocking modification operations (DROP, DELETE, UPDATE, INSERT).
* **Self-Healing SQL Loop**: If a generated query encounters a syntax or column error, the error traceback is intercepted and passed back to the LLM for automatic re-correction without crashing the API.
* **Category-Specific Outlier Analysis**: Outliers in resolution times are calculated via the Interquartile Range (IQR = Q3 - Q1, threshold > Q3 + 1.5 * IQR) isolated by ticket category (Billing, Technical, General), preventing cross-domain distribution skew.

---

## Dataset

* **Source File**: `data/support_tickets.csv` (500 records)
* **Columns**:
  * `ticket_id`: Unique identifier
  * `created_at`: Ticket creation timestamp
  * `category`: Billing, Technical, or General
  * `priority`: Low, Medium, High, or Critical
  * `status`: Open, Resolved, or Escalated
  * `response_time_hrs`: Elapsed time to initial response
  * `resolution_time_hrs`: Total resolution duration (null if unresolved)
  * `agent_id`: Assigned support engineer
  * `customer_rating`: Score between 1 and 5 (null if unresolved)[cite: 2]
  * `issue_summary`: Natural language description of reported issue[cite: 2]

---

## Setup & Installation

### Prerequisites

* Python 3.10+[cite: 2]
* Free Groq API Key (from console.groq.com)[cite: 2]

### Installation Steps

1. Clone the repository and enter the directory:

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd support-ticket-ai
Create and activate a virtual environment:Bashpython -m venv venv
On Windows:DOSvenv\Scripts\activate
On Linux/macOS:Bashsource venv/bin/activate
Install project dependencies:Bashpip install -r requirements.txt
Set up environment variables:Create a .env file in the root folder:Code snippetGROQ_API_KEY=your_groq_api_key_here
Running the System (Single Command)Start both the FastAPI backend and Streamlit UI simultaneously with one command[cite: 2]:Bashpython run.py
Interactive Web UI: http://localhost:8501[cite: 2]FastAPI Docs / Swagger: http://localhost:8000/docs[cite: 2]REST API SpecificationMethodEndpointDescriptionGET/healthVerifies database connectivity and data record volume (500 rows)[cite: 2].POST/queryConverts natural language input to SQL, executes it, and returns structured data + natural language answer[cite: 2].GET/anomaliesReturns list of unresolved SLA breaches and IQR resolution time outliers[cite: 2].Sample Queries & OutputsQuery: "How many tickets are currently open?"[cite: 2]Generated SQL: SELECT COUNT(*) FROM tickets WHERE status = 'Open';  Output: "There are currently 111 tickets open."Query: "Which agent has the lowest average customer rating?"[cite: 2]Generated SQL: SELECT agent_id, AVG(customer_rating) AS avg_rating FROM tickets WHERE customer_rating IS NOT NULL GROUP BY agent_id ORDER BY avg_rating ASC LIMIT 1;  Output: "Agent AGT-08 has the lowest average customer rating at approximately 3.25."Query: "Show me all Critical tickets not resolved within 12 hours."[cite: 2]Generated SQL: SELECT * FROM tickets WHERE priority = 'Critical' AND (resolution_time_hrs > 12 OR (status != 'Resolved'));[cite: 1, 2]Query: "What is the average customer rating for Technical category tickets?"[cite: 2]Generated SQL: SELECT AVG(customer_rating) AS avg_rating FROM tickets WHERE category = 'Technical' AND customer_rating IS NOT NULL;[cite: 1, 2]Automated TestingExecute the test suite to verify endpoints and query execution[cite: 2]:Bashpython -m pytest tests/test_api.py
Known Limitations & Production RoadmapRate Limits: Currently uses the Groq free tier; a production setup would route to self-hosted Ollama instances or an enterprise API gateway[cite: 2].Caching Layer: Frequent aggregate queries can be cached with Redis to reduce repeated LLM inference latency.Complex Temporal Filtering: Pre-processing human expressions like "last fiscal quarter" into explicit timestamp bounds before prompt delivery.