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

# Map ticket to maturity
def get_maturity_name(col_name):
    mappings = {
        "3M": "3M",
        "2": "2Y",
        "5": "5Y",
        "10": "10Y",
        "30": "30Y"
    }
    
    for key, value in mappings.items():
        if key in col_name:
            return value
    return col_name  # Return original if no match

# Load data
@st.cache_data
def load_data(file_path):
    try:
        # Determine file type
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            st.error("Unsupported file format. Please use CSV or Excel.")
            return None

        # Convert Date column to datetime
        df["Date"] = pd.to_datetime(df["Date"])

        # Set Date as index
        df.set_index("Date", inplace=True)

        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    

# Plot the bond yield curve for a selected day
def plot_yield_curve(df, selected_date, country):
    if country not in yield_columns:
        st.error("Yield columns for this country are not defined.")
        return

    # Filter data for the selected date
    df_filtered = df[df.index == pd.to_datetime(selected_date)]

    if df_filtered.empty:
        st.warning(f"No data available for {selected_date.strftime('%d-%m-%Y')}")
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
            maturities.append(get_maturity_name(col))  # Column name represents maturity
            yields.append(df_filtered.iloc[0][col])  # Yield value

    if not maturities:
        st.warning(f"No yield data available for {selected_date.strftime('%d-%m-%Y')}")
        return

    # Create DataFrame for plotting
    plot_df = pd.DataFrame({"Maturity": maturities, "Yield (%)": yields})

    # Plot using Plotly
    fig = px.line(plot_df, x="Maturity", y="Yield (%)", markers=True,
                  title=f"{country} Government Bond Yield Curve on {selected_date.strftime('%d-%m-%Y')}",
                  labels={"Maturity": "Bond Maturity", "Yield (%)": "Yield (%)"})

    fig.update_traces(marker_size=8, hoverinfo="x+y", mode="lines+markers")

    st.plotly_chart(fig)


# Plot the bond yield curve heatmap for a selected period
def plot_yield_curve_heatmap(df, country, start_date, end_date):
    # Ensure the selected country exists in the yield columns dictionary
    if country not in yield_columns:
        st.error("Invalid country selection.")
        return

    # Filter data based on selected date range
    df_filtered = df.loc[start_date:end_date, yield_columns[country]]
    df_filtered = df_filtered.rename(columns=lambda col: get_maturity_name(col))

    # Convert dataframe from wide to long format for heatmap
    df_long = df_filtered.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield")

    # Define the desired maturity order (from bottom to top)
    maturity_order = ["30Y", "10Y", "5Y", "2Y", "3M"]

    # Convert "Maturity" column to categorical with the custom order
    df_long["Maturity"] = pd.Categorical(df_long["Maturity"], categories=maturity_order, ordered=True)


    # Create heatmap using Plotly
    fig = px.imshow(df_long.pivot(index="Maturity", columns="Date", values="Yield"),
                    aspect="auto",
                    color_continuous_scale="Blues",  # Darker blue = Higher yield
                    labels={"color": "Yield (%)"},
                    title=f"{country} Government Bond Yield Curve (Heatmap) from {start_date} to {end_date}")

    # Show the heatmap
    st.plotly_chart(fig)
