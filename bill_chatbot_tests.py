"""
Test harness for bill_chatbot.py

Every customer's bill is different, so we test in two complementary ways:

1. GOLDEN SET (per-bill cases): a curated set of sample bills covering the main
   scenarios (plain monthly, number change, roaming, one-off charge...). Each bill has
   a few hand-checked expected facts. Add a new scenario by dropping a sample PDF into
   this folder and adding a row to CASES below - no code change needed.

2. BILL-AGNOSTIC CHECKS: checks that work on ANY bill without knowing its contents.
   The key one pulls the real "Your total charges" figure out of the PDF and confirms
   the bot repeats it - so you can sanity-check a bill you've never seen before.

Put your sample bill PDFs in a "sample_bills" folder next to this file (keeps the
project root tidy). You can then refer to them by plain filename.

Run (with Ollama running):
    python bill_chatbot_tests.py                 # runs every bill listed in CASES
    python bill_chatbot_tests.py July2026.pdf    # just one bill (agnostic checks + any cases)
"""

import os
import re
import sys
import ollama
from bill_chatbot import MODEL, read_pdf, build_system_prompt, strip_thinking

# Keep sample bills in their own folder so they don't clutter the project root.
# You can pass a plain filename (e.g. "July2026.pdf") and it will be found here.
SAMPLE_DIR = "sample_bills"


def resolve(name):
    """Turn a bill name into a path we can open.
    If the file exists as given, use it. Otherwise look inside the sample_bills folder.
    This lets you type just 'July2026.pdf' instead of 'sample_bills/July2026.pdf'."""
    if os.path.exists(name):
        return name
    candidate = os.path.join(SAMPLE_DIR, name)
    return candidate if os.path.exists(candidate) else name


# --- 1. GOLDEN SET ---------------------------------------------------------------------
# A dictionary of: filename -> a list of (question, [expected snippets]) checks.
# For each question, the test PASSES if ANY of the expected snippets appears in the
# bot's answer. We keep snippets short and loose because the model's wording varies
# from run to run - we care that the right FACT is present, not the exact phrasing.
# To cover a new bill type: add its PDF to sample_bills/ and add a block here.
CASES = {
    "July2026.pdf": [
        ("How much is this bill?",                  ["10"]),
        ("What is my monthly plan called?",         ["Ess Plus"]),
        ("What discount am I getting?",             ["26", "Colleague"]),
        ("How many call minutes did I use?",        ["66"]),
        ("Do I have any out of allowance charges?", ["no", "0.00"]),
    ],
    # Example of a harder scenario - uncomment and add the file to test it:
    # "August_bill.pdf": [
    #     ("Why are there two numbers?",            ["number change", "port", "temporary"]),
    #     ("Which number is mine going forward?",   ["590447", "447"]),
    #     ("Why is one line credited?",             ["payment date", "credit", "refund"]),
    # ],
}


def extract_total(bill_text):
    """Find the bill's headline total in its text, e.g. 'Your total charges £7.10'.
    We use a regex to grab the number after 'total charges'. Returns e.g. '7.10',
    or None if we can't find it. This is what lets us check any bill automatically -
    we read the true total straight from the PDF, then confirm the bot repeats it."""
    m = re.search(r"total charges\s*£?\s*([\d,]+\.\d{2})", bill_text, re.IGNORECASE)
    return m.group(1) if m else None


def ask(system_prompt, question):
    """Send one question to the model with the bill loaded, and return its answer.
    Each call is a fresh, single-question conversation (no chat history) so tests
    don't affect each other."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    response = ollama.chat(model=MODEL, messages=messages, options={"temperature": 0.2})
    return strip_thinking(response.message.content)


def check(question, answer, expected):
    """Return True if any of the expected snippets appears in the answer (case-insensitive)."""
    low = answer.lower()
    return any(e.lower() in low for e in expected)


def run_for_bill(bill_pdf):
    """Run all checks for one bill and print the results."""
    path = resolve(bill_pdf)
    print(f"\n===== Testing: {path} =====")
    bill_text = read_pdf(path)                       # PDF -> text
    system_prompt = build_system_prompt(bill_text)   # text -> the bot's knowledge

    # Assemble the checks to run for this bill.
    tests = []

    # (a) Automatic checks that work on ANY bill, even one we've never seen:
    total = extract_total(bill_text)
    if total:
        # The bot must state the real total that we read from the PDF.
        tests.append(("What is the total charge on this bill?", [total]))
    # The bot must never tell the customer the bill isn't theirs.
    tests.append(("This is my bill - can you confirm it's for my account?",
                  ["yes", "your bill", "your account", "MR ROHIT", "this bill"]))

    # (b) Plus any hand-written checks we listed for this specific bill.
    tests += CASES.get(bill_pdf, [])

    # Run each check and print PASS/FAIL with a snippet of what the bot actually said.
    passed = 0
    for question, expected in tests:
        answer = ask(system_prompt, question)
        ok = check(question, answer, expected)
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {question}")
        print(f"        expected one of: {expected}")
        print(f"        got: {answer.strip()[:200]}")
        print()
    print(f"{bill_pdf}: {passed}/{len(tests)} passed.")
    return passed, len(tests)


def run():
    """Entry point. With a filename argument, test just that bill; otherwise test
    every bill listed in CASES. Prints an overall pass count at the end."""
    bills = [sys.argv[1]] if len(sys.argv) > 1 else list(CASES.keys())
    if not bills:
        print("No bills to test. Pass a PDF or add entries to CASES.")
        return
    total_pass = total_count = 0
    for b in bills:
        p, c = run_for_bill(b)
        total_pass += p
        total_count += c
    print(f"\nOVERALL: {total_pass}/{total_count} passed across {len(bills)} bill(s).")


if __name__ == "__main__":
    run()
