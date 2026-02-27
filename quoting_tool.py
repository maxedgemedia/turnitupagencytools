import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"
TAB_NAME   = "Quotes"

AGENT_PASSWORDS = {
    "Agent 1":  "pass1",
    "Agent 2":  "pass2",
    "Agent 3":  "pass3",
    "Manager":  "manager123",
}

HEALTH_CLASSES = ["Preferred Plus", "Preferred", "Standard Plus", "Standard", "Table B", "Table D"]
PRODUCTS       = ["Term – 10yr", "Term – 20yr", "Term – 30yr", "Whole Life", "Final Expense", "IUL"]

RATE_TABLE = {
    "Term – 10yr": {"Preferred Plus": {"M": 0.05, "F": 0.04}, "Preferred": {"M": 0.07, "F": 0.06}, "Standard Plus": {"M": 0.09, "F": 0.08}, "Standard": {"M": 0.12, "F": 0.10}, "Table B": {"M": 0.16, "F": 0.14}, "Table D": {"M": 0.22, "F": 0.19}},
    "Term – 20yr": {"Preferred Plus": {"M": 0.08, "F": 0.07}, "Preferred": {"M": 0.11, "F": 0.09}, "Standard Plus": {"M": 0.14, "F": 0.12}, "Standard": {"M": 0.18, "F": 0.16}, "Table B": {"M": 0.24, "F": 0.21}, "Table D": {"M": 0.32, "F": 0.28}},
    "Term – 30yr": {"Preferred Plus": {"M": 0.11, "F": 0.09}, "Preferred": {"M": 0.15, "F": 0.13}, "Standard Plus": {"M": 0.19, "F": 0.17}, "Standard": {"M": 0.25, "F": 0.22}, "Table B": {"M": 0.33, "F": 0.29}, "Table D": {"M": 0.44, "F": 0.39}},
    "Whole Life":  {"Preferred Plus": {"M": 0.45, "F": 0.38}, "Preferred": {"M": 0.55, "F": 0.47}, "Standard Plus": {"M": 0.65, "F": 0.55}, "Standard": {"M": 0.75, "F": 0.64}, "Table B": {"M": 0.90, "F": 0.77}, "Table D": {"M": 1.10, "F": 0.94}},
    "Final Expense": {"Preferred Plus": {"M": 2.20, "F": 1.80}, "Preferred": {"M": 2.60, "F": 2.10}, "Standard Plus": {"M": 3.00, "F": 2.50}, "Standard": {"M": 3.50, "F": 2.90}, "Table B": {"M": 4.20, "F": 3.50}, "Table D": {"M": 5.50, "F": 4.60}},
    "IUL":         {"Preferred Plus": {"M": 0.35, "F": 0.29}, "Preferred": {"M": 0.45, "F": 0.37}, "Standard Plus": {"M": 0.55, "F": 0.46}, "Standard": {"M": 0.65, "F": 0.54}, "Table B": {"M": 0.80, "F": 0.67}, "Table D": {"M": 1.00, "F": 0.84}},
}

CARRIERS = {
    "Carrier A": {"multiplier": 1.00, "features": "Living benefits, conversion option, accelerated UW"},
    "Carrier B": {"multiplier": 1.08, "features": "Strong brand, dividend history, fast processing"},
    "Carrier C": {"multiplier": 0.94, "features": "Budget option, online application, 24hr approval"},
    "Carrier D": {"multiplier": 1.15, "features": "Best living benefits, guaranteed renewability"},
    "Carrier E": {"multiplier": 0.88, "features": "Lowest premium, simplified issue available"},
}

def calc_premium(product, health_class, gender, coverage_k, age, tobacco):
    base = RATE_TABLE[product][health_class][gender]
    age_factor = 1 + max(0, (age - 30)) * 0.018
    tobacco_factor = 1.6 if tobacco else 1.0
    return round(base * coverage_k * age_factor * tobacco_factor, 2)

def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=11)
        ws.append_row(["Timestamp", "Agent", "Client Name", "Age", "Gender",
                       "Product", "Coverage", "Health Class", "Tobacco",
                       "Best Carrier", "Best Monthly Premium"])
    return ws

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    st.title("💰 Quoting Tool")
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

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Quoting Tool", page_icon="💰", layout="centered")
st.title("💰 Quoting Tool")
st.caption(f"Logged in as **{agent}**")
if st.button("Logout"):
    del st.session_state.agent
    st.rerun()

ws = get_sheet()
tab1, tab2 = st.tabs(["Generate Quote", "Quote History"])

with tab1:
    st.subheader("Client Quote Details")
    with st.form("quote_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_name  = st.text_input("Client Name")
            age          = st.number_input("Age", 18, 85, 40)
            gender       = st.radio("Gender", ["M", "F"], horizontal=True)
            tobacco      = st.checkbox("Tobacco user")
        with col2:
            product      = st.selectbox("Product Type", PRODUCTS)
            coverage     = st.number_input("Coverage Amount ($)", 10000, 2000000, 250000, step=10000)
            health_class = st.selectbox("Health Classification", HEALTH_CLASSES)
            state        = st.text_input("State", max_chars=2).upper()
        notes = st.text_area("Talking Points / Notes", height=80)
        run   = st.form_submit_button("📊 Generate Comparison", use_container_width=True)

    if run:
        coverage_k = coverage / 1000
        results = []
        for carrier_name, carrier_data in CARRIERS.items():
            base    = calc_premium(product, health_class, gender, coverage_k, age, tobacco)
            monthly = round(base * carrier_data["multiplier"], 2)
            annual  = round(monthly * 12, 2)
            results.append({"Carrier": carrier_name, "Monthly Premium": f"${monthly:,.2f}",
                            "Annual Premium": f"${annual:,.2f}", "Key Features": carrier_data["features"],
                            "_monthly_raw": monthly})
        results.sort(key=lambda x: x["_monthly_raw"])
        st.markdown("---")
        st.subheader("📋 Carrier Comparison")
        st.caption(f"Client: {client_name} | {age}yr {gender} | {product} | ${coverage:,} | {health_class} | {'Tobacco' if tobacco else 'Non-tobacco'}")
        for i, r in enumerate(results):
            label = "⭐ Best Value" if i == 0 else ("💡 Alt Option" if i == 1 else "")
            with st.expander(f"{r['Carrier']}  —  {r['Monthly Premium']}/mo  {label}", expanded=(i < 2)):
                col1, col2 = st.columns(2)
                col1.metric("Monthly", r["Monthly Premium"])
                col2.metric("Annual", r["Annual Premium"])
                st.write(f"**Features:** {r['Key Features']}")
        best = results[0]
        st.markdown("---")
        st.subheader("🗣️ Presentation Talking Points")
        st.markdown(f"""
- **Recommended:** {best['Carrier']} at **{best['Monthly Premium']}/month**
- Coverage: **${coverage:,}** in {product}
- Health class: **{health_class}** {"(tobacco rated)" if tobacco else ""}
- Budget alternative: {results[1]['Carrier']} at {results[1]['Monthly Premium']}/month
- {notes if notes else 'Add custom talking points above.'}
        """)
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), agent, client_name,
                       age, gender, product, f"${coverage:,}", health_class,
                       tobacco, best["Carrier"], best["Monthly Premium"]])
        st.success("✅ Quote saved to history.")

with tab2:
    st.subheader(f"Your Quotes — {agent}")
    rows = ws.get_all_records()
    mine = [r for r in rows if r.get("Agent") == agent]
    if not mine:
        st.info("No quotes generated yet.")
    else:
        st.metric("Total Quotes Generated", len(mine))
        st.dataframe(mine, use_container_width=True)
