import streamlit as st
from datetime import datetime, timedelta
from util.visualization_util import load_data, min_date, plot_yield_curve, plot_yield_curve_heatmap, plot_animated_yield_curve, plot_3d_yield_curve

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Visualization",
    page_icon="📊",
)
# Side bar -------------------------------------
# Dropdown to select country
country = st.sidebar.selectbox("Select country", ["Japan", "China", "Australia"])

# Default end date (fixed as 2024-10-31)
default_end = datetime(2024, 10, 31)

# Default start date (30 days before end date)
default_start = default_end - timedelta(days=30)

# Add date selection to the sidebar
st.sidebar.subheader("Select a Specific Date")
selected_date = st.sidebar.date_input("Select a date", datetime(2024, 10, 31), min_value=min_date[country], max_value=datetime(2024, 10, 31))

st.sidebar.subheader("Select Date Range")
start_date = st.sidebar.date_input("Start Date", default_start, min_value=min_date[country], max_value=datetime(2024, 10, 31))
end_date = st.sidebar.date_input("End Date", default_end, min_value=min_date[country], max_value=datetime(2024, 10, 31))

# Check if start_date is invalid
if start_date >= end_date:
    st.sidebar.warning("⚠️ Start date must be earlier than end date!")
    st.session_state.invalid_date = True
else:
    st.session_state.invalid_date = False

# Main page -------------------------------------
st.title(country)

# 1. Visualization for 1 day:
st.header("Visualization for 1 day")
st.write(f"Select a date from the Sidebar to view the Government Bond Yield Curve of {country} on that day.")

# Load and plot yield data
file_path = f"data/combined_data/{country.lower()}_full_yields_only.csv"
df = load_data(file_path)

if df is not None:
    plot_yield_curve(df, selected_date, country)

# 2. Visualization for a period:
st.divider()
st.header("Visualization for a period")

# Draw yield curve heatmap
if "invalid_date" not in st.session_state or st.session_state.invalid_date == False:
    plot_yield_curve_heatmap(df, country, start_date, end_date)
    plot_3d_yield_curve(df, country, start_date, end_date)
    plot_animated_yield_curve(df, country, start_date, end_date, selected_date)

