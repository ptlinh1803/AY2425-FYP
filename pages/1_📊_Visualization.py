import streamlit as st
from datetime import datetime
from util.visualization_util import load_data, min_date, plot_yield_curve

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Visualization",
    page_icon="📊",
)
# Side bar -------------------------------------
# Dropdown to select country
country = st.sidebar.selectbox("Select country", ["Japan", "China", "Australia"])

# Main page -------------------------------------
st.title(country)

st.header("Visualization for 1 day")
st.write(f"Select a specific day to see the Government Bond Yield Curve of {country} for that day.")

# Default date (last day 31/10/2024)
selected_date = st.date_input("Select a date", datetime(2024, 10, 31), min_value=min_date[country], max_value=datetime(2024, 10, 31))

# Display selected date
st.write(f"Selected Date: **{selected_date.strftime('%d-%m-%Y')}**")

# Load data
df = load_data(country)

if df is not None:
    plot_yield_curve(df, selected_date, country)