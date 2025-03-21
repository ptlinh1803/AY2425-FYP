import streamlit as st
import pandas as pd

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

# Callback function to update session state
def update_country_pred():
    st.session_state.country_pred = st.session_state["country_pred_picker"]
def update_pred_window():
    st.session_state.pred_window = st.session_state["pred_window_picker"]
def update_input_mode():
    st.session_state.input_mode = st.session_state["input_mode_picker"]

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

# Select input mode
st.sidebar.radio(
    "Choose input method", 
    ["Upload your data", "Generate synthetic data"],
    index=["Upload your data", "Generate synthetic data"].index(st.session_state.input_mode),
    key="input_mode_picker",
    on_change=update_input_mode
)

# Predict button
if st.sidebar.button("Predict", type="primary"):
    st.sidebar.success("Start predicting...")

# Main page -------------------------------------
st.title(st.session_state.country_pred)
st.header("Prepare Input")

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
            
            # Store DataFrame in session state
            if df is not None:
                st.session_state.input_df = df 
        except Exception as e:
            st.error(f"Error reading file: {e}")

else:
    st.info("Generate synthetic data here")
    # save the generated data in st.session_state.input_df

# Display the stored DataFrame
st.subheader("Display your input")
if st.session_state.input_df is not None:
    st.write("Upload a new file or generate new synthetic data to overwrite.")
    # if synthetic data, don't display "Date", or remove "Date" column completely
    st.dataframe(st.session_state.input_df.tail())
else:
    st.info("No input data available yet. Please upload a file or generate synthetic data.")