import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"
TAB_NAME   = "Calls"

# ← Edit: add real agent names and passwords
AGENTS = ["Demo Agent", "Manager"]
SHARED_PASSWORD = "TurnItUp2026"



CALL_TYPES = ["Inbound Lead", "Outbound Follow-Up", "Client Service", "Recruit Call"]
OUTCOMES   = ["Appointment Set", "Callback Requested", "No Answer", "Not Interested", "Policy Sold"]

# ── GOOGLE SHEETS AUTH ────────────────────────────────────────────────────────
def get_sheet():
 scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
 ]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open(SHEET_NAME)
    try:
        ws = sh.worksheet(TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=10)
        ws.append_row(["Timestamp", "Agent", "Caller Name", "Phone",
                        "Call Type", "Outcome", "Notes", "Next Action", "Due Date"])
    return ws

def load_calls(ws, agent):
    rows = ws.get_all_records()
    return [r for r in rows if r.get("Agent") == agent]

def save_call(ws, row):
    ws.append_row(row)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    st.title("Turn It Up Agency Call Logger")
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if username not in AGENTS:
            st.error("Username not recognized.")
        elif password == SHARED_PASSWORD:
            st.session_state.agent = username
            st.rerun()
        else:
            st.error("Incorrect password. Try again.")

if "agent" not in st.session_state:
    login_screen()
    st.stop()

agent = st.session_state.agent

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Turn It Up Agency Call Logger", layout="centered")
st.title("Turn It Up Agency Call Logger")
st.caption(f"Logged in as **{agent}**")
if st.button("Logout", key="logout"):
    del st.session_state.agent
    st.rerun()

ws = get_sheet()
tab1, tab2 = st.tabs(["Log a Call", "My Call History"])

# ── TAB 1: LOG ────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("New Call Entry")
    with st.form("call_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            call_date = st.date_input("Date", value=date.today())
            call_time = st.time_input("Time", value=datetime.now().time())
            caller    = st.text_input("Caller Name *")
            phone     = st.text_input("Phone Number")
        with col2:
            call_type = st.selectbox("Call Type *", CALL_TYPES)
            outcome   = st.selectbox("Outcome *", OUTCOMES)
            notes     = st.text_area("Notes / Summary", height=120)

        next_action, due_date = "", ""
        if outcome in ["Appointment Set", "Callback Requested"]:
            st.markdown("---")
            st.markdown("**📅 Follow-Up Details**")
            c1, c2 = st.columns(2)
            with c1:
                next_action = st.text_input("Next Action")
            with c2:
                due_date = st.date_input("Due Date", value=date.today())

        submitted = st.form_submit_button("✅ Save Call Log", use_container_width=True)

    if submitted:
        if not caller or not call_type or not outcome:
            st.error("Please fill in all required fields (*).")
        else:
            ts = f"{call_date} {call_time.strftime('%H:%M')}"
            save_call(ws, [ts, agent, caller, phone, call_type,
                           outcome, notes, next_action, str(due_date) if due_date else ""])
            st.success(f"✅ Call logged for {caller}!")
            if outcome == "Appointment Set":
                st.info("📅 Reminder: Create a calendar event for this appointment.")
            if outcome == "Callback Requested":
                st.info(f"🔔 Follow-up due: {due_date}")

# ── TAB 2: HISTORY ────────────────────────────────────────────────────────────
with tab2:
    st.subheader(f"Your Calls — {agent}")
    calls = load_calls(ws, agent)
    if not calls:
        st.info("No calls logged yet. Start logging above!")
    else:
        st.metric("Total Calls Logged", len(calls))
        sold = sum(1 for c in calls if c["Outcome"] == "Policy Sold")
        appt = sum(1 for c in calls if c["Outcome"] == "Appointment Set")
        col1, col2, col3 = st.columns(3)
        col1.metric("Policies Sold", sold)
        col2.metric("Appointments Set", appt)
        col3.metric("Conversion Rate", f"{round((sold+appt)/len(calls)*100)}%" if calls else "0%")
        st.dataframe(calls, use_container_width=True)
