import pandas as pd
from src.db import get_connection

def get_sla_breaches() -> list[dict]:
    """
    Rule-based SLA Breach:
    Flags high-urgency tickets (High or Critical) that are not resolved yet.
    """
    conn = get_connection()
    query = """
        SELECT ticket_id, created_at, category, priority, status, agent_id, issue_summary
        FROM tickets
        WHERE status IN ('Open', 'Escalated')
          AND priority IN ('High', 'Critical')
        ORDER BY created_at ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient="records")

def get_resolution_outliers() -> list[dict]:
    """
    Statistical Outliers (IQR Method):
    Flags resolved tickets whose resolution_time_hrs exceeds Q3 + 1.5 * IQR per category.
    """
    conn = get_connection()
    query = """
        SELECT ticket_id, category, priority, resolution_time_hrs, agent_id, issue_summary
        FROM tickets
        WHERE status = 'Resolved' AND resolution_time_hrs IS NOT NULL;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return []

    outliers = []
    # Compute IQR per category so Technical doesn't skew Billing/General thresholds
    for category, group in df.groupby("category"):
        q1 = group["resolution_time_hrs"].quantile(0.25)
        q3 = group["resolution_time_hrs"].quantile(0.75)
        iqr = q3 - q1
        cutoff = q3 + (1.5 * iqr)

        flagged = group[group["resolution_time_hrs"] > cutoff].copy()
        flagged["iqr_cutoff_hrs"] = round(cutoff, 2)
        outliers.append(flagged)

    if not outliers:
        return []

    outlier_df = pd.concat(outliers)
    return outlier_df.to_dict(orient="records")

def fetch_anomalies_summary() -> dict:
    """Combines both SLA breaches and outlier tickets into a unified response."""
    return {
        "sla_breaches": get_sla_breaches(),
        "resolution_outliers": get_resolution_outliers()
    }

if __name__ == "__main__":
    result = fetch_anomalies_summary()
    print(f"Total SLA Breaches found: {len(result['sla_breaches'])}")
    print(f"Total Resolution Outliers found: {len(result['resolution_outliers'])}")