import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime
import time

# 1. Page Configuration
st.set_page_config(page_title="SADANI OVERSEAS - Quality Dashboard", layout="wide")

# --- HEADER SECTION ---
header_container = st.container()
with header_container:
    col_logo, col_title, col_time = st.columns([1, 4, 1])
    with col_logo:
        st.markdown("<h1 style='color: #2E7D32; margin:0;'>SADANI</h1>", unsafe_allow_html=True)
    with col_title:
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
    with col_time:
        now = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"<p style='text-align:right; color:gray; font-size:12px;'>Last Refresh:<br><b>{now}</b></p>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #E8F5E9; margin-bottom: 25px;'>", unsafe_allow_html=True)

# 2. Data Loading (Live Connection)
@st.cache_data(ttl=60) 
def load_data():
    try:
        sheet_url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
        df = pd.read_csv(sheet_url)
        df = df.iloc[:, :7] # This line stops the Row 65 data error
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY Checked', 'Rejected Qty', 'Rework Qty']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        for col in ['QTY Checked', 'Rejected Qty', 'Rework Qty']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Waiting for data: {e}")
        return None

df = load_data()

if df is not None:
    # 3. Sidebar Filters
    with st.sidebar:
        st.header("🔍 Filters")
        checker_f = st.multiselect("Select Checker:", options=sorted(df['Checker Name'].unique()), default=df['Checker Name'].unique())
        polisher_f = st.multiselect("Select Polisher:", options=sorted(df['Polisher Name'].unique()), default=df['Polisher Name'].unique())

    df_selection = df[(df['Checker Name'].isin(checker_f)) & (df['Polisher Name'].isin(polisher_f))].copy()

    if not df_selection.empty:
        # 4. KPI Metrics
        total_prod = df_selection['QTY Checked'].sum()
        total_rej = df_selection['Rejected Qty'].sum()
        total_rew = df_selection['Rework Qty'].sum()
        avg_rej = (total_rej / total_prod * 100) if total_prod > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Production", f"{int(total_prod):,}")
        m2.metric("Total Rejection", f"{int(total_rej):,}")
        m3.metric("Total Rework", f"{int(total_rew):,}")
        m4.metric("Avg Rejection %", f"{avg_rej:.2f}%")

        # 5. Trend Graph
        st.markdown("---")
        st.subheader("📈 Quality Trend")
        trend_data = df_selection.groupby(df_selection['Date'].dt.date).agg({'QTY Checked':'sum', 'Rejected Qty':'sum'}).reset_index()
        trend_data['Rej%'] = (trend_data['Rejected Qty'] / trend_data['QTY Checked'] * 100).round(2)
        fig = px.line(trend_data, x='Date', y='Rej%', title="Daily Rejection Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # 6. Quality Data Table with Color Logic
        st.markdown("---")
        st.subheader("📑 Full Quality Data")
        df_selection['Rej%'] = (df_selection['Rejected Qty'] / df_selection['QTY Checked'] * 100).round(2)
        
        def color_rej(val):
            color = '#C8E6C9' if val < 2 else '#FFCDD2' # Green if <2%, Red if >2%
            return f'background-color: {color}'

        st.dataframe(df_selection.style.applymap(color_rej, subset=['Rej%']), use_container_width=True)

        # 7. Download Button (Uses CSV to avoid the Excel tool error)
        csv_data = df_selection.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Report",
            data=csv_data,
            file_name="Sadani_Overseas_Report.csv",
            mime="text/csv"
        )

    else:
        st.warning("No data matches filters.")

# Auto-refresh
time.sleep(60)
st.rerun()
