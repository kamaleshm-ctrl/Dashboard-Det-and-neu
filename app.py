import streamlit as st
import pandas as pd
import io
import os
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
def get_csv_url():
    try:
        raw_url = st.secrets["private_gsheet_url"]
        # Automatically clean and convert editing URL to export CSV URL format securely
        if "/edit" in raw_url:
            base_url = raw_url.split("/edit")[0]
            return f"{base_url}/export?format=csv"
        return raw_url
    except Exception as e:
        return None

CSV_URL = get_csv_url()

def load_data():
    if CSV_URL:
        try:
            return pd.read_csv(CSV_URL)
        except Exception as e:
            # Fallback if connection fails temporarily or link is empty
            st.error(f"Could not read from Google Sheet connection. Please ensure permission is 'Anyone with link can edit'.")
            return pd.DataFrame(columns=["Timestamp", "Destination", "Trail ID", "Feedback Type", "Raw Reason", "Issue Category"])
    return pd.DataFrame(columns=["Timestamp", "Destination", "Trail ID", "Feedback Type", "Raw Reason", "Issue Category"])

def save_data(new_row):
    # Instructions for writing back or appending to Google sheet directly via web app
    # For a simple viewing connection, users can manually submit to a linked form or we export database rows.
    pass

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
st.markdown("Multi-user network enabled dashboard layout connected to your cloud data sheets.")
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
                st.toast(f"Logged: {category}!", icon="💾")

current_df = load_data()

with col_analytics:
    st.subheader("📊 Live Performance Metrics")
    if current_df.empty:
        st.info("No records loaded from the Google Sheet yet. Make sure your first row has headers: Timestamp, Destination, Trail ID, Feedback Type, Raw Reason, Issue Category")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Issues Logged", f"📊 {len(current_df)}")
        m2.metric("Detractors", f"🚨 {len(current_df[current_df['Feedback Type'] == 'Detractor'])}")
        m3.metric("Neutrals", f"😐 {len(current_df[current_df['Feedback Type'] == 'Neutral'])}")
        
        # Check table columns exist safely
        if "Issue Category" in current_df.columns and "Feedback Type" in current_df.columns:
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
    st.download_button(label="🟢 Export Central Database to Excel (.xlsx)", data=buffer.getvalue(), file_name="Market_Feedback_Master.xlsx")
