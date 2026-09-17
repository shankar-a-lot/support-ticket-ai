import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Support Ticket Intelligence", layout="wide", page_icon="🎫")
st.title("🎫 Support Ticket AI Intelligence System")

tab_chat, tab_anomalies = st.tabs(["💬 Natural Language Query", "⚠️ Anomaly Detection Dashboard"])

# ----------------- TAB 1: Natural Language Query -----------------
with tab_chat:
    st.subheader("Query Ticket Data with Plain English")
    
    sample_queries = [
        "How many tickets are currently open?",
        "Which agent resolved the most tickets this month?",
        "Show me all Critical tickets not resolved within 12 hours.",
        "What is the average customer rating for Technical category tickets?",
        "Which agent has the lowest average customer rating?"
    ]
    
    selected_sample = st.selectbox("Select a benchmark sample query (or type your own below):", [""] + sample_queries)
    user_query = st.text_input("Enter your question:", value=selected_sample)

    if st.button("Submit Query", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing data and generating query..."):
                try:
                    res = requests.post(f"{API_URL}/query", json={"question": user_query})
                    if res.status_code == 200:
                        payload = res.json()
                        st.markdown("### Answer")
                        st.success(payload["answer"])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.expander("Generated SQL Query", expanded=True):
                                st.code(payload["sql"], language="sql")
                        with col2:
                            with st.expander("Raw Result Data", expanded=True):
                                if payload["data"]:
                                    st.dataframe(pd.DataFrame(payload["data"]), use_container_width=True)
                                else:
                                    st.info("No records returned.")
                    else:
                        st.error(res.json().get("detail", "Error executing query."))
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to FastAPI backend. Make sure the API is running on port 8000.")

# ----------------- TAB 2: Anomaly Detection Dashboard -----------------
with tab_anomalies:
    st.subheader("System Anomaly Scanner")
    st.write("Scan the dataset for SLA breaches and statistical resolution time outliers.")

    if st.button("Run Anomaly Scan"):
        with st.spinner("Scanning tickets..."):
            try:
                res = requests.get(f"{API_URL}/anomalies")
                if res.status_code == 200:
                    data = res.json()
                    sla_list = data["sla_breaches"]
                    outlier_list = data["resolution_outliers"]

                    col_metric1, col_metric2 = st.columns(2)
                    col_metric1.metric("🚨 SLA Breaches (Unresolved High/Critical)", len(sla_list))
                    col_metric2.metric("⏱️ Resolution Outliers (IQR Method)", len(outlier_list))

                    st.markdown("#### SLA Breaches")
                    if sla_list:
                        st.dataframe(pd.DataFrame(sla_list), use_container_width=True)
                    else:
                        st.info("No SLA breaches detected.")

                    st.markdown("#### Resolution Time Outliers (Exceeding Q3 + 1.5×IQR by Category)")
                    if outlier_list:
                        st.dataframe(pd.DataFrame(outlier_list), use_container_width=True)
                    else:
                        st.info("No statistical outliers detected.")
                else:
                    st.error("Failed to fetch anomalies from the server.")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to FastAPI backend. Ensure `uvicorn api:app` is running.")