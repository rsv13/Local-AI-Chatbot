import streamlit as st
import ollama
from pypdf import PdfReader

MODEL = "llama3"

BASE_INSTRUCTIONS = (
    "You are a friendly EE billing assistant. Use ONLY the bill text below to answer. "
    "If something isn't shown, say you can't see it on this bill. Never invent numbers."
)


def read_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def build_system_prompt(bill_text):
    return f"{BASE_INSTRUCTIONS}\n\n--- BILL TEXT ---\n{bill_text}\n--- END BILL TEXT ---"


st.title("EE Bill Help Bot")

uploaded = st.sidebar.file_uploader("Upload your bill (PDF)", type="pdf")
if uploaded is not None:
    if st.session_state.get("bill_name") != uploaded.name:
        st.session_state.bill_name = uploaded.name
        st.session_state.messages = [
            {"role": "system", "content": build_system_prompt(read_pdf(uploaded))}
        ]

if "messages" not in st.session_state:
    st.info("Please upload your EE bill (PDF) in the sidebar to get started.")
    st.stop()

question = st.chat_input("Ask a question about your bill: ")

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
        response = ollama.chat(model=MODEL, messages=st.session_state.messages)
        answer = response.message.content
    except Exception:
        answer = "Sorry, I couldn't reach the model. Is Ollama running?"
    with st.chat_message("assistant"):
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
