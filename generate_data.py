import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
random.seed(42)


def generate_ledger(n=200):
    rows = []

    start_date = datetime(2026, 7, 1)

    for i in range(n):
        date = start_date + timedelta(days=random.randint(0, 60))

        rows.append({
            "transaction_id": f"LED{i:04d}",
            "date": date.strftime("%Y-%m-%d"),
            "description": random.choice([
                fake.company(),
                "Vendor payment",
                "Salary payout",
                "Office rent",
                "AWS invoice",
                "Client payment received"
            ]),
            "amount": round(random.uniform(-50000, 80000), 2)
        })

    return pd.DataFrame(rows)


def generate_bank_statement(
    ledger_df,
    drop_rate=0.05,
    dup_rate=0.03,
    shift_rate=0.05
):
    rows = ledger_df.to_dict("records")

    bank_rows = []

    for r in rows:

        # Sometimes remove a transaction
        if random.random() < drop_rate:
            continue

        row = r.copy()

        # Give the bank transaction a bank reference
        row["bank_ref"] = f"BNK{random.randint(10000, 99999)}"

        # Sometimes shift the date by 1 or 2 days
        if random.random() < shift_rate:
            d = datetime.strptime(
                row["date"],
                "%Y-%m-%d"
            ) + timedelta(
                days=random.choice([1, 2])
            )

            row["date"] = d.strftime("%Y-%m-%d")

        bank_rows.append(row)

        # Sometimes create a duplicate transaction
        if random.random() < dup_rate:
            dup = row.copy()

            dup["bank_ref"] = f"BNK{random.randint(10000, 99999)}"

            bank_rows.append(dup)

    # Add one obvious anomaly
    bank_rows.append({
        "transaction_id": "LED9999",
        "date": "2026-08-14",
        "description": "Vendor payment - URGENT",
        "amount": -420000,
        "bank_ref": "BNK99999"
    })

    return pd.DataFrame(bank_rows)


if __name__ == "__main__":

    ledger = generate_ledger()

    bank = generate_bank_statement(ledger)

    ledger.to_csv("ledger.csv", index=False)

    bank.to_csv("bank_statement.csv", index=False)

    print(
        f"Generated {len(ledger)} ledger rows "
        f"and {len(bank)} bank rows."
    )