# AP2 + Aani Open Finance Demo

This is a sandbox-style demo showing how **AP2 mandate logic** can work on top of **Aani payments** in an **Open Finance** context.  
It is intended as an MVP prototype for demos with stakeholders (e.g., CBUAE).

---

## 🚀 Features

- **User Consent Screen** → User approves an IntentMandate (e.g., AED 500 via Aani).  
- **CBUAE Consent Registration** → Consent is mock-registered with the CBUAE API Hub.  
- **Mandate Registry View** → Shows all issued mandates (CartMandate, IntentMandate, PaymentMandate).  
- **Risk & AML Check** → Simulated sanctions/AML screening with colored results:  
  - ✅ Green → Low Risk  
  - ⚠️ Amber → Medium Risk  
  - ❌ Red → High Risk  
- **Payment Execution Simulation** → Mock settlement via Aani (instant) or UAEFTS/RTGS (high value).  
- **Audit Trail View** → Complete trace with signed mandate, agent identity, transaction ID, and CBUAE registration log.  

---

## 🖼️ Workflow Diagram

![Workflow Diagram](https://raw.githubusercontent.com/akhil-rao/ap2-aani-demo/main/Demo%20env%20workflow.png)

---

## ▶️ Running the Demo

You don’t need to install anything locally if using **Streamlit Cloud**.  
Just deploy this repo on [Streamlit Cloud](https://streamlit.io/cloud) and it will automatically install dependencies from `requirements.txt`.  

If you want to run locally:  

```bash
git clone https://github.com/akhil-rao/ap2-aani-demo.git
cd ap2-aani-demo
pip install -r requirements.txt
streamlit run PaymentLabs_AP2_Aani_Demo.py
