# 🧾 LedgerMind — AI Finance Controller

> Reconciliation shouldn't feel like detective work. LedgerMind reads your books, catches what's wrong, explains why, and tells you what to do about it — in plain English.

**[🔗 Live Demo](https://gucdssntdegcascnarwcdw.streamlit.app/)** 

---

## The problem

Every small business without a dedicated finance team faces the same quiet drain: someone manually cross-checks the bank statement against the books, misses a duplicate charge or a suspicious payment until weeks later, and has no early warning when cash is about to run out. It's slow, it's error-prone, and it doesn't scale past a spreadsheet.

## What LedgerMind does about it

LedgerMind is a pipeline of small, focused AI agents — not one giant model trying to do everything. Upload a ledger and a bank statement, and it will:

- **Reconcile transactions automatically** — exact matches on ID, amount, and date; near-matches (likely bank posting delays) get flagged separately
- **Resolve ambiguous cases with Gemini** — not guessed, not auto-approved. Every ambiguous match gets a decision, a confidence score, and a plain-English reason you can actually read
- **Catch anomalies before they cost you** — statistical outliers and duplicate transactions are flagged by rules first (fast, free), with AI explanation available on demand
- **Forecast your cash runway** — current balance, daily burn, and a 90-day projection, so "are we okay?" has a real answer
- **Write your financial briefing for you** — a Controller agent synthesizes reconciliation, anomalies, and forecast into one short, readable summary
- **Answer your questions** — a Controller Copilot chat, grounded strictly in your actual numbers, so you can just ask "why is runway a concern?" instead of hunting through tabs
- **Remember your last run** — a "What Changed" comparison shows you what moved since yesterday, not just where you stand today
- **Flag risk before you ask** — proactive alerts surface the moment reconciliation runs, based on runway and anomaly thresholds

## The thing I actually care about

Most AI demos are "prompt → LLM → answer" — impressive for thirty seconds, useless the moment you need to trust it. LedgerMind is built the opposite way: **every AI decision is auditable.** Click any flagged transaction and you see the exact source data and the exact reasoning behind the AI's call, with a visible confidence score. That's the bar a real finance tool has to clear, and it's the design decision I kept coming back to at every step.

---

## Architecture

```
CSV uploads (ledger + bank statement)
            │
            ▼
   Data cleaning & validation
   (reports exactly what was fixed or rejected)
            │
            ▼
     Rule-based reconciliation
            │
   ┌────────┴────────┐
   ▼                 ▼
Ambiguous cases   Anomaly candidates
   → Gemini          → rules first,
   (on click)        Gemini explains
   │                 (on click)
   └────────┬────────┘
            ▼
     Cash runway forecast
            │
            ▼
   Controller agent (Gemini)
   → Financial briefing
   → Copilot chat (grounded Q&A)
            │
            ▼
   Proactive alerts + "What Changed"
   (SQLite-backed run history)
```

**Why rules first, AI only where it's actually needed:** sending every transaction to an LLM is slow, expensive, and hard to defend. Rules resolve the vast majority of cases instantly and for free. AI is reserved for the genuinely ambiguous cases — where a confident, explainable judgment call is actually worth the cost.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Full interactive dashboard in pure Python — no separate frontend needed |
| Data | pandas | Standard, reliable tabular data handling |
| AI | Gemini (`gemini-3.6-flash`) | Fast, cheap, structured JSON output for confidence-scored decisions |
| Persistence | SQLite | Zero-setup local history for run-over-run comparison |
| Visualization | Plotly | Interactive charts with real axis control, unlike default chart libraries |

No React, no Docker, no microservices — deliberately. Every added layer of infrastructure is a place a first-time builder can lose a week to configuration instead of building the actual product. This stack ships.

---

## Getting started

```bash
git clone https://github.com/Thathika/ledgermind.git
cd ledgermind
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

Run it:
```bash
streamlit run app.py
```

Sample synthetic data (`ledger.csv`, `bank_statement.csv`) is included so you can try it immediately without your own financial data.

---

## What's honestly not finished

I'd rather tell you than have you find out:

- **Current balance assumes the ledger starts at zero.** A real system would pull an opening balance from an actual accounting system — I didn't have one to connect to, so this is the simplification I made and I'm not pretending otherwise.
- **The runway forecast is a simple linear projection**, not seasonally adjusted. It's honest about what it is: a straight-line extrapolation of recent average cash flow.
- **Anomaly detection uses statistical rules** (outliers, duplicates), not a trained fraud model. Good enough to demonstrate the pattern, not production-grade fraud detection.
- **SQLite is single-user.** It's the right tool for a local demo; it is not the right tool for ten people using this at once.

## What I'd build next with more time

- Multi-user support with real authentication
- A trained anomaly-detection model instead of statistical thresholds
- Integration with an actual accounting system for real opening balances
- Migration to Google's newer `google.genai` SDK (the current package is deprecated, though still functional)

---

## A note on how this was actually built

This wasn't a smooth ten-day build, and I think that's worth saying plainly. Along the way I hit a Gemini quota error from calling the API too eagerly (fixed with a click-to-review pattern that turned into a real cost-control design), had a model I was using get deprecated mid-project (caught with a debug trace, fixed across every affected file), and found two genuine bugs — a numpy/JSON serialization issue and a parameter-order mismatch in my comparison logic — purely because I deliberately tested with malformed and edge-case data instead of only testing the happy path. Every one of those was a real problem that a "review with AI" click would have quietly surfaced in front of a live audience if I hadn't caught it first.

---

