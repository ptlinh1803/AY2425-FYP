import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import ast
import plotly.graph_objects as go

pred_window_mapping = {
    "5 past days → Predict next 1 day": 5,
    "30 past days → Predict next 5 days": 30,
    "60 past days → Predict next 7 days": 60,
    "90 past days → Predict next 30 days": 90
}

available_quarters = pd.read_csv("data/synthetic_data/available_quarters.csv")

long_sequences = pd.read_csv("data/synthetic_data/summary_long_sequences.csv")

# 1. Process uploaded input-----------------------------------------------------
@st.cache_data
def preprocess_upload_input(original_df, selected_maturities, column_mapping, has_date, date_order, pred_window):
    if not selected_maturities:
        st.warning("Please select at least 1 maturity to predict")
        return None
    
    if not column_mapping or any(v is None for v in column_mapping.values()):
        st.warning("All selected maturities must have a corresponding column mapping.")
        return None

    df = original_df.copy()
    
    # Keep only the mapped columns
    columns_to_keep = list(column_mapping.values())
    if has_date:
        columns_to_keep.insert(0, "Date")
    df = df[columns_to_keep]

    # Rename columns
    df = df.rename(columns={v: k for k, v in column_mapping.items()})  # Swap keys & values

    # Handle "Date" column and sort df
    if has_date:
        if "Date" not in original_df.columns:
            st.error("Error: `had_date=True`, but no 'Date' column found in the file!")
            return None
        
        # Convert Date column to datetime (if not already)
        df["Date"] = pd.to_datetime(original_df["Date"], errors="coerce")
        
        # Drop any rows where Date could not be parsed
        df = df.dropna(subset=["Date"])

        # Sort in ascending order (oldest → latest)
        df = df.sort_values(by="Date")
    else:
        # Handle date ordering manually if no Date column exists
        if date_order == "Descending (latest first)":
            df = df.iloc[::-1]  # Reverse order (to oldest → latest)

    # keep only the latest "input_days" row
    input_days = pred_window_mapping[pred_window]
    if len(df) >= input_days:
        df = df.tail(input_days).reset_index(drop=True)  # Keep only the last "input_days" rows
    else:
        st.warning(f"Only {len(df)} rows available, which is less than the required {input_days}. Please prepare enough data for your selected lookback window.")
        return None

    return df

# 2. Process synthetic data-----------------------------------------------------
# 2.1. Get available years for each country + maturity
# used in main Prediction page
@st.cache_data
def get_available_year(country, maturity_yield):
    """
    e.g. get_available_year("China", "3M Yield")
    output: [2011, 2012, 2013, 2014, 2015, 2016]
    """
    global available_quarters
    target_maturity = f"{country} {maturity_yield}"
    row = available_quarters[available_quarters['Maturity'] == target_maturity]
    
    if row.empty:
        st.warning(f"Not enough data for the {target_maturity}")
        # this should never be the case
        return []
    
    quarters = row.iloc[0]['Quarter_Year']
    # Handle stringified list case
    if isinstance(quarters, str):
        try:
            quarters = ast.literal_eval(quarters)
        except Exception:
            st.warning(f"Invalid format in Quarter_Year for {target_maturity}")
            return []
        
    years = sorted(set(int(q[:4]) for q in quarters))  # extract year from each "YYYYQx"
    return years

# 2.2. Get available quarters for the chosen year
# used in main prediction page
@st.cache_data
def get_available_quarter_for_year(country, maturity_yield, year):
    """
    e.g. get_available_quarter_for_year("China", "3M Yield", 2016)
    output: ['Q1', 'Q2']
    """
    global available_quarters
    years = get_available_year(country, maturity_yield)
    target_maturity = f"{country} {maturity_yield}"
    
    if year not in years:
        st.warning(f"Not enough available data for {target_maturity} in this year")
        return []

    row = available_quarters[available_quarters['Maturity'] == target_maturity]
    
    if row.empty:
        st.warning(f"Not enough available data for {target_maturity} in this year")
        return []

    quarters = row.iloc[0]['Quarter_Year']
    # Handle stringified list case
    if isinstance(quarters, str):
        try:
            quarters = ast.literal_eval(quarters)
        except Exception:
            st.warning(f"Invalid format in Quarter_Year for {target_maturity}")
            return []
        
    available_quarters_list = [q[-2:] for q in quarters if int(q[:4]) == year]
    return sorted(available_quarters_list)


# 2.3. Get min and max yield for the chosen priod to mimic
# used in 2.7. rescale_and_add_noise()
@st.cache_data
def get_min_max_yield(country, maturity_yield, year, quarter):
    """
    only call this when year and quarter are valid
    e.g. get_min_max_yield("Australia", "3M Yield", 2021, "Q2")
    output: (-0.2247, 0.0053)
    """
    target_maturity = f"{country} {maturity_yield}"
    target_quarter = f"{year}Q{quarter[-1]}"  # ensure format like "2020Q1"
    
    # Filter the matching row
    match = long_sequences[
        (long_sequences['Maturity'] == target_maturity) &
        (long_sequences['Quarter_Year'] == target_quarter)
    ]
    
    if match.empty:
        st.warning(f"Not enough available data for {target_maturity} in {target_quarter}")
        return None
    
    min_yield = match.iloc[0]['Min_Yield']
    max_yield = match.iloc[0]['Max_Yield']
    return (float(min_yield), float(max_yield))


# 2.4. Construct scenario context
# used in 2.5 generate_raw_synthetic_data()
@st.cache_data
def construct_scenario_context(country, maturities, quarter_year_mapping):
    """
    country: select from sidebar
    maturities: select from sidebar
    quarter_year_mapping: dictionary of maturity - quarter_year based on what user selected
    """
    symbols = [f"{country}_{maturity}" for maturity in maturities]
    maturities_list = [f"{country} {maturity}" for maturity in maturities]
    quarter_year_list = [quarter_year_mapping[maturity] for maturity in maturities]

    scenario_context = pd.DataFrame(data={
    'Symbol': symbols,
    'Maturity': maturities_list,
    'Quarter_Year': quarter_year_list
    })

    return scenario_context

# 2.5. Generate synthetic data (raw, unscaled, long format)
# 1st step of 2.8
@st.cache_data
def generate_raw_synthetic_data(_synthesizer, country, maturities, quarter_year_mapping, pred_window):
    sequence_length = pred_window_mapping[pred_window]

    scenario_context = construct_scenario_context(country, maturities, quarter_year_mapping)
    fake_data = _synthesizer.sample_sequential_columns(
        context_columns=scenario_context,
        sequence_length=sequence_length
    )

    return fake_data


# 2.6. Reshape raw data the synthesizer produces
# 2nd step of 2.8
@st.cache_data
def reshape_fake_data_to_wide(fake_data):
    """
    input of this function is the raw data produced by the synthesizer
    """
    # Extract just the yield type (remove country)
    fake_data = fake_data.copy()
    fake_data['Yield_Type'] = fake_data['Maturity'].apply(lambda x: ' '.join(x.split()[1:]))

    # Assign time index (0 to length-1) within each sequence
    fake_data['Step'] = fake_data.groupby('Yield_Type').cumcount()

    # Pivot to wide format
    wide_df = fake_data.pivot(index='Step', columns='Yield_Type', values='Yield').reset_index(drop=True)

    # Remove column index name
    wide_df.columns.name = None

    # Reorder columns to preferred order if all exist
    preferred_order = ["3M Yield", "2Y Yield", "5Y Yield", "10Y Yield", "30Y Yield"]
    existing_order = [col for col in preferred_order if col in wide_df.columns]
    remaining_cols = [col for col in wide_df.columns if col not in existing_order]
    wide_df = wide_df[existing_order + remaining_cols]

    return wide_df

# 2.7. Rescale and add noise
# 3rd step of 2.8
@st.cache_data
def rescale_add_noise(df_wide, country, quarter_year_mapping, volatility=0.0):
    """
    df_wide: reshaped synthetic data to wide format
    country: user selection
    quarter_year_mapping: dictionary of maturity - quarter_year based on what user selected
    volatility: float, user selection
    """
    df_scaled = df_wide.copy()
    
    for col in df_scaled.columns:
        # Get min and max yield from real data
        quarter_year = quarter_year_mapping[col]
        year = int(quarter_year[:4])
        quarter = quarter_year[4:]
        minmax = get_min_max_yield(country, col, year, quarter)
        if minmax is None:
            continue  # Skip if not available
        min_yield, max_yield = minmax

        # Use MinMaxScaler to inverse transform from [0,1] back to original range
        scaler = MinMaxScaler(feature_range=(min_yield, max_yield))
        df_scaled[[col]] = scaler.fit_transform(df_scaled[[col]])

        # Add Gaussian noise if requested
        if volatility > 0:
            noise = np.random.normal(loc=0, scale=volatility, size=len(df_scaled))
            df_scaled[col] += noise

    return df_scaled

# 2.8. Master function to generate synthetic data, reshape, and rescale
def generate_synthetic_data(synthesizer, country, selected_maturities, pred_window, quarter_year_mapping, volatility):
    """
    synthesizer: load from data/synthetic_data/yield_synthesizer_newest.pkl
    country: st.session_state.country_pred
    selected_maturities: st.session_state.selected_maturities
    pred_window=st.session_state.pred_window
    quarter_year_mapping: default first option
    volatility: default = 0.0
    """
    try:
        if not selected_maturities:
            st.warning("Please select at least 1 maturity to predict")
            return None
        # 1. Generate raw synthetic data
        fake_data = generate_raw_synthetic_data(synthesizer, country, selected_maturities, quarter_year_mapping, pred_window)

        # 2. Reshape raw data from long to wide format
        wide_df = reshape_fake_data_to_wide(fake_data)

        # 3. Rescale and add noise
        final_df = rescale_add_noise(wide_df, country, quarter_year_mapping, volatility)

        # return
        return final_df
    except Exception as e:
        st.error(f"Error generating synthetic data: {e}")
        return None

# 3. Show metadata of input-----------------------------------------------------
def show_input_metadata(input_metadata):
    # Format for display
    display_meta = {
        "Country": input_metadata.get("country", "N/A"),
        "Maturities": ", ".join(input_metadata.get("maturities", [])) or "N/A",
        "Lookback Window": input_metadata.get("lookback_window", "N/A"),
        "Input Mode": input_metadata.get("input_mode", "N/A")
    }

    if "noise_level" in input_metadata:
        display_meta["Additional Noise"] = f"{input_metadata['noise_level'] / 0.01:.0f} bps"
    
    st.markdown("**Metadata of the latest processed input:**")
    st.table(pd.DataFrame(display_meta.items(), columns=["Parameter", "Value"]))

    if "quarter_year_mapping" in input_metadata:
        st.markdown("**Reference Time Periods for Each Maturity:**")
        st.table(pd.DataFrame(input_metadata["quarter_year_mapping"].items(), columns=["Maturity", "Reference Period"]))


# 4. Prediction-----------------------------------------------------
# 4.1. Load model and scalers for a single maturity
# used in 4.2
def load_model_and_scalers(country, maturity, pred_window):
    """
    for a single maturity of a country
    e.g. load_model_and_scalers("Japan", "5Y Yield", "5 past days → Predict next 1 day")
    feature_scaler is not actually in use cuz the only feature is the historical yield
    """
    # import here to reduce loading time at the start of the page
    import tensorflow as tf 
    import joblib

    pred_window_to_folder_name = {
        "5 past days → Predict next 1 day": "5in-1out",
        "30 past days → Predict next 5 days": "30in-5out",
        "60 past days → Predict next 7 days": "60in-7out",
        "90 past days → Predict next 30 days": "90in-30out"
    }
    path = f"models/{country}/{maturity}"
    subfolder = pred_window_to_folder_name[pred_window]

    model_filepath = f"{path}/{subfolder}/lstm.keras"
    scaler_filepath = f"{path}/{subfolder}/scalers.pkl"

    # Load the trained model
    model = tf.keras.models.load_model(model_filepath)
    print(f"Model loaded from: {model_filepath}")

    # Load the scalers
    feature_scaler, target_scaler = joblib.load(scaler_filepath)
    print(f"Scalers loaded from: {scaler_filepath}")

    return model, feature_scaler, target_scaler

# 4.2. Get prediction for 1 maturity
# used in 4.3
def get_prediction_single_maturity(input_df, country, maturity, pred_window):
    df = input_df.copy()
    model, _, target_scaler = load_model_and_scalers(country, maturity, pred_window)

    if maturity not in df.columns:
        raise ValueError(f"Maturity '{maturity}' not found in input data.")


    data = df[maturity]
    data_df = data.to_frame(name="Close")

    # get input X
    X = data_df.values

    # Scale X using target_scaler
    X_scaled = target_scaler.transform(pd.DataFrame(X, columns=data_df.columns))

    # Reshape X to match LSTM input shape (samples, time steps, features)
    X_scaled = np.reshape(X_scaled, (1, X_scaled.shape[0], 1))  # (1 sample, input_days time steps, 1 feature)

    # Predict using the loaded model
    y_pred_scaled = model.predict(X_scaled)

    # Inverse transform predictions back to original scale and reshape to (output_days,1)
    y_pred_reshaped = target_scaler.inverse_transform(y_pred_scaled).reshape(-1, 1)

    # Create df_single of the prediction
    df_single = pd.DataFrame(
        y_pred_reshaped,
        columns=[f"Predicted {maturity}"]
    )

    return df_single

# 4.3. Get prediction all at once
def get_all_predictions(input_df, country, selected_maturities, pred_window):
    """
    input_df: st.session_state.input_df
    country: st.session_state.country_pred
    selected_maturities: st.session_state.selected_maturities
    pred_window: st.session_state.pred_window
    """
    final_df = pd.DataFrame()

    if not selected_maturities:
        raise ValueError("No maturities selected for prediction.")
    
    try:
        for maturity in selected_maturities:
            df_temp = get_prediction_single_maturity(input_df, country, maturity, pred_window)

            # Combine columns horizontally
            if final_df.empty:
                final_df = df_temp
            else:
                final_df = pd.concat([final_df, df_temp], axis=1)

        return final_df
    except Exception as e:
        st.error(f"Error predicting: {e}")
        return None

# 4.4. Convert output_df to csv for download 
@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")

# 4.5. Plot outputs
def visualize_prediction_output(output_df):
    """
    Visualize prediction results from output_df.
    Each maturity is plotted in a separate Plotly chart.
    """
    if output_df is None or output_df.empty:
        st.info("No prediction data available.")
        return

    # Handle the special case: only one row of prediction
    if len(output_df) == 1:
        st.warning("Only one predicted value. Plotting skipped.")
        for col in output_df.columns:
            st.markdown(f"**{col}**: {output_df[col].iloc[0]:.4f}")
        return

    st.markdown("### 📊 Forecast Charts (per maturity)")
    for col in output_df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(output_df))),
            y=output_df[col],
            mode='lines+markers',
            name=col,
            line=dict(width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title=col,
            xaxis_title="Prediction Step",
            yaxis_title="Yield",
            hovermode="x unified",
            margin=dict(l=30, r=30, t=40, b=30),
            height=350,
        )

        # Enable scroll-to-zoom, drag, zoom buttons, etc.
        fig.update_layout(
            dragmode='zoom',
            hoverdistance=100,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

# 4.6. Plot input along with output
def visualize_input_and_prediction(input_df, output_df):
    """
    For each maturity, show a Plotly chart combining historical input and predicted output.
    Assumes input_df uses raw maturity names (e.g., "3M Yield") and output_df uses "Predicted {maturity}".
    """
    if output_df is None or output_df.empty:
        st.info("No prediction data available.")
        return

    st.markdown("### 📊 Input + Prediction Charts")

    for col in output_df.columns:
        # Extract maturity name from prediction column
        if not col.startswith("Predicted "):
            continue  # skip unexpected columns

        maturity = col.replace("Predicted ", "")
        
        # Make sure corresponding input exists
        if maturity not in input_df.columns:
            st.warning(f"Input data for {maturity} not found.")
            continue

        # Prepare full sequence
        historical = input_df[maturity].dropna().values
        predicted = output_df[col].dropna().values
        full_sequence = list(historical) + list(predicted)

        # Generate x-axis
        historical_x = list(range(len(historical)))
        predicted_x = list(range(len(historical), len(historical) + len(predicted)))

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=historical_x,
            y=historical,
            mode='lines',
            name='Historical',
            line=dict(color='royalblue')
        ))
        fig.add_trace(go.Scatter(
            x=predicted_x,
            y=predicted,
            mode='lines',
            name='Predicted',
            line=dict(color='orange'),
            # marker=dict(size=6)
        ))

        fig.update_layout(
            title=maturity,
            xaxis_title="Time Step",
            yaxis_title="Yield",
            hovermode="x unified",
            margin=dict(l=30, r=30, t=40, b=30),
            height=350,
            legend=dict(orientation="h", y=-0.2)
        )

        st.plotly_chart(fig, use_container_width=True)