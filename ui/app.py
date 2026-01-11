import streamlit as st
import requests
import pandas as pd


# ================= Feature Flags =================
if "FEATURE_FLAGS" not in st.session_state:
    st.session_state.FEATURE_FLAGS = {
        "self_consistency": True,
        "cross_model_agreement": True,
        "reason_validation": True,
        "drift_detection": True,
    }

with st.sidebar.expander("🔧 Developer Controls"):
    for k, v in st.session_state.FEATURE_FLAGS.items():
        st.session_state.FEATURE_FLAGS[k] = st.checkbox(
            k.replace("_", " ").title(), value=v
        )


# ================= API CONFIG =================
API_BASE = st.secrets.get("API_URL", "http://localhost:8000")

# ================= PAGE =================
st.set_page_config(page_title="Smart Expense Canonizer", layout="centered")
st.title("💼 Smart Expense Canonizer — Trust-First AI Classification")

classification_response = None
counterfactual_response = None


# ================= TABS =================
tab1, tab2, tab3 = st.tabs(
    ["Single Entry", "CSV Upload", "Counterfactual What-If"]
)

# -------- SINGLE ENTRY --------
with tab1:
    desc = st.text_input("Transaction Description")
    amt = st.number_input("Amount", value=0.0, step=0.01)

    if st.button("Classify"):
        if not desc.strip():
            st.warning("Please enter a description.")
        else:
            classification_response = requests.post(
                f"{API_BASE}/classify",
                json={"description": desc, "amount": amt},
            ).json()

            st.subheader("RAW Backend JSON")
            st.json(classification_response)


# -------- CSV UPLOAD --------
with tab2:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded:
        df = pd.read_csv(uploaded)

        if "description" not in df.columns:
            st.error("CSV must contain a 'description' column.")
        else:
            results = []

            for _, row in df.iterrows():
                payload = {
                    "description": str(row.get("description", "")),
                    "amount": float(row.get("amount", 0))
                    if "amount" in df.columns
                    else None,
                    "date": str(row.get("date", ""))
                    if "date" in df.columns
                    else None,
                }

                api_res = requests.post(
                    f"{API_BASE}/classify", json=payload
                ).json()

                results.append(api_res)

            combined = pd.concat(
                [df.reset_index(drop=True), pd.DataFrame(results)], axis=1
            )

            st.dataframe(combined, use_container_width=True)


# -------- COUNTERFACTUAL --------
with tab3:
    base = st.text_input("Original Description")
    mod = st.text_input("Modifier Text (e.g., 'client dinner')")

    if st.button("Run What-If"):
        if base and mod:
            counterfactual_response = requests.post(
                f"{API_BASE}/counterfactual",
                json={"description": base, "modifier": mod},
            ).json()

            st.subheader("Counterfactual Result")
            st.json(counterfactual_response)


# =========================================================
# CLASSIFICATION UI — SHOWN ONLY FOR /classify
# =========================================================
if classification_response and "decision" in classification_response:

    decision = classification_response.get("decision", {})
    trust = classification_response.get("trust", {})
    evidence = classification_response.get("evidence", {})
    risk = classification_response.get("risk", {})

    st.markdown("### 🔐 Decision Quality")

    col1, col2 = st.columns(2)

    conf = decision.get("confidence")
    agree = trust.get("agreement_score")

    if conf is not None:
        col1.metric("Model Confidence", f"{conf:.2f}")
    else:
        col1.metric("Model Confidence", "-")

    if agree is not None:
        col2.metric("Cross-Model Agreement", f"{agree:.2f}")
    else:
        col2.metric("Cross-Model Agreement", "-")

    # ---------- DECISION SUMMARY ----------
    st.markdown("### 🟩 Decision Summary")

    if decision.get("risk_level") == "High":
        st.error("🔴 High Risk — Human Review Recommended")
    elif decision.get("needs_review"):
        st.warning("⚠ Human Review Recommended")
    else:
        st.success("🟢 Low-Risk Classification")

    st.json(
        {
            "Final Category": decision.get("final_category"),
            "Confidence": decision.get("confidence"),
            "Needs Review": decision.get("needs_review"),
            "Risk Level": decision.get("risk_level"),
            "Source": decision.get("source"),
        }
    )

    # ---------- TRUST SIGNALS ----------
    st.markdown("### 🟦 Model Trust Signals")
    st.json(
        {
            "Agreement Score": trust.get("agreement_score"),
            "Self-Consistent": trust.get("self_consistent"),
            "Cross-Model Used": trust.get("cross_model_used"),
            "Risk Flags": trust.get("risk_flags"),
        }
    )

    # ---------- EVIDENCE ----------
    st.markdown("### 🟪 Evidence Trail")
    st.json(
        {
            "Normalized Merchant": evidence.get("merchant_normalized"),
            "Evidence": evidence.get("evidence_list"),
            "Summary": evidence.get("summary"),
        }
    )

    # ---------- RISK ----------
    st.markdown("### 🟨 Risk & Safety Flags")
    st.json(
        {
            "Risk Score": risk.get("risk_score"),
            "Needs Review": risk.get("needs_review"),
            "PII Redaction": risk.get("pii_redaction"),
            "Risk Flags": risk.get("risk_flags"),
        }
    )


# =========================================================
# COUNTERFACTUAL UI — ONLY WHEN CALLED
# =========================================================
if counterfactual_response and "original_category" in counterfactual_response:

    st.markdown("### 🟧 Counterfactual Reasoning")

    st.json(counterfactual_response)

    if counterfactual_response.get("changed"):
        st.success("Category WOULD change based on modifier.")
    else:
        st.info("Category would NOT change — modifier does not shift classification.")
