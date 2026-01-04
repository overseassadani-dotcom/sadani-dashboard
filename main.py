import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Page Configuration
st.set_page_config(page_title="SADANI OVERSEAS - Dashboard", layout="wide")

# --- HEADER SECTION ---
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

# 2. Data Loading (Connected to your Google Sheet)
@st.cache_data(ttl=60) 
def load_data():
    try:
        # Link to your published Google Sheet
        sheet_url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
        df = pd.read_csv(sheet_url)
        # Select first 7 columns based on your data entry format
        df = df.iloc[:, :7]
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY Checked', 'Rejected Qty', 'Rework Qty']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        # Convert values to numbers for calculation
        for col in ['QTY Checked', 'Rejected Qty', 'Rework Qty']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Connecting to live data... {e}")
        return None

df = load_data()

if df is not None:
    # 3. Sidebar Filters
    with st.sidebar:
        st.header("🔍 Filters")
        checker_f = st.multiselect("Select Checker:", options=sorted(df['Checker Name'].unique()), default=df['Checker Name'].unique())
        item_f = st.multiselect("Select Item:", options=sorted(df['Item Name'].unique()), default=df['Item Name'].unique())

    # Apply filters
    df_selection = df[(df['Checker Name'].isin(checker_f)) & (df['Item Name'].isin(item_f))].copy()

    if not df_selection.empty:
        # 4. KPI Metrics (Calculating based on your 188,719+ total)
        total_prod = df_selection['QTY Checked'].sum()
        total_rej = df_selection['Rejected Qty'].sum()
        total_rew = df_selection['Rework Qty'].sum()
        avg_rej = (total_rej / total_prod * 100) if total_prod > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Production", f"{int(total_prod):,}")
        m2.metric("Total Rejection", f"{int(total_rej):,}")
        m3.metric("Total Rework", f"{int(total_rew):,}")
        m4.metric("Avg Rejection %", f"{avg_rej:.2f}%")

        # 5. Daily Trend Graph
        st.markdown("---")
        st.subheader("📈 Daily Quality Trend")
        trend = df_selection.groupby(df_selection['Date'].dt.date).agg({'QTY Checked':'sum', 'Rejected Qty':'sum'}).reset_index()
        trend['Rej%'] = (trend['Rejected Qty'] / trend['QTY Checked'] * 100).round(2)
        fig_trend = px.line(trend, x='Date', y='Rej%', title="Daily Rejection Rate (%)", markers=True, color_discrete_sequence=['#1B5E20'])
        st.plotly_chart(fig_trend, use_container_width=True)

        # 6. TWO COLUMNS FOR GRAPHS
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👤 Checker Performance")
            checker_stats = df_selection.groupby('Checker Name').agg({'QTY Checked': 'sum'}).reset_index()
            fig_checker = px.bar(checker_stats, x='Checker Name', y='QTY Checked', text='QTY Checked', color_discrete_sequence=['#4CAF50'])
            fig_checker.update_traces(textposition='outside')
            st.plotly_chart(fig_checker, use_container_width=True)

        with col2:
            st.subheader("📦 Top Items by Rejection")
            # New Graph: Shows which items have the most rejections
            item_stats = df_selection.groupby('Item Name').agg({'Rejected Qty': 'sum'}).sort_values('Rejected Qty', ascending=False).head(10).reset_index()
            fig_item = px.bar(item_stats, x='Rejected Qty', y='Item Name', orientation='h', color_discrete_sequence=['#E53935'])
            st.plotly_chart(fig_item, use_container_width=True)

        # 7. Quality Table
        st.markdown("---")
        st.subheader("📑 Production Log")
        df_selection['Rej%'] = (df_selection['Rejected Qty'] / df_selection['QTY Checked'] * 100).round(2)
        
        def color_logic(val):
            # Green for good quality, Red for issues
            color = '#C8E6C9' if val < 2 else '#FFCDD2'
            return f'background-color: {color}; font-weight: bold'

        st.dataframe(df_selection.style.applymap(color_logic, subset=['Rej%']), use_container_width=True)

        # 8. Download Button (CSV to prevent red error box)
        csv = df_selection.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Data Report", data=csv, file_name="Sadani_Quality_Report.csv", mime="text/csv")
    else:
        st.warning("No data found for selected filters.")

# 9. Auto-refresh every 60 seconds
time.sleep(60)
st.rerun()
