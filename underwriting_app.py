import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"
TAB_NAME   = "Underwriting"

AGENT_PASSWORDS = {
    "Agent 1":  "pass1",
    "Agent 2":  "pass2",
    "Agent 3":  "pass3",
    "Manager":  "manager123",
}

CARRIERS = {
    "Carrier A – Final Expense Plus": {
        "products": ["Final Expense", "Whole Life"],
        "max_bmi": 40, "accepts_tobacco": True, "tobacco_lookback_years": 0,
        "accepts_marijuana": True, "a1c_max": 8.5, "accepts_diabetes": True,
        "accepts_heart_disease": False, "accepts_cancer_years": 5,
        "dui_lookback_years": 3, "processing_days": "7–10",
        "notes": "Very lenient for final expense. Guaranteed issue option available.",
    },
    "Carrier B – Term Solutions": {
        "products": ["Term Life", "Mortgage Protection"],
        "max_bmi": 35, "accepts_tobacco": True, "tobacco_lookback_years": 1,
        "accepts_marijuana": True, "a1c_max": 8.0, "accepts_diabetes": True,
        "accepts_heart_disease": False, "accepts_cancer_years": 10,
        "dui_lookback_years": 5, "processing_days": "3–5",
        "notes": "Accelerated underwriting available. Fast approval for healthy profiles.",
    },
    "Carrier C – IUL Preferred": {
        "products": ["IUL", "Whole Life"],
        "max_bmi": 32, "accepts_tobacco": False, "tobacco_lookback_years": 3,
        "accepts_marijuana": False, "a1c_max": 7.5, "accepts_diabetes": True,
        "accepts_heart_disease": True, "accepts_cancer_years": 7,
        "dui_lookback_years": 10, "processing_days": "14–21",
        "notes": "Stricter underwriting. Best rates for preferred+ health. Living benefits included.",
    },
    "Carrier D – Guaranteed Issue": {
        "products": ["Final Expense", "Whole Life"],
        "max_bmi": 999, "accepts_tobacco": True, "tobacco_lookback_years": 0,
        "accepts_marijuana": True, "a1c_max": 999, "accepts_diabetes": True,
        "accepts_heart_disease": True, "accepts_cancer_years": 0,
        "dui_lookback_years": 0, "processing_days": "1–3",
        "notes": "No health questions. Graded benefit first 2 years. Last resort option.",
    },
}

CONDITIONS = ["None", "Type 2 Diabetes", "Type 1 Diabetes", "Heart Disease / Heart Attack",
              "Stroke", "Cancer (active)", "Cancer (history)", "COPD / Emphysema",
              "Kidney Disease", "Depression / Anxiety", "HIV/AIDS", "Other"]

def score_carrier(c, profile):
    carrier = CARRIERS[c]
    flags, score = [], 0
    bmi = profile["bmi"]
    if bmi <= carrier["max_bmi"]: score += 2
    else: flags.append(f"BMI {bmi:.1f} exceeds limit of {carrier['max_bmi']}")
    if profile["tobacco"] and not carrier["accepts_tobacco"]:
        flags.append(f"Tobacco use — carrier requires {carrier['tobacco_lookback_years']}-yr abstinence")
    elif not profile["tobacco"]: score += 2
    if profile["marijuana"] and not carrier["accepts_marijuana"]:
        flags.append("Marijuana use not accepted")
    elif not profile["marijuana"]: score += 1
    if "Diabetes" in profile["condition"]:
        if carrier["accepts_diabetes"] and profile["a1c"] <= carrier["a1c_max"]: score += 2
        elif not carrier["accepts_diabetes"]: flags.append("Carrier does not accept diabetes")
        else: flags.append(f"A1C {profile['a1c']} exceeds carrier max of {carrier['a1c_max']}")
    if "Heart" in profile["condition"] and not carrier["accepts_heart_disease"]:
        flags.append("Heart disease not accepted by this carrier")
    elif "Heart" not in profile["condition"]: score += 1
    if profile["dui"] and profile["dui_years"] < carrier["dui_lookback_years"]:
        flags.append(f"DUI within {carrier['dui_lookback_years']}-yr lookback period")
    elif not profile["dui"]: score += 1
    if profile["product"] in carrier["products"]: score += 3
    else: flags.append(f"Carrier doesn't specialize in {profile['product']}")
    return score, flags

def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=12)
        ws.append_row(["Timestamp", "Agent", "Client Name", "Age", "BMI", "Tobacco",
                       "Condition", "Product", "Top Carrier", "2nd Carrier", "3rd Carrier", "Notes"])
    return ws

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    st.title("🏥 Underwriting Tool")
    st.subheader("Login")
    name = st.selectbox("Your Name", ["Select..."] + list(AGENT_PASSWORDS.keys()))
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if name == "Select...":
            st.error("Please select your name.")
        elif AGENT_PASSWORDS.get(name) == password:
            st.session_state.agent = name
            st.rerun()
        else:
            st.error("Incorrect password. Try again.")

if "agent" not in st.session_state:
    login_screen()
    st.stop()

agent = st.session_state.agent

st.set_page_config(page_title="Underwriting Tool", page_icon="🏥", layout="centered")
st.title("🏥 Underwriting Reference Tool")
st.caption(f"Logged in as **{agent}**")
if st.button("Logout"):
    del st.session_state.agent
    st.rerun()

ws = get_sheet()
tab1, tab2 = st.tabs(["Run Underwriting", "My History"])

with tab1:
    st.subheader("Client Health Profile")
    with st.form("uw_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name")
            age         = st.number_input("Age", 18, 85, 45)
            height_ft   = st.number_input("Height (ft)", 4, 7, 5)
            height_in   = st.number_input("Height (in)", 0, 11, 8)
            weight      = st.number_input("Weight (lbs)", 80, 500, 180)
        with col2:
            product   = st.selectbox("Product Seeking", ["Final Expense", "Term Life", "Whole Life", "IUL", "Mortgage Protection"])
            tobacco   = st.checkbox("Tobacco / Nicotine use")
            marijuana = st.checkbox("Marijuana use")
            dui       = st.checkbox("DUI / DWI history")
            dui_years = st.number_input("Years since DUI", 0, 30, 0) if dui else 0
        condition = st.selectbox("Primary Health Condition", CONDITIONS)
        a1c = 0.0
        if "Diabetes" in condition:
            a1c = st.number_input("A1C level", 4.0, 15.0, 7.0, step=0.1)
        meds  = st.text_area("Current Medications", height=80)
        notes = st.text_area("Additional Notes", height=60)
        run   = st.form_submit_button("🔍 Find Best Carriers", use_container_width=True)

    if run:
        height_inches = (height_ft * 12) + height_in
        bmi = (weight / (height_inches ** 2)) * 703
        profile = {"bmi": bmi, "tobacco": tobacco, "marijuana": marijuana,
                   "dui": dui, "dui_years": dui_years, "condition": condition,
                   "a1c": a1c, "product": product}
        results = sorted([(n, *score_carrier(n, profile)) for n in CARRIERS],
                         key=lambda x: x[1], reverse=True)
        st.markdown("---")
        st.subheader("📊 Carrier Recommendations")
        for i, (name, score, flags) in enumerate(results[:3]):
            carrier = CARRIERS[name]
            medal = ["🥇","🥈","🥉"][i]
            with st.expander(f"{medal} {name}  —  Score: {score}/12", expanded=(i==0)):
                st.write(f"**Processing Time:** {carrier['processing_days']} business days")
                st.write(f"**Products:** {', '.join(carrier['products'])}")
                st.write(f"**Notes:** {carrier['notes']}")
                if flags: st.warning("⚠️ Red Flags:\n" + "\n".join(f"- {f}" for f in flags))
                else: st.success("✅ Clean match — no red flags")
        top3 = [r[0] for r in results[:3]]
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), agent, client_name,
                       age, round(bmi,1), tobacco, condition, product,
                       top3[0], top3[1] if len(top3)>1 else "", top3[2] if len(top3)>2 else "", notes])
        st.success("✅ Lookup saved.")

with tab2:
    st.subheader(f"Your UW Lookups — {agent}")
    rows = ws.get_all_records()
    mine = [r for r in rows if r.get("Agent") == agent]
    if not mine: st.info("No lookups yet.")
    else: st.dataframe(mine, use_container_width=True)
