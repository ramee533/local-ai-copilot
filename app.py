import streamlit as st
import os
import json
from datetime import datetime, timedelta

from llm import stream_response
from rag import add_docs, search_docs
from utils import read_file, chunk_text

# ---------------------------
# CONFIG
# ---------------------------
CHAT_DIR = "chats"
os.makedirs(CHAT_DIR, exist_ok=True)

st.set_page_config(page_title="DE Copilot", layout="wide")
st.title("🧠 Data Engineering Copilot")

# ---------------------------
# CHAT HELPERS
# ---------------------------
def get_today_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(CHAT_DIR, today)
    os.makedirs(path, exist_ok=True)
    return path

def generate_chat_title(user_input):
    title = user_input.strip().split("\n")[0]
    title = title[:40]
    title = "".join(c for c in title if c.isalnum() or c in (" ", "_"))
    return title.replace(" ", "_")

def create_new_chat(user_input=None):
    folder = get_today_folder()

    if user_input:
        title = generate_chat_title(user_input)
    else:
        title = datetime.now().strftime("%H%M%S")

    filename = f"{title}.json"
    path = os.path.join(folder, filename)

    # avoid overwrite
    counter = 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{title}_{counter}.json")
        counter += 1

    with open(path, "w") as f:
        json.dump([], f)

    return path

def load_chat(path):
    with open(path, "r") as f:
        return json.load(f)

def save_chat(path, messages):
    with open(path, "w") as f:
        json.dump(messages, f)

# ---------------------------
# SIDEBAR - CHAT UI
# ---------------------------
st.sidebar.header("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_path = None
    st.session_state.messages = []

# ---------------------------
# GROUP CHAT BY DATE (FIXED)
# ---------------------------
def list_chat_days():
    if not os.path.exists(CHAT_DIR):
        return []

    items = os.listdir(CHAT_DIR)
    valid_days = []

    for item in items:
        path = os.path.join(CHAT_DIR, item)

        if os.path.isdir(path):
            try:
                datetime.strptime(item, "%Y-%m-%d")
                valid_days.append(item)
            except:
                continue  # skip invalid folders/files

    return sorted(valid_days, reverse=True)

def get_label(date_str):
    try:
        today = datetime.now().date()
        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        if file_date == today:
            return "🟢 Today"
        elif file_date == today - timedelta(days=1):
            return "🟡 Yesterday"
        elif file_date >= today - timedelta(days=3):
            return "🔵 Last 3 Days"
        else:
            return f"📁 {date_str}"
    except:
        return None

# ---------------------------
# DISPLAY CHAT LIST
# ---------------------------
days = list_chat_days()

for day in days:
    label = get_label(day)

    if not label:
        continue

    st.sidebar.markdown(f"### {label}")

    day_path = os.path.join(CHAT_DIR, day)
    chats = sorted(os.listdir(day_path), reverse=True)

    for chat_file in chats:
        chat_path = os.path.join(day_path, chat_file)

        display_name = chat_file.replace(".json", "").replace("_", " ")

        if st.sidebar.button(display_name, key=chat_path):
            st.session_state.chat_path = chat_path
            st.session_state.messages = load_chat(chat_path)

# ---------------------------
# INIT CHAT
# ---------------------------
if "chat_path" not in st.session_state:
    st.session_state.chat_path = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------
# SIDEBAR - DOC UPLOAD
# ---------------------------
st.sidebar.header("📂 Upload Docs")

files = st.sidebar.file_uploader(
    "Upload PDFs, SQL, YAML",
    accept_multiple_files=True
)

if files:
    with st.sidebar.spinner("📚 Indexing..."):
        for file in files:
            text = read_file(file)
            chunks = chunk_text(text)
            add_docs(chunks)
    st.sidebar.success("Indexed!")

# ---------------------------
# DISPLAY CHAT
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# USER INPUT
# ---------------------------
user_input = st.chat_input("Ask anything...")

if user_input:

    # 👉 create chat only on first message
    if not st.session_state.chat_path:
        st.session_state.chat_path = create_new_chat(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # 🧠 Conversation memory
    history = "\n".join([
        f"{m['role']}: {m['content']}"
        for m in st.session_state.messages[-5:]
    ])

    # 🔍 RAG
    with st.spinner("🔍 Searching docs..."):
        context = search_docs(user_input)

    context = context[:2000]

    prompt = f"""
You are a senior data engineer.

Conversation:
{history}

Context:
{context}

User Query:
{user_input}

Rules:
- Use past conversation if relevant
- Generate production-ready code
- Include Docker/YAML if needed
- Be precise
"""

    # ---------------------------
    # STREAM RESPONSE
    # ---------------------------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        with st.spinner("🤖 Thinking..."):
            for chunk in stream_response(prompt):
                full_response += chunk
                placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

    # 💾 Save chat
    save_chat(st.session_state.chat_path, st.session_state.messages)