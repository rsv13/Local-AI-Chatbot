# Local AI Bill Assistant

A personal Python project that answers questions about mobile-bill PDFs using **Streamlit, pypdf and Ollama**. It explores document-grounded conversation, local LLM integration and multi-bill comparisons.

The interface calls this project “EE Bill Help Bot”. It is an independent learning project, not an official EE/BT product or an endorsed source of billing advice.

## Features

- Upload one or more text-based PDF bills.
- Ask about charges, credits, discounts and changes across months.
- Preserve chat history while adding bills within a Streamlit session.
- Clear the conversation separately from removing uploaded bills.
- Keep application logic, domain prompts and a response-checking harness in separate modules.

## How it works

1. `pypdf` extracts text from the uploaded PDFs.
2. `build_system_prompt` combines instructions and labelled bill text.
3. Streamlit stores bill text and conversation history in `st.session_state`.
4. `ollama.chat` receives the system prompt, few-shot examples and chat history.
5. The app removes `<think>` blocks and displays the response.

This implementation puts extracted document text directly into the prompt. It does not implement an embedding index, vector database or retrieval pipeline.

## Run locally

Prerequisites: Python 3.10+ and [Ollama](https://ollama.com/download). The model must fit your available memory.

```bash
git clone https://github.com/rsv13/Local-AI-Chatbot.git
cd Local-AI-Chatbot
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
ollama pull qwen3:14b
streamlit run bill_chatbot.py
```

Make sure Ollama is running. The current `MODEL` constant in `bill_chatbot.py` is `qwen3:14b`; to use a smaller local model, pull it and update that constant to the same model name. The UI normally opens at `http://localhost:8501`.

## Project structure

| File | Purpose |
| --- | --- |
| `bill_chatbot.py` | PDF extraction, Streamlit UI, session state and Ollama integration |
| `prompts.py` | Base instructions and few-shot examples |
| `bill_chatbot_tests.py` | Response-checking test harness |
| `sample_bills/` | Test-fixture directory |
| `requirements.txt` | Python dependencies |

## Try it

Use synthetic or fully redacted bills. Upload a small number of PDFs, then ask “What charges appear on this bill?” or “What changed between these months?” Check the response against the document.

- **Clear chat:** removes conversation turns while retaining loaded bills.
- **Remove all bills:** resets both the bill collection and conversation.
- Restarting the Streamlit process clears session-held data; there is no on-disk persistence feature.

## Evaluation

A separate harness checks responses to billing questions against expected figures. With a synthetic fixture available, the existing invocation pattern is:

```bash
python bill_chatbot_tests.py synthetic_bill.pdf
```

Inspect the harness when configuring fixture paths and expected values. This is a response-checking tool, not evidence of guaranteed answer accuracy or a comprehensive automated test suite.

## Limitations and data handling

- Text-based PDFs only; scanned bills require OCR, which is not included.
- Large documents and long conversations can exceed the model context window.
- LLM answers and arithmetic can be incorrect; verify all figures against source bills.
- The intended configuration uses a local Ollama model. Data handling depends on the runtime, endpoint and hosting configuration; local execution is not a security audit.
- Do not commit real customer bills, account details, proprietary material or confidential employer documents.
- `DEBUG` is `False` by default; enabling it displays the active system prompt and bill text in the UI.

## Learning focus

Python application structure, PDF text extraction, prompt composition, local inference, session-state management, model error handling and evaluation of generated responses.
