import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Support Ticket Intelligence", layout="wide", page_icon="🎫")
st.title("🎫 Support Ticket AI Intelligence System")

tab_chat, tab_anomalies = st.tabs(["💬 Natural Language Query", "⚠️ Anomaly Detection Dashboard"])

# ----------------- Helper: Tab 1 Dynamic Visualizer -----------------
def render_data_visualization(df: pd.DataFrame):
    """Dynamically generates visual charts for non-technical users in Tab 1."""
    if df is None or df.empty:
        return

    # Scenario 1: Single numeric KPI (e.g., total counts or single averages)
    if len(df) == 1 and len(df.columns) == 1:
        col_name = str(df.columns[0])
        val = df.iloc[0, 0]
        st.metric(label=col_name.replace("_", " ").title(), value=val)
        return

    # Scenario 2: Two-column aggregate data (e.g., Agent/Category vs. Count/Average)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
        x_col = non_numeric_cols[0]
        y_col = numeric_cols[0]

        st.markdown(f"#### 📊 Visual Breakdown: `{x_col}` vs `{y_col}`")
        chart_df = df[[x_col, y_col]].dropna().copy()
        chart_df = chart_df.set_index(x_col)
        
        if "date" in x_col.lower() or "created" in x_col.lower():
            st.line_chart(chart_df)
        else:
            st.bar_chart(chart_df)

    # Scenario 3: Single categorical column breakdown
    elif len(non_numeric_cols) == 1 and len(numeric_cols) == 0:
        cat_col = non_numeric_cols[0]
        st.markdown(f"#### 📊 Distribution by `{cat_col}`")
        counts = df[cat_col].value_counts()
        st.bar_chart(counts)

# ----------------- TAB 1: Natural Language Query -----------------
with tab_chat:
    st.subheader("Query Ticket Data with Plain English")
    
    sample_queries = [
        "How many tickets are currently open?",
        "Which agent resolved the most tickets this month?",
        "Show me all Critical tickets not resolved within 12 hours.",
        "What is the average customer rating for Technical category tickets?",
        "Which agent has the lowest average customer rating?",
        "Show the total count of tickets by category"
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
                        st.markdown("### Executive Summary")
                        st.success(payload.get("answer", "No answer generated."))
                        
                        raw_records = payload.get("data", [])
                        df_res = pd.DataFrame(raw_records) if raw_records else pd.DataFrame()

                        if not df_res.empty:
                            render_data_visualization(df_res)

                        st.markdown("### 📋 Retrieved Data Table")
                        if not df_res.empty:
                            st.dataframe(df_res, use_container_width=True, hide_index=True)
                        else:
                            st.info("No matching records found in the database.")

                        with st.expander("🔍 View Generated SQL Query", expanded=False):
                            st.code(payload.get("sql", "-- No SQL returned"), language="sql")
                    else:
                        st.error(res.json().get("detail", "Error executing query."))
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to FastAPI backend. Ensure uvicorn api:app is running on port 8000.")

# ----------------- TAB 2: Anomaly Detection Dashboard -----------------
with tab_anomalies:
    st.subheader("System Anomaly Scanner")
    st.write("Scan the dataset for SLA breaches and statistical resolution time outliers.")

    if st.button("Run Anomaly Scan", type="primary"):
        with st.spinner("Scanning tickets for operational anomalies..."):
            try:
                res = requests.get(f"{API_URL}/anomalies")
                if res.status_code == 200:
                    data = res.json()
                    sla_list = data.get("sla_breaches", [])
                    outlier_list = data.get("resolution_outliers", [])

                    # Summary Metrics Cards
                    col_metric1, col_metric2 = st.columns(2)
                    col_metric1.metric("🚨 SLA Breaches (Unresolved High/Critical)", len(sla_list))
                    col_metric2.metric("⏱️ Resolution Outliers (IQR Method)", len(outlier_list))

                    st.markdown("---")

                    # Section 1: SLA Breaches
                    st.markdown("### 🚨 SLA Breaches Analysis")
                    if sla_list:
                        df_sla = pd.DataFrame(sla_list)

                        # Visual breakdown by category and priority
                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            st.markdown("##### Breaches by Category")
                            st.bar_chart(df_sla["category"].value_counts())
                        with col_chart2:
                            st.markdown("##### Breaches by Priority")
                            st.bar_chart(df_sla["priority"].value_counts())

                        st.markdown("##### Detailed SLA Breach Records")
                        st.dataframe(df_sla, use_container_width=True, hide_index=True)
                    else:
                        st.info("No SLA breaches detected.")

                    st.markdown("---")

                    # Section 2: Resolution Time Outliers
                    st.markdown("### ⏱️ Resolution Outliers (Exceeding Q3 + 1.5×IQR)")
                    if outlier_list:
                        df_outliers = pd.DataFrame(outlier_list)

                        # Visual breakdown: Outliers count per category
                        col_out1, col_out2 = st.columns([1, 2])
                        with col_out1:
                            st.markdown("##### Outlier Volume by Category")
                            st.bar_chart(df_outliers["category"].value_counts())
                        with col_out2:
                            st.markdown("##### Resolution Time (Hrs) vs Category Cutoff")
                            chart_data = df_outliers[["ticket_id", "resolution_time_hrs", "iqr_cutoff_hrs"]].set_index("ticket_id")
                            st.line_chart(chart_data)

                        st.markdown("##### Detailed Resolution Outliers Table")
                        st.dataframe(df_outliers, use_container_width=True, hide_index=True)
                    else:
                        st.info("No statistical outliers detected.")
                else:
                    st.error("Failed to fetch anomalies from the server.")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to FastAPI backend. Ensure `uvicorn api:app` is running on port 8000.")