{\rtf1\ansi\ansicpg1252\cocoartf2820
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import gspread\
from google.oauth2.service_account import Credentials\
from datetime import datetime, date, timedelta\
import json\
\
# \uc0\u9472 \u9472  CONFIG \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
SHEET_NAME = "InsuranceAgencyTools"\
TAB_NAME   = "Referrals"\
AGENTS     = ["Select agent...", "Agent 1", "Agent 2", "Agent 3", "Manager"]  # \uc0\u8592  edit\
\
REFERRAL_STAGES = ["Requested", "Received", "Contacted", "Appointment Set", "Policy Issued", "Closed Lost"]\
\
TEMPLATES = \{\
    "Initial Ask (7 days post-policy)": """Hi \{client_name\}! This is \{agent\} \'97 I just wanted to check in and make sure everything went smoothly with your new policy. I really enjoyed working with you!\
\
If you have any friends or family who might benefit from the same protection, I'd love the chance to help them too. A quick introduction is all it takes \'97 I'll handle everything from there.\
\
Would you be open to introducing me to 2\'963 people you care about?""",\
\
    "Follow-Up Ask (30 days)": """Hi \{client_name\}, hope you're doing well! I wanted to follow up one more time \'97 if anyone comes to mind who could use some protection for their family, I'm always happy to help.\
\
No pressure at all, just wanted to keep the door open. Thanks again for trusting me with your family's coverage!""",\
\
    "Thank You \'96 Referral Received": """Hi \{client_name\}, thank you so much for thinking of me and referring \{referral_name\}! I really appreciate your trust.\
\
I'll be reaching out to them shortly and will make sure they're well taken care of. You're amazing!""",\
\
    "Thank You \'96 Referral Became Client": """Hi \{client_name\}, I just wanted to share some great news \'97 \{referral_name\} just got their policy! \uc0\u55356 \u57225 \
\
Thank you so much for the introduction. Your referral made a real difference for their family. I'm truly grateful to have clients like you!""",\
\}\
\
# \uc0\u9472 \u9472  GOOGLE SHEETS \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
def get_sheet():\
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]\
    creds = Credentials.from_service_account_info(\
        json.loads(st.secrets["GOOGLE_CREDENTIALS"]), scopes=scopes)\
    client = gspread.authorize(creds)\
    sh = client.open(SHEET_NAME)\
    try:\
        ws = sh.worksheet(TAB_NAME)\
    except gspread.WorksheetNotFound:\
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=12)\
        ws.append_row(["Timestamp", "Agent", "Client Name", "Client Phone",\
                       "Referral Name", "Referral Phone", "Stage",\
                       "Request Date", "Follow Up Date", "Converted",\
                       "Notes", "Template Used"])\
    return ws\
\
def load_referrals(ws, agent, is_manager):\
    rows = ws.get_all_records()\
    return rows if is_manager else [r for r in rows if r.get("Agent") == agent]\
\
# \uc0\u9472 \u9472  UI \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.set_page_config(page_title="Referral Tool", page_icon="\uc0\u55358 \u56605 ", layout="centered")\
st.title("\uc0\u55358 \u56605  Referral Management")\
st.caption("Track referrals, send the right message at the right time.")\
\
agent = st.selectbox("Who are you?", AGENTS)\
if agent == "Select agent...":\
    st.stop()\
\
is_manager = agent == "Manager"\
ws = get_sheet()\
\
tab1, tab2, tab3 = st.tabs(["Log Referral Request", "Message Templates", "Referral Board"])\
\
# \uc0\u9472 \u9472  TAB 1: LOG \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
with tab1:\
    st.subheader("Log a Referral Request or Received Referral")\
    with st.form("ref_form", clear_on_submit=True):\
        col1, col2 = st.columns(2)\
        with col1:\
            st.markdown("**Existing Client (Referrer)**")\
            client_name  = st.text_input("Client Name *")\
            client_phone = st.text_input("Client Phone")\
        with col2:\
            st.markdown("**Referral (New Prospect)**")\
            ref_name     = st.text_input("Referral Name (if received)")\
            ref_phone    = st.text_input("Referral Phone")\
\
        stage      = st.selectbox("Stage", REFERRAL_STAGES)\
        follow_up  = st.date_input("Follow-Up Date", value=date.today() + timedelta(days=7))\
        notes      = st.text_area("Notes")\
        submitted  = st.form_submit_button("\uc0\u55357 \u56510  Save Referral", use_container_width=True)\
\
    if submitted:\
        if not client_name:\
            st.error("Client name is required.")\
        else:\
            ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), agent,\
                           client_name, client_phone, ref_name, ref_phone,\
                           stage, date.today().strftime("%Y-%m-%d"),\
                           str(follow_up), "No", notes, ""])\
            st.success("\uc0\u9989  Referral logged!")\
            if stage == "Requested":\
                st.info("\uc0\u55357 \u56562  Send the 'Initial Ask' message template from the Templates tab.")\
            elif stage == "Received":\
                st.info("\uc0\u55357 \u56562  Send the 'Thank You \'96 Referral Received' message.")\
\
# \uc0\u9472 \u9472  TAB 2: TEMPLATES \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
with tab2:\
    st.subheader("Message Templates")\
    st.caption("Fill in the fields below, then copy the message to send.")\
\
    template_choice = st.selectbox("Select Template", list(TEMPLATES.keys()))\
    col1, col2 = st.columns(2)\
    with col1:\
        client_name_t  = st.text_input("Client Name", key="t_client")\
    with col2:\
        referral_name_t = st.text_input("Referral Name (if applicable)", key="t_ref")\
\
    msg = TEMPLATES[template_choice]\\\
        .replace("\{client_name\}", client_name_t or "[Client Name]")\\\
        .replace("\{agent\}", agent)\\\
        .replace("\{referral_name\}", referral_name_t or "[Referral Name]")\
\
    st.markdown("---")\
    st.subheader("\uc0\u55357 \u56523  Your Message")\
    st.text_area("Copy this message:", value=msg, height=220, key="msg_out")\
    st.info("\uc0\u55357 \u56481  Copy the message above and send via text, GHL, or your preferred platform.")\
\
# \uc0\u9472 \u9472  TAB 3: BOARD \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
with tab3:\
    title = "All Referrals" if is_manager else f"Your Referrals \'97 \{agent\}"\
    st.subheader(title)\
    referrals = load_referrals(ws, agent, is_manager)\
\
    if not referrals:\
        st.info("No referrals logged yet.")\
    else:\
        total     = len(referrals)\
        received  = sum(1 for r in referrals if r.get("Referral Name") and r.get("Referral Name") != "")\
        converted = sum(1 for r in referrals if r.get("Stage") == "Policy Issued")\
        c1, c2, c3, c4 = st.columns(4)\
        c1.metric("Requests Made", total)\
        c2.metric("Referrals Received", received)\
        c3.metric("Policies Issued", converted)\
        c4.metric("Conversion Rate", f"\{round(converted/received*100)\}%" if received else "0%")\
\
        if is_manager:\
            agents_list = [a for a in AGENTS if a != "Select agent..." and a != "Manager"]\
            sel = st.selectbox("Filter by agent", ["All"] + agents_list)\
            if sel != "All":\
                referrals = [r for r in referrals if r.get("Agent") == sel]\
\
        st.dataframe(referrals, use_container_width=True)}