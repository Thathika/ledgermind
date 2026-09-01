import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.6-flash")


def answer_question(question, context):
    """
    Answers a founder's free-form question, grounded strictly in the
    current run's real data — not general knowledge. This prevents
    the AI from inventing numbers that aren't actually in the dashboard.
    """
    prompt = f"""You are a financial controller assistant. Answer the founder's question using ONLY the data below. If the answer isn't determinable from this data, say so clearly instead of guessing.

Current financial data:
- Reconciliation: {context['matched']} matched, {context['ambiguous']} ambiguous, {context['unmatched_ledger']} unmatched ledger, {context['unmatched_bank']} unmatched bank
- Anomalies flagged: {context['anomalies_flagged']}
- Current balance: ₹{context['current_balance']:,.0f}
- Average daily net cash flow: ₹{context['avg_daily_net']:,.0f}
- Runway: {context['runway_days']} days (None means cash flow positive, no runway risk)
- Financial briefing already generated: "{context.get('briefing', 'not available')}"

Founder's question: {question}

Answer in 2-4 sentences, plain English, no jargon. Do not invent numbers not shown above."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        return text if text else "I couldn't generate an answer — try rephrasing your question."
    except Exception:
        return "The AI assistant is temporarily unavailable. Please review the dashboard sections above directly."


if __name__ == "__main__":
    fake_context = {
        "matched": 182, "ambiguous": 10, "unmatched_ledger": 8, "unmatched_bank": 9,
        "anomalies_flagged": 17, "current_balance": 2863116.01, "avg_daily_net": 48527.39,
        "runway_days": None, "briefing": "Cash position is healthy with no immediate risk."
    }
    print(answer_question("Why is there an anomaly alert?", fake_context))