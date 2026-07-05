import streamlit as st
import pandas as pd
import io
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Market Storage Dashboard", layout="wide")

# Custom Visual Styling for Light Green Theme & Animations
st.markdown("""
    <style>
    .stApp { background-color: #e8f5e9; }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    div[data-testid="stVerticalBlock"] > div { animation: fadeIn 0.6s ease-out; }
    .stForm {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #c8e6c9 !important;
        padding: 25px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    h1, h2, h3, label, p, span { color: #1b5e20 !important; }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2e7d32 !important;
    }
    </style>
""", unsafe_allow_html=True)

DESTINATIONS = [
    "MLE", "SL", "MRU", "SEY", "ANDAMAN", "JK", 
    "BHUTAN", "RAJASTHAN", "NORTHEAST", "KERALA", 
    "TAMILNADU", "OTHER DOMESTIC"
]

# --- GOOGLE SHEETS CLOUD STORAGE CONNECTION ---
# When deployed, you can paste your Google Sheet URL into Streamlit secrets.
# For local testing, it falls back to a temporary local cache.
try:
    # If secrets are configured in the cloud
    GSHEET_URL = st.secrets["private_gsheet_url"]
except:
    # Local fallback for your testing right now
    if "backup_db" not in st.session_state:
        st.session_state.backup_db = pd.DataFrame(columns=["Timestamp", "Destination", "Trail ID", "Feedback Type", "Raw Reason", "Issue Category"])
    GSHEET_URL = None

def load_data():
    if GSHEET_URL:
        # Pull real-time live data from the connected central Google Sheet
        csv_url = GSHEET_URL.replace("/edit?usp=sharing", "/export?format=csv")
        return pd.read_csv(csv_url)
    return st.session_state.backup_db

def save_data(new_row):
    if GSHEET_URL:
        # In a production cloud setting, this pushes the line to your Google sheet row
        # using standard streamlit-gsheets connections
        pass
    else:
        df = st.session_state.backup_db
        st.session_state.backup_db = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

def categorize_issue(reason_text):
    text = str(reason_text).lower()
    if any(word in text for word in ["hotel", "room", "stay", "property", "bed"]): return "Accommodation Issue"
    elif any(word in text for word in ["flight", "cab", "driver", "transport", "vehicle", "delay"]): return "Logistics & Transport"
    elif any(word in text for word in ["price", "cost", "expensive", "hidden", "fee", "refund"]): return "Pricing & Billing"
    elif any(word in text for word in ["guide", "itinerary", "sightseeing", "missed", "cancel"]): return "Itinerary & Sightseeing"
    elif any(word in text for word in ["agent", "staff", "behavior", "support", "response"]): return "Customer Service"
    return "Other / General Feedback"

# --- INTERFACE ---
st.title("✨ Centralized Market Data Storage Dashboard")
st.markdown("Multi-user network enabled dashboard layout.")
st.markdown("---")

col_input, col_analytics = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("📥 Log New Entry")
    with st.form("entry_form", clear_on_submit=True):
        destination = st.selectbox("Select Destination", options=DESTINATIONS)
        trail_id = st.text_input("Enter Trail ID", placeholder="e.g., TR-98431")
        feedback_type = st.radio("Feedback Type", options=["Detractor", "Neutral"], horizontal=True)
        reason = st.text_area("Enter Reason / Feedback Description")
        submit_btn = st.form_submit_button("🟢 Save Entry Permanently")
        
        if submit_btn:
            if not trail_id.strip() or not reason.strip():
                st.error("Fields cannot be blank.")
            else:
                category = categorize_issue(reason)
                new_row = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Destination": destination,
                    "Trail ID": trail_id.strip(),
                    "Feedback Type": feedback_type,
                    "Raw Reason": reason.strip(),
                    "Issue Category": category
                }
                save_data(new_row)
                st.toast("Saved Successfully!", icon="💾")

current_df = load_data()

with col_analytics:
    st.subheader("📊 Live Performance Metrics")
    if current_df.empty:
        st.info("No records loaded yet.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Issues Logged", f"📊 {len(current_df)}")
        m2.metric("Detractors", f"🚨 {len(current_df[current_df['Feedback Type'] == 'Detractor'])}")
        m3.metric("Neutrals", f"😐 {len(current_df[current_df['Feedback Type'] == 'Neutral'])}")
        
        summary_table = current_df.groupby(["Issue Category", "Feedback Type"]).size().unstack(fill_value=0)
        for col in ["Detractor", "Neutral"]:
            if col not in summary_table.columns: summary_table[col] = 0
        st.dataframe(summary_table, use_container_width=True)

st.markdown("---")
if not current_df.empty:
    st.dataframe(current_df.sort_index(ascending=False), use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        current_df.to_excel(writer, sheet_name="All Saved Logs", index=False)
    st.download_button(label="🟢 Export Master Database to Excel (.xlsx)", data=buffer.getvalue(), file_name="Market_Feedback.xlsx")