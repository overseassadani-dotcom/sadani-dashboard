import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Page Setup
st.set_page_config(page_title="SADANI OVERSEAS - Quality Dashboard", layout="wide")

# --- HEADER ---
st.markdown("""
    <div style='text-align: left;'>
        <h1 style='font-family: "Times New Roman", serif; font-style: italic; color: #1B5E20; font-size: 48px; margin-bottom: 0px;'>
            Sadani Overseas
        </h1>
        <p style='color: #4CAF50; font-size: 18px; font-weight: 600; letter-spacing: 1.5px; margin-top: -5px;'>
            PRODUCTION & QUALITY ANALYTICS DASHBOARD
        </p>
    </div>
    <hr style='border: 1px solid #E8F5E9; margin-bottom: 25px;'>
    """, unsafe_allow_html=True)

# 2. Load Data from Google Sheet
@st.cache_data(ttl=60) 
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
        df = pd.read_csv(url).iloc[:, :7]
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY Checked', 'Rejected Qty', 'Rework Qty']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        for col in ['QTY Checked', 'Rejected Qty', 'Rework Qty']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return None

df = load_data()

if df is not None:
    # 3. Filters
    with st.sidebar:
        st.header("🔍 Filters")
        checker_f = st.multiselect("Select Checker:", options=sorted(df['Checker Name'].unique()), default=df['Checker Name'].unique())
        item_f = st.multiselect("Select Item:", options=sorted(df['Item Name'].unique()), default=df['Item Name'].unique())

    df_filtered = df[(df['Checker Name'].isin(checker_f)) & (df['Item Name'].isin(item_f))].copy()

    if not df_filtered.empty:
        # 4. KPI Metrics
        total_p = df_filtered['QTY Checked'].sum()
        total_r = df_filtered['Rejected Qty'].sum()
        avg_rej = (total_r / total_p * 100) if total_p > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Production", f"{int(total_p):,}")
        c2.metric("Total Rejection", f"{int(total_r):,}")
        c3.metric("Avg Rejection %", f"{avg_rej:.2f}%")

        # 5. GRAPHS
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Checker-wise Performance")
            c_data = df_filtered.groupby('Checker Name').agg({'QTY Checked': 'sum'}).reset_index()
            fig1 = px.bar(c_data, x='Checker Name', y='QTY Checked', text='QTY Checked', color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("📈 Rejection Trend")
            t_data = df_filtered.groupby('Date').agg({'Rejected Qty': 'sum'}).reset_index()
            fig2 = px.line(t_data, x='Date', y='Rejected Qty', markers=True, color_discrete_sequence=['#E53935'])
            st.plotly_chart(fig2, use_container_width=True)

        # 6. Quality Table
        st.markdown("---")
        st.subheader("📑 Production Log")
        df_filtered['Rej%'] = (df_filtered['Rejected Qty'] / df_filtered['QTY Checked'] * 100).round(2)
        st.dataframe(df_filtered.style.applymap(lambda v: 'background-color: #C8E6C9' if v < 2 else 'background-color: #FFCDD2', subset=['Rej%']), use_container_width=True)

        # 7. Download Button (CSV to fix the Red Error)
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", data=csv, file_name="Sadani_Report.csv", mime="text/csv")
    else:
        st.warning("No data found for current filters.")

# Auto-refresh every minute
time.sleep(60)
st.rerun()
