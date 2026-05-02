import streamlit as st
from llm import stream_response
from rag import add_docs, search_docs
from utils import read_file, chunk_text

st.set_page_config(page_title="Data Engineering Copilot", layout="wide")

st.title("🧠 Data Engineering Copilot (Local LLM)")

# ---------------------------
# SIDEBAR (Upload Docs)
# ---------------------------
st.sidebar.header("📂 Upload Documents")

files = st.sidebar.file_uploader(
    "Upload PDFs, SQL, YAML, JSON",
    accept_multiple_files=True
)

if files:
    with st.sidebar.spinner("📚 Indexing documents..."):
        for file in files:
            text = read_file(file)
            chunks = chunk_text(text)
            add_docs(chunks)
    st.sidebar.success("Documents indexed!")

# ---------------------------
# CHAT MEMORY
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------
# DISPLAY CHAT
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# USER INPUT
# ---------------------------
user_input = st.chat_input("Ask about ETL, SQL, Docker, dbt...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # 🔍 Retrieve context with spinner
    with st.spinner("🔍 Searching documents..."):
        context = search_docs(user_input)

    # ⚡ limit context (VERY IMPORTANT for speed)
    context = context[:2000]

    prompt = f"""
You are a senior data engineer.

Context:
{context}

User Query:
{user_input}

Rules:
- Generate production-ready code
- Include SQL / YAML / Docker if needed
- Be precise
- Avoid generic answers
"""

    # ---------------------------
    # STREAMING RESPONSE
    # ---------------------------
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("🤖 Thinking..."):
            for chunk in stream_response(prompt):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )