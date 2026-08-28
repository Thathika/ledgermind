import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def resolve_ambiguous(ledger_row, bank_row):

    prompt = f"""
You are a financial reconciliation assistant.

Two transactions share the same transaction ID and amount,
but their dates are different.

Ledger entry:
Transaction ID: {ledger_row['transaction_id']}
Date: {ledger_row['date']}
Description: {ledger_row['description']}
Amount: {ledger_row['amount']}

Bank entry:
Transaction ID: {bank_row['transaction_id']}
Date: {bank_row['date']}
Amount: {bank_row['amount']}

Decide whether these are likely the same transaction.

A difference of 1-2 days may be a normal bank posting delay.
A larger or unusual difference should be flagged for review.

Respond with ONLY valid JSON in this exact format:

{{
    "same_transaction": true,
    "confidence": 90,
    "reasoning": "Short explanation"
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )

        raw_text = response.text.strip()

        try:
            return json.loads(raw_text)

        except json.JSONDecodeError:

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": "AI returned an invalid response format."
            }

    except Exception as e:

        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": "Gemini API quota reached. Please wait and try again."
            }

        return {
            "same_transaction": None,
            "confidence": 0,
            "reasoning": f"AI request failed: {error_message}"
        }


if __name__ == "__main__":

    test_ledger = {
        "transaction_id": "LED0020",
        "date": "2026-07-10",
        "description": "Vendor payment",
        "amount": -8000
    }

    test_bank = {
        "transaction_id": "LED0020",
        "date": "2026-07-12",
        "amount": -8000
    }

    result = resolve_ambiguous(
        test_ledger,
        test_bank
    )

    print(json.dumps(result, indent=2))