# AP2 + Aani Demo (MVP Prototype)

This is a sandbox-style **Streamlit demo** showing how **AP2 mandates** can work on top of **Aani payments**.  
It is **not production-ready** — just a clickable prototype for demonstration.

## Features

- **Consent Screen** → User approves an `IntentMandate` (e.g., AED 500 via Aani).
- **Mandate Registry** → View mandates (`CartMandate`, `IntentMandate`, `PaymentMandate`).
- **Payment Execution** → Simulate settlement using a mocked Aani API.
- **Audit Trail** → Records *Signed Mandate + Agent Identity + Transaction ID*.

## Demo Flow

1. **Consent Screen**: Create an IntentMandate (user approves).  
2. **Mandate Registry**: Inspect, convert Intent → Payment, revoke, or export JSON.  
3. **Payment Execution**: Run a mocked Aani payment call (returns transaction id + status).  
4. **Audit Trail**: View chronological signed events with dummy HMAC signatures.

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/ap2-aani-demo.git
cd ap2-aani-demo

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Streamlit app
streamlit run PaymentLabs_AP2_Aani_Demo.py
