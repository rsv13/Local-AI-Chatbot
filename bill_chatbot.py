import streamlit as st
import ollama
from pypdf import PdfReader

MODEL = "llama3"

BASE_INSTRUCTIONS = """You are an experienced EE mobile billing advisor. Explain the
bill and WHY it looks the way it does, tying charges to the dates on the bill.

- Use ONLY the bill text provided. Never invent numbers.
- PRO-RATA / PART-MONTH CHARGES: when a line starts, stops, or the billing date moves
  mid-cycle, EE charges or credits only for the days used in that partial period.
- NUMBER CHANGE / PORT-IN: a new number can appear while an old one winds down; the
  new/kept line is charged going forward and the old line is credited/closed.
- PAYMENT DATE CHANGE: moving the billing date credits days already paid for and
  re-charges from the new date, so you can see a credit and a part-charge together.
- DISCOUNTS: e.g. Colleague SIMO Offer -26.00 reduces a 36.00 plan to 10.00/month."""

# A hidden worked example the model can mirror.
FEWSHOT = [
    {"role": "user", "content": "Why does my bill show two numbers, one charged and one credited?"},
    {"role": "assistant", "content": (
        "This usually means your number changed or was ported in. The old line is "
        "credited for days already paid, and the new line is charged from the day it "
        "started. You still have one active number going forward."
    )},
]


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
        api_messages = [st.session_state.messages[0]] + FEWSHOT + st.session_state.messages[1:]
        response = ollama.chat(model=MODEL, messages=api_messages, options={"temperature": 0.2})
        answer = response.message.content
    except Exception:
        answer = "Sorry, I couldn't reach the model. Is Ollama running?"
    with st.chat_message("assistant"):
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
