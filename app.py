import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from reconcile import reconcile
from ai_resolver import resolve_ambiguous
from anomaly_detector import flag_candidates, explain_anomaly
from data_cleaning import clean_data
from forecast import calculate_runway

from controller import build_summary, generate_briefing


try:
    from controller import generate_diff_narrative
except ImportError:
    from controller import generate_change_narrative as generate_diff_narrative

from alerts import evaluate_alerts

from history import (
    save_run,
    get_previous_run,
    get_run_count
)


st.set_page_config(
    page_title="LedgerMind",
    layout="wide"
)


st.title("LedgerMind — AI Finance Controller")

st.write(
    "Upload your ledger and bank statement to run reconciliation."
)


ledger_file = st.file_uploader(
    "Upload ledger CSV",
    type="csv"
)

bank_file = st.file_uploader(
    "Upload bank statement CSV",
    type="csv"
)


if "ai_results" not in st.session_state:
    st.session_state.ai_results = {}

if "anomaly_results" not in st.session_state:
    st.session_state.anomaly_results = {}

if "briefing" not in st.session_state:
    st.session_state.briefing = None

if "diff_narrative" not in st.session_state:
    st.session_state.diff_narrative = None

if "history_save_pending" not in st.session_state:
    st.session_state.history_save_pending = False


if st.button("Run Reconciliation"):

    if ledger_file is None or bank_file is None:

        st.error(
            "Please upload both files before running reconciliation."
        )

    else:

        raw_ledger_df = pd.read_csv(
            ledger_file,
            dtype={"transaction_id": str}
        )

        raw_bank_df = pd.read_csv(
            bank_file,
            dtype={"transaction_id": str}
        )


        ledger_df, ledger_report = clean_data(
            raw_ledger_df,
            [
                "transaction_id",
                "date",
                "description",
                "amount"
            ],
            label="ledger"
        )


        bank_df, bank_report = clean_data(
            raw_bank_df,
            [
                "transaction_id",
                "date",
                "amount",
                "bank_ref"
            ],
            label="bank statement"
        )


        st.session_state.ledger_report = ledger_report
        st.session_state.bank_report = bank_report


        if ledger_df.empty or bank_df.empty:

            st.session_state.reconciliation_result = None
            st.session_state.briefing = None
            st.session_state.diff_narrative = None
            st.session_state.ai_results = {}
            st.session_state.anomaly_results = {}
            st.session_state.history_save_pending = False

            st.error(
                "One of the files is missing required columns "
                "or has no valid rows after cleaning."
            )

        else:

            result = reconcile(
                ledger_df,
                bank_df
            )

            st.session_state.reconciliation_result = result
            st.session_state.ledger_df = ledger_df
            st.session_state.bank_df = bank_df

            st.session_state.ai_results = {}
            st.session_state.anomaly_results = {}
            st.session_state.briefing = None
            st.session_state.diff_narrative = None

            st.session_state.history_save_pending = True

            st.success(
                "Data cleaned and reconciliation complete."
            )


if "ledger_report" in st.session_state:

    st.divider()

    st.subheader("Data Quality Report")

    col1, col2 = st.columns(2)


    with col1:

        st.markdown("### Ledger")

        st.write(
            f"Rows before cleaning: "
            f"{st.session_state.ledger_report['rows_before']}"
        )

        st.write(
            f"Rows after cleaning: "
            f"{st.session_state.ledger_report['rows_after']}"
        )

        st.write(
            f"Invalid dates: "
            f"{st.session_state.ledger_report['invalid_dates']}"
        )

        st.write(
            f"Invalid amounts: "
            f"{st.session_state.ledger_report['invalid_amounts']}"
        )

        st.write(
            f"Missing essential fields: "
            f"{st.session_state.ledger_report['missing_essential_fields']}"
        )

        st.write(
            f"Duplicates removed: "
            f"{st.session_state.ledger_report['duplicates_removed']}"
        )


        if st.session_state.ledger_report["missing_columns"]:

            st.error(
                "Missing columns: "
                + ", ".join(
                    st.session_state.ledger_report["missing_columns"]
                )
            )

        else:

            st.success(
                "Ledger data passed validation."
            )


    with col2:

        st.markdown("### Bank Statement")

        st.write(
            f"Rows before cleaning: "
            f"{st.session_state.bank_report['rows_before']}"
        )

        st.write(
            f"Rows after cleaning: "
            f"{st.session_state.bank_report['rows_after']}"
        )

        st.write(
            f"Invalid dates: "
            f"{st.session_state.bank_report['invalid_dates']}"
        )

        st.write(
            f"Invalid amounts: "
            f"{st.session_state.bank_report['invalid_amounts']}"
        )

        st.write(
            f"Missing essential fields: "
            f"{st.session_state.bank_report['missing_essential_fields']}"
        )

        st.write(
            f"Duplicates removed: "
            f"{st.session_state.bank_report['duplicates_removed']}"
        )


        if st.session_state.bank_report["missing_columns"]:

            st.error(
                "Missing columns: "
                + ", ".join(
                    st.session_state.bank_report["missing_columns"]
                )
            )

        else:

            st.success(
                "Bank statement passed validation."
            )


if (
    "reconciliation_result" in st.session_state
    and st.session_state.reconciliation_result is not None
):

    result = st.session_state.reconciliation_result

    ledger_df = st.session_state.ledger_df
    bank_df = st.session_state.bank_df


    candidates = flag_candidates(
        ledger_df,
        bank_df
    )


    try:

        runway = calculate_runway(
            ledger_df
        )

        runway_error = None

    except Exception as e:

        runway = None
        runway_error = str(e)


    # ============================================================
    # TOP RECONCILIATION METRICS
    # ============================================================

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


    # ============================================================
    # DAY 7 - PROACTIVE ALERTS
    # ============================================================

    st.divider()

    st.subheader("Alerts")


    if runway is not None:

        alert_list = evaluate_alerts(
            result,
            len(candidates),
            runway
        )


        if len(alert_list) > 0:

            for alert in alert_list:

                if alert["severity"] == "critical":

                    st.error(
                        f"🔴 {alert['message']}"
                    )

                elif alert["severity"] == "warning":

                    st.warning(
                        f"🟡 {alert['message']}"
                    )

                else:

                    st.info(
                        f"🔵 {alert['message']}"
                    )

        else:

            st.success(
                "No alerts — books look healthy."
            )

    else:

        st.warning(
            "Alerts unavailable because the cash runway "
            "forecast could not be generated."
        )


    # ============================================================
    # FINANCIAL BRIEFING
    # ============================================================

    st.divider()

    st.subheader("Financial Briefing")


    if runway is None:

        st.warning(
            "Financial briefing unavailable because the "
            "cash runway forecast could not be generated."
        )

        st.write(
            f"Reason: {runway_error}"
        )

    else:

        st.info(
            "The Controller uses Gemini to generate this financial "
            "briefing from the reconciliation, anomaly, and cash-flow results."
        )


        if st.session_state.briefing is None:

            with st.spinner(
                "Controller agent is synthesizing the briefing..."
            ):

                summary = build_summary(
                    result,
                    len(candidates),
                    runway
                )

                st.session_state.briefing = generate_briefing(
                    summary
                )


        st.info(
            st.session_state.briefing
        )


    # ============================================================
    # DAY 8 - WHAT CHANGED SINCE LAST RUN
    # ============================================================

    st.divider()

    st.subheader(
        "What Changed Since Last Run"
    )


    if runway is None:

        st.warning(
            "What Changed is unavailable because the "
            "cash runway forecast could not be generated."
        )

    else:

        current_summary = build_summary(
            result,
            len(candidates),
            runway
        )


        previous_summary = get_previous_run()


        if previous_summary is None:

            st.info(
                f"This is run #{get_run_count() + 1} — "
                "no previous run to compare against yet."
            )

        else:

            if st.session_state.diff_narrative is None:

                with st.spinner(
                    "Controller is comparing this run with the previous run..."
                ):

                    st.session_state.diff_narrative = (
                        generate_diff_narrative(
                            current_summary,
                            previous_summary
                        )
                    )


            st.info(
                st.session_state.diff_narrative
            )


        if st.session_state.history_save_pending:

            save_run(
                current_summary
            )

            st.session_state.history_save_pending = False


    # ============================================================
    # MATCHED TRANSACTIONS
    # ============================================================

    st.divider()

    st.subheader(
        "Matched transactions"
    )


    if len(result["matched"]) > 0:

        st.dataframe(
            pd.DataFrame(result["matched"]),
            width="stretch"
        )

    else:

        st.write(
            "No matched transactions."
        )


    # ============================================================
    # AMBIGUOUS TRANSACTIONS - AI REVIEW
    # ============================================================

    st.divider()

    st.subheader(
        "Ambiguous transactions — AI review"
    )


    st.info(
        "Gemini is used for detailed transaction review only "
        "when you click 'Review with AI'."
    )


    if len(result["ambiguous"]) == 0:

        st.success(
            "No ambiguous transactions to review."
        )

    else:

        for index, item in enumerate(
            result["ambiguous"]
        ):

            ledger_matches = ledger_df[
                ledger_df["transaction_id"].astype(str)
                == str(item["ledger_id"])
            ]


            bank_matches = bank_df[
                bank_df["bank_ref"].astype(str)
                == str(item["bank_ref"])
            ]


            if ledger_matches.empty or bank_matches.empty:

                st.warning(
                    f"Could not find data for "
                    f"{item['ledger_id']} or "
                    f"{item['bank_ref']}."
                )

                continue


            ledger_row = ledger_matches.iloc[0]
            bank_row = bank_matches.iloc[0]


            transaction_key = (
                f"{item['ledger_id']}_{item['bank_ref']}"
            )


            with st.expander(
                f"{item['ledger_id']} ↔ {item['bank_ref']}"
            ):

                # SOURCE DATA

                col1, col2 = st.columns(2)


                with col1:

                    st.markdown("### Ledger")

                    st.write(
                        f"**Transaction ID:** "
                        f"{ledger_row['transaction_id']}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{ledger_row['date']}"
                    )

                    st.write(
                        f"**Description:** "
                        f"{ledger_row['description']}"
                    )

                    st.write(
                        f"**Amount:** "
                        f"₹{ledger_row['amount']}"
                    )


                with col2:

                    st.markdown("### Bank")

                    st.write(
                        f"**Bank Reference:** "
                        f"{bank_row['bank_ref']}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{bank_row['date']}"
                    )

                    st.write(
                        f"**Amount:** "
                        f"₹{bank_row['amount']}"
                    )


                # AUDIT TRAIL

                st.divider()


                if transaction_key in st.session_state.ai_results:

                    ai_result = (
                        st.session_state.ai_results[
                            transaction_key
                        ]
                    )


                    if ai_result["status"] == "success":

                        if ai_result["same_transaction"] is True:

                            st.success(
                                "AI Decision: Same transaction"
                            )

                        elif ai_result["same_transaction"] is False:

                            st.error(
                                "AI Decision: Needs manual review"
                            )

                        else:

                            st.warning(
                                "AI Decision: Could not determine"
                            )


                        confidence = ai_result.get(
                            "confidence",
                            0
                        )


                        try:

                            confidence = float(
                                confidence
                            )

                        except (TypeError, ValueError):

                            confidence = 0


                        confidence = max(
                            0,
                            min(
                                100,
                                confidence
                            )
                        )


                        st.write(
                            f"**AI Confidence:** "
                            f"{confidence:.0f}%"
                        )

                        st.progress(
                            confidence / 100
                        )

                        st.write(
                            f"**AI Reasoning:** "
                            f"{ai_result['reasoning']}"
                        )


                    else:

                        st.warning(
                            "Gemini is temporarily unavailable."
                        )

                        st.write(
                            f"**Reason:** "
                            f"{ai_result['reasoning']}"
                        )

                        st.info(
                            "You can try the AI review again later."
                        )


                else:

                    if st.button(
                        "Review with AI",
                        key=f"ai_review_{index}"
                    ):

                        with st.spinner(
                            "Gemini is reviewing this transaction..."
                        ):

                            try:

                                ai_result = resolve_ambiguous(
                                    ledger_row,
                                    bank_row
                                )


                                st.session_state.ai_results[
                                    transaction_key
                                ] = {
                                    "status": "success",
                                    "same_transaction":
                                        ai_result.get(
                                            "same_transaction"
                                        ),
                                    "confidence":
                                        ai_result.get(
                                            "confidence",
                                            0
                                        ),
                                    "reasoning":
                                        ai_result.get(
                                            "reasoning",
                                            ""
                                        )
                                }


                                st.rerun()


                            except Exception as e:

                                st.session_state.ai_results[
                                    transaction_key
                                ] = {
                                    "status": "error",
                                    "same_transaction": None,
                                    "confidence": 0,
                                    "reasoning": str(e)
                                }


                                st.rerun()


    # ============================================================
    # ANOMALY DETECTION
    # ============================================================

    st.divider()

    st.subheader(
        "Anomaly Detection"
    )


    st.info(
        "Anomalies are detected using rule-based checks first. "
        "Gemini provides a detailed explanation only when you click "
        "'Review with AI'."
    )


    if len(candidates) == 0:

        st.success(
            "No anomalies were flagged by the rule-based checks."
        )

    else:

        st.write(
            f"{len(candidates)} transactions flagged for review."
        )


        for index, candidate in enumerate(candidates):

            row = candidate["row"]

            bank_ref = str(
                candidate["bank_ref"]
            )

            reason = candidate["reason"]

            anomaly_key = (
                f"anomaly_{bank_ref}"
            )


            with st.expander(
                f"{bank_ref} — {reason}"
            ):

                # SOURCE DATA

                col1, col2 = st.columns(2)


                with col1:

                    st.write(
                        f"**Transaction ID:** "
                        f"{row['transaction_id']}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{row['date']}"
                    )


                with col2:

                    st.write(
                        f"**Amount:** "
                        f"₹{row['amount']}"
                    )

                    st.write(
                        f"**Flag reason:** "
                        f"{reason}"
                    )


                # AUDIT TRAIL

                st.divider()


                if anomaly_key in st.session_state.anomaly_results:

                    anomaly_result = (
                        st.session_state.anomaly_results[
                            anomaly_key
                        ]
                    )


                    if anomaly_result["status"] == "success":

                        st.success(
                            "AI anomaly review completed."
                        )


                        confidence = anomaly_result.get(
                            "confidence",
                            0
                        )


                        try:

                            confidence = float(
                                confidence
                            )

                        except (TypeError, ValueError):

                            confidence = 0


                        confidence = max(
                            0,
                            min(
                                100,
                                confidence
                            )
                        )


                        st.write(
                            f"**AI Confidence:** "
                            f"{confidence:.0f}%"
                        )

                        st.progress(
                            confidence / 100
                        )

                        st.write(
                            f"**AI Explanation:** "
                            f"{anomaly_result['explanation']}"
                        )


                    else:

                        st.warning(
                            "Gemini is temporarily unavailable."
                        )

                        st.write(
                            f"**Reason:** "
                            f"{anomaly_result['explanation']}"
                        )

                        st.info(
                            "You can try the AI review again later."
                        )


                else:

                    if st.button(
                        "Review with AI",
                        key=f"anomaly_review_{index}_{bank_ref}"
                    ):

                        with st.spinner(
                            "Gemini is analyzing this anomaly..."
                        ):

                            try:

                                ai_result = explain_anomaly(
                                    row,
                                    reason
                                )


                                st.session_state.anomaly_results[
                                    anomaly_key
                                ] = {
                                    "status": "success",
                                    "confidence":
                                        ai_result.get(
                                            "confidence",
                                            0
                                        ),
                                    "explanation":
                                        ai_result.get(
                                            "explanation",
                                            ""
                                        )
                                }


                                st.rerun()


                            except Exception as e:

                                st.session_state.anomaly_results[
                                    anomaly_key
                                ] = {
                                    "status": "error",
                                    "confidence": 0,
                                    "explanation": str(e)
                                }


                                st.rerun()


    # ============================================================
    # CASH RUNWAY FORECAST
    # ============================================================

    st.divider()

    st.subheader(
        "Cash Runway Forecast"
    )


    st.info(
        "This forecast uses the transaction history to calculate "
        "the current balance, average daily cash flow, and estimated "
        "cash runway."
    )


    if runway is None:

        st.error(
            "Could not generate the cash runway forecast."
        )

        st.write(
            f"Reason: {runway_error}"
        )

    else:

        col1, col2, col3 = st.columns(3)


        col1.metric(
            "Current Balance",
            f"₹{runway['current_balance']:,.0f}"
        )


        if runway["avg_daily_net"] >= 0:

            col2.metric(
                "Avg Daily Net Flow",
                f"+₹{runway['avg_daily_net']:,.0f}"
            )

        else:

            col2.metric(
                "Avg Daily Burn",
                f"₹{runway['daily_burn']:,.0f}"
            )


        if runway["runway_days"] is None:

            col3.metric(
                "Runway",
                "Cash flow positive"
            )

        else:

            col3.metric(
                "Runway",
                f"{runway['runway_days']} days"
            )


        st.markdown(
            "### 90-Day Cash Projection"
        )


        fig = go.Figure()


        fig.add_trace(
            go.Scatter(
                x=runway["projection_df"]["date"],
                y=runway["projection_df"]["projected_balance"],
                mode="lines",
                name="Projected balance",
                line=dict(width=3)
            )
        )


        fig.update_layout(
            title="90-day cash projection",
            xaxis_title="Date",
            yaxis_title="Balance (₹)",
            yaxis=dict(
                rangemode="tozero"
                if runway["current_balance"] < 500000
                else "normal"
            ),
            height=350,
            margin=dict(
                l=40,
                r=20,
                t=40,
                b=40
            )
        )


        st.plotly_chart(
            fig,
            width="stretch"
        )


        st.write(
            f"**Average daily net flow:** "
            f"₹{runway['avg_daily_net']:,.2f}"
        )


    # ============================================================
    # UNMATCHED TRANSACTIONS
    # ============================================================

    st.divider()

    st.subheader(
        "Unmatched ledger transaction IDs"
    )


    if len(result["unmatched_ledger"]) > 0:

        st.write(
            result["unmatched_ledger"]
        )

    else:

        st.write(
            "No unmatched ledger transactions."
        )


    st.subheader(
        "Unmatched bank references"
    )


    if len(result["unmatched_bank"]) > 0:

        st.write(
            result["unmatched_bank"]
        )

    else:

        st.write(
            "No unmatched bank transactions."
        )