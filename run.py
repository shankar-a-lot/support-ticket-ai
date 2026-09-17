import subprocess
import sys
import time

def main():
    print("==================================================")
    print("  Booting Support Ticket AI Engine System")
    print("==================================================")

    # 1. Start FastAPI Backend (port 8000)
    print("[1/2] Starting FastAPI server on http://localhost:8000...")
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api:app", "--port", "8000"
    ])

    # Wait 2 seconds for database initialization & API startup
    time.sleep(2)

    # 2. Start Streamlit UI (port 8501)
    print("[2/2] Starting Streamlit interface on http://localhost:8501...")
    frontend = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"
    ])

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nGracefully shutting down services...")
        backend.terminate()
        frontend.terminate()
        print("Done.")

if __name__ == "__main__":
    main()