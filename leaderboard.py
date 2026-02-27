import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from datetime import datetime, timedelta
import json

# ── CONFIG ────────────────────────────────────────────────────────────────────
SHEET_NAME = "InsuranceAgencyTools"
AGENTS     = ["Agent 1", "Agent 2", "Agent 3"]  # ← edit — exclude Manager
MANAGER_PASSWORD = "manager123"  # ← change this

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

# ── SCORING ───────────────────────────────────────────────────────────────────
def score_agent(agent, data, since=None):
    def recent(rows, date_field="Timestamp"):
        if not since:
            return rows
        return [r for r in rows if r.get(date_field, "") >= since]

    calls     = [r for r in recent(data["Calls"])      if r.get("Agent") == agent]
    leads     = [r for r in recent(data["Leads"])      if r.get("Logged By") == agent]
    quotes    = [r for r in recent(data["Quotes"])     if r.get("Agent") == agent]
    referrals = [r for r in recent(data["Referrals"])  if r.get("Agent") == agent]

    sold  = sum(1 for c in calls if c.get("Outcome") == "Policy Sold")
    appts = sum(1 for c in calls if c.get("Outcome") == "Appointment Set")
    refs  = sum(1 for r in referrals if r.get("Stage") == "Policy Issued")

    # Points system
    points = (sold * 10) + (appts * 4) + (refs * 6) + (len(calls)) + (len(quotes))

    return {
        "Agent":          agent,
        "Points 🏆":      points,
        "Calls Made":     len(calls),
        "Appts Set":      appts,
        "Policies Sold":  sold,
        "Quotes Run":     len(quotes),
        "Referrals Won":  refs,
        "Conversion %":   f"{round((sold+appts)/len(calls)*100)}%" if calls else "0%",
    }

# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Manager Leaderboard", page_icon="🏆", layout="wide")
st.title("🏆 Agency Leaderboard & Dashboard")

# Simple password gate
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Manager Password", type="password")
    if st.button("Login"):
        if pwd == MANAGER_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

sh   = get_sheet()
data = load_all_data(sh)

# Date filter
period = st.radio("Period", ["All Time", "This Week", "This Month"], horizontal=True)
since  = None
if period == "This Week":
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
elif period == "This Month":
    since = datetime.now().strftime("%Y-%m-01")

# ── LEADERBOARD ───────────────────────────────────────────────────────────────
scores = [score_agent(a, data, since) for a in AGENTS]
scores.sort(key=lambda x: x["Points 🏆"], reverse=True)

st.subheader(f"🥇 Agent Rankings — {period}")
medals = ["🥇", "🥈", "🥉"]
cols   = st.columns(len(scores))
for i, (col, s) in enumerate(zip(cols, scores)):
    with col:
        medal = medals[i] if i < 3 else f"#{i+1}"
        st.markdown(f"### {medal} {s['Agent']}")
        st.metric("Points", s["Points 🏆"])
        st.metric("Policies Sold", s["Policies Sold"])
        st.metric("Appts Set", s["Appts Set"])
        st.metric("Calls Made", s["Calls Made"])
        st.metric("Conversion", s["Conversion %"])

st.markdown("---")

# ── FULL TABLE ────────────────────────────────────────────────────────────────
st.subheader("📊 Full Breakdown")
st.dataframe(scores, use_container_width=True, hide_index=True)

# ── TEAM TOTALS ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Team Totals")
tc1, tc2, tc3, tc4, tc5 = st.columns(5)
tc1.metric("Total Calls",    sum(s["Calls Made"]    for s in scores))
tc2.metric("Total Appts",    sum(s["Appts Set"]     for s in scores))
tc3.metric("Total Policies", sum(s["Policies Sold"] for s in scores))
tc4.metric("Total Quotes",   sum(s["Quotes Run"]    for s in scores))
tc5.metric("Total Referrals",sum(s["Referrals Won"] for s in scores))

# ── RAW DATA EXPLORER ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔍 Raw Data Explorer")
tab_choice = st.selectbox("View Tab", ["Calls", "Leads", "Quotes", "Referrals", "Underwriting"])
agent_filter = st.selectbox("Filter by Agent", ["All"] + AGENTS)
rows = data[tab_choice]
if agent_filter != "All":
    field = "Logged By" if tab_choice == "Leads" else "Agent"
    rows = [r for r in rows if r.get(field) == agent_filter]
st.dataframe(rows, use_container_width=True)

# Logout
st.markdown("---")
if st.button("🔒 Logout"):
    st.session_state.auth = False
    st.rerun()
