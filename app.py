import streamlit as st
import pandas as pd
from reconcile import reconcile

st.set_page_config(page_title="LedgerMind", layout="wide")

st.title("LedgerMind — AI Finance Controller")

st.write("Upload your ledger and bank statement to run reconciliation.")

ledger_file = st.file_uploader(
    "Upload ledger CSV",
    type="csv"
)

bank_file = st.file_uploader(
    "Upload bank statement CSV",
    type="csv"
)

if st.button("Run Reconciliation"):

    if ledger_file is None or bank_file is None:
        st.error("Please upload both files before running reconciliation.")

    else:
        ledger_df = pd.read_csv(
            ledger_file,
            dtype={"transaction_id": str}
        )

        bank_df = pd.read_csv(
            bank_file,
            dtype={"transaction_id": str}
        )

        result = reconcile(ledger_df, bank_df)

        st.success("Reconciliation complete.")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Matched",
            len(result["matched"])
        )

        col2.metric(
            "Ambiguous",
            len(result["ambiguous"])
        )

        col3.metric(
            "Unmatched (ledger)",
            len(result["unmatched_ledger"])
        )

        col4.metric(
            "Unmatched (bank)",
            len(result["unmatched_bank"])
        )

        st.subheader("Matched transactions")

        st.dataframe(
            pd.DataFrame(result["matched"])
        )

        st.subheader("Ambiguous transactions (date mismatch)")

        st.dataframe(
            pd.DataFrame(result["ambiguous"])
        )

        st.subheader("Unmatched ledger transaction IDs")

        st.write(
            result["unmatched_ledger"]
        )

        st.subheader("Unmatched bank references")

        st.write(
            result["unmatched_bank"]
        )