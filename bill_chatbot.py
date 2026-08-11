"""
EE Bill Help Bot  -  main application
=====================================

A small chatbot that reads a customer's EE mobile phone bill (a PDF) and answers
plain-English questions about it: what the charges are, why a credit appeared,
what changed between months, and so on.

HOW IT WORKS (the big picture):
  1. The customer uploads one or more bill PDFs in the sidebar.
  2. We extract the plain text from each PDF (pypdf).
  3. We build a "system prompt" = our instructions + the bill text. This is the
     knowledge we hand to the AI model.
  4. When the customer asks a question, we send [instructions + bill text +
     conversation] to a local AI model (via Ollama) and show its reply.

Everything runs locally on the user's machine - no bill data leaves the computer.

TECH USED:
  - Streamlit : builds the web chat UI with very little code.
  - Ollama    : runs the AI model (e.g. qwen3) locally.
  - pypdf     : reads text out of PDF files.
"""

import re
import streamlit as st
import ollama
from pypdf import PdfReader

# The bot's instructions and billing knowledge live in prompts.py. Keeping them in a
# separate file means we can tweak how the bot "thinks" without touching app code.
from prompts import BASE_INSTRUCTIONS, FEWSHOT

# Which local AI model to use. Change this to any model you've pulled with Ollama.
# For 16GB Macs: "llama3.1" is a smooth upgrade; "qwen3:14b" reasons best but is heavier.
# Pull it first from a terminal, e.g.:  ollama pull qwen3:14b
MODEL = "qwen3:14b"

# A developer switch. When True, a debug panel shows exactly what the bot is holding.
# Keep it False for customers so they don't see the behind-the-scenes prompt.
DEBUG = False


# --------------------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------------------

def strip_thinking(text):
    """Some models (like Qwen3) 'think out loud' inside <think>...</think> tags before
    giving their answer. We remove those blocks so the customer only sees the final
    reply. If a model doesn't use them, this simply changes nothing."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def read_pdf(uploaded_file):
    """Open a PDF and return all its text as one big string.
    We read each page, grab its text (or "" if a page has none), and join them."""
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def build_system_prompt(bills):
    """Create the 'system prompt' - the full set of knowledge we give the AI.

    It is our instructions (BASE_INSTRUCTIONS) followed by the text of every bill.

    `bills` can be:
      - a single string (one bill's text), or
      - a dict of {filename: bill_text} (several bills).
    Each bill gets a clear header line so the model can tell them apart and compare
    them month to month.
    """
    # Accept a plain string too, so callers (and the tests) can pass just one bill.
    if isinstance(bills, str):
        bills = {"your bill": bills}

    # Label each bill with its filename, e.g. "===== BILL: July2026.pdf ====="
    sections = [f"===== BILL: {name} =====\n{text}" for name, text in bills.items()]
    joined = "\n\n".join(sections)

    # Instructions first, then all the bills wrapped in clear markers.
    return (
        f"{BASE_INSTRUCTIONS}\n\n"
        f"--- BILLS ON FILE ({len(bills)} uploaded) ---\n{joined}\n--- END BILLS ---"
    )


# --------------------------------------------------------------------------------------
# App UI starts here. Streamlit re-runs this whole file top-to-bottom on every
# interaction (every click or message), so we keep anything that must survive between
# runs in `st.session_state` (Streamlit's per-user memory).
# --------------------------------------------------------------------------------------

st.title("EE Bill Help Bot")

# --- Set up our "memory" the first time the app runs for this user ---
# bills:        {filename: bill_text} - every bill uploaded this session.
# messages:     the conversation. messages[0] is the hidden system prompt; the rest
#               are the visible user/assistant turns.
# uploader_key: a trick to reset the file uploader (explained at the Remove button).
if "bills" not in st.session_state:
    st.session_state.bills = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- Sidebar: the upload area. Bills ADD to the collection instead of replacing it,
# so a customer can load several months and compare them. ---
st.sidebar.header("Your bills")
uploaded_files = st.sidebar.file_uploader(
    "Upload bill(s) (PDF)",
    type="pdf",
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",  # changing this key resets the widget
)

# Read any newly uploaded file once and store its text. Files we've already read are
# left alone (so we don't re-read the same PDF on every rerun).
if uploaded_files:
    for uf in uploaded_files:
        if uf.name not in st.session_state.bills:
            st.session_state.bills[uf.name] = read_pdf(uf)

# Rebuild the system prompt so it always reflects every bill currently on file.
# Important: we only replace messages[0] (the system prompt) and leave the rest of the
# conversation untouched - that's what keeps the chat history when a new bill is added.
if st.session_state.bills:
    system_prompt = build_system_prompt(st.session_state.bills)
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
    else:
        st.session_state.messages[0] = {"role": "system", "content": system_prompt}

# Show the list of bills currently loaded, so the customer can see the trail.
if st.session_state.bills:
    st.sidebar.success(f"{len(st.session_state.bills)} bill(s) loaded:")
    for name in st.session_state.bills:
        st.sidebar.write(f"• {name}")

# Two reset buttons, side by side.
col1, col2 = st.sidebar.columns(2)
if col1.button("Clear chat"):
    # Keep the bills, just drop the questions/answers (keep messages[0], the prompt).
    st.session_state.messages = st.session_state.messages[:1]
if col2.button("Remove all bills"):
    # Forget the bills and the chat...
    st.session_state.bills = {}
    st.session_state.messages = []
    # ...but the uploader widget still holds the files internally. Bumping its key makes
    # Streamlit build a fresh, empty uploader. st.rerun() refreshes the page right away.
    st.session_state.uploader_key += 1
    st.rerun()

# Developer-only panel to confirm what the bot is actually holding. Hidden unless DEBUG.
if DEBUG and st.session_state.messages:
    with st.sidebar.expander("What the bot has loaded"):
        total = sum(len(t) for t in st.session_state.bills.values())
        st.caption(f"{len(st.session_state.bills)} bill(s), {total} characters total")
        st.text_area("Active system prompt", st.session_state.messages[0]["content"], height=200)

# If nothing has been uploaded yet, prompt for a bill and stop here (nothing to chat about).
if not st.session_state.messages:
    st.info("Please upload one or more EE bills (PDF) in the sidebar to get started.")
    st.stop()

# The text box at the bottom of the page where the customer types a question.
question = st.chat_input("Ask about your bill(s) - e.g. 'what changed since last month?' ")

# Redraw the conversation so far. We skip the system message because it's internal.
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle a new question ---
if question:

    # 1. Save the question to history, then show it on screen.
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # 2. Ask the model and show the answer in the assistant's chat bubble.
    with st.chat_message("assistant"):
        # st.spinner shows an animated "working..." message with clear text so the
        # customer knows the bot is busy - important because a big model like qwen3:14b
        # can take a while to answer. The spinner disappears once we have the reply.
        with st.spinner("Reading your bill and working out the answer... this can take a moment."):
            # Wrapped in try/except so the app shows a friendly message instead of
            # crashing if Ollama isn't running.
            try:
                # What we send the model, in order:
                #   - messages[0]  : the system prompt (instructions + bill text)
                #   - FEWSHOT      : a hidden worked example so it mirrors good reasoning
                #   - messages[1:] : the real back-and-forth conversation
                api_messages = (
                    [st.session_state.messages[0]]
                    + FEWSHOT
                    + st.session_state.messages[1:]
                )
                # temperature 0.2 = low randomness, so answers stay factual and consistent.
                response = ollama.chat(
                    model=MODEL,
                    messages=api_messages,
                    options={"temperature": 0.2},
                )
                # Clean off any <think> reasoning before showing the reply.
                answer = strip_thinking(response.message.content)
            except Exception:
                answer = "Sorry, I couldn't reach the model. Is Ollama running?"

        # 3. Show the answer (spinner is now gone) and save it to history.
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
