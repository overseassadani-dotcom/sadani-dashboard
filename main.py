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

# 2. Data Loading Function
@st.cache_data(ttl=60)
def load_data():
    # This is the correct CSV link format
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR849g1kFi3pJDRDIOHmaubGJEebfCEPyMj3cPQbPn6LFRGWKrZFBWzUNj20yXwB-iJvIbWRd6ox8aW/pub?output=csv"
    
    try:
        # Step 1: Load the data while skipping problematic rows like Line 65
        df = pd.read_csv(url, on_bad_lines='skip', engine='python', sep=None)
        
        # Step 2: STRICTLY keep only the first 7 columns to stop the "Saw 10 fields" error
        df = df.iloc[:, :7] 
        
        # Step 3: Name the columns exactly like your spreadsheet headers
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY / PCS Checked', 'Rejected Qty/Pcs', 'Rework Qty/PCS']
        
        # Step 4: Remove empty rows
        df = df.dropna(subset=['Date']) 
        
        # Step 5: Clean the data for the charts
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Checker'] = df['Checker Name'].astype(str).str.strip()
        df['Polisher'] = df['Polisher Name'].astype(str).str.strip()
        df['Part'] = df['Item Name'].astype(str).str.strip()
        
        # Convert numbers and fill missing spots with 0
        df['Production'] = pd.to_numeric(df['QTY / PCS Checked'], errors='coerce').fillna(0)
        df['Rejected'] = pd.to_numeric(df['Rejected Qty/Pcs'], errors='coerce').fillna(0)
        df['Rework'] = pd.to_numeric(df['Rework Qty/PCS'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Waiting for clean data... {e}")
        return None

# Run the data loader
df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    with st.sidebar:
        st.header("🔍 Filters")
        start_date = st.date_input("Start Date", value=df['Date'].min().date())
        end_date = st.date_input("End Date", value=df['Date'].max().date())
        checker_f = st.multiselect("Checker:", options=sorted(df['Checker'].unique()), default=df['Checker'].unique())
        polisher_f = st.multiselect("Polisher:", options=sorted(df['Polisher'].unique()), default=df['Polisher'].unique())

    # Apply filters
    df_selection = df[
        (df['Date'].dt.date >= start_date) & 
        (df['Date'].dt.date <= end_date) & 
        (df['Checker'].isin(checker_f)) & 
        (df['Polisher'].isin(polisher_f))
    ].copy()

    if not df_selection.empty:
        # KPI CALCULATIONS
        total_prod = df_selection['Production'].sum()
        total_rej = df_selection['Rejected'].sum()
        total_rew = df_selection['Rework'].sum()
        rej_percent = (total_rej / total_prod * 100) if total_prod > 0 else 0

        # Display Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Production", f"{int(total_prod):,}")
        c2.metric("Total Rejected", f"{int(total_rej):,}")
        c3.metric("Total Rework", f"{int(total_rew):,}")
        c4.metric("Rejection %", f"{rej_percent:.2f}%")

        # Master Table with Coloring
        st.markdown("---")
        st.subheader("📑 Quality Data Table")
        df_display = df_selection.copy()
        df_display['Rejection %'] = (df_display['Rejected'] / df_display['Production'] * 100).fillna(0).round(2)
        
        def color_logic(val):
            if val == 0: return 'background-color: #BBDEFB' # Blue
            elif val < 2.0: return 'background-color: #C8E6C9' # Green
            else: return 'background-color: #FFCDD2' # Red

        st.dataframe(df_display.style.applymap(color_logic, subset=['Rejection %']), use_container_width=True)

        # Download Button
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False)
        st.download_button("📥 Download Excel Report", data=buf.getvalue(), file_name="Quality_Report.xlsx")

# Auto-refresh logic
time.sleep(60)
st.rerun()
