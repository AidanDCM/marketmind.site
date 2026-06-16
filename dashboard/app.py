"""Slice 15: Streamlit operator dashboard.

Run:
    streamlit run dashboard/app.py

The dashboard connects directly to the SQLite database (same DATABASE_URL
used by the API). It does NOT call the FastAPI server — it imports from
marketmind directly. This means it shares the same business logic without
requiring the API to be running.

Pages:
  - Overview: today's daily report (revenue, orders, CAC, refund rate)
  - Approval Queue: list pending actions; approve or deny with a note
  - Score a Product: form → explainable product score
"""

from __future__ import annotations

import os
import sys

# Allow running from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from marketmind.db.approval_store import approve, deny, list_approvals, list_pending
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.reports import generate_daily_report
from marketmind.schemas import ApprovalStatus, ProductCandidate
from marketmind.scoring import score_product

# ---------------------------------------------------------------------------
# Engine (shared across reruns via session state)
# ---------------------------------------------------------------------------


def _get_engine():
    if "engine" not in st.session_state:
        engine = make_engine()
        Base.metadata.create_all(engine)
        st.session_state["engine"] = engine
    return st.session_state["engine"]


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="MarketMind Autopilot", layout="wide")
st.title("MarketMind Autopilot")

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Approval Queue", "Score a Product"],
)

engine = _get_engine()

# ---------------------------------------------------------------------------
# Page: Overview
# ---------------------------------------------------------------------------

if page == "Overview":
    from datetime import date

    st.header("Daily Overview")
    report_date = st.date_input("Report date", value=date.today()).isoformat()

    pending = list_pending(engine)
    report = generate_daily_report(report_date, [], pending)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Orders", report.metrics.orders)
    col2.metric("Revenue", f"${report.metrics.revenue:,.2f}")
    col3.metric("Ad Spend", f"${report.metrics.ad_spend:,.2f}")
    col4.metric("CAC", f"${report.metrics.cac:,.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Contribution $", f"${report.metrics.contribution_profit:,.2f}")
    col6.metric("Conversion %", f"{report.metrics.conversion_rate:.1%}")
    col7.metric("Refund %", f"{report.metrics.refund_rate:.1%}")

    if report.risks:
        st.subheader("Risks")
        for r in report.risks:
            st.warning(r)

    if report.recommendations:
        st.subheader("Recommendations")
        for r in report.recommendations:
            st.info(r)

    if report.lessons:
        st.subheader("Lessons")
        for lesson in report.lessons:
            st.write(f"• {lesson}")

    if report.pending_approvals:
        st.warning(f"{len(report.pending_approvals)} approval(s) pending — check Approval Queue.")

# ---------------------------------------------------------------------------
# Page: Approval Queue
# ---------------------------------------------------------------------------

elif page == "Approval Queue":
    st.header("Approval Queue")

    status_filter = st.selectbox(
        "Filter by status",
        ["pending", "all", "approved", "denied", "blocked", "auto_allowed"],
    )
    filter_status = None if status_filter == "all" else ApprovalStatus(status_filter)
    records = list_approvals(engine, status=filter_status)

    if not records:
        st.info("No approvals match this filter.")
    else:
        for rec in records:
            with st.expander(
                f"[{rec.status.value.upper()}] {rec.action} — {rec.approval_id}"
            ):
                st.write(f"**Summary:** {rec.summary}")
                st.write(f"**Risk:** {rec.risk_level.value.upper()}")
                st.write(f"**Expected cost:** ${rec.expected_cost:,.2f}")
                if rec.rollback_plan:
                    st.write(f"**Rollback:** {rec.rollback_plan}")
                if rec.reason:
                    st.write(f"**Gate reason:** {rec.reason}")

                if rec.status == ApprovalStatus.PENDING:
                    note = st.text_input("Note (optional)", key=f"note_{rec.approval_id}")
                    col_a, col_b = st.columns(2)
                    if col_a.button("Approve", key=f"approve_{rec.approval_id}"):
                        try:
                            approve(engine, rec.approval_id, note=note)
                            st.success("Approved.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                    if col_b.button("Deny", key=f"deny_{rec.approval_id}"):
                        try:
                            deny(engine, rec.approval_id, note=note)
                            st.error("Denied.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

# ---------------------------------------------------------------------------
# Page: Score a Product
# ---------------------------------------------------------------------------

elif page == "Score a Product":
    st.header("Score a Product Candidate")

    with st.form("score_form"):
        product_name = st.text_input("Product name", "Daily Driver Interior Refresh Kit")
        est_sale_price = st.number_input("Sale price ($)", value=59.0, min_value=0.01)
        est_product_cost = st.number_input("Product cost ($)", value=18.0, min_value=0.0)
        est_shipping_cost = st.number_input("Shipping cost ($)", value=4.0, min_value=0.0)
        competition = st.slider("Competition (higher = worse)", 0.0, 1.0, 0.3)
        return_risk = st.slider("Return risk (higher = worse)", 0.0, 1.0, 0.2)
        evidence_quality = st.slider("Evidence quality", 0.0, 1.0, 0.7)
        personal_fit = st.slider("Personal fit", 0.0, 1.0, 0.9)
        submitted = st.form_submit_button("Score")

    if submitted:
        try:
            candidate = ProductCandidate(
                product_name=product_name,
                est_sale_price=est_sale_price,
                est_product_cost=est_product_cost,
                est_shipping_cost=est_shipping_cost,
                competition=competition,
                return_risk=return_risk,
                evidence_quality=evidence_quality,
                personal_fit=personal_fit,
            )
            result = score_product(candidate)
            verdict_color = {"pass": "green", "review": "orange", "reject": "red"}.get(
                result.verdict.value, "gray"
            )
            st.markdown(
                f"### Verdict: :{verdict_color}[{result.verdict.value.upper()}]"
                f"  (score {result.overall_score:.2f}, confidence {result.confidence:.2f})"
            )
            st.write(result.reason_summary)

            if result.criteria:
                st.subheader("Criterion breakdown")
                import pandas as pd

                df = pd.DataFrame(
                    [
                        {"criterion": c.name, "score": f"{c.raw:.2f}", "reason": c.reason}
                        for c in result.criteria
                    ]
                )
                st.dataframe(df, use_container_width=True)

            if result.risks:
                st.subheader("Risks")
                for r in result.risks:
                    st.warning(r)

        except ValueError as exc:
            st.error(str(exc))
