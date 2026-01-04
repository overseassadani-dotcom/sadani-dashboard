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
        # Check for local logo or display text header
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        else:
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

# 2. Data Loading (Connected to Live Google Sheets)
@st.cache_data(ttl=60) 
def load_data():
    try:
        # Direct link to your Google Sheets CSV
        sheet_url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
        df = pd.read_csv(sheet_url)
        
        # Clean data to prevent the Row 65 error
        df = df.iloc[:, :7]
        df.columns = ['Date', 'Checker Name', 'Polisher Name', 'Item Name', 'QTY Checked', 'Rejected Qty', 'Rework Qty']
        
        # Format columns for dashboard logic
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df['Checker'] = df['Checker Name'].astype(str)
        df['Polisher'] = df['Polisher Name'].astype(str)
        df['Part'] = df['Item Name'].astype(str)
        
        # Ensure numbers are treated as numbers
        for col in ['QTY Checked', 'Rejected Qty', 'Rework Qty']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error connecting to data: {e}")
        return None

df = load_data()

if df is not None:
    # 3. Sidebar Filters
    with st.sidebar:
        st.header("🔍 Filters")
        start_date = st.date_input("Start Date", value=df['Date'].min().date())
        end_date = st.date_input("End Date", value=df['Date'].max().date())
        checker_f = st.multiselect("Select Checker:", options=sorted(df['Checker'].unique()), default=df['Checker'].unique())
        polisher_f = st.multiselect("Select Polisher:", options=sorted(df['Polisher'].unique()), default=df['Polisher'].unique())
        part_f = st.multiselect("Select Part Name:", options=sorted(df['Part'].unique()), default=df['Part'].unique())

    # Apply Filters to the Data
    df_selection = df[
        (df['Date'].dt.date >= start_date) & 
        (df['Date'].dt.date <= end_date) & 
        (df['Checker'].isin(checker_f)) & 
        (df['Polisher'].isin(polisher_f)) & 
        (df['Part'].isin(part_f))
    ].copy()

    if not df_selection.empty:
        # 4. KPI Metrics (Colored Boxes)
        total_prod = df_selection['QTY Checked'].sum()
        total_rej = df_selection['Rejected Qty'].sum()
        total_rew = df_selection['Rework Qty'].sum()
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

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Performance Highlights (Top 3)
        st.markdown("### 🏆 Performance Highlights")
        s1, s2 = st.columns(2)
        with s1:
            best_pol = df_selection.groupby('Polisher').agg({'QTY Checked':'sum', 'Rejected Qty':'sum'})
            best_pol['Rej%'] = (best_pol['Rejected Qty'] / best_pol['QTY Checked'] * 100).fillna(0).round(2)
            st.success("✨ **Top 3 Polishers (Best Quality)**")
            st.table(best_pol.sort_values('Rej%').head(3)[['Rej%']])
        with s2:
            worst_part = df_selection.groupby('Part').agg({'QTY Checked':'sum', 'Rejected Qty':'sum'})
            worst_part['Rej%'] = (worst_part['Rejected Qty'] / worst_part['QTY Checked'] * 100).fillna(0).round(2)
            st.error("⚠️ **Top 3 Parts (High Rejection)**")
            st.table(worst_part.sort_values('Rej%', ascending=False).head(3)[['Rej%']])

        # 6. Trend Analysis Graph
        st.markdown("---")
        st.subheader("📈 Monthly Quality Trend")
        df_trend = df.copy()
        df_trend['Month'] = df_trend['Date'].dt.to_period('M').astype(str)
        trend_data = df_trend.groupby('Month').agg({'QTY Checked':'sum', 'Rejected Qty':'sum'}).reset_index()
        trend_data['Rej%'] = (trend_data['Rejected Qty'] / trend_data['QTY Checked'] * 100).fillna(0).round(2)
        
        fig_trend = px.line(trend_data, x='Month', y='Rej%', text='Rej%', markers=True, color_discrete_sequence=['#1B5E20'])
        fig_trend.update_traces(textposition="top center")
        st.plotly_chart(fig_trend, use_container_width=True)

        # 7. Quality Performance Graphs
        st.markdown("---")
        color_map = {"QTY Checked": "#2E7D32", "Rejected Qty": "#D32F2F", "Rework Qty": "#FBC02D"}

        def display_graph_with_data(data, x_col, title):
            summary = data.groupby(x_col)[["QTY Checked", "Rejected Qty", "Rework Qty"]].sum().reset_index()
            summary['Rej%'] = (summary['Rejected Qty'] / summary['QTY Checked'] * 100).fillna(0).round(2)
            melted = summary.drop(columns=['Rej%']).melt(id_vars=x_col, var_name="Type", value_name="Total")
            
            fig = px.bar(melted, x=x_col, y="Total", color="Type", barmode="group", text="Total",
                         color_discrete_map=color_map, title=f"<b>{title}</b>", height=450, template="plotly_white")
            fig.update_traces(textposition='outside', cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander(f"📊 View {title} Table"):
                st.table(summary.style.background_gradient(subset=['Rej%'], cmap='Reds'))

        display_graph_with_data(df_selection, "Polisher", "Polisher Quality Performance")
        display_graph_with_data(df_selection, "Part", "Part-wise Quality Analysis")

        # 8. Color-Coded Master Table
        st.markdown("---")
        st.subheader("📑 Full Quality Data Table")
        
        df_display = df_selection.copy()
        df_display['Rej%'] = (df_display['Rejected Qty'] / df_display['QTY Checked'] * 100).fillna(0).round(2)
        
        # Color Logic: Blue (0%), Green (<2%), Yellow (2-5%), Red (>5%)
        def style_master_table(val):
            if val == 0: return 'background-color: #BBDEFB; color: black; font-weight: bold' 
            elif val < 2.0: return 'background-color: #C8E6C9; color: black; font-weight: bold' 
            elif val < 5.0: return 'background-color: #FFF9C4; color: black; font-weight: bold' 
            else: return 'background-color: #FFCDD2; color: #990000; font-weight: bold' 

        st.dataframe(df_display.style.applymap(style_master_table, subset=['Rej%']), use_container_width=True)

        # 9. Excel Download Button
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False, sheet_name='MasterReport')
        
        st.download_button(
            label="📥 Download Full Report (Excel)",
            data=buf.getvalue(),
            file_name=f"Sadani_Quality_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )

    else:
        st.warning("⚠️ No data matches your selected filters.")

# 10. Auto-Refresh (Updates every 60 seconds)
time.sleep(60)
st.rerun()
