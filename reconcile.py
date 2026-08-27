import pandas as pd

def reconcile(ledger_df, bank_df):
    matched = []
    unmatched_ledger = []
    ambiguous = []

    bank_remaining = bank_df.copy()
    bank_remaining["used"] = False

    for _, led_row in ledger_df.iterrows():

        # Check for exact match
        exact = bank_remaining[
            (bank_remaining["transaction_id"] == led_row["transaction_id"]) &
            (bank_remaining["amount"] == led_row["amount"]) &
            (bank_remaining["date"] == led_row["date"]) &
            (~bank_remaining["used"])
        ]

        if len(exact) > 0:
            idx = exact.index[0]

            bank_remaining.loc[idx, "used"] = True

            matched.append({
                "ledger_id": led_row["transaction_id"],
                "bank_ref": exact.loc[idx, "bank_ref"],
                "type": "exact"
            })

            continue

        # Check for near match
        near = bank_remaining[
            (bank_remaining["transaction_id"] == led_row["transaction_id"]) &
            (bank_remaining["amount"] == led_row["amount"]) &
            (~bank_remaining["used"])
        ]

        if len(near) > 0:
            idx = near.index[0]

            bank_remaining.loc[idx, "used"] = True

            ambiguous.append({
                "ledger_id": led_row["transaction_id"],
                "bank_ref": near.loc[idx, "bank_ref"],
                "reason": "same id/amount, date differs"
            })

            continue

        # No matching bank transaction found
        unmatched_ledger.append(led_row["transaction_id"])

    # Find bank transactions that were never used
    unmatched_bank = bank_remaining[
        ~bank_remaining["used"]
    ]["bank_ref"].tolist()

    return {
        "matched": matched,
        "ambiguous": ambiguous,
        "unmatched_ledger": unmatched_ledger,
        "unmatched_bank": unmatched_bank
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

    result = reconcile(ledger, bank)

    print(f"Matched exactly: {len(result['matched'])}")
    print(f"Ambiguous (date mismatch): {len(result['ambiguous'])}")
    print(f"Unmatched ledger entries: {len(result['unmatched_ledger'])}")
    print(f"Unmatched bank entries: {len(result['unmatched_bank'])}")