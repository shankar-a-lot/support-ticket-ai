import sqlite3
import pandas as pd
from pathlib import Path

# Set paths to data files
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "tickets.db"
CSV_PATH = BASE_DIR / "data" / "support_tickets.csv"

def init_db():
    """Reads support_tickets.csv and loads it into an SQLite table named 'tickets'."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}. Please place support_tickets.csv in the data/ folder.")
    
    df = pd.read_csv(CSV_PATH)
    
    # Standardize the date format
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Connect and save to SQLite
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("tickets", conn, index=False, if_exists="replace")
    conn.close()
    print("Database initialized successfully at:", DB_PATH)

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def run_query(sql: str):
    """Executes a SELECT query and returns rows as a list of dictionaries."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()