import os
import json
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

client = genai.Client(api_key=api_key)


MODEL_NAME = "gemini-3.6-flash"


def extract_json(text):
    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:
        return json.loads(match.group(0))

    raise json.JSONDecodeError(
        "No valid JSON object found",
        text,
        0
    )


def validate_result(result):

    if not isinstance(result, dict):
        raise ValueError(
            "AI response is not a JSON object."
        )

    if "same_transaction" not in result:
        raise ValueError(
            "AI response is missing 'same_transaction'."
        )

    if "confidence" not in result:
        raise ValueError(
            "AI response is missing 'confidence'."
        )

    if "reasoning" not in result:
        raise ValueError(
            "AI response is missing 'reasoning'."
        )

    same_transaction = result["same_transaction"]

    if not isinstance(same_transaction, bool):
        raise ValueError(
            "'same_transaction' must be true or false."
        )

    try:
        confidence = float(result["confidence"])

    except (TypeError, ValueError):
        raise ValueError(
            "'confidence' must be a number."
        )

    confidence = max(
        0,
        min(100, confidence)
    )

    reasoning = str(
        result["reasoning"]
    ).strip()

    return {
        "same_transaction": same_transaction,
        "confidence": confidence,
        "reasoning": reasoning
    }


def resolve_ambiguous(ledger_row, bank_row):

    prompt = f"""
You are a financial reconciliation assistant.

Compare the following two transactions and determine whether they
are likely to represent the same real-world transaction.

Ledger entry:

Transaction ID: {ledger_row['transaction_id']}
Date: {ledger_row['date']}
Description: {ledger_row['description']}
Amount: {ledger_row['amount']}

Bank entry:

Transaction ID: {bank_row['transaction_id']}
Date: {bank_row['date']}
Amount: {bank_row['amount']}

Rules:

1. The transaction ID and amount are important matching signals.

2. A date difference of 1-2 days may be a normal bank posting delay.

3. A larger date difference should reduce confidence.

4. Consider the transaction description and available details.

5. Give a clear decision.

6. Confidence must be a number from 0 to 100.

Return ONLY a JSON object.

Use exactly this structure:

{{
    "same_transaction": true,
    "confidence": 90,
    "reasoning": "The transaction ID and amount match, and the small date difference may represent a normal bank posting delay."
}}

Do not use Markdown.
Do not use code fences.
Do not add any text before or after the JSON.
"""

    try:

        print("Calling Gemini...")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = response.text.strip()

        print("Gemini response received.")

        if not raw_text:

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": "Gemini returned an empty response."
            }

        try:

            result = extract_json(raw_text)

            return validate_result(result)

        except (
            json.JSONDecodeError,
            ValueError
        ) as e:

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": (
                    "Gemini returned an invalid JSON response. "
                    f"Raw response: {raw_text}"
                )
            }

    except Exception as e:

        error_message = str(e)

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
        ):

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": (
                    "Gemini API quota was reached. "
                    "Please wait and try again."
                )
            }

        if (
            "404" in error_message
            or "NOT_FOUND" in error_message
        ):

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": (
                    f"Gemini model '{MODEL_NAME}' was not found. "
                    "Check the installed Google GenAI SDK and "
                    "available Gemini models."
                )
            }

        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
        ):

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": (
                    "Gemini is temporarily unavailable. "
                    "Please wait a moment and try again."
                )
            }

        if (
            "401" in error_message
            or "403" in error_message
            or "API key" in error_message
        ):

            return {
                "same_transaction": None,
                "confidence": 0,
                "reasoning": (
                    "Gemini API authentication failed. "
                    "Check the GEMINI_API_KEY in the .env file."
                )
            }

        return {
            "same_transaction": None,
            "confidence": 0,
            "reasoning": (
                f"Gemini API request failed: {error_message}"
            )
        }


if __name__ == "__main__":

    print()
    print("=" * 50)
    print("Testing Gemini AI resolver...")
    print("=" * 50)
    print()

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

    print()
    print("AI Result:")
    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print()
    print("=" * 50)
    print("Test completed.")
    print("=" * 50)