import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from datetime import datetime, timedelta
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"

AGENT_PASSWORDS = {
    "Agent 1":  "pass1",
    "Agent 2":  "pass2",
    "Agent 3":  "pass3",
    "Manager":  "manager123",
}

AGENTS = ["Agent 1", "Agent 2", "Agent 3"]  # ← exclude Manager

# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
def get_ws(sh, tab):
    try:
        return sh.worksheet(tab)
    except:
        return None

@st.cache_data(ttl=60)
def load_all_data(_sh):
    data = {}
    for tab in ["Calls", "Leads", "Quotes", "Referrals", "Underwriting"]:
        ws = get_ws(_sh, tab)
        data[tab] = ws.get_all_records() if ws else []
    return data

def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)

def score_agent(agent, data, since=None):
    def recent(rows, date_field="Timestamp"):
        if not since:
            return rows
        return [r for r in rows if str(r.get(date_field, "")) >= since]

    calls     = [r for r in recent(data["Calls"])     if r.get("Agent") == agent]
    leads     = [r for r in recent(data["Leads"])     if r.get("Logged By") == agent]
    quotes    = [r for r in recent(data["Quotes"])    if r.get("Agent") == agent]
    referrals = [r for r in recent(data["Referrals"]) if r.get("Agent") == agent]

    sold  = sum(1 for c in calls if c.get("Outcome") == "Policy Sold")
    appts = sum(1 for c in calls if c.get("Outcome") == "Appointment Set")
    refs  = sum(1 for r in referrals if r.get("Stage") == "Policy Issued")
    points = (sold * 10) + (appts * 4) + (refs * 6) + len(calls) + len(quotes)

    return {
        "Agent":         agent,
        "Points 🏆":     points,
        "Calls Made":    len(calls),
        "Appts Set":     appts,
        "Policies Sold": sold,
        "Quotes Run":    len(quotes),
        "Referrals Won": refs,
        "Conversion %":  f"{round((sold+appts)/len(calls)*100)}%" if calls else "0%",
    }

# ── LOGIN — MANAGER ONLY ──────────────────────────────────────────────────────
def login_screen():
    st.title("🏆 Agency Leaderboard")
    st.subheader("Manager Login")
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if password == AGENT_PASSWORDS["Manager"]:
            st.session_state.agent = "Manager"
            st.rerun()
        else:
            st.error("Incorrect password.")

if "agent" not in st.session_state:
    login_screen()
    st.stop()

if st.session_state.agent != "Manager":
    st.error("This page is for managers only.")
    if st.button("Logout"):
        del st.session_state.agent
        st.rerun()
    st.stop()

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")
st.title("🏆 Agency Leaderboard & Dashboard")
if st.button("Logout"):
    del st.session_state.agent
    st.rerun()

sh   = get_sheet()
data = load_all_data(sh)

period = st.radio("Period", ["All Time", "This Week", "This Month"], horizontal=True)
since  = None
if period == "This Week":
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
elif period == "This Month":
    since = datetime.now().strftime("%Y-%m-01")

scores = sorted([score_agent(a, data, since) for a in AGENTS],
                key=lambda x: x["Points 🏆"], reverse=True)

st.subheader(f"🥇 Agent Rankings — {period}")
medals = ["🥇", "🥈", "🥉"]
cols   = st.columns(len(scores))
for i, (col, s) in enumerate(zip(cols, scores)):
    with col:
        medal = medals[i] if i < 3 else f"#{i+1}"
        st.markdown(f"### {medal} {s['Agent']}")
        st.metric("Points",         s["Points 🏆"])
        st.metric("Policies Sold",  s["Policies Sold"])
        st.metric("Appts Set",      s["Appts Set"])
        st.metric("Calls Made",     s["Calls Made"])
        st.metric("Conversion",     s["Conversion %"])

st.markdown("---")
st.subheader("📊 Full Breakdown")
st.dataframe(scores, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📈 Team Totals")
tc1, tc2, tc3, tc4, tc5 = st.columns(5)
tc1.metric("Total Calls",     sum(s["Calls Made"]    for s in scores))
tc2.metric("Total Appts",     sum(s["Appts Set"]     for s in scores))
tc3.metric("Total Policies",  sum(s["Policies Sold"] for s in scores))
tc4.metric("Total Quotes",    sum(s["Quotes Run"]    for s in scores))
tc5.metric("Total Referrals", sum(s["Referrals Won"] for s in scores))

st.markdown("---")
st.subheader("🔍 Raw Data Explorer")
tab_choice   = st.selectbox("View Tab", ["Calls", "Leads", "Quotes", "Referrals", "Underwriting"])
agent_filter = st.selectbox("Filter by Agent", ["All"] + AGENTS)
rows = data[tab_choice]
if agent_filter != "All":
    field = "Logged By" if tab_choice == "Leads" else "Agent"
    rows  = [r for r in rows if r.get(field) == agent_filter]
st.dataframe(rows, use_container_width=True)
