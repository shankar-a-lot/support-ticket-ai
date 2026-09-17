import os
import re
from dotenv import load_dotenv
from groq import Groq
from src.db import run_query

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment or .env file.")

client = Groq(api_key=api_key)

DB_SCHEMA = """
Table: tickets
Columns:
- ticket_id: TEXT (Primary key, e.g. 'TKT-001')
- created_at: TEXT (Format: 'YYYY-MM-DD HH:MM:SS')
- category: TEXT (Allowed values: 'Billing', 'Technical', 'General')
- priority: TEXT (Allowed values: 'Low', 'Medium', 'High', 'Critical')
- status: TEXT (Allowed values: 'Open', 'Resolved', 'Escalated')
- response_time_hrs: REAL
- resolution_time_hrs: REAL (NULL if not resolved)
- agent_id: TEXT (e.g. 'AGT-01')
- customer_rating: INTEGER (1 to 5, NULL if not resolved)
- issue_summary: TEXT
"""

def clean_sql(raw_sql: str) -> str:
    """Removes markdown code fences if the LLM includes them."""
    cleaned = re.sub(r"```sql", "", raw_sql, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()

def validate_sql(sql: str):
    """Safety guardrail: Ensure query is read-only (SELECT)."""
    sql_upper = sql.upper().strip()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        raise ValueError("Security violation: Only SELECT queries are permitted.")
    for forbidden in ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER "]:
        if forbidden in sql_upper:
            raise ValueError(f"Security violation: Statement contains forbidden operation '{forbidden.strip()}'.")

def generate_sql(question: str, error_context: str = None) -> str:
    """Converts a user question into a valid SQLite SELECT query."""
    system_prompt = f"""
    You are an expert SQLite developer. Convert user questions into clean SQLite SELECT queries.
    Strict Rules:
    1. Output ONLY the raw SQL query. No explanations, no markdown ticks.
    2. Use the exact table name: tickets.
    3. Unresolved tickets have status IN ('Open', 'Escalated') or resolution_time_hrs IS NULL.
    4. For ranking/top/lowest, use ORDER BY with LIMIT.
    
    Database Schema:
    {DB_SCHEMA}
    """
    
    user_prompt = f"Question: {question}"
    if error_context:
        user_prompt += f"\nPrevious attempt failed with error: {error_context}. Please fix it."

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    return clean_sql(response.choices[0].message.content)

def synthesize_answer(question: str, data: list) -> str:
    """Uses LLM to summarize raw SQL table output into clear natural language."""
    # Truncate large lists to 10 rows for clean summary
    data_sample = data[:10] if data else "No records found matching criteria."
    prompt = f"""
    Question: {question}
    SQL Execution Result: {data_sample}

    Instructions:
    Provide a concise, direct 1-to-2 sentence answer for a support manager based strictly on the result.
    """
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def process_nl_query(question: str) -> dict:
    """
    Full pipeline: Question -> Text-to-SQL -> Execution -> Self-Healing Retry -> Plain English
    """
    sql = generate_sql(question)
    error = None

    # Self-healing retry loop (tries twice if SQL has a syntax issue)
    for attempt in range(2):
        try:
            validate_sql(sql)
            rows = run_query(sql)
            answer = synthesize_answer(question, rows)
            return {
                "question": question,
                "sql": sql,
                "data": rows,
                "answer": answer
            }
        except Exception as e:
            error = str(e)
            sql = generate_sql(question, error_context=error)

    # Final execution after retries
    validate_sql(sql)
    rows = run_query(sql)
    answer = synthesize_answer(question, rows)
    return {
        "question": question,
        "sql": sql,
        "data": rows,
        "answer": answer
    }

if __name__ == "__main__":
    test_q = "How many tickets are currently open?"
    print(f"Testing Question: '{test_q}'...")
    res = process_nl_query(test_q)
    print("\n--- Result ---")
    print("Generated SQL:", res["sql"])
    print("Raw Data:", res["data"])
    print("Final Answer:", res["answer"])