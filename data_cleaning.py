import pandas as pd


def clean_data(df, required_columns, label="dataset"):

    report = {
        "label": label,
        "rows_before": len(df),
        "missing_columns": [],
        "invalid_dates": 0,
        "invalid_amounts": 0,
        "missing_essential_fields": 0,
        "duplicates_removed": 0,
        "rows_after": 0
    }

    missing_cols = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_cols:
        report["missing_columns"] = missing_cols
        report["rows_after"] = 0
        return pd.DataFrame(), report

    df = df.copy()

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        report["invalid_dates"] = df["date"].isna().sum()

        df = df[df["date"].notna()]

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        report["invalid_amounts"] = df["amount"].isna().sum()

        df = df[df["amount"].notna()]

    essential = [
        c for c in ["transaction_id"]
        if c in df.columns
    ]

    before_essential = len(df)

    df = df.dropna(
        subset=essential
    )

    report["missing_essential_fields"] = (
        before_essential - len(df)
    )

    before_dupes = len(df)

    df = df.drop_duplicates()

    report["duplicates_removed"] = (
        before_dupes - len(df)
    )

    report["rows_after"] = len(df)

    return df, report


if __name__ == "__main__":

    messy = pd.DataFrame({
        "transaction_id": [
            "LED0001",
            "LED0002",
            None,
            "LED0004",
            "LED0001"
        ],
        "date": [
            "2026-07-05",
            "not-a-date",
            "2026-07-06",
            "2026-07-07",
            "2026-07-05"
        ],
        "description": [
            "AWS",
            "Rent",
            "Salary",
            "Vendor",
            "AWS"
        ],
        "amount": [
            -500,
            "abc",
            3000,
            -1200,
            -500
        ]
    })

    cleaned, report = clean_data(
        messy,
        [
            "transaction_id",
            "date",
            "amount"
        ],
        label="test"
    )

    print(report)
    print(cleaned)