import re
import streamlit as st
import ollama
from pypdf import PdfReader

MODEL = "qwen3:14b"

# Developer switch: show a debug panel of what the bot has loaded.
DEBUG = False

BASE_INSTRUCTIONS = """You are an experienced EE mobile billing advisor. Explain the
bill and WHY it looks the way it does, tying charges to the dates on the bill.

- Use ONLY the bill text provided. Never invent numbers.\n- TRUST THE CUSTOMER ABOUT THEIR OWN NUMBER: if they tell you which number is\n  theirs, believe them and anchor your analysis to it. Never argue a bill isn't\n  theirs; explain any mismatch as a number change / port-in.\n- The EARLIEST bill often shows a TEMPORARY number; the customer's real number is\n  the one that CONTINUES on the most recent bills and is charged month after month.
- PRO-RATA / PART-MONTH CHARGES: partial periods are charged/credited by the day.
- NUMBER CHANGE / PORT-IN: a new number can appear while an old one winds down.
- PAYMENT DATE CHANGE: credits days already paid and re-charges from the new date.
- DISCOUNTS: e.g. Colleague SIMO Offer -26.00 reduces a 36.00 plan to 10.00/month.

COMPARING MULTIPLE BILLS: you may be given several bills, each under a header line
"===== BILL: <filename> =====". Compare months and explain why a bill went up or down,
and estimate next month from the recurring charge (make clear it's an estimate)."""

FEWSHOT = [
    {"role": "user", "content": "Why does my bill show two numbers, one charged and one credited?"},
    {"role": "assistant", "content": (
        "This usually means your number changed or was ported in. The old line is "
        "credited for days already paid, and the new line is charged from the day it "
        "started. You still have one active number going forward."
    )},
]


def strip_thinking(text):
    """Remove <think>...</think> reasoning (e.g. Qwen3) so only the answer shows."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


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

st.sidebar.header("Your bills")
uploaded_files = st.sidebar.file_uploader("Upload bill(s) (PDF)", type="pdf", accept_multiple_files=True)
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

if st.sidebar.button("Clear chat"):
    st.session_state.messages = st.session_state.messages[:1]

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
