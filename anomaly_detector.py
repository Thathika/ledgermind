import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-3.6-flash"


def flag_candidates(ledger_df, bank_df):
    candidates = []

    mean_amt = ledger_df["amount"].mean()
    std_amt = ledger_df["amount"].std()

    for _, row in bank_df.iterrows():

        if std_amt > 0 and abs(row["amount"] - mean_amt) > 4 * std_amt:
            candidates.append({
                "bank_ref": row["bank_ref"],
                "reason": "statistical outlier",
                "row": row
            })

    duplicate_ids = bank_df[
        "transaction_id"
    ][
        bank_df["transaction_id"].duplicated(keep=False)
    ].unique()

    for transaction_id in duplicate_ids:

        duplicate_rows = bank_df[
            bank_df["transaction_id"] == transaction_id
        ]

        for _, row in duplicate_rows.iterrows():

            candidates.append({
                "bank_ref": row["bank_ref"],
                "reason": "duplicate transaction ID",
                "row": row
            })

    seen = set()
    unique_candidates = []

    for candidate in candidates:

        bank_ref = candidate["bank_ref"]

        if bank_ref not in seen:

            seen.add(bank_ref)
            unique_candidates.append(candidate)

    return unique_candidates


def explain_anomaly(candidate_row, reason):

    prompt = f"""
You are a financial anomaly-detection assistant.

A rule-based system flagged this bank transaction for review.

Transaction ID: {candidate_row['transaction_id']}
Date: {candidate_row['date']}
Amount: {candidate_row['amount']}
Bank Reference: {candidate_row['bank_ref']}

Reason flagged:
{reason}

Explain briefly why a finance controller should review this transaction.

Also give a confidence score from 0 to 100 indicating how likely
this is to be a genuine financial anomaly.

Return ONLY valid JSON in this format:

{{
    "confidence": 85,
    "explanation": "Short explanation"
}}
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = response.text.strip()

        raw_text = raw_text.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        result = json.loads(raw_text)

        return {
            "confidence": int(result.get("confidence", 0)),
            "explanation": result.get(
                "explanation",
                "No explanation returned."
            )
        }

    except Exception as error:

        return {
            "confidence": 0,
            "explanation": (
                "Gemini is temporarily unavailable. "
                "The transaction was flagged by the rule-based "
                "anomaly detector. Please try the AI review again later."
            ),
            "error": str(error)
        }


if __name__ == "__main__":

    ledger = pd.read_csv(
        "ledger.csv",
        dtype={"transaction_id": str}
    )

    bank = pd.read_csv(
        "bank_statement.csv",
        dtype={"transaction_id": str}
    )

    candidates = flag_candidates(
        ledger,
        bank
    )

    print(
        f"Flagged {len(candidates)} candidates by rules alone."
    )

    if candidates:

        print("\nFirst candidate:")

        print(
            candidates[0]["bank_ref"]
        )

        print(
            candidates[0]["reason"]
        )

        result = explain_anomaly(
            candidates[0]["row"],
            candidates[0]["reason"]
        )

        print("\nAI Result:")

        print(
            json.dumps(
                result,
                indent=2
            )
        )

    else:

        print(
            "No anomaly candidates found."
        )