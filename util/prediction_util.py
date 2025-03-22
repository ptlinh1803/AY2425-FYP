import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from sdv.sequential import PARSynthesizer
import numpy as np

pred_window_mapping = {
    "5 past days → Predict next 1 day": 5,
    "30 past days → Predict next 5 days": 30,
    "60 past days → Predict next 7 days": 60,
    "90 past days → Predict next 30 days": 90
}

available_quarters = pd.read_csv("synthetic_data/available_quarters.csv")

long_sequences = pd.read_csv("synthetic_data/summary_long_sequences.csv")

synthesizer = PARSynthesizer.load('synthetic_data/yield_synthesizer_newest.pkl')

# 1. Process uploaded input
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

# 2. Process synthetic data
# 2.1. Get available years for each country + maturity
@st.cache_data
def get_available_year(country, maturity_yield):
    """
    e.g. get_available_year("China", "3M Yield")
    output: [2011, 2012, 2013, 2014, 2015, 2016]
    """
    target_maturity = f"{country} {maturity_yield}"
    row = available_quarters[available_quarters['Maturity'] == target_maturity]
    
    if row.empty:
        st.warning(f"Not enough data for the {target_maturity}")
        # this should never be the case
        return []
    
    quarters = row.iloc[0]['Quarter_Year']
    years = sorted(set(int(q[:4]) for q in quarters))  # extract year from each "YYYYQx"
    return years

# 2.2. Get available quarters for the chosen year
@st.cache_data
def get_available_quarter_for_year(country, maturity_yield, year):
    """
    e.g. get_available_quarter_for_year("China", "3M Yield", 2016)
    output: ['Q1', 'Q2']
    """
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
    available_quarters = [q[-2:] for q in quarters if int(q[:4]) == year]
    return sorted(available_quarters)

# 2.3. Get min and max yield for the chosen priod to mimic
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
@st.cache_data
def generate_raw_synthetic_data(country, maturities, quarter_year_mapping, pred_window):
    sequence_length = pred_window_mapping[pred_window]

    scenario_context = construct_scenario_context(country, maturities, quarter_year_mapping)
    fake_data = synthesizer.sample_sequential_columns(
        context_columns=scenario_context,
        sequence_length=sequence_length
    )

    return fake_data


# 2.6. Reshape raw data the synthesizer produces
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

    return wide_df

# 2.7. Rescale and add noise
@st.cache_data
def rescale_and_add_noise(df_wide, country, quarter_year_mapping, volatility=0.0):
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


