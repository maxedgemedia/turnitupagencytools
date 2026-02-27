{\rtf1\ansi\ansicpg1252\cocoartf2820
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import gspread\
from google.oauth2.service_account import Credentials\
from collections import defaultdict\
from datetime import datetime, timedelta\
import json\
\
# \uc0\u9472 \u9472  CONFIG \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
SHEET_NAME = "InsuranceAgencyTools"\
AGENTS     = ["Agent 1", "Agent 2", "Agent 3"]  # \uc0\u8592  edit \'97 exclude Manager\
MANAGER_PASSWORD = "manager123"  # \uc0\u8592  change this\
\
# \uc0\u9472 \u9472  GOOGLE SHEETS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
def get_ws(sh, tab):\
    try:\
        return sh.worksheet(tab)\
    except:\
        return None\
\
@st.cache_data(ttl=60)\
def load_all_data(_sh):\
    data = \{\}\
    for tab in ["Calls", "Leads", "Quotes", "Referrals", "Underwriting"]:\
        ws = get_ws(_sh, tab)\
        data[tab] = ws.get_all_records() if ws else []\
    return data\
\
def get_sheet():\
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]\
    creds = Credentials.from_service_account_info(\
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)\
    client = gspread.authorize(creds)\
    return client.open(SHEET_NAME)\
\
# \uc0\u9472 \u9472  SCORING \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
def score_agent(agent, data, since=None):\
    def recent(rows, date_field="Timestamp"):\
        if not since:\
            return rows\
        return [r for r in rows if r.get(date_field, "") >= since]\
\
    calls     = [r for r in recent(data["Calls"])      if r.get("Agent") == agent]\
    leads     = [r for r in recent(data["Leads"])      if r.get("Logged By") == agent]\
    quotes    = [r for r in recent(data["Quotes"])     if r.get("Agent") == agent]\
    referrals = [r for r in recent(data["Referrals"])  if r.get("Agent") == agent]\
\
    sold  = sum(1 for c in calls if c.get("Outcome") == "Policy Sold")\
    appts = sum(1 for c in calls if c.get("Outcome") == "Appointment Set")\
    refs  = sum(1 for r in referrals if r.get("Stage") == "Policy Issued")\
\
    # Points system\
    points = (sold * 10) + (appts * 4) + (refs * 6) + (len(calls)) + (len(quotes))\
\
    return \{\
        "Agent":          agent,\
        "Points \uc0\u55356 \u57286 ":      points,\
        "Calls Made":     len(calls),\
        "Appts Set":      appts,\
        "Policies Sold":  sold,\
        "Quotes Run":     len(quotes),\
        "Referrals Won":  refs,\
        "Conversion %":   f"\{round((sold+appts)/len(calls)*100)\}%" if calls else "0%",\
    \}\
\
# \uc0\u9472 \u9472  UI \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.set_page_config(page_title="Manager Leaderboard", page_icon="\uc0\u55356 \u57286 ", layout="wide")\
st.title("\uc0\u55356 \u57286  Agency Leaderboard & Dashboard")\
\
# Simple password gate\
if "auth" not in st.session_state:\
    st.session_state.auth = False\
\
if not st.session_state.auth:\
    pwd = st.text_input("Manager Password", type="password")\
    if st.button("Login"):\
        if pwd == MANAGER_PASSWORD:\
            st.session_state.auth = True\
            st.rerun()\
        else:\
            st.error("Incorrect password.")\
    st.stop()\
\
sh   = get_sheet()\
data = load_all_data(sh)\
\
# Date filter\
period = st.radio("Period", ["All Time", "This Week", "This Month"], horizontal=True)\
since  = None\
if period == "This Week":\
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")\
elif period == "This Month":\
    since = datetime.now().strftime("%Y-%m-01")\
\
# \uc0\u9472 \u9472  LEADERBOARD \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
scores = [score_agent(a, data, since) for a in AGENTS]\
scores.sort(key=lambda x: x["Points \uc0\u55356 \u57286 "], reverse=True)\
\
st.subheader(f"\uc0\u55358 \u56647  Agent Rankings \'97 \{period\}")\
medals = ["\uc0\u55358 \u56647 ", "\u55358 \u56648 ", "\u55358 \u56649 "]\
cols   = st.columns(len(scores))\
for i, (col, s) in enumerate(zip(cols, scores)):\
    with col:\
        medal = medals[i] if i < 3 else f"#\{i+1\}"\
        st.markdown(f"### \{medal\} \{s['Agent']\}")\
        st.metric("Points", s["Points \uc0\u55356 \u57286 "])\
        st.metric("Policies Sold", s["Policies Sold"])\
        st.metric("Appts Set", s["Appts Set"])\
        st.metric("Calls Made", s["Calls Made"])\
        st.metric("Conversion", s["Conversion %"])\
\
st.markdown("---")\
\
# \uc0\u9472 \u9472  FULL TABLE \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.subheader("\uc0\u55357 \u56522  Full Breakdown")\
st.dataframe(scores, use_container_width=True, hide_index=True)\
\
# \uc0\u9472 \u9472  TEAM TOTALS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.markdown("---")\
st.subheader("\uc0\u55357 \u56520  Team Totals")\
tc1, tc2, tc3, tc4, tc5 = st.columns(5)\
tc1.metric("Total Calls",    sum(s["Calls Made"]    for s in scores))\
tc2.metric("Total Appts",    sum(s["Appts Set"]     for s in scores))\
tc3.metric("Total Policies", sum(s["Policies Sold"] for s in scores))\
tc4.metric("Total Quotes",   sum(s["Quotes Run"]    for s in scores))\
tc5.metric("Total Referrals",sum(s["Referrals Won"] for s in scores))\
\
# \uc0\u9472 \u9472  RAW DATA EXPLORER \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.markdown("---")\
st.subheader("\uc0\u55357 \u56589  Raw Data Explorer")\
tab_choice = st.selectbox("View Tab", ["Calls", "Leads", "Quotes", "Referrals", "Underwriting"])\
agent_filter = st.selectbox("Filter by Agent", ["All"] + AGENTS)\
rows = data[tab_choice]\
if agent_filter != "All":\
    field = "Logged By" if tab_choice == "Leads" else "Agent"\
    rows = [r for r in rows if r.get(field) == agent_filter]\
st.dataframe(rows, use_container_width=True)\
\
# Logout\
st.markdown("---")\
if st.button("\uc0\u55357 \u56594  Logout"):\
    st.session_state.auth = False\
    st.rerun()}