import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. Page Configuration
st.set_page_config(page_title="SADANI OVERSEAS - Quality Dashboard", layout="wide")

# --- HEADER SECTION ---
st.markdown("""
    <div style='text-align: left;'>
        <h1 style='font-family: "Times New Roman", serif; font-style: italic; color: #1B5E20; font-size: 48px;'>
            Sadani Overseas
        </h1>
        <p style='color: #4CAF50; font-size: 18px; font-weight: 600; letter-spacing: 1.5px; margin-top: -5px;'>
            DAILY PRODUCTION VS REJECTION DASHBOARD
        </p>
    </div>
""", unsafe_allow_html=True)

# 2. Load Data from Google Sheets
@st.cache_data(ttl=600)
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
    df = pd.read_csv(sheet_url)
    # FIX: Only keep the first 7 columns to ignore the Row 65 error
    df = df.iloc[:, :7]
    df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY Checked', 'Rejected Qty', 'Rework Qty']
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Convert numeric columns safely
    for col in ['QTY Checked', 'Rejected Qty', 'Rework Qty']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Options")
    checker_filter = st.sidebar.multiselect("Select Checker:", options=df['Checker Name'].unique())
    polisher_filter = st.sidebar.multiselect("Select Polisher:", options=df['Polisher Name'].unique())

    filtered_df = df.copy()
    if checker_filter:
        filtered_df = filtered_df[filtered_df['Checker Name'].isin(checker_filter)]
    if polisher_filter:
        filtered_df = filtered_df[filtered_df['Polisher Name'].isin(polisher_filter)]

    # --- METRICS SECTION ---
    total_prod = filtered_df['QTY Checked'].sum()
    total_rej = filtered_df['Rejected Qty'].sum()
    total_rew = filtered_df['Rework Qty'].sum()
    rej_percent = (total_rej / total_prod * 100) if total_prod > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Production", f"{total_prod:,.0f}")
    col2.metric("Total Rejection", f"{total_rej:,.0f}")
    col3.metric("Total Rework", f"{total_rew:,.0f}")
    col4.metric("Avg Rejection %", f"{rej_percent:.2f}%")

    st.markdown("---")

    # --- DATA TABLE ---
    st.subheader("📝 Quality Data Table")
    st.dataframe(filtered_df, use_container_width=True)

    # --- EXCEL DOWNLOAD ---
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Report')
    
    st.download_button(
        label="📥 Download Excel Report",
        data=buf.getvalue(),
        file_name=f"Sadani_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"Dashboard is updating. Please wait 1 minute. Error: {e}")
