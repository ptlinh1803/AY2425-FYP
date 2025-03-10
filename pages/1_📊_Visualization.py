import streamlit as st
from datetime import datetime, timedelta
import util.visualization_util as viz

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Visualization",
    page_icon="📊",
)
# Side bar -------------------------------------
# Dropdown to select country
if "country" not in st.session_state:
    st.session_state.country = "Japan"
country = st.sidebar.selectbox("Select country", 
                               ["Japan", "China", "Australia"],
                               index=["Japan", "China", "Australia"].index(st.session_state.country))
st.session_state.country = country

# Default end date (fixed as 2024-10-31)
default_end = datetime(2024, 10, 31)

# Default start date (30 days before end date)
default_start = default_end - timedelta(days=30)

# Ensure session state keys exist
if "start_date" not in st.session_state:
    st.session_state.start_date = default_start
if "end_date" not in st.session_state:
    st.session_state.end_date = default_end
if "selected_date" not in st.session_state:
    st.session_state.selected_date = default_end
if "invalid_date" not in st.session_state:
    st.session_state.invalid_date = False
if "selected_graphs" not in st.session_state:
    st.session_state.selected_graphs = []

# Add date selection to the sidebar
st.sidebar.subheader("Select a Single Day")
selected_date = st.sidebar.date_input("Select a date", st.session_state.selected_date, min_value=viz.min_date[country], max_value=default_end)

st.sidebar.subheader("Select a Time Period")
start_date = st.sidebar.date_input("Start Date", st.session_state.start_date, min_value=viz.min_date[country], max_value=default_end)
end_date = st.sidebar.date_input("End Date", st.session_state.end_date, min_value=viz.min_date[country], max_value=default_end)

# Check if start_date is invalid
if start_date >= end_date:
    st.sidebar.warning("⚠️ Start date must be earlier than end date!")
    st.session_state.invalid_date = True
else:
    st.session_state.invalid_date = False

# Update session state with new values
st.session_state.selected_date = selected_date
st.session_state.start_date = start_date
st.session_state.end_date = end_date

# Sidebar: Additional Graph Selection
selected_graphs = st.sidebar.multiselect(
    "Choose up to 5 additional graphs to visualize in this period:",
    options=viz.additional_graphs[st.session_state.country],
    default=st.session_state.selected_graphs,
    max_selections=5  # Restrict to 5 selections
)

# Update session state with selected graphs
st.session_state.selected_graphs = selected_graphs

# Main page -------------------------------------
st.title(st.session_state.country)

# 1. Visualization for 1 day:
st.header("Visualization for a Single Day")
st.write(f"Select a date from the Sidebar to view the Government Bond Yield Curve of {st.session_state.country} on that day.")

# Load and plot yield data
file_path = f"data/combined_data/{st.session_state.country.lower()}_full_yields_only.csv"
df = viz.load_data(file_path)

if df is not None:
    viz.plot_yield_curve(df, st.session_state.selected_date, st.session_state.country)

# 2. Visualization for a period:
st.divider()
st.header("Visualization for a Selected Period")

if "invalid_date" not in st.session_state or st.session_state.invalid_date == False:
    # Yield curve heat map
    viz.plot_yield_curve_heatmap(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date)
    
    # 3D yield curve
    viz.plot_3d_yield_curve(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date)
    
    # Animated yield curve
    viz.plot_animated_yield_curve(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date, st.session_state.selected_date)

    # Try plotting 5Y yield with MA
    st.markdown("##### **5-Year Government Bond Yield with Moving Averages (NEW)**")
    df_5y = viz.filter_ticker_columns(df, "GJGB5")
    ma_columns = viz.find_moving_average_columns(df_5y)
    required_columns = ["Close"] + list(ma_columns.values())
    viz.plot_multiple_lines(df_5y, start_date, end_date, required_columns, "Japan Gov Bond Yield 5Y Maturity (NEW)")

    # Try plotting Japan Swap
    st.markdown("##### **Japan Swap Rate (NEW)**")
    df_swap = viz.load_data("data/combined_data/japan_swap_combined.csv")
    required_columns_swap = ["JYSOC_Close", "JYSO2_Close", "JYSO5_Close", "JYSO10_Close", "JYSO30_Close"]
    viz.plot_multiple_lines(df_swap, start_date, end_date, required_columns_swap, "Japan Swap Rate (NEW)")