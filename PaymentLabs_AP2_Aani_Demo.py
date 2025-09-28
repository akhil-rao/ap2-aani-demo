"""
Streamlit MVP Prototype: AP2 mandates + Aani-style payment simulation
Filename: PaymentLabs_AP2_Aani_Demo.py

Polished improvements:
- Global Oxanium font across app.
- Graphviz workflow diagram updated with professional color scheme.
- User node icon-like style, Aani node in blue, audit in green.
- Headers styled bolder (Oxanium 600 weight).
- Overall polished look for enterprise/demo readiness.
"""

import streamlit as st
from dataclasses import dataclass, asdict
from typing import Dict, Any
import uuid
import json
from datetime import datetime
import hashlib
import hmac
import base64
import random

# ---------------------------
# Utility helpers
# ---------------------------

def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sign_payload(payload: Dict[str, Any], secret: str = "demo_secret_key") -> str:
    payload_json = json.dumps(payload, sort_keys=True).encode()
    digest = hmac.new(secret.encode(), payload_json, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()

def mock_aani_payment_api(mandate: Dict[str, Any]) -> Dict[str, Any]:
    txid = "TX-" + uuid.uuid4().hex[:12].upper()
    status = random.choice(["SETTLED", "PENDING", "FAILED"])
    response = {
        "transaction_id": txid,
        "status": status,
        "settlement_time": now_iso() if status == "SETTLED" else None,
        "amount": mandate.get("amount"),
        "currency": mandate.get("currency", "AED"),
        "meta": {"processor": "Aani-mock", "mode": "test"}
    }
    return response

# ---------------------------
# Data models
# ---------------------------

@dataclass
class Mandate:
    mandate_id: str
    mandate_type: str
    amount: float
    currency: str
    created_at: str
    issued_by: str
    status: str
    meta: Dict[str, Any]

    def to_dict(self):
        return asdict(self)

# ---------------------------
# Initialize session state
# ---------------------------

if "mandates" not in st.session_state:
    st.session_state.mandates = []

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

if "agent_identity" not in st.session_state:
    st.session_state.agent_identity = {
        "agent_id": "agent-uae-fintech",
        "name": "UAE Fintech Agent",
        "pubkey": "demo_pubkey_UAE2025",
    }

if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = "Landing"

# ---------------------------
# Page Config + Custom Font
# ---------------------------

st.set_page_config(page_title="AP2 + Aani Open Finance Demo", layout="wide")

# Inject Oxanium font with bolder headers
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@400;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Oxanium', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Navigation helper
# ---------------------------

def go_to(step):
    st.session_state.workflow_step = step

step = st.session_state.workflow_step

# ---------------------------
# Landing Page
# ---------------------------

if step == "Landing":
    st.title("AP2 + Open Finance + Aani — Sandbox Demo")
    st.markdown("""
    ### Introduction
    This sandbox demonstrates how **AP2 mandate logic** works on top of **Aani payments** in an **Open Finance** context.

    **Workflow**:
    1. User Consent (IntentMandate)
    2. Mandate Registry
    3. Payment Execution (mock Aani)
    4. Audit Trail
    """)

    # Graphviz workflow diagram with styled nodes
    st.subheader("Workflow Diagram")
    workflow = """
    digraph {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="Oxanium"];

      User [label="User", shape=circle, fillcolor=lightblue, style=filled, color=black];
      Consent [label="User Consent\\n(IntentMandate)", fillcolor=white, color=black];
      Registry [label="Mandate Registry", fillcolor=lightgrey, color=black];
      Payment [label="Payment Execution\\n(Aani)", fillcolor=lightblue, color=blue, fontcolor=black];
      Audit [label="Audit Trail", fillcolor=lightgreen, color=darkgreen, fontcolor=black];

      User -> Consent -> Registry -> Payment -> Audit;
    }
    """
    st.graphviz_chart(workflow)

    if st.button("Start Demo"):
        go_to("Consent")

# ---------------------------
# Consent Screen
# ---------------------------

elif step == "Consent":
    st.header("Step 1 — User Consent: Create an IntentMandate")
    with st.form("consent_form"):
        user_name = st.text_input("User name", value="Mohammed Al Zarooni")
        agent = st.selectbox("Agent receiving mandate", options=[st.session_state.agent_identity['agent_id'], "merchant:emaar-store"])
        amount = st.number_input("Amount (AED)", value=500.00, min_value=0.01, step=1.00)
        currency = st.selectbox("Currency", ["AED", "USD", "EUR"], index=0)
        purpose = st.text_area("Purpose / Description", value="IntentMandate for subscription / one-off purchase via Aani")
        submitted = st.form_submit_button("Approve IntentMandate")

    if submitted:
        mandate_id = "M-" + uuid.uuid4().hex[:10].upper()
        mandate = Mandate(
            mandate_id=mandate_id,
            mandate_type="IntentMandate",
            amount=float(amount),
            currency=currency,
            created_at=now_iso(),
            issued_by=user_name,
            status="ACTIVE",
            meta={"agent": agent, "purpose": purpose}
        )
        st.session_state.mandates.insert(0, mandate)
        signed = sign_payload(mandate.to_dict())
        st.session_state.audit_log.append({
            "event": "MANDATE_ISSUED",
            "mandate_id": mandate.mandate_id,
            "mandate_type": mandate.mandate_type,
            "agent": agent,
            "user": user_name,
            "timestamp": now_iso(),
            "signature": signed,
        })
        st.success(f"IntentMandate {mandate_id} issued and recorded.")

    if st.button("Next Step → Mandate Registry"):
        go_to("Registry")

# ---------------------------
# Mandate Registry
# ---------------------------

elif step == "Registry":
    st.header("Step 2 — Mandate Registry")
    mandates = st.session_state.mandates
    if not mandates:
        st.info("No mandates yet. Go back to Consent Screen.")
    else:
        rows = [{"mandate_id": m.mandate_id, "type": m.mandate_type, "amount": f"{m.amount:.2f}", "currency": m.currency, "status": m.status, "issued_by": m.issued_by, "created_at": m.created_at} for m in mandates]
        st.table(rows)
        sel = st.selectbox("Select a mandate to inspect", options=[m.mandate_id for m in mandates])
        sel_mandate = next((m for m in mandates if m.mandate_id == sel), None)
        if sel_mandate:
            st.json(sel_mandate.to_dict())
            if st.button("Convert Intent → Payment"):
                if sel_mandate.mandate_type == "IntentMandate":
                    sel_mandate.mandate_type = "PaymentMandate"
                    sel_mandate.status = "ISSUED"
                    st.session_state.audit_log.append({"event": "INTENT_CONVERTED", "mandate_id": sel_mandate.mandate_id, "timestamp": now_iso()})
                    st.success("Converted to PaymentMandate.")
    if st.button("Next Step → Payment Execution"):
        go_to("Payment")

# ---------------------------
# Payment Execution
# ---------------------------

elif step == "Payment":
    st.header("Step 3 — Payment Execution")
    available = [m for m in st.session_state.mandates if m.mandate_type == "PaymentMandate" and m.status in ("ACTIVE", "ISSUED")]
    if not available:
        st.info("No PaymentMandates available. Convert one in Registry.")
    else:
        options = {m.mandate_id: m for m in available}
        sel_id = st.selectbox("Choose mandate to execute", options=list(options.keys()))
        mandate = options[sel_id]
        st.json(mandate.to_dict())
        if st.button("Execute Payment (mock Aani)"):
            response = mock_aani_payment_api(mandate.to_dict())
            mandate.status = response["status"]
            st.session_state.audit_log.append({
                "event": "PAYMENT_EXECUTED",
                "mandate_id": mandate.mandate_id,
                "transaction_id": response["transaction_id"],
                "status": response["status"],
                "timestamp": now_iso(),
                "agent": st.session_state.agent_identity,
                "signature": sign_payload({"mandate_id": mandate.mandate_id, "txid": response["transaction_id"]}),
                "response": response,
            })
            st.success(f"Payment executed. Transaction {response['transaction_id']} → {response['status']}")
            st.json(response)
    if st.button("Next Step → Audit Trail"):
        go_to("Audit")

# ---------------------------
# Audit Trail
# ---------------------------

elif step == "Audit":
    st.header("Step 4 — Audit Trail")
    logs = list(reversed(st.session_state.audit_log))
    if not logs:
        st.info("No audit events yet.")
    else:
        for entry in logs:
            with st.expander(f"{entry.get('timestamp', '')} — {entry.get('event')} — {entry.get('mandate_id','')}"):
                st.json(entry)
    if st.button("🔄 Restart Demo"):
        go_to("Landing")
