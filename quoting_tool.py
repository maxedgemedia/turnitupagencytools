{\rtf1\ansi\ansicpg1252\cocoartf2820
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\froman\fcharset0 Times-Roman;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs24 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 import streamlit as st\
import gspread\
from google.oauth2.service_account import Credentials\
from datetime import datetime\
import json\
\
# \uc0\u9472 \u9472  CONFIG \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
SHEET_NAME = "InsuranceAgencyTools"\
TAB_NAME   = "Quotes"\
AGENTS     = ["Select agent...", "Agent 1", "Agent 2", "Agent 3", "Manager"]  # \uc0\u8592  edit\
\
HEALTH_CLASSES = ["Preferred Plus", "Preferred", "Standard Plus", "Standard", "Table B", "Table D"]\
PRODUCTS       = ["Term \'96 10yr", "Term \'96 20yr", "Term \'96 30yr", "Whole Life", "Final Expense", "IUL"]\
\
# \uc0\u9472 \u9472  RATE TABLE (placeholder \'97 replace with real carrier rate sheets) \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
# Format: rates[product][health_class][gender] = base monthly per $1k coverage\
# Client should supply actual rate sheets \'97 these are illustrative only.\
RATE_TABLE = \{\
    "Term \'96 10yr": \{\
        "Preferred Plus": \{"M": 0.05, "F": 0.04\},\
        "Preferred":      \{"M": 0.07, "F": 0.06\},\
        "Standard Plus":  \{"M": 0.09, "F": 0.08\},\
        "Standard":       \{"M": 0.12, "F": 0.10\},\
        "Table B":        \{"M": 0.16, "F": 0.14\},\
        "Table D":        \{"M": 0.22, "F": 0.19\},\
    \},\
    "Term \'96 20yr": \{\
        "Preferred Plus": \{"M": 0.08, "F": 0.07\},\
        "Preferred":      \{"M": 0.11, "F": 0.09\},\
        "Standard Plus":  \{"M": 0.14, "F": 0.12\},\
        "Standard":       \{"M": 0.18, "F": 0.16\},\
        "Table B":        \{"M": 0.24, "F": 0.21\},\
        "Table D":        \{"M": 0.32, "F": 0.28\},\
    \},\
    "Term \'96 30yr": \{\
        "Preferred Plus": \{"M": 0.11, "F": 0.09\},\
        "Preferred":      \{"M": 0.15, "F": 0.13\},\
        "Standard Plus":  \{"M": 0.19, "F": 0.17\},\
        "Standard":       \{"M": 0.25, "F": 0.22\},\
        "Table B":        \{"M": 0.33, "F": 0.29\},\
        "Table D":        \{"M": 0.44, "F": 0.39\},\
    \},\
    "Whole Life": \{\
        "Preferred Plus": \{"M": 0.45, "F": 0.38\},\
        "Preferred":      \{"M": 0.55, "F": 0.47\},\
        "Standard Plus":  \{"M": 0.65, "F": 0.55\},\
        "Standard":       \{"M": 0.75, "F": 0.64\},\
        "Table B":        \{"M": 0.90, "F": 0.77\},\
        "Table D":        \{"M": 1.10, "F": 0.94\},\
    \},\
    "Final Expense": \{\
        "Preferred Plus": \{"M": 2.20, "F": 1.80\},\
        "Preferred":      \{"M": 2.60, "F": 2.10\},\
        "Standard Plus":  \{"M": 3.00, "F": 2.50\},\
        "Standard":       \{"M": 3.50, "F": 2.90\},\
        "Table B":        \{"M": 4.20, "F": 3.50\},\
        "Table D":        \{"M": 5.50, "F": 4.60\},\
    \},\
    "IUL": \{\
        "Preferred Plus": \{"M": 0.35, "F": 0.29\},\
        "Preferred":      \{"M": 0.45, "F": 0.37\},\
        "Standard Plus":  \{"M": 0.55, "F": 0.46\},\
        "Standard":       \{"M": 0.65, "F": 0.54\},\
        "Table B":        \{"M": 0.80, "F": 0.67\},\
        "Table D":        \{"M": 1.00, "F": 0.84\},\
    \},\
\}\
\
# Carrier multipliers (simulates different carrier pricing)\
CARRIERS = \{\
    "Carrier A": \{"multiplier": 1.00, "features": "Living benefits, conversion option, accelerated UW"\},\
    "Carrier B": \{"multiplier": 1.08, "features": "Strong brand, dividend history, fast processing"\},\
    "Carrier C": \{"multiplier": 0.94, "features": "Budget option, online application, 24hr approval"\},\
    "Carrier D": \{"multiplier": 1.15, "features": "Best living benefits, guaranteed renewability"\},\
    "Carrier E": \{"multiplier": 0.88, "features": "Lowest premium, simplified issue available"\},\
\}\
\
def calc_premium(product, health_class, gender, coverage_k, age, tobacco):\
    base = RATE_TABLE[product][health_class][gender]\
    age_factor = 1 + max(0, (age - 30)) * 0.018\
    tobacco_factor = 1.6 if tobacco else 1.0\
    return round(base * coverage_k * age_factor * tobacco_factor, 2)\
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
        ws = sh.add_worksheet(TAB_NAME, rows=1000, cols=11)\
        ws.append_row(["Timestamp", "Agent", "Client Name", "Age", "Gender",\
                       "Product", "Coverage", "Health Class", "Tobacco",\
                       "Best Carrier", "Best Monthly Premium"])\
    return ws\
\
# \uc0\u9472 \u9472  UI \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \u9472 \
st.set_page_config(page_title="Quoting Tool", page_icon="\uc0\u55357 \u56496 ", layout="centered")\
st.title("\uc0\u55357 \u56496  Quoting Tool")\
st.caption("Generate side-by-side premium comparisons for client presentations.")\
\
agent = st.selectbox("Who are you?", AGENTS)\
if agent == "Select agent...":\
    st.stop()\
\
ws = get_sheet()\
tab1, tab2 = st.tabs(["Generate Quote", "Quote History"])\
\
with tab1:\
    st.subheader("Client Quote Details")\
    with st.form("quote_form"):\
        col1, col2 = st.columns(2)\
        with col1:\
            client_name  = st.text_input("Client Name")\
            age          = st.number_input("Age", 18, 85, 40)\
            gender       = st.radio("Gender", ["M", "F"], horizontal=True)\
            tobacco      = st.checkbox("Tobacco user")\
        with col2:\
            product      = st.selectbox("Product Type", PRODUCTS)\
            coverage     = st.number_input("Coverage Amount ($)", 10000, 2000000, 250000, step=10000)\
            health_class = st.selectbox("Health Classification", HEALTH_CLASSES)\
            state        = st.text_input("State", max_chars=2).upper()\
\
        notes = st.text_area("Talking Points / Notes", height=80)\
        run   = st.form_submit_button("\uc0\u55357 \u56522  Generate Comparison", use_container_width=True)\
\
    if run:\
        coverage_k = coverage / 1000\
        results = []\
        for carrier_name, carrier_data in CARRIERS.items():\
            base = calc_premium(product, health_class, gender, coverage_k, age, tobacco)\
            monthly = round(base * carrier_data["multiplier"], 2)\
            annual  = round(monthly * 12, 2)\
            results.append(\{\
                "Carrier":          carrier_name,\
                "Monthly Premium":  f"$\{monthly:,.2f\}",\
                "Annual Premium":   f"$\{annual:,.2f\}",\
                "Key Features":     carrier_data["features"],\
                "_monthly_raw":     monthly,\
            \})\
\
        results.sort(key=lambda x: x["_monthly_raw"])\
\
        st.markdown("---")\
        st.subheader("\uc0\u55357 \u56523  Carrier Comparison")\
        st.caption(f"Client: \{client_name\} | \{age\}yr \{gender\} | \{product\} | $\{coverage:,\} | \{health_class\} | \{'Tobacco' if tobacco else 'Non-tobacco'\}")\
\
        for i, r in enumerate(results):\
            label = "\uc0\u11088  Best Value" if i == 0 else ("\u55357 \u56481  Alt Option" if i == 1 else "")\
            with st.expander(f"\{r['Carrier']\}  \'97  \{r['Monthly Premium']\}/mo  \{label\}", expanded=(i < 2)):\
                col1, col2 = st.columns(2)\
                col1.metric("Monthly", r["Monthly Premium"])\
                col2.metric("Annual", r["Annual Premium"])\
                st.write(f"**Features:** \{r['Key Features']\}")\
\
        # Talking points\
        best = results[0]\
        st.markdown("---")\
        st.subheader("\uc0\u55357 \u56803 \u65039  Presentation Talking Points")\
        st.markdown(f"""\
- **Recommended:** \{best['Carrier']\} at **\{best['Monthly Premium']\}/month**\
- Coverage: **$\{coverage:,\}** in \{product\}\
- Health class: **\{health_class\}** \{"(tobacco rated)" if tobacco else ""\}\
- Budget alternative: \{results[1]['Carrier']\} at \{results[1]['Monthly Premium']\}/month\
- \{notes if notes else 'Add custom talking points above.'\}\
        """)\
\
        # Save\
        ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), agent, client_name,\
                       age, gender, product, f"$\{coverage:,\}", health_class,\
                       tobacco, best["Carrier"], best["Monthly Premium"]])\
        st.success("\uc0\u9989  Quote saved to history.")\
\
with tab2:\
    st.subheader(f"Your Quotes \'97 \{agent\}")\
    rows = ws.get_all_records()\
    mine = [r for r in rows if r.get("Agent") == agent]\
    if not mine:\
        st.info("No quotes generated yet.")\
    else:\
        st.metric("Total Quotes Generated", len(mine))\
        st.dataframe(mine, use_container_width=True)}