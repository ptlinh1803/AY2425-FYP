import pandas as pd
# Mapping of tickers to human-readable maturities
ticker_mapping = {
    "GJTB3MO_Close": "3M Yield",
    "GJGB2_Close": "2Y Yield",
    "GJGB5_Close": "5Y Yield",
    "GJGB10_Close": "10Y Yield",
    "GJGB30_Close": "30Y Yield",
    "GCNY3M_Close": "3M Yield",
    "GCNY2YR_Close": "2Y Yield",
    "GCNY5YR_Close": "5Y Yield",
    "GCNY10YR_Close": "10Y Yield",
    "GCNY30YR_Close": "30Y Yield",
    "GACGB3M_Close": "3M Yield",
    "GACGB2_Close": "2Y Yield",
    "GACGB5_Close": "5Y Yield",
    "GACGB10_Close": "10Y Yield",
    "GACGB30_Close": "30Y Yield",

}
# Summarize basic trends only
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

    summary = [f"📊 **{title} Summary:**\n"]

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

        if col in ticker_mapping:
            col = ticker_mapping[col]

        # Format the summary
        summary.append(f"📈 **{col}**: {trend} ({start:.2f} → {end:.2f}, Change: {change:+.2f}, {percent_change:+.2f}%). {volatility}.\n")

    return "\n".join(summary)
