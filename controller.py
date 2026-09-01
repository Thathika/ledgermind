import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-3.6-flash")


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
        summary["unmatched_ledger"]
        + summary["unmatched_bank"]
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
Do not include a preamble.
"""

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


def generate_change_narrative(previous_summary, current_summary):
    """
    Compare the previous dashboard run with the current run
    and generate a short plain-English explanation of what changed.
    """

    if previous_summary is None:
        return "This is the first recorded run, so there is no previous run to compare with."

    changes = []

    fields = [
        ("current_balance", "cash balance"),
        ("matched", "matched transactions"),
        ("ambiguous", "ambiguous transactions"),
        ("unmatched_ledger", "unmatched ledger transactions"),
        ("unmatched_bank", "unmatched bank transactions"),
        ("anomalies_flagged", "anomalies flagged"),
        ("avg_daily_net", "average daily net cash flow"),
        ("runway_days", "cash runway")
    ]

    for field, label in fields:

        previous = previous_summary.get(field)
        current = current_summary.get(field)

        if previous == current:
            continue

        if field == "current_balance":

            if previous is None or current is None:
                changes.append(
                    f"{label.capitalize()} changed from "
                    f"{previous} to {current}."
                )
            else:
                difference = current - previous

                changes.append(
                    f"Cash balance changed from "
                    f"₹{previous:,.0f} to ₹{current:,.0f}, "
                    f"a change of ₹{difference:+,.0f}."
                )

        elif field == "avg_daily_net":

            if previous is None or current is None:
                changes.append(
                    f"{label.capitalize()} changed from "
                    f"{previous} to {current}."
                )
            else:
                difference = current - previous

                changes.append(
                    f"Average daily net cash flow changed from "
                    f"₹{previous:,.0f} to ₹{current:,.0f}, "
                    f"a change of ₹{difference:+,.0f}."
                )

        elif field == "runway_days":

            if previous is None and current is None:
                continue

            if previous is None:
                changes.append(
                    f"Cash runway changed from unavailable "
                    f"to {current} days."
                )

            elif current is None:
                changes.append(
                    f"Cash runway changed from "
                    f"{previous} days to no immediate runway risk."
                )

            else:
                difference = current - previous

                changes.append(
                    f"Cash runway changed from "
                    f"{previous} days to {current} days, "
                    f"a change of {difference:+} days."
                )

        else:

            if previous is None or current is None:
                changes.append(
                    f"{label.capitalize()} changed from "
                    f"{previous} to {current}."
                )
            else:
                difference = current - previous

                changes.append(
                    f"{label.capitalize()} changed from "
                    f"{previous} to {current}, "
                    f"a change of {difference:+}."
                )

    if not changes:
        return "No changes were detected compared with the previous run."

    detected_changes = "\n".join(
        f"- {change}"
        for change in changes
    )

    prompt = f"""You are a financial controller explaining what changed between two dashboard runs.

Previous run:
{json.dumps(previous_summary, indent=2)}

Current run:
{json.dumps(current_summary, indent=2)}

Detected changes:
{detected_changes}

Write a short explanation for a founder with no accounting background.

Requirements:
- Explain the most important changes first.
- Use plain English.
- Use only the numbers provided.
- Do not invent any information.
- Do not make unsupported assumptions.
- Explain whether the changes are positive, negative, or require attention when this is clear from the numbers.
- Keep the response to 3-5 sentences.
- Do not use accounting jargon.
- Do not include a heading.
- Do not use markdown.
- Respond with ONLY the explanation.
"""

    try:
        response = model.generate_content(prompt)

        if response and response.text:
            text = response.text.strip()

            if text:
                return text

    except Exception:
        pass

    return " ".join(changes)


if __name__ == "__main__":

    fake_previous_summary = {
        "matched": 180,
        "ambiguous": 12,
        "unmatched_ledger": 8,
        "unmatched_bank": 9,
        "anomalies_flagged": 15,
        "current_balance": 2800000,
        "avg_daily_net": 42000,
        "daily_burn": 0,
        "runway_days": None
    }

    fake_current_summary = {
        "matched": 182,
        "ambiguous": 10,
        "unmatched_ledger": 8,
        "unmatched_bank": 9,
        "anomalies_flagged": 17,
        "current_balance": 2863116.01,
        "avg_daily_net": 48527.39,
        "daily_burn": 0,
        "runway_days": None
    }

    print("Previous Summary:")
    print(
        json.dumps(
            fake_previous_summary,
            indent=2
        )
    )

    print("\nCurrent Summary:")
    print(
        json.dumps(
            fake_current_summary,
            indent=2
        )
    )

    print("\nWhat Changed:")
    print(
        generate_change_narrative(
            fake_previous_summary,
            fake_current_summary
        )
    )