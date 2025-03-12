import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# 1. GLOBAL VARIABLES-------------------------------------
# 1.1. Yield column names
yield_columns = {
    "Japan": ["GJTB3MO_Close", "GJGB2_Close", "GJGB5_Close", "GJGB10_Close", "GJGB30_Close"],
    "China": ['GCNY3M_Close', 'GCNY2YR_Close', 'GCNY5YR_Close', 'GCNY10YR_Close', 'GCNY30YR_Close'],
    "Australia": ['GACGB3M_Close', 'GACGB2_Close', 'GACGB5_Close', 'GACGB10_Close', 'GACGB30_Close'],
}

# 1.2. Additional graphs
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

# 1.3. Predefined Plotly color cycle
plotly_colors = [
    "blue", "green", "red", "purple", "orange", "brown", "pink", "gray", "cyan", "magenta"
]

# 1.4. Yield mapping
yield_mapping = {
    '3M Gov Yield': {
        'Japan': 'GJTB3MO',
        'China': 'GCNY3M',
        'Australia': 'GACGB3M',
        'title': '3-Month Government Bond Yield Over Time'
    },
    '2Y Gov Yield': {
        'Japan': 'GJGB2',
        'China': 'GCNY2YR',
        'Australia': 'GACGB2',
        'title': '2-Year Government Bond Yield Over Time'
    },
    '5Y Gov Yield': {
        'Japan': 'GJGB5',
        'China': 'GCNY5YR',
        'Australia': 'GACGB5',
        'title': '5-Year Government Bond Yield Over Time'
    },
    '10Y Gov Yield': {
        'Japan': 'GJGB10',
        'China': 'GCNY10YR',
        'Australia': 'GACGB10',
        'title': '10-Year Government Bond Yield Over Time'
    },
    '30Y Gov Yield': {
        'Japan': 'GJGB30',
        'China': 'GCNY30YR',
        'Australia': 'GACGB30',
        'title': '30-Year Government Bond Yield Over Time'
    },
}

# 1.5. multiple lines mapping
multiple_lines_mapping = {
    'JPY Swap Rates': {
        "title": "JPY Overnight Index Swap (OIS) Rates Across Maturities",
        "file_path": "data/combined_data/japan_swap_combined.csv",
        "required_columns": ["JYSOC_Close", "JYSO2_Close", "JYSO5_Close", "JYSO10_Close", "JYSO30_Close"]
    },
    'TIBOR Fixing Rates': {
        "title": "Japan TIBOR Fixing Rates Across Maturities",
        "file_path": "data/combined_data/japan_tibor_fixing_rate_df_combined.csv",
        "required_columns": ["TI0001M_Ask Price", "TI0003M_Ask Price", "TI0006M_Ask Price", "TI0012M_Ask Price"]
    },
    'CNY Swap Rates': {
        "title": "CNY Interest Rate Swaps (IRS) on 7-Day Repo",
        "file_path": "data/combined_data/china_swap_combined.csv",
        "required_columns": ["CCSWOC_Close", "CCSWO2_Close", "CCSWO5_Close", "CCSWO10_Close"]
    },
    'SHIBOR Fixing Rate': {
        "title": "Shanghai Interbank Offered Rate (SHIBOR) Trends Over Time",
        "file_path": "data/combined_data/china_shibor_fixing_rate_combined.csv",
        "required_columns": ["SHIF1Y_Close", "SHIF3M_Close"]
    },
    'AUD Swap Rates': {
        "title": "AUD Interest Rate Swaps (IRS) vs. 6M Benchmark",
        "file_path": "data/combined_data/australia_swap_combined.csv",
        "required_columns": ["ADSWAP2_Close", "ADSWAP5_Close", "ADSWAP10_Close", "ADSWAP30_Close"]
    }
}

# 1.6. multiple lines mapping with MA
multiple_lines_mapping_with_ma = {
    'TONAR Rate': {
        "title": "TONAR: Japan's Unsecured Overnight Call Rate Movements Over Time",
        "file_path": "data/others/MUTKCALM Bank of Japan Final Result - Unsecured Overnight Call Rate TONAR.xlsx",
    },
    'USD/JPY Exchange Rate': {
        "title": "USD/JPY Exchange Rate",
        "file_path": "data/others/USDJPY Exchange Rate USD-JPY.xlsx",
    },
    'Nikkei 225 Index': {
        "title": "Nikkei 225 Index",
        "file_path": "data/others/NKY Nikkei 225.xlsx",
    },
    'USD/CNY Exchange Rate': {
        "title": "USD/CNY Exchange Rate",
        "file_path": "data/others/USDCNY Exchange Rate USD-CNY.xlsx",
    },
    'CSI 300 Index': {
        "title": "CSI 300 Index",
        "file_path": "data/others/SHSZ300 CSI 300 Index.xlsx",
    },
    'USD/AUD Exchange Rate': {
        "title": "USD/AUD Exchange Rate",
        "file_path": "data/others/AUDUSD Exchange Rate USD-AUD.xlsx",
    },
    'ASX 200 Index': {
        "title": "ASX 200 Index",
        "file_path": "data/others/AS51 ASX 200 Index.xlsx",
    }
}

# 1.7. others mapping
others_mapping = {
    'CPI YoY': {
        "title": "Consumer Price Index (CPI) Year-on-Year Growth",
        "Japan": {
            "file_path": "data/others/EHPIJP Japan Consumer Price Index (YoY _).xlsx",
            "col": "Mid Price",
            "frequency": "quarterly"
        },
        "China": {
            "file_path": "data/others/CNCPIYOY Daily China CPI YoY.xlsx",
            "col": "Last Price",
            "frequency": "monthly"
        },
        "Australia": {
            "file_path": "data/others/AUCPIYOY Australia CPI All Items YoY (Quarterly).xlsx",
            "col": "Last Price",
            "frequency": "quarterly"
        },
    },
    'GDP YoY': {
        "title": "Gross Domestic Product (GDP) Year-on-Year Growth",
        "Japan": {
            "file_path": "data/others/JGDPNSAQ Japan GDP Real Chained NSA YoY_.xlsx",
            "col": "Last Price",
            "frequency": "quarterly"
        },
        "China": {
            "file_path": "data/others/EHGDCN China Real Quarterly GDP (Annual YoY _).xlsx",
            "col": "Mid Price",
            "frequency": "quarterly"
        },
        "Australia": {
            "file_path": "data/others/AUNAGDPY Australia GDP SA YoY.xlsx",
            "col": "Last Price",
            "frequency": "quarterly"
        },
    },
    'Gov Debt % GDP': {
        "title": "Government Debt as a Percentage of GDP",
        "Japan": {
            "file_path": "data/others/GDDBJAPN Japan Debt as a Percentage of GDP.xlsx",
            "col": "Mid Price",
            "frequency": "yearly"
        },
        "China": {
            "file_path": "data/others/CHBGDGOP China Government Debt as Percentage of GDP.xlsx",
            "col": "Mid Price",
            "frequency": "yearly"
        },
        "Australia": {
            "file_path": "data/others/GDDBAUSL Australia Debt as a Percentage of GDP.xlsx",
            "col": "Mid Price",
            "frequency": "yearly"
        },
    },
    'Unemployment Rate': {
        "title": "Unemployment Rate",
        "Japan": {
            "file_path": "data/others/EHUPJP Japan Unemployment Rate.xlsx",
            "col": "Mid Price",
            "frequency": "quarterly"
        },
        "China": {
            "file_path": "data/others/EHSRUCN China Quarterly Surveyed Unemployment Rate.xlsx",
            "col": "Mid Price",
            "frequency": "quarterly"
        },
        "Australia": {
            "file_path": "data/others/EHUPAU Australia Unemployment Rate.xlsx",
            "col": "Mid Price",
            "frequency": "quarterly"
        },
    },
    'Wage Growth YoY': {
        "title": "Hourly Wage Growth (Excluding Bonuses, Year-on-Year, Seasonally Adjusted)",
        "Australia": {
            "file_path": "data/others/AUWCYSA Australia Wage Cost Hourly Rates of Pay Ex Bonuses YoY SA.xlsx",
            "col": "Last Price",
            "frequency": "quarterly"
        }
    },
    'Cash Rate Target': {
        "title": "RBA Cash Rate Target",
        "Australia": {
            "file_path": "data/others/RBATCTR Australia RBA Cash Rate Target.xlsx",
            "col": "Last Price",
            "frequency": "monthly"
        }
    }
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
        df = df.sort_index()

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

# 2.6. Dynamic downsampling based on length of data
@st.cache_data
def adaptive_downsampling(df):
    num_rows = len(df)
    
    # Dynamically determine downsampling factor
    if num_rows > 5000:
        step = max(2, num_rows // 500)  # Keeps about 500 rows
    elif num_rows > 2000:
        step = max(2, num_rows // 400)  # Keeps about 400 rows
    elif num_rows > 1000:
        step = max(2, num_rows // 300)  # Keeps about 300 rows
    else:
        return df  # No downsampling needed
    
    return df.iloc[::step]

# 2.7. Filter data based on selected frequency
@st.cache_data
def filter_data_by_frequency(df, start_date, end_date, frequency):
    """Filter data based on selected frequency (monthly, quarterly, or yearly)."""
    df_filtered = df.copy()
    
    # Ensure the index is in datetime format
    df_filtered.index = pd.to_datetime(df_filtered.index)
    
    # Filter based on frequency
    if frequency == "yearly":
        df_filtered = df_filtered[(df_filtered.index.year >= start_date.year) & 
                                  (df_filtered.index.year <= end_date.year)]
    
    elif frequency == "monthly":
        # Convert start_date and end_date to pandas Timestamp
        start_date_pd = pd.Timestamp(start_date)
        end_date_pd = pd.Timestamp(end_date)

        df_filtered = df_filtered[
            (df_filtered.index.to_period("M") >= start_date_pd.to_period("M")) & 
            (df_filtered.index.to_period("M") <= end_date_pd.to_period("M"))
        ]

    
    elif frequency == "quarterly":
        start_qtr = (start_date.month - 1) // 3 + 1
        end_qtr = (end_date.month - 1) // 3 + 1
        df_filtered = df_filtered[(df_filtered.index.year >= start_date.year) & 
                                  (df_filtered.index.year <= end_date.year)]
        df_filtered = df_filtered[df_filtered.index.to_period("Q").isin(pd.period_range(
            f"{start_date.year}Q{start_qtr}", f"{end_date.year}Q{end_qtr}", freq="Q"
        ))]
    
    return df_filtered

# 2.8. Format date/index column
def format_date_column(df):
    df_copy = df.copy()
    try:
        if "Date" in df_copy.columns:
            # Try formatting the "Date" column
            df_copy["Date"] = df_copy["Date"].dt.strftime("%d/%m/%Y")
        elif isinstance(df_copy.index, pd.DatetimeIndex):
            # Try formatting the index if it's a DatetimeIndex
            df_copy.index = df_copy.index.strftime("%d/%m/%Y")
    except Exception as e:
        return df

    return df_copy
    

# 3. VISUALIZATION-------------------------------------
# 3.1. Plot the bond yield curve for a selected day
def plot_yield_curve(df, selected_date, country):
    if country not in yield_columns:
        st.error("Yield columns for this country are not defined.")
        return

    # Filter data for the selected date
    df_filtered = df[df.index == pd.to_datetime(selected_date)]

    if df_filtered.empty:
        st.warning(f"No data available for {selected_date.strftime('%d/%m/%Y')}")
        return

    # Keep only the selected yield columns
    selected_columns = [col for col in yield_columns[country] if col in df_filtered.columns]
    df_filtered = df_filtered[selected_columns]
    df_filtered_copy = format_date_column(df_filtered)
    st.dataframe(df_filtered_copy)

    # Extract available maturities & yields
    maturities = []
    yields = []

    for col in selected_columns:
        if not pd.isna(df_filtered.iloc[0][col]):  # Check for non-null values
            maturities.append(get_maturity_name(col))  # Column name represents maturity
            yields.append(df_filtered.iloc[0][col])  # Yield value

    if not maturities:
        st.warning(f"No yield data available for {selected_date.strftime('%d/%m/%Y')}")
        return

    # Create DataFrame for plotting
    plot_df = pd.DataFrame({"Maturity": maturities, "Yield (%)": yields})

    # Plot using Plotly
    fig = px.line(plot_df, x="Maturity", y="Yield (%)", markers=True,
                  title=f"{country} Government Bond Yield Curve on {selected_date.strftime('%d/%m/%Y')}",
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
                    )
    
    fig.update_layout(
        title="",
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

    # If too long, downsample to reduce frames
    df_filtered = adaptive_downsampling(df_filtered)

    # Convert to long format for Plotly
    df_long = df_filtered.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield")

    # Ensure maturities are in correct order
    df_long["Maturity"] = pd.Categorical(df_long["Maturity"], categories=maturity_labels, ordered=True)

    # Convert Date to string to ensure proper animation frame handling
    df_long["Date"] = df_long["Date"].dt.strftime('%d/%m/%Y')

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
            name=f"Static: {selected_date.strftime('%d/%m/%Y')}",
            line=dict(color="red", width=2),
            marker=dict(symbol="circle"),
        ))

    # Update layout for a better look
    fig.update_layout(
        title="",
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
        title="",
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

# 3.5. Draw plot with multiple lines
def plot_multiple_lines(df, start_date, end_date, required_columns, title, is_filtered=False):
    # Filter data based on the selected date range
    if not is_filtered:
        df_filtered = filter_dataframe(df, start_date, end_date, required_columns)
    else:
        df_filtered = df # df is already filtered
    
    if df_filtered is None or df_filtered.empty:
        st.warning(f"No valid data available between {start_date.strftime('%d/%m/%Y')} and {end_date.strftime('%d/%m/%Y')}.")
        return
    
    if len(df_filtered) < 4:
        # Not enough data points. Show DataFrame instead of plotting
        st.dataframe(format_date_column(df_filtered[required_columns]))
        return
    
    # If too long, downsample to reduce frames
    df_filtered = adaptive_downsampling(df_filtered)
    
    # Initialize session state for checkboxes
    for key in required_columns:
        session_key = f"{key}_{title}"
        if session_key not in st.session_state:
            st.session_state[session_key] = True # Default: show all traces
    
    # Create plot
    fig = go.Figure()

    # Dictionary to store checkbox states
    checkbox_states = {}

    # Dynamically determine number of columns (max 5 for better layout)
    num_cols = min(len(required_columns), 5)  # Use up to 5 columns
    cols = st.columns(num_cols)  # Create dynamic columns

    # Distribute checkboxes across columns evenly
    for idx, col in enumerate(required_columns):
        with cols[idx % num_cols]:  # Cycle through available columns
            checkbox_states[col] = st.checkbox(f"{col}", key=f"{col}_{title}")

    # Add traces dynamically with different colors
    for idx, (col, state) in enumerate(checkbox_states.items()):
        if state:
            fig.add_trace(go.Scatter(
                x=df_filtered.index, 
                y=df_filtered[col], 
                mode="lines", 
                name=col,
                line=dict(color=plotly_colors[idx % len(plotly_colors)]),  # Cycle colors
                showlegend=True # Always show legend
            ))

    # Only show the plot if at least one trace is present
    if len(fig.data) > 0:
        # Update layout for better appearance
        fig.update_layout(
            xaxis_title="Date",
            height=500,
            margin=dict(t=40, b=40, l=30, r=30),
            legend_title="Legend",
        )

        # Show the plot
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
    else:
        st.warning("Please select at least one checkbox to display the graph.")


# 3.6. Plot or show tables
def plot_or_show_table(df, column_name, start_date, end_date, frequency, is_filtered=False):
    if not is_filtered:
        df_filtered = filter_data_by_frequency(df, start_date, end_date, frequency)
    else:
        df_filtered = df # already filtered
    
    if df_filtered is None or df_filtered.empty:
        st.warning("No data available for the selected period.")
        return
    
    if column_name not in df_filtered.columns:
        st.warning(f"Column '{column_name}' not found in the filtered data.")
        return

    if len(df_filtered) < 4:
        # Not enough data points. Show DataFrame instead of plotting
        st.dataframe(format_date_column(df_filtered[[column_name]]))
    else:
        # Plot normal line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_filtered.index, 
            y=df_filtered[column_name], 
            mode="lines", 
            name=column_name
        ))
        fig.update_layout(
            xaxis_title="Date",
            height=500,
            margin=dict(t=40, b=40, l=30, r=30),
        )
        st.plotly_chart(fig, use_container_width=True)

