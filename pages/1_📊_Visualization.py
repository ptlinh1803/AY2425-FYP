import streamlit as st
from datetime import datetime, timedelta
import util.visualization_util as viz
import util.openai_util as openai_util

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
if "ai_summary_single_response" not in st.session_state:
    st.session_state.ai_summary_single_response = None
if "ai_summary_trend_response" not in st.session_state:
    st.session_state.ai_summary_trend_response = None
if "ai_summary_multi_response" not in st.session_state:
    st.session_state.ai_summary_multi_response = None

# Callback function to update session state
def update_country():
    st.session_state.country = st.session_state["country_picker"]
    st.session_state.ai_summary_single_response = None

def update_selected_date():
    st.session_state.selected_date = datetime.combine(st.session_state["selected_date_picker"], datetime.min.time())
    st.session_state.ai_summary_single_response = None # clear AI summary for the previously selected date

def update_start_date():
    st.session_state.start_date = datetime.combine(st.session_state["start_date_picker"], datetime.min.time())
    st.session_state.ai_summary_trend_response = None

def update_end_date():
    st.session_state.end_date = datetime.combine(st.session_state["end_date_picker"], datetime.min.time())
    st.session_state.ai_summary_trend_response = None

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

# If selected_graphs change, clear the previous response
if "prev_selected_graphs" not in st.session_state:
    st.session_state.prev_selected_graphs = selected_graphs

if selected_graphs != st.session_state.prev_selected_graphs:
    st.session_state.ai_summary_multi_response = None  # Clear AI response when graphs change
    st.session_state.prev_selected_graphs = selected_graphs  # Update stored graphs

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

if df is not None:
    df_filtered = viz.select_yield_for_one_day(df, st.session_state.selected_date, st.session_state.country)
    if df_filtered is not None and not df_filtered.empty:
        
        if st.button("💡 AI Summary", key="ai_summary_single"):
            # Call OpenAI API and get response
            prompt = openai_util.generate_prompt_for_a_single_day(df_filtered, st.session_state.selected_date, st.session_state.country)
            with st.status("🔄 Analyzing the Yield Curve...", expanded=False):
                st.session_state.ai_summary_single_response = openai_util.get_openai_response(prompt, basic=True)

if st.session_state.ai_summary_single_response:
    # Display response in an expander
    with st.expander("📊 AI-Generated Analysis"):
        st.markdown(st.session_state.ai_summary_single_response)
        

# 2. Visualization for a period:
st.header("Visualization for a Selected Period")
summary_for_prompt = []

if "invalid_date" not in st.session_state or st.session_state.invalid_date == False:
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Yield Curve Trends", "🌍 3D Yield Curve", "🔥 Yield Curve Heatmap", "🎞️ Yield Curve Animation"])
    # Line plot of yield curve trends
    title = f"{st.session_state.country} Government Bond Yield Trends by Maturity"
    with tab1:
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

    # Summary of key trends
    required_columns = viz.yield_columns[st.session_state.country]
    df_filtered = viz.filter_dataframe(df, st.session_state.start_date, st.session_state.end_date, required_columns)
    summary_yield_curve_key_trends = openai_util.summarize_basic_trends(df_filtered, st.session_state.start_date, st.session_state.end_date, title)
    summary_for_prompt.append(summary_yield_curve_key_trends)
    with st.expander("📑 Key Trend Insights"):
        st.markdown(summary_yield_curve_key_trends)

    # Get AI Summary for the whole yield curve during this period
    if st.button("💡 AI Summary", key="ai_summary_trend"):
        prompt_trend = openai_util.generate_yield_curve_trend_prompt(st.session_state.country, st.session_state.start_date, st.session_state.end_date, summary_yield_curve_key_trends)
        with st.status("🔄 Analyzing the Yield Curve over a period...", expanded=False):
            st.session_state.ai_summary_trend_response = openai_util.get_openai_response(prompt_trend)

    if st.session_state.ai_summary_trend_response:
        with st.expander("📊 AI Analysis (Trend)"):
            st.markdown(st.session_state.ai_summary_trend_response)

    st.divider()
    # Plot additional graphs
    if selected_graphs:
        st.subheader("Additional Insights:")

    for sg in selected_graphs:
        # Individual maturity
        if sg in viz.yield_mapping:
            title = f"{st.session_state.country} {viz.yield_mapping[sg]['title']}"
            st.markdown(f"##### **{title}**")
            df_y = viz.filter_ticker_columns(df, viz.yield_mapping[sg][st.session_state.country])
            ma_columns = viz.find_moving_average_columns(df_y)
            required_columns = ["Close"] + list(ma_columns.values())
            viz.plot_multiple_lines(df_y, st.session_state.start_date, st.session_state.end_date, required_columns, title)
        
        # Special case for China Loan Prime Rate
        elif st.session_state.country == "China" and sg == "Loan Prime Rate":
            st.markdown("##### **China Loan Prime Rate**")
            df_china_loan = viz.load_data("data/combined_data/china_loan_prime_rate_combined.csv")
            df_china_loan_filtered = viz.filter_data_by_frequency(df_china_loan, st.session_state.start_date, st.session_state.end_date, "monthly")
            required_columns_china_loan = ["CHLRLPR1_Last Price", "CHLRLPR5_Last Price"]
            viz.plot_multiple_lines(df_china_loan_filtered, st.session_state.start_date, st.session_state.end_date, required_columns_china_loan, "China Loan Prime Rate", is_filtered=True)

            if df_china_loan_filtered is not None and not df_china_loan_filtered.empty:
                summary_china_loan = openai_util.summarize_basic_trends(df_china_loan_filtered, st.session_state.start_date, st.session_state.end_date, "China Loan Prime Rate")
                summary_for_prompt.append(summary_china_loan)
                with st.expander("📑 Key Trend Insights"):
                    st.markdown(summary_china_loan)
        
        # Multiple lines without MA
        elif sg in viz.multiple_lines_mapping:
            title = viz.multiple_lines_mapping[sg]["title"]
            st.markdown(f"##### **{title}**")
            df_temp = viz.load_data(viz.multiple_lines_mapping[sg]["file_path"])
            required_columns = viz.multiple_lines_mapping[sg]["required_columns"]
            df_temp_filtered = viz.filter_dataframe(df_temp, st.session_state.start_date, st.session_state.end_date, required_columns)
            viz.plot_multiple_lines(df_temp_filtered, st.session_state.start_date, st.session_state.end_date, required_columns, title, is_filtered=True)

            if df_temp_filtered is not None and not df_temp_filtered.empty:
                summary_temp = openai_util.summarize_basic_trends(df_temp_filtered, st.session_state.start_date, st.session_state.end_date, title)
                summary_for_prompt.append(summary_temp)
                with st.expander("📑 Key Trend Insights"):
                    st.markdown(summary_temp)

        # Multiple lines with MA
        elif sg in viz.multiple_lines_mapping_with_ma:
            title = viz.multiple_lines_mapping_with_ma[sg]["title"]
            st.markdown(f"##### **{title}**")
            df_temp = viz.load_data(viz.multiple_lines_mapping_with_ma[sg]["file_path"])
            df_temp.columns = [col.replace("on Close", "").strip() for col in df_temp.columns]
            ma_columns = viz.find_moving_average_columns(df_temp)
            required_columns = ["Close"] + list(ma_columns.values())
            df_temp_filtered = viz.filter_dataframe(df_temp, st.session_state.start_date, st.session_state.end_date, required_columns)
            viz.plot_multiple_lines(df_temp_filtered, st.session_state.start_date, st.session_state.end_date, required_columns, title, is_filtered=True)

            if df_temp_filtered is not None and not df_temp_filtered.empty:
                summary_temp = openai_util.summarize_basic_trends(df_temp_filtered, st.session_state.start_date, st.session_state.end_date, title)
                summary_for_prompt.append(summary_temp)
                with st.expander("📑 Key Trend Insights"):
                    st.markdown(summary_temp)

        # Others
        elif sg in viz.others_mapping:
            title = viz.others_mapping[sg]["title"]
            file_path = viz.others_mapping[sg][st.session_state.country]["file_path"]
            col_name = viz.others_mapping[sg][st.session_state.country]["col"]
            frequency = viz.others_mapping[sg][st.session_state.country]["frequency"]
            st.markdown(f"##### **{st.session_state.country} {title}**")
            df_temp = viz.load_data(file_path)
            df_temp_filtered = viz.filter_data_by_frequency(df_temp, st.session_state.start_date, st.session_state.end_date, frequency)
            viz.plot_or_show_table(df_temp_filtered, col_name, st.session_state.start_date, st.session_state.end_date, frequency, is_filtered=True)

            if df_temp_filtered is not None and not df_temp_filtered.empty:
                summary_temp = openai_util.summarize_basic_trends(df_temp_filtered, st.session_state.start_date, st.session_state.end_date, title)
                summary_for_prompt.append(summary_temp)
                with st.expander("📑 Key Trend Insights"):
                    st.markdown(summary_temp)

        else:
            st.warning(f"⚠️ {sg} is not available for {st.session_state.country}.")

    # Generate the AI Summary button only if additional insights exist
    if len(summary_for_prompt) > 1:
        if st.button("💡 AI Summary (Multi-Factor Analysis)", key="ai_summary_multi"):
            with st.status("🔄 Generating AI insights for Multi-Factor Analysis...", expanded=False):
                prompt = openai_util.generate_multi_data_prompt(
                    st.session_state.country,
                    st.session_state.start_date.strftime('%d/%m/%Y'),
                    st.session_state.end_date.strftime('%d/%m/%Y'),
                    summary_for_prompt
                )
                st.session_state.ai_summary_multi_response = openai_util.get_openai_response(prompt)

    # Display AI response if available
    if st.session_state.ai_summary_multi_response:
        with st.expander("📊 AI Analysis (Multi-Factor Impact)"):
            st.markdown(st.session_state.ai_summary_multi_response)

