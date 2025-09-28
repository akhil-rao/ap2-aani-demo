"""
Streamlit MVP Prototype: AP2 mandates + Aani-style payment simulation
Filename: PaymentLabs_AP2_Aani_Demo.py
Run: pip install streamlit && streamlit run PaymentLabs_AP2_Aani_Demo.py

Features:
- User Consent Screen -> create IntentMandate for AED 500 via Aani
- Mandate Registry View -> shows CartMandate, IntentMandate, PaymentMandate
- Payment Execution Simulation -> mocked Aani test-mode API call
- Audit Trail View -> Signed Mandate + Agent Identity + Transaction ID

This is a single-file demo using dummy data and mocked APIs so you have a clickable sandbox.
"""

import streamlit as st
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
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
    """Simple HMAC-based 'signature' for demo audit trail."""
    payload_json = json.dumps(payload, sort_keys=True).encode()
    digest = hmac.new(secret.encode(), payload_json, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()

def mock_aani_payment_api(mandate: Dict[str, Any]) -> Dict[str, Any]:
    """Mocked Aani payment API response in test-mode. Replace with real HTTP calls if needed."""
    txid = "TX-" + uuid.uuid4().hex[:12].upper()
    # random settlement simulation
    status = random.choice(["SETTLED", "PENDING", "FAILED"])
    response = {
        "transaction_id": txid,
        "status": status,
        "settlement_time": now_iso() if status == "SETTLED" else None,
        "amount": mandate.get("amount"),
        "currency": mandate.get("currency", "AED"),
        "meta": {
            "processor": "Aani-mock",
            "mode": "test"
        }
    }
    return response

# ---------------------------
# Data models
# ---------------------------

@dataclass
class Mandate:
    mandate_id: str
    mandate_type: str  # CartMandate | IntentMandate | PaymentMandate
    amount: float
    currency: str
    created_at: str
    issued_by: str  # user/agent
    status: str  # e.g., ISSUED | ACTIVE | EXECUTED | REVOKED
    meta: Dict[str, Any]

    def to_dict(self):
        return asdict(self)

# ---------------------------
# Initialize session state
# ---------------------------

if "mandates" not in st.session_state:
    # seed with a CartMandate and a PaymentMandate example
    st.session_state.mandates = [
        Mandate(
            mandate_id="M-" + uuid.uuid4().hex[:8].upper(),
            mandate_type="CartMandate",
            amount=123.45,
            currency="AED",
            created_at=now_iso(),
            issued_by="merchant:nucleus-demo",
            status="ISSUED",
            meta={"cart_id": "CART-001", "items": [
                {"name": "Widget A", "price": 100.00}, {"name": "Service B", "price": 23.45}
            ]}
        ),
        Mandate(
            mandate_id="M-" + uuid.uuid4().hex[:8].upper(),
            mandate_type="PaymentMandate",
            amount=250.00,
            currency="AED",
            created_at=now_iso(),
            issued_by="merchant:acceleron",
            status="EXECUTED",
            meta={"reference": "PAY-REF-09"}
        )
    ]

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

if "agent_identity" not in st.session_state:
    st.session_state.agent_identity = {
        "agent_id": "agent-nucleus-demo",
        "name": "Nucleus Demo Agent",
        "pubkey": "demo_pubkey_ABC123",
    }

# ---------------------------
# UI Layout
# ---------------------------

st.set_page_config(page_title="PaymentLabs AP2 + Aani Demo", layout="wide")
st.title("PaymentLabs — AP2 mandates + Aani (mock) demo")

menu = st.sidebar.radio("Demo view", ["Consent Screen", "Mandate Registry", "Payment Execution", "Audit Trail", "About & Run Instructions"]) 

# ---------------------------
# Consent Screen
# ---------------------------

if menu == "Consent Screen":
    st.header("User Consent — create an IntentMandate")
    st.markdown("This screen simulates the user approving an IntentMandate for a future charge. The demo creates a signed mandate and records it in the registry.")

    with st.form("consent_form"):
        user_name = st.text_input("User name", value="Alice Demo")
        agent = st.selectbox("Agent receiving mandate", options=[st.session_state.agent_identity['agent_id'], "merchant:demo-store"])
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

        # create signed representation for audit
        signed = sign_payload(mandate.to_dict())
        audit_entry = {
            "event": "MANDATE_ISSUED",
            "mandate_id": mandate.mandate_id,
            "mandate_type": mandate.mandate_type,
            "agent": agent,
            "user": user_name,
            "timestamp": now_iso(),
            "signature": signed,
        }
        st.session_state.audit_log.append(audit_entry)

        st.success(f"IntentMandate {mandate_id} issued and recorded. You can view it under 'Mandate Registry'.")
        st.json(mandate.to_dict())

# ---------------------------
# Mandate Registry
# ---------------------------

elif menu == "Mandate Registry":
    st.header("Mandate Registry")
    st.markdown("Shows issued mandates (CartMandate, IntentMandate, PaymentMandate). You can inspect, activate, revoke or convert intent -> payment.")

    mandates = st.session_state.mandates
    rows = []
    for m in mandates:
        rows.append({
            "mandate_id": m.mandate_id,
            "type": m.mandate_type,
            "amount": f"{m.amount:.2f}",
            "currency": m.currency,
            "status": m.status,
            "issued_by": m.issued_by,
            "created_at": m.created_at,
        })

    st.table(rows)

    st.markdown("---")
    sel = st.selectbox("Select a mandate to inspect", options=[m.mandate_id for m in mandates])
    sel_mandate = next((m for m in mandates if m.mandate_id == sel), None)
    if sel_mandate:
        st.subheader(f"Mandate {sel_mandate.mandate_id}")
        st.json(sel_mandate.to_dict())

        cols = st.columns(3)
        if cols[0].button("Convert Intent -> Payment"):
            if sel_mandate.mandate_type != "IntentMandate":
                st.warning("Only IntentMandate can be converted to PaymentMandate in this demo.")
            else:
                sel_mandate.mandate_type = "PaymentMandate"
                sel_mandate.status = "ISSUED"
                st.session_state.audit_log.append({
                    "event": "INTENT_CONVERTED",
                    "mandate_id": sel_mandate.mandate_id,
                    "timestamp": now_iso(),
                    "note": "Converted by demo user",
                })
                st.success("Converted to PaymentMandate. You can now execute a payment from 'Payment Execution'.")
                st.experimental_rerun()

        if cols[1].button("Revoke Mandate"):
            sel_mandate.status = "REVOKED"
            st.session_state.audit_log.append({
                "event": "MANDATE_REVOKED",
                "mandate_id": sel_mandate.mandate_id,
                "timestamp": now_iso(),
                "note": "Revoked by demo user",
            })
            st.success("Mandate revoked.")
            st.experimental_rerun()

        if cols[2].button("Export Mandate JSON"):
            st.download_button("Download JSON", data=json.dumps(sel_mandate.to_dict(), indent=2), file_name=f"{sel_mandate.mandate_id}.json")

# ---------------------------
# Payment Execution Simulation
# ---------------------------

elif menu == "Payment Execution":
    st.header("Payment Execution — simulate Aani (test-mode)")
    st.markdown("Select a PaymentMandate and execute. This demo calls a mocked Aani API and records the result in the audit trail.")

    available = [m for m in st.session_state.mandates if m.mandate_type in ("PaymentMandate", "IntentMandate") and m.status in ("ACTIVE", "ISSUED")]
    if not available:
        st.info("No active Payment/Intent mandates available. Create one in Consent Screen or convert an intent in Mandate Registry.")
    else:
        options = {m.mandate_id: m for m in available}
        sel_id = st.selectbox("Choose mandate to execute", options=list(options.keys()))
        mandate = options[sel_id]
        st.write("Mandate details")
        st.json(mandate.to_dict())

        if st.button("Execute Payment (mock Aani)"):
            st.info("Calling Aani (mock) ...")
            response = mock_aani_payment_api(mandate.to_dict())

            if response["status"] == "SETTLED":
                mandate.status = "EXECUTED"
            elif response["status"] == "FAILED":
                mandate.status = "FAILED"
            else:
                mandate.status = "PENDING"

            audit_entry = {
                "event": "PAYMENT_EXECUTED",
                "mandate_id": mandate.mandate_id,
                "transaction_id": response["transaction_id"],
                "status": response["status"],
                "timestamp": now_iso(),
                "agent": st.session_state.agent_identity,
                "signature": sign_payload({"mandate_id": mandate.mandate_id, "txid": response["transaction_id"]}),
                "response": response,
            }
            st.session_state.audit_log.append(audit_entry)

            st.success(f"Payment simulation finished: {response['status']}")
            st.json(response)

# ---------------------------
# Audit Trail View
# ---------------------------

elif menu == "Audit Trail":
    st.header("Audit Trail — Signed Mandates / Agent Identity / Transaction IDs")
    st.markdown("Chronological audit log of demo events. Each entry contains a signature shown as a base64 string (HMAC SHA256 demo).")

    logs = list(reversed(st.session_state.audit_log))
    if not logs:
        st.info("No audit events yet. Interact with Consent / Mandate / Payment screens to generate events.")
    else:
        for idx, entry in enumerate(logs):
            with st.expander(f"{entry.get('timestamp', '')} — {entry.get('event')} — {entry.get('mandate_id','')}"):
                st.json(entry)

    st.markdown("---")
    if st.button("Export audit log JSON"):
        st.download_button("Download audit.json", data=json.dumps(st.session_state.audit_log, indent=2), file_name="audit_log.json")

# ---------------------------
# About & Run Instructions
# ---------------------------

elif menu == "About & Run Instructions":
    st.header("About this demo")
    st.markdown(
        """
### What this demo shows
- How an AP2-style flow can sit on top of a payments provider (Aani) using three mandate concepts: CartMandate, IntentMandate, PaymentMandate.
- Consent flow to create an IntentMandate (user approval).
- Mandate registry where intents are inspected, converted, revoked, and exported.
- Mocked Aani test-mode payment execution that returns transaction ids and settlement status.
- An audit trail recording signed artifacts and agent identity for compliance demo.

### How to run locally
1. Install Streamlit: `pip install streamlit`
2. Start the app: `streamlit run PaymentLabs_AP2_Aani_Demo.py`

### Replace mock Aani with real API
- Replace `mock_aani_payment_api` with an HTTP client that calls Aani test endpoints.
- Use secure storage for agent secret keys and verify signatures using your production keys.

"""
    )
    st.markdown("---")
    st.markdown("Quick links:")
    st.markdown("- Convert IntentMandate -> PaymentMandate in Mandate Registry to simulate issuance.\n- Use Payment Execution pane to simulate settlement.\n- Audit Trail shows signed records and transaction ids.")

