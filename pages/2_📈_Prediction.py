import streamlit as st
import pandas as pd
import util.visualization_util as viz
import util.prediction_util as pred
import util.openai_util as openai_util

# PREDICTION PAGE
st.set_page_config(
    page_title="Prediction",
    page_icon="📈",
)

# Side bar -------------------------------------
# Initialize session state variables
if "country_pred" not in st.session_state:
    st.session_state.country_pred = "Japan"
if "pred_window" not in st.session_state:
    st.session_state.pred_window = "60 past days → Predict next 7 days"
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "Upload your data"
if "input_df" not in st.session_state:
    st.session_state.input_df = None
if "selected_maturities" not in st.session_state:
    st.session_state.selected_maturities = ["3M Yield", "2Y Yield", "5Y Yield", "10Y Yield", "30Y Yield"]
if "input_metadata" not in st.session_state:
    st.session_state.input_metadata = None
if "input_df" not in st.session_state:
    st.session_state.input_df = None
if "output_df" not in st.session_state:
    st.session_state.output_df = None

# Callback function to update session state
def update_country_pred():
    st.session_state.country_pred = st.session_state["country_pred_picker"]
def update_pred_window():
    st.session_state.pred_window = st.session_state["pred_window_picker"]
def update_input_mode():
    st.session_state.input_mode = st.session_state["input_mode_picker"]
def update_selected_maturities():
    st.session_state.selected_maturities = st.session_state["maturity_picker"]

# Select country
st.sidebar.selectbox(
    "Select country", 
    ["Japan", "China", "Australia"],
    index=["Japan", "China", "Australia"].index(st.session_state.country_pred),
    key="country_pred_picker",
    on_change=update_country_pred
)

# Select window size
windows = ["5 past days → Predict next 1 day",
           "30 past days → Predict next 5 days",
           "60 past days → Predict next 7 days",
           "90 past days → Predict next 30 days"
           ]
st.sidebar.selectbox(
    "Select a lookback window", 
    windows,
    index=windows.index(st.session_state.pred_window),
    key="pred_window_picker",
    on_change=update_pred_window
)

# Select maturities to predict
st.sidebar.multiselect(
    "Select maturities to predict:",
    options=["3M Yield", "2Y Yield", "5Y Yield", "10Y Yield", "30Y Yield"],
    default=st.session_state.selected_maturities,
    key="maturity_picker",
    on_change=update_selected_maturities
)

# Select input mode
st.sidebar.radio(
    "Choose input method", 
    ["Upload your data", "Generate synthetic data"],
    index=["Upload your data", "Generate synthetic data"].index(st.session_state.input_mode),
    key="input_mode_picker",
    on_change=update_input_mode
)

# Main page -------------------------------------
st.title(st.session_state.country_pred)
st.header("Prepare Input")

# 1. UPLOAD DATA
if st.session_state.input_mode == "Upload your data":
    st.caption("If your uploaded data has more rows than the selected lookback window, only the latest rows will be used for prediction.")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx"]
    )
    
    # If a file is uploaded, process it and store in session state
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file type.")
                df = None
        except Exception as e:
            st.error(f"Error reading file: {e}")

        # Preprocess raw input data
        if df is not None:
            # Preview the uploaded file
            st.markdown("#### Preview of Uploaded Data")
            st.dataframe(df.head())

            # Clarify some information about the uploaded file
            st.markdown("##### Please provide more information about your file")

            # --- Column Mapping for Selected Maturities ---
            st.markdown("Map Your Columns to Maturities")
            column_mapping = {}
            cols = st.columns(2)
            df_columns = [col for col in df.columns if col != "Date"]
            selected_columns = set()

            for i, mat in enumerate(st.session_state.selected_maturities):
                with cols[i % 2]:  # Distribute options across columns
                    available_options = [col for col in df_columns if col not in selected_columns]

                    column_mapping[mat] = st.selectbox(
                        f"**{mat}**:",
                        options=available_options,
                        index=None,
                        key=f"map_{mat}"
                    )

                    if column_mapping[mat] in selected_columns:
                        st.warning(f"Column **{column_mapping[mat]}** is already selected for another maturity! Please choose a different column.")
                    else:
                        if column_mapping[mat] is not None:
                            selected_columns.add(column_mapping[mat])
            # st.write(column_mapping)

            # --- Date Handling ---
            has_date = "Date" in df.columns
            if not has_date:
                st.write("No 'Date' column detected.")
                date_order = st.radio(
                    "Is your data ordered with most recent rows first or last?",
                    ["Ascending (oldest first)", "Descending (latest first)"],
                    key="date_order_radio"
                )
            else:
                date_order = "Ignore"

            # --- Preprocess Data ---
            if st.button("Preprocess Data", key="process_upload_input"):
                st.session_state.input_df = pred.preprocess_upload_input(
                    df,
                    selected_maturities=st.session_state.selected_maturities,
                    column_mapping=column_mapping,
                    has_date=has_date,
                    date_order=date_order,
                    pred_window=st.session_state.pred_window
                )

                if st.session_state.input_df is not None:
                    st.success("Data preprocessed successfully!")

                    st.session_state.input_metadata = {
                        "country": st.session_state.country_pred,
                        "maturities": st.session_state.selected_maturities,
                        "lookback_window": st.session_state.pred_window,
                        "input_mode": st.session_state.input_mode
                    }

# 2. GENERATE SYNTHETIC DATA
else:
    # 0. Load synthesizer
    @st.cache_resource
    def load_synthesizer():
        import torch
        from sdv.sequential import PARSynthesizer

        # work around to avoid streamlit's warning about torch
        try:
            if hasattr(torch, "classes") and hasattr(torch.classes, "__path__"):
                torch.classes.__path__ = []
        except Exception:
            pass
        return PARSynthesizer.load("data/synthetic_data/yield_synthesizer_newest.pkl")

    synthesizer = load_synthesizer()

    # 1. Choose year and quarter to generate synthetic data from
    st.markdown("##### Select a reference time period you want the synthetic data to resemble")
    st.caption("Synthetic data reflects the conditions of the selected period, but is not real data — so it can still be used for fresh predictions.")
    quarter_year_mapping = dict()
    # if Japan: choose the same year and quarter for all
    if st.session_state.country_pred == "Japan":
        st.write("Choose the same year and quarter for all maturities")

        col1, col2 = st.columns(2)

        with col1:
            year = st.selectbox("Year", list(range(2000, 2025)), key="japan_year", index=24)

        with col2:
            if year == 2024:
                quarter_options = ['Q1', 'Q2', 'Q3']
            else:
                quarter_options = ['Q1', 'Q2', 'Q3', 'Q4']
            quarter = st.selectbox("Quarter", quarter_options, key="japan_quarter")

        # Build the mapping
        for maturity in st.session_state.selected_maturities:
            quarter_year_mapping[maturity] = f"{year}{quarter}"

    # if China/Australia: choose year and quarter for each maturity
    else:
        st.info(
            f"Different maturities in {st.session_state.country_pred} may have different available time periods."
        )
        with st.expander("⚠️ Why does this matter?"):
            st.warning(
                "📌 We need to select reference time for each maturity individually because of differences in available data. "
                "If a selected time period didn't have enough training data for a maturity, the model may not generate realistic results.\n\n"
                "📊 In real financial markets, yields for all maturities in a country are observed at the same time. "
                "If you choose different years and quarters for each maturity, the resulting synthetic yield curve "
                "may not reflect a real-world yield curve structure.\n\n"
                "🧠 This flexibility is helpful for testing ideas or filling missing data, "
                "but for realistic simulations, it's better to use the same time period for all maturities."
            )

        # Option to apply the same period for all (selected by Default)
        use_same_reference = st.checkbox("Use the same year and quarter for all maturities (if available)")
        if use_same_reference:
            st.markdown("**Select a shared year and quarter for all maturities:**")

            col1, col2 = st.columns(2)

            with col1:
                common_year = st.selectbox("Year (shared)", list(range(2000, 2025)), key="shared_year", index=24)

            with col2:
                if common_year == 2024:
                    common_quarters = ['Q1', 'Q2', 'Q3']
                else:
                    common_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
                common_quarter = st.selectbox("Quarter (shared)", common_quarters, key="shared_quarter")

        for maturity in st.session_state.selected_maturities:
            st.markdown(f"**{maturity}**")

            available_years = pred.get_available_year(st.session_state.country_pred, maturity)
            if use_same_reference and common_year in available_years:
                available_quarters = pred.get_available_quarter_for_year(st.session_state.country_pred, maturity, common_year)
                if common_quarter in available_quarters:
                    # ✅ Apply shared selection
                    st.success(f"Using {common_year}{common_quarter} for {maturity}")
                    quarter_year_mapping[maturity] = f"{common_year}{common_quarter}"
                    continue  # Skip manual selection

            # Otherwise fallback to manual
            col1, col2 = st.columns(2)
            with col1:
                year = st.selectbox(f"Year ({maturity})", available_years, key=f"{maturity}_year")

            available_quarters = pred.get_available_quarter_for_year(st.session_state.country_pred, maturity, year)
            with col2:
                quarter = st.selectbox(f"Quarter ({maturity})", available_quarters, key=f"{maturity}_quarter")

            quarter_year_mapping[maturity] = f"{year}{quarter}"


    # 2. Choose volatility (add noise)
    st.markdown("##### Add more randomness to simulate market volatility")
    volatility = st.slider(
        "Noise standard deviation (higher = more random variation)",
        min_value=0.00,
        max_value=1.00, # max change = 1% = 100 bps (yield is alr shown in %)
        value=0.00,
        step=0.01, # each step = 1 bps = 0.01%
        format="%.2f",
        help="Standard deviation of Gaussian noise (in percent units) 0.01 = 1 bps"
    )
    st.caption(f"Current noise level: {volatility / 0.01:.0f} bps")


    # 3. Generate synthetic data
    if st.button("Generate Synthetic Data", key="process_synthetic_input"):
        st.session_state.input_df = pred.generate_synthetic_data(
            synthesizer=synthesizer,
            country=st.session_state.country_pred,
            selected_maturities=st.session_state.selected_maturities,
            pred_window=st.session_state.pred_window,
            quarter_year_mapping=quarter_year_mapping,
            volatility=volatility
        )

        if st.session_state.input_df is not None:
            st.success("Successfully generated synthetic data!")

            st.session_state.input_metadata = {
                "country": st.session_state.country_pred,
                "maturities": st.session_state.selected_maturities,
                "lookback_window": st.session_state.pred_window,
                "input_mode": st.session_state.input_mode,
                "quarter_year_mapping": quarter_year_mapping,
                "noise_level": volatility
            }



# Display the processed input DataFrame
if st.session_state.input_df is not None:
    # prepare to ask OpenAI API
    summary_for_prompt = []

    st.header("Input Overview")
    st.info("**Want to overwrite?** Process a new file or generate new synthetic data.")

    # Display metadata
    if st.session_state.input_metadata is not None:
        pred.show_input_metadata(st.session_state.input_metadata)

    # Display more details
    tab1, tab2, tab3 = st.tabs(["🔢 View Input as a Table", "📊 Visualize Input Data", "📑 Input Trend Summary"])
    # Show input table
    with tab1:
        st.dataframe(st.session_state.input_df)

    # Draw plot
    with tab2:
        required_columns = [col for col in st.session_state.input_df if col != "Date"]
        viz.plot_multiple_lines(st.session_state.input_df, 
                                None, 
                                None, 
                                required_columns, 
                                "Visualization of the Processed Input", 
                                is_filtered=True)
    
    # Summary trends
    with tab3:
        summary_input_trends = openai_util.summarize_basic_trends(st.session_state.input_df, None, None, "Input Yields", show_bps=True)
        summary_for_prompt.append(summary_input_trends)
        st.markdown(summary_input_trends)

    # Predict button - THIS SHOULD BE ENABLED ONLY IF INPUT IS READY
    if st.sidebar.button("Predict", type="primary"):
        with st.spinner("🔄 Generating predictions... Please wait.", show_time=True):
            # Get prediction
            st.session_state.output_df = pred.get_all_predictions(st.session_state.input_df, 
                                                                  st.session_state.country_pred, 
                                                                  st.session_state.selected_maturities, 
                                                                  st.session_state.pred_window)
        if st.session_state.output_df is not None and not st.session_state.output_df.empty:
            st.success("Prediction completed successfully!")

    # Show the latest predicted result
    if st.session_state.output_df is not None and not st.session_state.output_df.empty:
        st.header("Prediction Results")
        # Display more details
        tab1, tab2, tab3 = st.tabs(["🔢 View Output as a Table", "📊 Visualize Output Data", "📑 Input Output Summary"])
        # Show input table
        with tab1:
            st.dataframe(st.session_state.output_df)

        # Draw plot
        with tab2:
            pred.visualize_prediction_output(st.session_state.output_df)
            
        # Summary trends
        with tab3:
            summary_output_trends = openai_util.summarize_basic_trends(st.session_state.output_df, None, None, "Forecasted Yield Curve", show_bps=True)
            summary_for_prompt.append(summary_output_trends)
            st.markdown(summary_output_trends)

        # Download
        csv = pred.convert_for_download(st.session_state.output_df)
        st.download_button(
            label="Save Results as CSV",
            data=csv,
            file_name="prediction_result.csv",
            mime="text/csv",
            icon=":material/download:",
        )


