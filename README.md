# EE Bill Help Bot

A simple local chatbot that reads an EE mobile phone bill (PDF) and answers customer
questions about it — charges, discounts, credits, number changes, pro-rata amounts,
and comparisons across months. Built with Streamlit + Ollama (runs fully on your
machine, no data leaves your computer).

## What's in this folder

- `bill_chatbot.py` — the app (upload bills, chat about them). App/UI logic only.
- `prompts.py` — the bot's instructions and EE billing knowledge. Edit here to change
  how it explains bills, without touching the app code.
- `bill_chatbot_tests.py` — a quick test harness that checks answers against a bill.
- `sample_bills/` — put your own test bill PDFs here (used only by the tests, not the app).
- `requirements.txt` — Python dependencies.
- `README.md` — this file.

## 1. Prerequisites

- **Python 3.10+**
- **Ollama** — download from https://ollama.com/download and install it.

## 2. Pull a model

llama3 works but is weak at multi-step reasoning. Recommended:

```
ollama pull qwen3:14b     # best reasoning (needs ~9GB, slower on 16GB Macs)
# or
ollama pull qwen3:8b      # lighter and faster, still good
# or
ollama pull llama3.1      # solid middle option
```

Then set the model near the top of `bill_chatbot.py`:

```python
MODEL = "qwen3:14b"
```

## 3. Install dependencies

From this folder:

```
pip install -r requirements.txt
```

(Optional but tidy: use a virtual environment first —
`python -m venv .venv && source .venv/bin/activate`)

## 4. Run the app

Make sure Ollama is running (open the Ollama app, or run `ollama serve`), then:

```
streamlit run bill_chatbot.py
```

It opens in your browser (usually http://localhost:8501).

## 5. Use it

- In the sidebar, upload one or more EE bills (PDF).
- Bills **accumulate** — upload more months and they're all kept, so you can ask
  things like "what changed since last month?" or "roughly what will next month be?"
- The chat history is preserved when you add a new bill.
- "Clear chat" wipes the questions but keeps the bills; "Remove all bills" resets.
- A developer "What the bot has loaded" panel is hidden by default. To see it while
  testing, set `DEBUG = True` near the top of `bill_chatbot.py`. Leave it `False` for
  customers.

## 6. Run the tests (optional)

The test harness asks a set of questions and checks the answers contain the right
figures. Point it at a real bill PDF placed in this folder:

```
python bill_chatbot_tests.py July2026.pdf
```

## Notes / limits

- Works on normal text-based PDF bills. Scanned/photo bills would need OCR (not included).
- Each bill is ~1,500 tokens. Loading many at once can exceed the model's context
  window — 2–4 bills at a time is the sweet spot for comparisons.
- Everything lives in the browser session. Fully restarting Streamlit clears the
  loaded bills and chat. (Ask if you want on-disk persistence across sessions.)
- Answer quality depends heavily on the model. Bigger models (qwen3:14b) explain
  complex bills far more reliably than small ones.
