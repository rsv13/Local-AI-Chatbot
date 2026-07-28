import streamlit as st
import ollama

MODEL = "llama3"
SYSTEM_PROMPT = "You are a helpful, friendly assistant. Answer clearly and concisely."

st.title("Chat Bot")
question = st.chat_input("Ask your question: ")

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
