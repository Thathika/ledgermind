import sqlite3
import json
from datetime import datetime


DB_PATH = "ledgermind_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            summary TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_run(summary):
    init_db()

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "INSERT INTO runs (timestamp, summary) VALUES (?, ?)",
        (
            datetime.now().isoformat(),
            json.dumps(summary)
        )
    )

    conn.commit()
    conn.close()


def get_previous_run():
    init_db()

    conn = sqlite3.connect(DB_PATH)

    row = conn.execute("""
        SELECT summary
        FROM runs
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if row is None:
        return None

    return json.loads(row[0])


def get_run_count():
    init_db()

    conn = sqlite3.connect(DB_PATH)

    count = conn.execute(
        "SELECT COUNT(*) FROM runs"
    ).fetchone()[0]

    conn.close()

    return count


if __name__ == "__main__":

    fake_summary_1 = {
        "current_balance": 2500000,
        "matched": 180,
        "ambiguous": 12,
        "anomalies_flagged": 10,
        "runway_days": 75
    }

    fake_summary_2 = {
        "current_balance": 2700000,
        "matched": 185,
        "ambiguous": 8,
        "anomalies_flagged": 7,
        "runway_days": 90
    }

    save_run(fake_summary_1)

    print(
        "Previous run before second save:",
        get_previous_run()
    )

    save_run(fake_summary_2)

    print(
        "Previous run after second save:",
        get_previous_run()
    )

    print(
        "Total runs stored:",
        get_run_count()
    )