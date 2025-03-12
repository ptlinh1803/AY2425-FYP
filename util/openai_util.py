import pandas as pd

# 1. Extract key trends
def extract_key_trends(df_filtered, start_date, end_date, title):
    """
    Given df_filtered (with only essential columns) and start_date, end_date, index = Date
    extract key data for each columm: 
    start, end, min, max, mean, median, std, changes, average_changes, trend reversals
    maybe no need SMAVG columns
    return text summary of each column
    """
    # Ensure Date is the index
    df_filtered = df_filtered.loc[start_date:end_date]
    
    # Drop columns containing "SMAVG"
    df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains("SMAVG")]

    if df_filtered is None or df_filtered.empty:
        return "No data to analyze."

    summary = []
    summary.append(f"📊 **Analysis of {title} from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}:**\n")
    
    for col in df_filtered.columns:
        series = df_filtered[col]
        
        start = series.dropna().iloc[0] if not series.dropna().empty else "Data Unavailable"
        end = series.dropna().iloc[-1] if not series.dropna().empty else "Data Unavailable"
        min_val = series.min()
        max_val = series.max()
        mean_val = series.mean()
        median_val = series.median()
        std_val = series.std()
        change = end - start if isinstance(start, (int, float)) and isinstance(end, (int, float)) else "N/A"
        percent_change = (change / start) * 100 if start != 0 else "N/A"
        avg_change = series.diff().mean()
        
        # Identify trend reversals (sign change in first difference)
        diff_series = series.diff().fillna(0)
        reversals = df_filtered.index[diff_series.mul(diff_series.shift(-1)) < 0].tolist()

        # Detect significant fluctuations (if max-min difference is large)
        fluctuation = series.max() - series.min()
        volatility = "⚠️ High fluctuations" if fluctuation > (0.1 * abs(start)) else "➡️ Relatively stable"
        
        # Format summary text
        summary.append(f"📈 **{col} Analysis:**\n"
                       f"- **Start**: {start:.4f}, **End**: {end:.4f}, **Change**: {change:+.4f}, {percent_change:+.2f}%\n"
                       f"- **Min**: {min_val:.4f}, **Max**: {max_val:.4f}\n"
                       f"- **Mean**: {mean_val:.4f}, **Median**: {median_val:.4f}, **Std Dev**: {std_val:.4f}\n"
                       f"- **Avg Change per Period**: {avg_change:+.4f}\n"
                       f"- **Trend Reversals**: {len(reversals)} times\n"
                       f"- {volatility}\n")

    return "\n".join(summary)

# 2. Summarize basic trends only
def summarize_basic_trends(df_filtered, start_date, end_date, title):
    """
    Summarizes key trends in a financial dataset with basic insights.

    Extracts:
    - First and last available values
    - Overall trend direction (up/down/stable)
    - Change in value (absolute & percentage)
    - Any significant fluctuations

    Args:
        df_filtered (pd.DataFrame): Filtered dataframe with Date as index.
        start_date (datetime): Start of the analysis period.
        end_date (datetime): End of the analysis period.
        title (str): Name of the dataset.

    Returns:
        str: Formatted basic summary of financial trends.
    """
    # Ensure Date is the index and filter for the given period
    df_filtered = df_filtered.loc[start_date:end_date]

    # Drop columns containing "SMAVG" (if applicable)
    df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains("SMAVG")]

    # Handle empty data
    if df_filtered.empty:
        return "No data to analyze."

    summary = [f"📊 **{title} Summary ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}):**\n"]

    for col in df_filtered.columns:
        series = df_filtered[col].dropna()

        if series.empty:
            summary.append(f"📈 **{col}**: No available data.")
            continue

        # Get first and last values
        start = series.iloc[0]
        end = series.iloc[-1]
        change = end - start
        percent_change = (change / start) * 100 if start != 0 else "N/A"

        # Determine overall trend direction
        trend = "⬆️ Increased" if end > start else "⬇️ Decreased" if end < start else "➡️ Stable"

        # Detect significant fluctuations (if max-min difference is large)
        fluctuation = series.max() - series.min()
        volatility = "⚠️ High fluctuations" if fluctuation > (0.1 * abs(start)) else "🔹 Relatively stable"

        # Format the summary
        summary.append(f"📈 **{col}**: {trend} ({start:.2f} → {end:.2f}, Change: {change:+.2f}, {percent_change:+.2f}%). {volatility}.\n")

    return "\n".join(summary)
