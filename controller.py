import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def build_summary(reconciliation_result, anomaly_count, forecast_result):
    return {
        "matched": len(reconciliation_result["matched"]),
        "ambiguous": len(reconciliation_result["ambiguous"]),
        "unmatched_ledger": len(reconciliation_result["unmatched_ledger"]),
        "unmatched_bank": len(reconciliation_result["unmatched_bank"]),
        "anomalies_flagged": anomaly_count,
        "current_balance": forecast_result["current_balance"],
        "avg_daily_net": forecast_result["avg_daily_net"],
        "daily_burn": forecast_result["daily_burn"],
        "runway_days": forecast_result["runway_days"]
    }


def _fallback_briefing(summary):
    if summary["runway_days"] is None:
        runway_text = (
            "there is currently no immediate runway risk since cash flow is positive"
        )
    else:
        runway_text = (
            f"the estimated runway is approximately "
            f"{summary['runway_days']} days"
        )

    flow_direction = (
        "positive"
        if summary["avg_daily_net"] >= 0
        else "negative"
    )

    unmatched_total = (
        summary["unmatched_ledger"] +
        summary["unmatched_bank"]
    )

    return (
        f"Current cash balance is approximately "
        f"₹{summary['current_balance']:,.0f}. "
        f"Average daily cash flow is {flow_direction} at approximately "
        f"₹{abs(summary['avg_daily_net']):,.0f}, and {runway_text}. "
        f"Reconciliation found {summary['matched']} matched transactions, "
        f"{summary['ambiguous']} ambiguous transactions, and "
        f"{unmatched_total} unmatched transactions that may need review. "
        f"Additionally, {summary['anomalies_flagged']} transactions have been "
        f"flagged for anomaly review. "
        f"Overall, review the flagged and unmatched items to confirm that "
        f"the books are fully reconciled."
    )


def generate_briefing(summary):
    runway_value = summary["runway_days"]

    if runway_value is None:
        runway_text = "cash flow positive, no immediate runway risk"
    else:
        runway_text = f"{runway_value} days"

    prompt = f"""You are a financial controller writing a brief daily summary for a founder with no accounting background.

Data:
- Matched transactions: {summary['matched']}
- Ambiguous transactions (need review): {summary['ambiguous']}
- Unmatched ledger transactions: {summary['unmatched_ledger']}
- Unmatched bank transactions: {summary['unmatched_bank']}
- Anomalies flagged: {summary['anomalies_flagged']}
- Current cash balance: ₹{summary['current_balance']:,.0f}
- Average daily net cash flow: ₹{summary['avg_daily_net']:,.0f}
- Runway: {runway_text}

Write a short briefing of 4-6 sentences in plain English with no accounting jargon.

Cover:
1. Overall cash health.
2. Whether runway is a concern.
3. What needs the founder's attention.
4. The reconciliation and anomaly situation.

Be direct and specific with the numbers provided above.

Do not invent, estimate, or calculate any numbers that are not provided above.

Respond with ONLY the briefing text.
Do not include headings.
Do not include markdown formatting.
Do not include a preamble."""


    try:
        response = model.generate_content(prompt)

        if not response or not response.text:
            return _fallback_briefing(summary)

        text = response.text.strip()

        if not text:
            return _fallback_briefing(summary)

        return text

    except Exception:
        return _fallback_briefing(summary)


if __name__ == "__main__":
    fake_reconciliation = {
        "matched": [0] * 182,
        "ambiguous": [0] * 10,
        "unmatched_ledger": [0] * 8,
        "unmatched_bank": [0] * 9
    }

    fake_forecast = {
        "current_balance": 2863116.01,
        "avg_daily_net": 48527.39,
        "daily_burn": 0,
        "runway_days": None
    }

    summary = build_summary(
        fake_reconciliation,
        17,
        fake_forecast
    )

    print("Summary:")
    print(json.dumps(summary, indent=2))

    print("\nBriefing:")
    print(generate_briefing(summary))