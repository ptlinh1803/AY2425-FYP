import streamlit as st
from datetime import datetime, timedelta
import util.visualization_util as viz

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Visualization",
    page_icon="📊",
)
# Side bar -------------------------------------

# Default end date (fixed as 2024-10-31)
default_end = datetime(2024, 10, 31)

# Default start date (30 days before end date)
default_start = default_end - timedelta(days=30)

# Initialize session state variables
if "country" not in st.session_state:
    st.session_state.country = "Japan"
if "start_date" not in st.session_state:
    st.session_state.start_date = default_start
if "end_date" not in st.session_state:
    st.session_state.end_date = default_end
if "selected_date" not in st.session_state:
    st.session_state.selected_date = default_end
if "invalid_date" not in st.session_state:
    st.session_state.invalid_date = False

# Callback function to update session state
def update_country():
    st.session_state.country = st.session_state["country_picker"]

def update_selected_date():
    st.session_state.selected_date = datetime.combine(st.session_state["selected_date_picker"], datetime.min.time())

def update_start_date():
    st.session_state.start_date = datetime.combine(st.session_state["start_date_picker"], datetime.min.time())

def update_end_date():
    st.session_state.end_date = datetime.combine(st.session_state["end_date_picker"], datetime.min.time())

# Dropdown to select country
st.sidebar.selectbox(
    "Select country", 
    ["Japan", "China", "Australia"],
    index=["Japan", "China", "Australia"].index(st.session_state.country),
    key="country_picker",
    on_change=update_country
)

# Add date selection to the sidebar
st.sidebar.subheader("Select a Single Day")
st.sidebar.date_input("Select a date", 
                      value=st.session_state.selected_date, 
                      min_value=datetime(2000, 1, 4), 
                      max_value=default_end,
                      key="selected_date_picker",
                      on_change=update_selected_date)

st.sidebar.subheader("Select a Time Period")
st.sidebar.date_input("Start Date", 
                      value=st.session_state.start_date, 
                      min_value=datetime(2000, 1, 4), 
                      max_value=default_end,
                      key="start_date_picker",
                      on_change=update_start_date)
st.sidebar.date_input("End Date", 
                      value=st.session_state.end_date, 
                      min_value=datetime(2000, 1, 4), 
                      max_value=default_end,
                      key="end_date_picker",
                      on_change=update_end_date)

# Check if start_date is invalid
if st.session_state.start_date >= st.session_state.end_date:
    st.sidebar.warning("⚠️ Start date must be earlier than end date!")
    st.session_state.invalid_date = True
else:
    st.session_state.invalid_date = False

# Sidebar: Additional Graph Selection
selected_graphs = st.sidebar.multiselect(
    "Choose up to 5 additional insights to explore in this period:",
    options=viz.additional_graphs[st.session_state.country],
    default=[],
    max_selections=5,
    key="graph_picker"
)

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
st.header("Visualization for a Selected Period")

if "invalid_date" not in st.session_state or st.session_state.invalid_date == False:
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Yield Curve Trends", "🌍 3D Yield Curve", "🔥 Yield Curve Heatmap", "🎞️ Yield Curve Animation"])
    # Line plot of yield curve trends
    with tab1:
       title = f"{st.session_state.country} Government Bond Yield Trends by Maturity"
       st.markdown(f"##### **{title}**")
       required_columns = viz.yield_columns[st.session_state.country]
       df_filtered_yields = viz.filter_dataframe(df, st.session_state.start_date, st.session_state.end_date, required_columns=required_columns)
       # Remove suffix _Close
       required_columns = [col.replace("_Close", "") for col in required_columns]
       df_filtered_yields.columns = [col.replace("_Close", "") for col in df_filtered_yields.columns]
       viz.plot_multiple_lines(df_filtered_yields, st.session_state.start_date, st.session_state.end_date, required_columns, title, is_filtered=True)
    # 3D yield curve
    with tab2:
        st.markdown(f"##### **{st.session_state.country} Government Bond Yield Curve 3D Surface**")
        viz.plot_3d_yield_curve(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date)
    # Yield curve heatmap 
    with tab3:
        st.markdown(f"##### **{st.session_state.country} Government Bond Yield Curve Heatmap**")
        viz.plot_yield_curve_heatmap(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date)
    # Animated yield curve
    with tab4:
        st.markdown(f"##### **{st.session_state.country} Government Bond Yield Curve Animation**")
        viz.plot_animated_yield_curve(df, st.session_state.country, st.session_state.start_date, st.session_state.end_date, st.session_state.selected_date)

    # Plot additional graphs
    for sg in selected_graphs:
        # Individual maturity
        if sg in viz.yield_mapping:
            st.markdown(f"##### **{st.session_state.country} {sg}**")
            df_y = viz.filter_ticker_columns(df, viz.yield_mapping[sg][st.session_state.country])
            ma_columns = viz.find_moving_average_columns(df_y)
            required_columns = ["Close"] + list(ma_columns.values())
            viz.plot_multiple_lines(df_y, st.session_state.start_date, st.session_state.end_date, required_columns, f"{st.session_state.country} {sg}")

