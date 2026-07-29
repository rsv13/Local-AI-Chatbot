import streamlit as st
import ollama

MODEL = "llama3"

# What the bot knows about the bill, baked in for now.
BILL_FACTS = """
EE mobile bill for Mr Rohit Vishwakarma. Account 225646602.
Plan: Ess Plus SIM UL 36 - normally 36.00/month, minus an EE Colleague SIMO Offer
discount of -26.00, so 10.00/month. Unlimited data, UK mins and texts, EU roaming.
Paid by Direct Debit. No out-of-allowance charges.
"""

SYSTEM_PROMPT = (
    "You are a friendly EE billing assistant. Answer clearly and concisely using "
    "only the bill information below.\n\n" + BILL_FACTS
)

st.title("EE Bill Help Bot")
question = st.chat_input("Ask a question about your bill: ")

if st.sidebar.button("Clear chat"):
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

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
