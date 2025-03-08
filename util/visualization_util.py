import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# Set min date for each country
min_date = {
    "Japan": datetime(2000, 1, 4),
    "China": datetime(2005, 6, 8),
    "Australia": datetime(2000, 1, 4),
}

# Yield column names
yield_columns = {
    "Japan": ["GJTB3MO_Close", "GJGB2_Close", "GJGB5_Close", "GJGB10_Close", "GJGB30_Close"],
    "China": ['GCNY3M_Close', 'GCNY2YR_Close', 'GCNY5YR_Close', 'GCNY10YR_Close', 'GCNY30YR_Close'],
    "Australia": ['GACGB3M_Close', 'GACGB2_Close', 'GACGB5_Close', 'GACGB10_Close', 'GACGB30_Close'],
}

# Load data
@st.cache_data
def load_data(country):
    file_path = f"data/combined_data/full_{country.lower()}_data.csv"
    
    try:
        # Read CSV normally, let pandas detect column names
        df = pd.read_csv(file_path)

        # Rename the first column as 'Date' (since it has no name)
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)

        # Convert Date column to datetime
        df["Date"] = pd.to_datetime(df["Date"])

        # Set Date as index
        df.set_index("Date", inplace=True)

        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    

# Function to plot the bond yield curve
def plot_yield_curve(df, selected_date, country):
    if country not in yield_columns:
        st.error("Yield columns for this country are not defined.")
        return

    # Filter data for the selected date
    df_filtered = df[df.index == pd.to_datetime(selected_date)]

    if df_filtered.empty:
        st.warning(f"No data available for {selected_date.strftime('%Y-%m-%d')}")
        return

    # Keep only the selected yield columns
    selected_columns = [col for col in yield_columns[country] if col in df_filtered.columns]
    df_filtered = df_filtered[selected_columns]
    st.dataframe(df_filtered)

    # Extract available maturities & yields
    maturities = []
    yields = []

    for col in selected_columns:
        if not pd.isna(df_filtered.iloc[0][col]):  # Check for non-null values
            maturities.append(col)  # Column name represents maturity
            yields.append(df_filtered.iloc[0][col])  # Yield value

    if not maturities:
        st.warning(f"No yield data available for {selected_date.strftime('%Y-%m-%d')}")
        return

    # Create DataFrame for plotting
    plot_df = pd.DataFrame({"Maturity": maturities, "Yield (%)": yields})

    # Plot using Plotly
    fig = px.line(plot_df, x="Maturity", y="Yield (%)", markers=True,
                  title=f"Government Bond Yield Curve for {country} on {selected_date.strftime('%Y-%m-%d')}",
                  labels={"Maturity": "Bond Maturity", "Yield (%)": "Yield (%)"})

    fig.update_traces(marker_size=8, hoverinfo="x+y", mode="lines+markers")

    st.plotly_chart(fig)
