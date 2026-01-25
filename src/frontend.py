import streamlit as st
import requests
import json

st.set_page_config(page_title="DB-LLM RAG Bot", page_icon="📊", layout="wide")

API_URL = "http://localhost:8000"

st.title("📊 DB-LLM RAG Assistant")
st.markdown("Interact with your database using natural language.")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Reports and Settings
with st.sidebar:
    st.header("📋 Predefined Reports")
    try:
        response = requests.get(f"{API_URL}/reports")
        if response.status_code == 200:
            reports = response.json()
            for report_id, info in reports.items():
                with st.expander(f"{report_id}: {info['name']}"):
                    st.write(info['description'])
                    if st.button(f"Run {report_id}", key=report_id):
                        # Add report request to chat
                        st.session_state.messages.append({"role": "user", "content": f"Run report {report_id}"})
                        st.rerun()
        else:
            st.error("Could not fetch reports from API.")
    except Exception:
        st.warning("API not reachable. Please start the backend.")

    st.divider()
    st.header("⚙️ Settings")
    format_instr = st.text_input("Custom Formatting", placeholder="e.g. Markdown table, list...")
    show_sql = st.checkbox("Show Executed SQL", value=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message and show_sql:
            with st.expander("Executed SQL"):
                for query in message["sql"]:
                    st.code(query, language="sql")

# Chat input
if prompt := st.chat_input("Ask a question about your data..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {"question": prompt}
                if format_instr:
                    payload["format_instruction"] = format_instr

                response = requests.post(f"{API_URL}/ask", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sql_queries = data.get("sql_queries", [])

                    st.markdown(answer)
                    if sql_queries and show_sql:
                        with st.expander("Executed SQL"):
                            for query in sql_queries:
                                st.code(query, language="sql")

                    # Save to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sql": sql_queries
                    })
                else:
                    error_msg = f"API Error ({response.status_code}): {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")
                st.session_state.messages.append({"role": "assistant", "content": f"Connection Error: {str(e)}"})
