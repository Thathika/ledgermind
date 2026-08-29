import pandas as pd
from datetime import timedelta


def calculate_runway(ledger_df, projection_days=90):

    df = ledger_df.copy()

    df["date"] = pd.to_datetime(df["date"])

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["date", "amount"]
    )

    df = df.sort_values("date")

    if df.empty:
        return {
            "current_balance": 0,
            "avg_daily_net": 0,
            "daily_burn": 0,
            "runway_days": None,
            "projection_df": pd.DataFrame()
        }

    current_balance = df["amount"].sum()

    daily_net = (
        df.groupby(df["date"].dt.date)["amount"]
        .sum()
    )

    avg_daily_net = daily_net.mean()

    if avg_daily_net < 0:

        daily_burn = abs(avg_daily_net)

        if current_balance > 0:
            runway_days = current_balance / daily_burn
        else:
            runway_days = 0

    else:

        daily_burn = 0
        runway_days = None

    last_date = df["date"].max()

    future_dates = [
        last_date + timedelta(days=i)
        for i in range(1, projection_days + 1)
    ]

    future_balances = [
        current_balance + (avg_daily_net * i)
        for i in range(1, projection_days + 1)
    ]

    projection_df = pd.DataFrame({
        "date": future_dates,
        "projected_balance": future_balances
    })

    return {
        "current_balance": round(
            current_balance,
            2
        ),
        "avg_daily_net": round(
            avg_daily_net,
            2
        ),
        "daily_burn": round(
            daily_burn,
            2
        ),
        "runway_days": (
            round(runway_days)
            if runway_days is not None
            else None
        ),
        "projection_df": projection_df
    }


if __name__ == "__main__":

    ledger = pd.read_csv(
        "ledger.csv",
        dtype={
            "transaction_id": str
        }
    )

    result = calculate_runway(
        ledger
    )

    print(
        f"Current balance: "
        f"{result['current_balance']}"
    )

    print(
        f"Avg daily net flow: "
        f"{result['avg_daily_net']}"
    )

    print(
        f"Daily burn: "
        f"{result['daily_burn']}"
    )

    print(
        f"Runway (days): "
        f"{result['runway_days']}"
    )

    print("\nProjected balances:")

    print(
        result["projection_df"].head()
    )