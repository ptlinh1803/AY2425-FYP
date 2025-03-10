import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# 1. GLOBAL VARIABLES-------------------------------------
# 1.1. Set min date for each country
min_date = {
    "Japan": datetime(2000, 1, 4),
    "China": datetime(2005, 6, 8),
    "Australia": datetime(2000, 1, 4),
}

# 1.2. Yield column names
yield_columns = {
    "Japan": ["GJTB3MO_Close", "GJGB2_Close", "GJGB5_Close", "GJGB10_Close", "GJGB30_Close"],
    "China": ['GCNY3M_Close', 'GCNY2YR_Close', 'GCNY5YR_Close', 'GCNY10YR_Close', 'GCNY30YR_Close'],
    "Australia": ['GACGB3M_Close', 'GACGB2_Close', 'GACGB5_Close', 'GACGB10_Close', 'GACGB30_Close'],
}

# 1.3. Additional graphs
additional_graphs = {
    "Japan": ['3M Gov Yield', '2Y Gov Yield', '5Y Gov Yield', '10Y Gov Yield', '30Y Gov Yield', 
              'JPY Swap Rates', 'TONAR Rate', 'TIBOR Fixing Rates', 'CPI YoY', 'GDP YoY', 
              'Gov Debt % GDP', 'USD/JPY Exchange Rate', 'Unemployment Rate', 'Nikkei 225 Index'],
    "China": ['3M Gov Yield', '2Y Gov Yield', '5Y Gov Yield', '10Y Gov Yield', '30Y Gov Yield',
              'CNY Swap Rates', 'Loan Prime Rate', 'SHIBOR Fixing Rate', 'CPI YoY', 'GDP YoY',
              'Gov Debt % GDP', 'USD/CNY Exchange Rate', 'Unemployment Rate', 'CSI 300 Index'],
    "Australia": ['3M Gov Yield', '2Y Gov Yield', '5Y Gov Yield', '10Y Gov Yield', '30Y Gov Yield',
                  'AUD Swap Rates', 'Cash Rate Target', 'CPI YoY', 'GDP YoY','Gov Debt % GDP', 
                  'USD/AUD Exchange Rate', 'Unemployment Rate', 'Wage Growth YoY', 'ASX 200 Index'],
}

# 2. MANIPULATE DATA-------------------------------------
# 2.1. Map ticket to maturity
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

# 2.2. Load data from file path
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

# 2.3. For some data, the columns are prefixed with the ticker symbol 
@st.cache_data
def filter_ticker_columns(df, ticker):
    """
    Extracts columns containing the given ticker and removes the ticker prefix from column names.
    """
    selected_columns = [col for col in df.columns if ticker in col]
    df_filtered = df[selected_columns].copy()
    df_filtered.columns = [col.replace(f"{ticker}_", "") for col in selected_columns]

    return df_filtered

# 2.4. Filter data based on selected date range and columns
@st.cache_data
def filter_dataframe(df, start_date, end_date, required_columns=None):
    """
    Filters data based on selected date range and keeps only the specified columns.

    Args:
        df (pd.DataFrame): The input dataframe.
        start_date (datetime): Start date for filtering.
        end_date (datetime): End date for filtering.
        required_columns (list, optional): List of required columns to keep. If None, keeps all columns.

    Returns:
        tuple: (filtered DataFrame, missing_columns list)
    """

    # If required_columns is None, keep all columns
    if required_columns is None:
        required_columns = df.columns.tolist()

    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return None

    # Filter data by date range and selected columns
    df_filtered = df.loc[start_date:end_date, required_columns].dropna(how="all")

    return df_filtered

# 2.5. Find moving average columns (column names are not consistent)
def find_moving_average_columns(df):
    ma_patterns = ["SMAVG (50)", "SMAVG (100)", "SMAVG (200)"]
    ma_columns = {}

    for ma in ma_patterns:
        matching_cols = [col for col in df.columns if ma in col]
        if matching_cols:
            ma_columns[ma] = matching_cols[0]  # Take the first match (assuming no duplicates)

    return ma_columns
    

# 3. VISUALIZATION-------------------------------------
# 3.1. Plot the bond yield curve for a selected day
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
    fig.update_layout(
        title_font=dict(size=18)
    )

    st.plotly_chart(fig)


# 3.2. Plot the bond yield curve heatmap for a selected period
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
    
    fig.update_layout(
        title_font=dict(size=18)
    )
    # Show the heatmap
    st.plotly_chart(fig)

# 3.3. Plot the animated bond yield curve for a selected period
def plot_animated_yield_curve(df, country, start_date, end_date, selected_date):
    if country not in yield_columns:
        st.error("Invalid country selection.")
        return

    # Filter data for animation range
    df_filtered = df.loc[start_date:end_date, yield_columns[country]]

    # Filter data for the static reference date
    df_static = df.loc[selected_date:selected_date, yield_columns[country]]

    # Rename columns to maturities
    maturity_labels = ["3M", "2Y", "5Y", "10Y", "30Y"]
    df_filtered = df_filtered.rename(columns=lambda col: get_maturity_name(col))

    # Convert to long format for Plotly
    df_long = df_filtered.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield")

    # Ensure maturities are in correct order
    df_long["Maturity"] = pd.Categorical(df_long["Maturity"], categories=maturity_labels, ordered=True)

    # Convert Date to string to ensure proper animation frame handling
    df_long["Date"] = df_long["Date"].dt.strftime('%d-%m-%Y')

    # Calculate dynamic Y-axis range with a small buffer
    y_min = df_long["Yield"].min()
    y_max = df_long["Yield"].max()

    if df_static is not None and not df_static.empty:
        df_static = df_static.rename(columns=lambda col: get_maturity_name(col))
        df_static_long = df_static.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield")
        df_static_long["Maturity"] = pd.Categorical(df_static_long["Maturity"], categories=maturity_labels, ordered=True)
        y_min = min(y_min, df_static_long["Yield"].min())
        y_max = max(y_max, df_static_long["Yield"].max())

    # Apply a buffer
    y_buffer = (y_max - y_min) * 0.3  
    y_max_adjusted = y_max + y_buffer 
    y_min_adjusted = y_min - y_buffer

    # Create the animated plot
    fig = px.line(
        df_long,
        x="Maturity",
        y="Yield",
        labels={"Maturity": "Maturity", "Yield": "Yield"},
        color="Date",
        color_discrete_sequence=["cornflowerblue"],  # Animation curve color
        animation_frame="Date",
        animation_group="Maturity",
        range_y=[y_min_adjusted, y_max_adjusted],
        markers="*",
        hover_data={"Maturity": True, "Yield": True, "Date": True},
    )

    if df_static is not None and not df_static.empty:
        # Add the static yield curve (selected date)
        static_curve = df_static.iloc[0, :]
        fig.add_trace(go.Scatter(
            x=static_curve.index,
            y=static_curve.values,
            mode="lines+markers",
            name=f"Static: {selected_date.strftime('%d-%m-%Y')}",
            line=dict(color="red", width=2),
            marker=dict(symbol="circle"),
        ))

    # Update layout for a better look
    fig.update_layout(
        title=f"{country} Yield Curve Animation from {start_date} to {end_date}",
        title_font=dict(size=18),
        autosize=True,
        height=600,
        margin=dict(t=70, b=90, l=20, r=20),
        legend_title="",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )

    # Check if the slider exists before modifying it
    if fig.layout.sliders:
        for step in fig.layout.sliders[0].steps:
            step["args"][1]["frame"]["redraw"] = True
    else:
        st.warning("Slider issue detected. Please check the Date format.")

    # Ensure the updatemenus exist before modifying them
    if fig.layout.updatemenus:
        for button in fig.layout.updatemenus[0].buttons:
            button["args"][1]["frame"]["redraw"] = True
            button["args"][1]["frame"]["duration"] = 200  # Adjust animation speed

    # Display in Streamlit
    st.plotly_chart(fig)

# 3.4. Plot the 3D yield curve surface
def plot_3d_yield_curve(df, country, start_date, end_date):
    if country not in yield_columns:
        st.error("Invalid country selection.")
        return

    # Filter data for the selected date range and maturities
    df_filtered = df.loc[start_date:end_date, yield_columns[country]]

    # Rename columns to maturities
    maturity_labels = ["3M", "2Y", "5Y", "10Y", "30Y"]
    df_filtered = df_filtered.rename(columns=lambda col: get_maturity_name(col))

    # Reverse maturities so 3M is displayed first
    df_filtered = df_filtered[maturity_labels[::-1]]

    # Convert index (Date) to string for plotting
    df_filtered.index = df_filtered.index.strftime('%Y-%m-%d')

    # Prepare x, y, z data for 3D surface
    x = df_filtered.columns  # Maturities
    y = df_filtered.index    # Dates
    z = df_filtered.values   # Yield values

    # Create 3D Surface plot
    fig = go.Figure()

    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        colorscale='ice',
        reversescale=True,
        showscale=False,
        hovertemplate='<br>Date: %{y}' +
                      '<br>Maturity: %{x}' +
                      '<br>Yield: %{z:.2f}%<extra></extra>'
    ))

    # Update layout for better readability
    fig.update_layout(
        title=f"{country} Yield Curve 3D Surface from {start_date} to {end_date}",
        title_font=dict(size=18),
        autosize=True,
        height=700,
        margin=dict(l=0, r=0, b=10, t=40),
        scene=dict(
            aspectratio={"x": 1, "y": 1.75, "z": 0.75},
            camera={"eye": {"x": 1.3, "y": 2.2, "z": 0.3}},  # Slightly tilted for better view
            xaxis_title="Maturity",
            yaxis_title="Date",
            zaxis_title="Yield (%)",
            xaxis=dict(showspikes=False, showline=True),
            yaxis=dict(showspikes=False, showline=True),
            zaxis=dict(showspikes=False, showline=True),
        )
    )

    # Display in Streamlit
    st.plotly_chart(fig)

# 3.5. The 1st type of additional graphs: daily "Close" with SMAVG 50/100/200
def plot_price_with_moving_averages(df, start_date, end_date, title):
    # Find actual moving average columns dynamically
    ma_columns = find_moving_average_columns(df)
    required_columns = ["Close"] + list(ma_columns.values())
    
    # Filter data based on the selected date range
    df_filtered = filter_dataframe(df, start_date, end_date, required_columns)
    if df_filtered is None:
        # Missing columns already handled in filter_dataframe()
        return
    
    if df_filtered.empty:
        st.warning(f"No valid data available between {start_date} and {end_date}.")
        return
    
    # Initialize session state for checkboxes
    for key in ["ma50", "ma100", "ma200"]:
        session_key = f"{key}_{start_date}_{end_date}_{title}"
        if session_key not in st.session_state:
            st.session_state[session_key] = (key == "ma50")  # Default: MA50 is checked
    
    # Create plot
    fig = go.Figure()

    # Always plot the 'Close' price
    fig.add_trace(go.Scatter(
        x=df_filtered.index, 
        y=df_filtered["Close"], 
        mode="lines", 
        name="Close Price",
        line=dict(color="black")
    ))

    # Checkboxes directly under the graph
    col1, col2, col3 = st.columns(3)
    with col1:
        show_ma50 = st.checkbox("50-day MA", key=f"ma50_{start_date}_{end_date}_{title}")
    with col2:
        show_ma100 = st.checkbox("100-day MA", key=f"ma100_{start_date}_{end_date}_{title}")
    with col3:
        show_ma200 = st.checkbox("200-day MA", key=f"ma200_{start_date}_{end_date}_{title}")

    # Add selected moving averages to the plot
    if show_ma50 and "SMAVG (50)" in ma_columns:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, 
            y=df_filtered[ma_columns["SMAVG (50)"]], 
            mode="lines", 
            name="50-day MA",
            line=dict(dash="dot", color="blue")
        ))

    if show_ma100 and "SMAVG (100)" in ma_columns:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, 
            y=df_filtered[ma_columns["SMAVG (100)"]], 
            mode="lines", 
            name="100-day MA",
            line=dict(dash="dot", color="green")
        ))

    if show_ma200 and "SMAVG (200)" in ma_columns:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, 
            y=df_filtered[ma_columns["SMAVG (200)"]], 
            mode="lines", 
            name="200-day MA",
            line=dict(dash="dot", color="red")
        ))

    # Update layout for better appearance
    fig.update_layout(
        xaxis_title="Date",
        height=500,
        margin=dict(t=40, b=40, l=30, r=30),
        legend_title="Legend",
    )

    # Redraw the plot only when checkboxes change (avoiding full rerun)
    st.plotly_chart(fig, use_container_width=True)

