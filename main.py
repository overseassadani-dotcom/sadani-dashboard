import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
import time

# 1. Page Configuration
st.set_page_config(page_title="SADANI OVERSEAS - Quality Dashboard", layout="wide")

# --- HEADER SECTION ---
st.markdown("""
    <div style='text-align: left;'>
        <h1 style='font-family: "Times New Roman", serif; font-style: italic; color: #1B5E20; font-size: 48px; margin-bottom: 0px;'>
            Sadani Overseas
        </h1>
        <p style='color: #4CAF50; font-size: 18px; font-weight: 600; letter-spacing: 1.5px; margin-top: -5px;'>
            DAILY PRODUCTION VS REJECTION DASHBOARD
        </p>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #E8F5E9; margin-bottom: 25px;'>", unsafe_allow_html=True)

# 2. Data Loading from Google Sheets
@st.cache_data(ttl=60) # Updates every 60 seconds
def load_data():
    # --- PASTE YOUR LINK BELOW ---
    google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR849g1kFi3pJDRDIOHmaubGJEebfCEPyMj3cPQbPn6LFRGWKrZFBWzUNj20yXwB-iJvIbWRd6ox8aW/pubhtml"
    
    try:
        # 2. Data Loading from Google Sheets
@st.cache_data(ttl=60)
def load_data():
    google_sheet_url = "PASTE_YOUR_LINK_HERE" # Keep your actual link here
    try:
        # This new line is much stronger against formatting errors
        df = pd.read_csv(google_sheet_url, on_bad_lines='skip', engine='python', sep=None)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Ensure we only use the first 7 necessary columns to avoid "ghost" data
        df = df.iloc[:, :7] 
        
        # Rename columns to match your dashboard exactly
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY / PCS Checked', 'Rejected Qty/Pcs', 'Rework Qty/PCS']
        
        # Convert data types
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) # Remove empty rows
        df['Checker'] = df['Checker Name'].astype(str)
        df['Polisher'] = df['Polisher Name'].astype(str)
        df['Part'] = df['Item Name'].astype(str)
        df['Production'] = pd.to_numeric(df['QTY / PCS Checked'], errors='coerce').fillna(0)
        df['Rejected'] = pd.to_numeric(df['Rejected Qty/Pcs'], errors='coerce').fillna(0)
        df['Rework'] = pd.to_numeric(df['Rework Qty/PCS'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Waiting for clean data... {e}")
        return None
        # Clean column names
        df.columns = df.columns.str.strip()
        df['Date'] = pd.to_datetime(df['Date'])
        df['Checker'] = df['Checker Name'].astype(str)
        df['Polisher'] = df['Polisher Name'].astype(str)
        df['Part'] = df['Item Name'].astype(str)
        df['Production'] = pd.to_numeric(df['QTY / PCS Checked'], errors='coerce').fillna(0)
        df['Rejected'] = pd.to_numeric(df['Rejected Qty/Pcs'], errors='coerce').fillna(0)
        df['Rework'] = pd.to_numeric(df['Rework Qty/PCS'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}. Check if your Google Sheet is 'Published to Web' as CSV.")
        return None

df = load_data()

if df is not None:
    # --- FILTERS ---
    with st.sidebar:
        st.header("🔍 Filters")
        start_date = st.date_input("Start Date", value=df['Date'].min().date())
        end_date = st.date_input("End Date", value=df['Date'].max().date())
        checker_f = st.multiselect("Checker:", options=sorted(df['Checker'].unique()), default=df['Checker'].unique())
        polisher_f = st.multiselect("Polisher:", options=sorted(df['Polisher'].unique()), default=df['Polisher'].unique())
        part_f = st.multiselect("Part Name:", options=sorted(df['Part'].unique()), default=df['Part'].unique())

    df_selection = df[
        (df['Date'].dt.date >= start_date) & 
        (df['Date'].dt.date <= end_date) & 
        (df['Checker'].isin(checker_f)) & 
        (df['Polisher'].isin(polisher_f)) & 
        (df['Part'].isin(part_f))
    ].copy()

    if not df_selection.empty:
        # KPI METRICS
        total_prod = df_selection['Production'].sum()
        total_rej = df_selection['Rejected'].sum()
        total_rew = df_selection['Rework'].sum()
        avg_rej_percent = (total_rej / total_prod * 100) if total_prod > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div style='text-align:center; background-color:#E8F5E9; padding:15px; border-radius:10px; border-left: 5px solid #2E7D32;'><p style='color:#2E7D32; font-size:16px; margin:0;'>Total Production</p><h2 style='color:#1B5E20; margin:0;'>{int(total_prod):,}</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div style='text-align:center; background-color:#FFEBEE; padding:15px; border-radius:10px; border-left: 5px solid #C62828;'><p style='color:#C62828; font-size:16px; margin:0;'>Total Rejection</p><h2 style='color:#B71C1C; margin:0;'>{int(total_rej):,}</h2></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div style='text-align:center; background-color:#FFF3E0; padding:15px; border-radius:10px; border-left: 5px solid #EF6C00;'><p style='color:#EF6C00; font-size:16px; margin:0;'>Total Rework</p><h2 style='color:#E65100; margin:0;'>{int(total_rew):,}</h2></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div style='text-align:center; background-color:#F3E5F5; padding:15px; border-radius:10px; border-left: 5px solid #7B1FA2;'><p style='color:#7B1FA2; font-size:16px; margin:0;'>Avg Rejection %</p><h2 style='color:#4A148C; margin:0;'>{avg_rej_percent:.2f}%</h2></div>", unsafe_allow_html=True)

        # Master Table with Color Logic
        st.markdown("---")
        st.subheader("📑 Full Master Data Table")
        df_display = df_selection.copy()
        df_display['Rejection %'] = (df_display['Rejected'] / df_display['Production'] * 100).fillna(0).round(2)
        
        def style_master_table(val):
            if val == 0: return 'background-color: #BBDEFB; color: black;' # Blue
            elif val < 2.0: return 'background-color: #C8E6C9; color: black;' # Green
            elif val < 5.0: return 'background-color: #FFF9C4; color: black;' # Yellow
            else: return 'background-color: #FFCDD2; color: #990000;' # Red

        st.dataframe(df_display.style.applymap(style_master_table, subset=['Rejection %']), use_container_width=True)

        # Download Report Button
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False)
        st.download_button(label="📥 Download Excel Report", data=buf.getvalue(), file_name="Sadani_Quality_Report.xlsx", mime="application/vnd.ms-excel")

    else:
        st.warning("⚠️ No data matches your filters.")

# Auto-refresh logic (checks for Google Sheet updates every 60s)
time.sleep(60)
st.rerun()
