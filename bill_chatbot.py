import re
import streamlit as st
import ollama
from pypdf import PdfReader

from prompts import BASE_INSTRUCTIONS, FEWSHOT

MODEL = "qwen3:14b"

# Developer switch: show a debug panel of what the bot has loaded.
DEBUG = False

def read_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def build_system_prompt(bills):
    if isinstance(bills, str):
        bills = {"your bill": bills}
    sections = [f"===== BILL: {name} =====\n{text}" for name, text in bills.items()]
    joined = "\n\n".join(sections)
    return f"{BASE_INSTRUCTIONS}\n\n--- BILLS ON FILE ({len(bills)}) ---\n{joined}\n--- END BILLS ---"


st.title("EE Bill Help Bot")

if "bills" not in st.session_state:
    st.session_state.bills = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

st.sidebar.header("Your bills")
uploaded_files = st.sidebar.file_uploader(
    "Upload bill(s) (PDF)", type="pdf", accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)
if uploaded_files:
    for uf in uploaded_files:
        if uf.name not in st.session_state.bills:
            st.session_state.bills[uf.name] = read_pdf(uf)

if st.session_state.bills:
    system_prompt = build_system_prompt(st.session_state.bills)
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
    else:
        st.session_state.messages[0] = {"role": "system", "content": system_prompt}
    st.sidebar.success(f"{len(st.session_state.bills)} bill(s) loaded:")
    for name in st.session_state.bills:
        st.sidebar.write(f"- {name}")

col1, col2 = st.sidebar.columns(2)
if col1.button("Clear chat"):
    st.session_state.messages = st.session_state.messages[:1]
if col2.button("Remove all bills"):
    st.session_state.bills = {}
    st.session_state.messages = []
    st.session_state.uploader_key += 1
    st.rerun()

if DEBUG and st.session_state.messages:
    with st.sidebar.expander("What the bot has loaded"):
        st.text_area("System prompt", st.session_state.messages[0]["content"], height=200)

if not st.session_state.messages:
    st.info("Please upload one or more EE bills (PDF) in the sidebar to get started.")
    st.stop()

question = st.chat_input("Ask about your bill(s): ")

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    try:
        api_messages = [st.session_state.messages[0]] + FEWSHOT + st.session_state.messages[1:]
        response = ollama.chat(model=MODEL, messages=api_messages, options={"temperature": 0.2})
        answer = strip_thinking(response.message.content)
    except Exception:
        answer = "Sorry, I couldn't reach the model. Is Ollama running?"
    with st.chat_message("assistant"):
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
