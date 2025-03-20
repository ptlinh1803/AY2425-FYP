import streamlit as st

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Prediction",
    page_icon="📈",
)

st.title("Prediction")

# Side bar -------------------------------------
# Initialize session state variables
if "country_pred" not in st.session_state:
    st.session_state.country_pred = "Japan"
if "pred_window" not in st.session_state:
    st.session_state.pred_window = "60 past days → Predict next 7 days"
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "Upload your data"

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

