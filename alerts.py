def evaluate_alerts(reconciliation_result, anomaly_count, runway_result):
    """
    Rule-based threshold checks.
    Returns alerts sorted by severity.
    """

    alerts = []

    total_ledger = (
        len(reconciliation_result["matched"])
        + len(reconciliation_result["ambiguous"])
        + len(reconciliation_result["unmatched_ledger"])
    )

    if runway_result["runway_days"] is not None:
        if runway_result["runway_days"] < 30:
            alerts.append({
                "severity": "critical",
                "message": (
                    f"Cash runway is only "
                    f"{runway_result['runway_days']} days. "
                    f"Immediate attention needed."
                )
            })

        elif runway_result["runway_days"] < 90:
            alerts.append({
                "severity": "warning",
                "message": (
                    f"Cash runway is "
                    f"{runway_result['runway_days']} days. "
                    f"Consider reviewing spending."
                )
            })

    if total_ledger > 0:
        anomaly_rate = anomaly_count / total_ledger

        if anomaly_rate > 0.05:
            alerts.append({
                "severity": "warning",
                "message": (
                    f"{anomaly_count} transactions flagged as anomalies "
                    f"— higher than usual for this data volume."
                )
            })

        elif anomaly_count > 0:
            alerts.append({
                "severity": "info",
                "message": (
                    f"{anomaly_count} transactions flagged "
                    f"for anomaly review."
                )
            })

    unmatched_total = (
        len(reconciliation_result["unmatched_ledger"])
        + len(reconciliation_result["unmatched_bank"])
    )

    if unmatched_total > 0:
        alerts.append({
            "severity": "info",
            "message": (
                f"{unmatched_total} transactions remain unmatched "
                f"and need manual review."
            )
        })

    if len(reconciliation_result["ambiguous"]) > 0:
        alerts.append({
            "severity": "info",
            "message": (
                f"{len(reconciliation_result['ambiguous'])} ambiguous "
                f"transactions are pending AI or manual review."
            )
        })

    severity_order = {
        "critical": 0,
        "warning": 1,
        "info": 2
    }

    alerts.sort(
        key=lambda alert: severity_order[alert["severity"]]
    )

    return alerts


if __name__ == "__main__":
    fake_reconciliation = {
        "matched": [0] * 182,
        "ambiguous": [0] * 10,
        "unmatched_ledger": [0] * 8,
        "unmatched_bank": [0] * 9
    }

    fake_runway = {
        "runway_days": 25
    }

    result = evaluate_alerts(
        fake_reconciliation,
        17,
        fake_runway
    )

    for alert in result:
        print(
            f"[{alert['severity'].upper()}] "
            f"{alert['message']}"
        )