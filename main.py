import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Basic Page Config
st.set_page_config(page_title="SADANI OVERSEAS", layout="wide")

# 2. Header
st.title("SADANI OVERSEAS")
st.subheader("DAILY PRODUCTION VS REJECTION DASHBOARD")

# 3. Data Loading Function
def load_data():
    try:
        # Link to your published Google Sheet CSV
        url = "https://docs.google.com/spreadsheets/d/1X15uV-k6UuSlo3D_46O9j1D0H6lR_0D_p9uD9l4qD98/pub?output=csv"
        df = pd.read_csv(url)
        
        # Clean the data: Taking only first 7 columns based on your data entry
        df = df.iloc[:, :7]
        df.columns = ['Date', 'Checker', 'Polisher', 'Item', 'Checked', 'Rejected', 'Rework']
        
        # Convert numbers
        df['Checked'] = pd.to_numeric(df['Checked'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# 4. Run the App
df = load_data()

if df is not None:
    # Show Summary Metrics
    total_prod = df['Checked'].sum()
    st.metric("Total Items Checked", f"{int(total_prod):,}")

    # Show the Performance Graph
    st.subheader("Checker Performance")
    fig = px.bar(df.groupby('Checker')['Checked'].sum().reset_index(), 
                 x='Checker', y='Checked', color_discrete_sequence=['#4CAF50'])
    st.plotly_chart(fig, use_container_width=True)

    # Show the Raw Data Table
    st.subheader("Recent Production Logs")
    st.write(df.tail(10))
else:
    st.warning("Data is loading... Please wait or refresh the page.")
