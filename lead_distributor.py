import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"
TAB_NAME   = "Leads"

AGENT_PASSWORDS = {
    "Agent 1":  "pass1",
    "Agent 2":  "pass2",
    "Agent 3":  "pass3",
    "Manager":  "manager123",
}

LEAD_SOURCES  = ["Inbound Web Form", "Purchased List – Mortgage Protection",
                 "Purchased List – Final Expense", "Referral", "Social Media", "Hot Transfer"]
PRODUCTS      = ["Mortgage Protection", "Final Expense", "IUL", "Term Life", "Whole Life"]
LANGUAGES     = ["English", "Spanish", "Other"]
PIPELINE_STAGES = ["New Lead", "Contacted", "Appointment Set", "App Submitted", "Issued", "Closed Lost"]

AGENT_PROFILES = {
    "Agent 1": {"languages": ["English"], "products": ["Mortgage Protection", "Term Life"],   "states": ["TX", "FL"], "senior": False},
    "Agent 2": {"languages": ["English", "Spanish"], "products": ["Final Expense", "IUL"],    "states": ["TX", "CA"], "senior": True},
    "Agent 3": {"languages": ["English"], "products": ["Final Expense", "Whole Life"],         "states": ["TX", "NY"], "senior": False},
}

def assign_agent(source, product, language, state):
    if source in ["Referral", "Hot Transfer"]:
        seniors = [a for a, p in AGENT_PROFILES.items() if p["senior"]]
        if seniors:
            return seniors[0], "Priority lead → Senior agent"
    if language != "English":
        bilingual = [a for a, p in AGENT_PROFILES.items() if language in p["languages"]]
        if bilingual:
            return bilingual[0], f"{language}-speaking lead → Bilingual agent"
    matches = [a for a, p in AGENT_PROFILES.items()
               if product in p["products"] and state in p["states"]]
    if matches:
        return matches[0], "Product & state match"
    all_agents = list(AGENT_PROFILES.keys())
    return all_agents[0], "Round-robin (no specific match)"

# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=14)
        ws.append_row(["Timestamp", "Lead Name", "Phone", "Email", "State",
                       "Language", "Lead Source", "Product Interest", "Pipeline Stage",
                       "Assigned Agent", "Assignment Reason", "Notes", "Logged By", "First Contact Time"])
    return ws

def load_leads(ws, agent, is_manager):
    rows = ws.get_all_records()
    return rows if is_manager else [r for r in rows if r.get("Assigned Agent") == agent]

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    st.title("📋 Lead Distributor")
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
is_manager = agent == "Manager"

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Lead Distributor", page_icon="📋", layout="centered")
st.title("📋 Lead Distributor")
st.caption(f"Logged in as **{agent}**")
if st.button("Logout"):
    del st.session_state.agent
    st.rerun()

ws = get_sheet()
tab1, tab2 = st.tabs(["Submit New Lead", "Lead Board"])

with tab1:
    st.subheader("Intake New Lead")
    with st.form("lead_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name     = st.text_input("Lead Full Name *")
            phone    = st.text_input("Phone Number *")
            email    = st.text_input("Email")
            state    = st.text_input("State (2-letter code) *", max_chars=2).upper()
        with col2:
            language = st.selectbox("Preferred Language", LANGUAGES)
            source   = st.selectbox("Lead Source *", LEAD_SOURCES)
            product  = st.selectbox("Product Interest *", PRODUCTS)
            stage    = st.selectbox("Pipeline Stage", PIPELINE_STAGES)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("➕ Submit Lead", use_container_width=True)

    if submitted:
        if not name or not phone or not state:
            st.error("Name, phone, and state are required.")
        else:
            assigned, reason = assign_agent(source, product, language, state)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            ws.append_row([ts, name, phone, email, state, language, source,
                           product, stage, assigned, reason, notes, agent, ""])
            st.success(f"✅ Lead submitted!")
            st.info(f"**Assigned to:** {assigned}  \n**Reason:** {reason}")
            st.warning("📲 Reminder: Send initial contact message within 5 minutes.")

with tab2:
    title = "All Leads" if is_manager else f"Your Leads — {agent}"
    st.subheader(title)
    leads = load_leads(ws, agent, is_manager)
    if not leads:
        st.info("No leads yet.")
    else:
        total  = len(leads)
        appts  = sum(1 for l in leads if l.get("Pipeline Stage") == "Appointment Set")
        issued = sum(1 for l in leads if l.get("Pipeline Stage") == "Issued")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Leads", total)
        c2.metric("Appointments", appts)
        c3.metric("Issued Policies", issued)
        if is_manager:
            sel = st.selectbox("Filter by agent", ["All"] + list(AGENT_PROFILES.keys()))
            if sel != "All":
                leads = [l for l in leads if l.get("Assigned Agent") == sel]
        st.dataframe(leads, use_container_width=True)
