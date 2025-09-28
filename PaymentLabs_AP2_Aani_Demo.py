"""
Streamlit MVP Prototype: AP2 mandates + Aani-style payment simulation
Filename: PaymentLabs_AP2_Aani_Demo.py

Final version:
- Static PNG workflow diagram embedded on Landing Page (from GitHub).
- All steps: Consent -> CBUAE registration -> Registry -> Risk/AML -> Payment (Aani/UAEFTS) -> Audit.
- Risk screening color-coded (Green/Amber/Red).
- Mock Aani API aligned with professional response format.
- Commentary at each step explaining what was done + Open Finance regulatory link.
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

def mock_aani_payment_api(mandate: Dict[str, Any], rail: str) -> Dict[str, Any]:
    txid = "TX-" + uuid.uuid4().hex[:12].upper()
    status = random.choice(["SETTLED", "PENDING", "FAILED"])

    if status == "SETTLED":
        settlement_time = now_iso()
        processing_code = "00"
        narrative = "Payment successful"
    elif status == "PENDING":
        settlement_time = now_iso()
        processing_code = "09"
        narrative = "Payment pending"
    else:
        settlement_time = now_iso()
        processing_code = "05"
        narrative = "Payment failed"

    response = {
        "transactionId": txid,
        "status": status,
        "amount": f"{mandate.get('amount'):.2f}",
        "currency": mandate.get("currency", "AED"),
        "rail": rail,
        "settlementTime": settlement_time,
        "processingCode": processing_code,
        "narrative": narrative,
        "meta": {
            "processor": "Aani-mock" if rail == "Aani" else "UAEFTS-mock",
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
# Landing Page with PNG from GitHub
# ---------------------------
if step == "Landing":
    st.title("AP2 + Open Finance + Aani — Sandbox Demo")
    st.markdown("""
    ### Introduction
    This sandbox demonstrates how **AP2 mandate logic** works on top of **Aani payments** in an **Open Finance** context.

    **Workflow implemented in this demo:**
    1. User Consent (IntentMandate)
    2. CBUAE Consent Registration (mock)
    3. Mandate Registry
    4. Risk & AML Check (mock)
    5. Payment Execution (choose rail: Aani or UAEFTS)
    6. Audit Trail
    """)

    st.subheader("Workflow Diagram (implemented steps)")
    st.image(
        "https://raw.githubusercontent.com/akhil-rao/ap2-aani-demo/main/Demo%20env%20workflow.png",
        caption="AP2 + UAE Aani/Open Finance Workflow",
        use_container_width=True
    )

    st.caption("**Note:** Risk screening results: LOW = Green, MEDIUM = Amber, HIGH = Red. "
               "Consent registration with CBUAE is simulated for demo purposes.")

    if st.button("Start Demo"):
        go_to("Consent")
        st.rerun()

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
        st.session_state.audit_log.append({
            "event": "CBUAE_CONSENT_REGISTERED",
            "mandate_id": mandate.mandate_id,
            "timestamp": now_iso(),
            "note": "Consent registered with CBUAE API Hub (mock)"
        })
        st.success(f"IntentMandate {mandate_id} issued and registered with CBUAE.")

        st.markdown("""
        ✅ Consent captured as **IntentMandate**.  
        🔒 Registered with **CBUAE Consent & Trust Framework** (mock).  

        **Open Finance Link:**  
        - Aligns with **customer-consent requirements** under UAE’s Open Finance.  
        - Consent must be explicit, digitally signed, and revocable.  
        - Mirrors **PSD2/Open Banking global practices**.
        """)

    if st.button("Next Step → Mandate Registry"):
        go_to("Registry")
        st.rerun()

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

        st.markdown("""
        📑 Mandates recorded in the **AP2 Registry**.  

        **Open Finance Link:**  
        - Provides a **centralized view of customer mandates**.  
        - Supports **customer right to revoke consent**.  
        - Enables transparency and reconciliation across ecosystem participants.
        """)

    if st.button("Next Step → Risk & AML Check"):
        go_to("RiskAML")
        st.rerun()

# ---------------------------
# Risk & AML Check
# ---------------------------
elif step == "RiskAML":
    st.header("Step 3 — Risk & AML Check")
    mandates = [m for m in st.session_state.mandates if m.status in ("ACTIVE", "ISSUED")]
    if not mandates:
        st.info("No mandates available for risk check.")
    else:
        sel_id = st.selectbox("Choose mandate to risk screen", options=[m.mandate_id for m in mandates])
        mandate = next(m for m in mandates if m.mandate_id == sel_id)
        if st.button("Run Risk Screening"):
            risk = random.choice(["LOW", "MEDIUM", "HIGH"])
            st.session_state.audit_log.append({
                "event": "RISK_CHECK",
                "mandate_id": mandate.mandate_id,
                "risk_level": risk,
                "timestamp": now_iso(),
                "note": "Sanctions & AML screening simulated"
            })
            if risk == "LOW":
                st.success(f"Risk screening complete. Risk level: {risk}")
            elif risk == "MEDIUM":
                st.warning(f"Risk screening complete. Risk level: {risk}")
            else:
                st.error(f"Risk screening complete. Risk level: {risk}")

            st.markdown(f"""
            🛡️ Risk screening performed via **AML/Sanctions engine**.  
            Risk signal = **{risk}** (color coded).  

            **Open Finance Link:**  
            - Ensures **FATF/CBUAE AML-CFT compliance** for TPPs.  
            - Demonstrates risk monitoring within Open Finance flows.  
            - Required for **real-time financial crime checks**.
            """)

    if st.button("Next Step → Payment Execution"):
        go_to("Payment")
        st.rerun()

# ---------------------------
# Payment Execution
# ---------------------------
elif step == "Payment":
    st.header("Step 4 — Payment Execution")
    available = [m for m in st.session_state.mandates if m.mandate_type in ("PaymentMandate", "IntentMandate") and m.status in ("ACTIVE", "ISSUED")]
    if not available:
        st.info("No mandates available. Create or convert one earlier.")
    else:
        sel_id = st.selectbox("Choose mandate to execute", options=[m.mandate_id for m in available])
        mandate = next(m for m in available if m.mandate_id == sel_id)
        rail = st.selectbox("Select Settlement Rail", ["Aani", "UAEFTS/RTGS"])
        if st.button("Execute Payment"):
            response = mock_aani_payment_api(mandate.to_dict(), rail)
            mandate.status = response["status"]
            st.session_state.audit_log.append({
                "event": "PAYMENT_EXECUTED",
                "mandate_id": mandate.mandate_id,
                "transaction_id": response["transactionId"],
                "status": response["status"],
                "rail": rail,
                "timestamp": now_iso(),
                "agent": st.session_state.agent_identity,
                "signature": sign_payload({"mandate_id": mandate.mandate_id, "txid": response["transactionId"]}),
                "response": response,
            })
            st.success(f"Payment executed on {rail}. Transaction {response['transactionId']} → {response['status']}")
            st.json(response)

            st.markdown(f"""
            💳 Payment instruction sent to **Payment Agent**.  
            Execution rail = **{rail}**.  

            **Open Finance Link:**  
            - Requires **Strong Customer Authentication (SCA)** before initiation.  
            - Execution routed via **licensed UAE rails** (Aani/UAEFTS).  
            - Demonstrates **secure API-driven initiation** under Open Finance.
            """)

    if st.button("Next Step → Audit Trail"):
        go_to("Audit")
        st.rerun()

# ---------------------------
# Audit Trail
# ---------------------------
elif step == "Audit":
    st.header("Step 5 — Audit Trail")
    logs = list(reversed(st.session_state.audit_log))
    if not logs:
        st.info("No audit events yet.")
    else:
        for entry in logs:
            with st.expander(f"{entry.get('timestamp', '')} — {entry.get('event')} — {entry.get('mandate_id','')}"):
                st.json(entry)

        st.markdown("""
        🕵️ Immutable audit log generated.  
        Includes mandate ID, agent identity, digital signature, transaction ID, and CBUAE registration.  

        **Open Finance Link:**  
        - Provides regulators, banks, and customers with **transparent transaction records**.  
        - Supports **dispute resolution** and **regulatory reporting**.  
        - Core requirement for **trust in Open Finance ecosystems**.
        """)

    if st.button("🔄 Restart Demo"):
        go_to("Landing")
        st.rerun()
"""
Streamlit MVP Prototype: AP2 mandates + Aani-style payment simulation
Filename: PaymentLabs_AP2_Aani_Demo.py

Final version:
- Static PNG workflow diagram embedded on Landing Page (from GitHub).
- All steps: Consent -> CBUAE registration -> Registry -> Risk/AML -> Payment (Aani/UAEFTS) -> Audit.
- Risk screening color-coded (Green/Amber/Red).
- Mock Aani API aligned with professional response format.
- Commentary at each step explaining what was done + Open Finance regulatory link.
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

def mock_aani_payment_api(mandate: Dict[str, Any], rail: str) -> Dict[str, Any]:
    txid = "TX-" + uuid.uuid4().hex[:12].upper()
    status = random.choice(["SETTLED", "PENDING", "FAILED"])

    if status == "SETTLED":
        settlement_time = now_iso()
        processing_code = "00"
        narrative = "Payment successful"
    elif status == "PENDING":
        settlement_time = now_iso()
        processing_code = "09"
        narrative = "Payment pending"
    else:
        settlement_time = now_iso()
        processing_code = "05"
        narrative = "Payment failed"

    response = {
        "transactionId": txid,
        "status": status,
        "amount": f"{mandate.get('amount'):.2f}",
        "currency": mandate.get("currency", "AED"),
        "rail": rail,
        "settlementTime": settlement_time,
        "processingCode": processing_code,
        "narrative": narrative,
        "meta": {
            "processor": "Aani-mock" if rail == "Aani" else "UAEFTS-mock",
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
# Landing Page with PNG from GitHub
# ---------------------------
if step == "Landing":
    st.title("AP2 + Open Finance + Aani — Sandbox Demo")
    st.markdown("""
    ### Introduction
    This sandbox demonstrates how **AP2 mandate logic** works on top of **Aani payments** in an **Open Finance** context.

    **Workflow implemented in this demo:**
    1. User Consent (IntentMandate)
    2. CBUAE Consent Registration (mock)
    3. Mandate Registry
    4. Risk & AML Check (mock)
    5. Payment Execution (choose rail: Aani or UAEFTS)
    6. Audit Trail
    """)

    st.subheader("Workflow Diagram (implemented steps)")
    st.image(
        "https://raw.githubusercontent.com/akhil-rao/ap2-aani-demo/main/Demo%20env%20workflow.png",
        caption="AP2 + UAE Aani/Open Finance Workflow",
        use_container_width=True
    )

    st.caption("**Note:** Risk screening results: LOW = Green, MEDIUM = Amber, HIGH = Red. "
               "Consent registration with CBUAE is simulated for demo purposes.")

    if st.button("Start Demo"):
        go_to("Consent")
        st.rerun()

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
        st.session_state.audit_log.append({
            "event": "CBUAE_CONSENT_REGISTERED",
            "mandate_id": mandate.mandate_id,
            "timestamp": now_iso(),
            "note": "Consent registered with CBUAE API Hub (mock)"
        })
        st.success(f"IntentMandate {mandate_id} issued and registered with CBUAE.")

        st.markdown("""
        ✅ Consent captured as **IntentMandate**.  
        🔒 Registered with **CBUAE Consent & Trust Framework** (mock).  

        **Open Finance Link:**  
        - Aligns with **customer-consent requirements** under UAE’s Open Finance.  
        - Consent must be explicit, digitally signed, and revocable.  
        - Mirrors **PSD2/Open Banking global practices**.
        """)

    if st.button("Next Step → Mandate Registry"):
        go_to("Registry")
        st.rerun()

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

        st.markdown("""
        📑 Mandates recorded in the **AP2 Registry**.  

        **Open Finance Link:**  
        - Provides a **centralized view of customer mandates**.  
        - Supports **customer right to revoke consent**.  
        - Enables transparency and reconciliation across ecosystem participants.
        """)

    if st.button("Next Step → Risk & AML Check"):
        go_to("RiskAML")
        st.rerun()

# ---------------------------
# Risk & AML Check
# ---------------------------
elif step == "RiskAML":
    st.header("Step 3 — Risk & AML Check")
    mandates = [m for m in st.session_state.mandates if m.status in ("ACTIVE", "ISSUED")]
    if not mandates:
        st.info("No mandates available for risk check.")
    else:
        sel_id = st.selectbox("Choose mandate to risk screen", options=[m.mandate_id for m in mandates])
        mandate = next(m for m in mandates if m.mandate_id == sel_id)
        if st.button("Run Risk Screening"):
            risk = random.choice(["LOW", "MEDIUM", "HIGH"])
            st.session_state.audit_log.append({
                "event": "RISK_CHECK",
                "mandate_id": mandate.mandate_id,
                "risk_level": risk,
                "timestamp": now_iso(),
                "note": "Sanctions & AML screening simulated"
            })
            if risk == "LOW":
                st.success(f"Risk screening complete. Risk level: {risk}")
            elif risk == "MEDIUM":
                st.warning(f"Risk screening complete. Risk level: {risk}")
            else:
                st.error(f"Risk screening complete. Risk level: {risk}")

            st.markdown(f"""
            🛡️ Risk screening performed via **AML/Sanctions engine**.  
            Risk signal = **{risk}** (color coded).  

            **Open Finance Link:**  
            - Ensures **FATF/CBUAE AML-CFT compliance** for TPPs.  
            - Demonstrates risk monitoring within Open Finance flows.  
            - Required for **real-time financial crime checks**.
            """)

    if st.button("Next Step → Payment Execution"):
        go_to("Payment")
        st.rerun()

# ---------------------------
# Payment Execution
# ---------------------------
elif step == "Payment":
    st.header("Step 4 — Payment Execution")
    available = [m for m in st.session_state.mandates if m.mandate_type in ("PaymentMandate", "IntentMandate") and m.status in ("ACTIVE", "ISSUED")]
    if not available:
        st.info("No mandates available. Create or convert one earlier.")
    else:
        sel_id = st.selectbox("Choose mandate to execute", options=[m.mandate_id for m in available])
        mandate = next(m for m in available if m.mandate_id == sel_id)
        rail = st.selectbox("Select Settlement Rail", ["Aani", "UAEFTS/RTGS"])
        if st.button("Execute Payment"):
            response = mock_aani_payment_api(mandate.to_dict(), rail)
            mandate.status = response["status"]
            st.session_state.audit_log.append({
                "event": "PAYMENT_EXECUTED",
                "mandate_id": mandate.mandate_id,
                "transaction_id": response["transactionId"],
                "status": response["status"],
                "rail": rail,
                "timestamp": now_iso(),
                "agent": st.session_state.agent_identity,
                "signature": sign_payload({"mandate_id": mandate.mandate_id, "txid": response["transactionId"]}),
                "response": response,
            })
            st.success(f"Payment executed on {rail}. Transaction {response['transactionId']} → {response['status']}")
            st.json(response)

            st.markdown(f"""
            💳 Payment instruction sent to **Payment Agent**.  
            Execution rail = **{rail}**.  

            **Open Finance Link:**  
            - Requires **Strong Customer Authentication (SCA)** before initiation.  
            - Execution routed via **licensed UAE rails** (Aani/UAEFTS).  
            - Demonstrates **secure API-driven initiation** under Open Finance.
            """)

    if st.button("Next Step → Audit Trail"):
        go_to("Audit")
        st.rerun()

# ---------------------------
# Audit Trail
# ---------------------------
elif step == "Audit":
    st.header("Step 5 — Audit Trail")
    logs = list(reversed(st.session_state.audit_log))
    if not logs:
        st.info("No audit events yet.")
    else:
        for entry in logs:
            with st.expander(f"{entry.get('timestamp', '')} — {entry.get('event')} — {entry.get('mandate_id','')}"):
                st.json(entry)

        st.markdown("""
        🕵️ Immutable audit log generated.  
        Includes mandate ID, agent identity, digital signature, transaction ID, and CBUAE registration.  

        **Open Finance Link:**  
        - Provides regulators, banks, and customers with **transparent transaction records**.  
        - Supports **dispute resolution** and **regulatory reporting**.  
        - Core requirement for **trust in Open Finance ecosystems**.
        """)

    if st.button("🔄 Restart Demo"):
        go_to("Landing")
        st.rerun()
