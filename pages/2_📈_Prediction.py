import streamlit as st
import pandas as pd
import util.visualization_util as viz
import util.prediction_util as pred

# VISUALIZATION PAGE
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

# Predict button - THIS SHOULD BE ENABLED IF SOME CONDITIONS ARE SATISFIED
if st.sidebar.button("Predict", type="primary"):
    st.sidebar.success("Start predicting...")

# Main page -------------------------------------
st.title(st.session_state.country_pred)
st.header("Prepare Input")

# 1. UPLOAD DATA
if st.session_state.input_mode == "Upload your data":
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
            if st.button("Preprocess Data"):
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
    st.success("Generate synthetic data here")

    # 1. Choose year and quarter to generate synthetic data from
    # 1.1. if Japan: choose the same year and quarter for all
    #...

    # 1.2. if China/Australia: choose year and quarter for each maturity
    # explain why in a st.info
    #...

    # 2. Choose volatility (add noise)
    #...

    # 3. Process generated synthetic data (reformat to the standard form)
    #...

    # 4. save the generated data in st.session_state.input_df and save metadata
    #...



# Display the input DataFrame
st.header("Visualize the Processed Input")
if st.session_state.input_df is not None:

    if st.session_state.input_metadata is not None:
        # Format for display
        display_meta = {
            "Country": st.session_state.input_metadata.get("country", "N/A"),
            "Maturities": ", ".join(st.session_state.input_metadata.get("maturities", [])) or "N/A",
            "Lookback Window": st.session_state.input_metadata.get("lookback_window", "N/A"),
            "Input Mode": st.session_state.input_metadata.get("input_mode", "N/A")
        }
        st.markdown("**Metadata of current processed input:**")
        st.table(pd.DataFrame(display_meta.items(), columns=["Parameter", "Value"]))

    st.info("Process a new file or generate new synthetic data to overwrite.")
    # st.warning("Change this later: display the processed data + graph")
    # if synthetic data, don't display "Date", or remove "Date" column completely
    st.dataframe(st.session_state.input_df)

    # draw plot
    required_columns = [col for col in st.session_state.input_df if col != "Date"]
    viz.plot_multiple_lines(st.session_state.input_df, 
                            None, 
                            None, 
                            required_columns, 
                            "Visualization of the Processed Input", 
                            is_filtered=True)
else:
    st.warning("No input data available yet. Please upload a file or generate synthetic data.")