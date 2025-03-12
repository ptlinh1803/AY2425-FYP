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

    summary = []
    summary.append(f"📊 **Analysis of {title} from {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}:**\n")
    
    for col in df_filtered.columns:
        series = df_filtered[col]
        
        start = series.iloc[0]
        end = series.iloc[-1]
        min_val = series.min()
        max_val = series.max()
        mean_val = series.mean()
        median_val = series.median()
        std_val = series.std()
        change = end - start
        avg_change = series.diff().mean()
        
        # Identify trend reversals (sign change in first difference)
        diff_series = series.diff().fillna(0)
        reversals = df_filtered.index[diff_series.mul(diff_series.shift(-1)) < 0].tolist()
        
        # Format summary text
        summary.append(f"📈 **{col} Analysis:**\n"
                       f"- **Start**: {start:.4f}, **End**: {end:.4f}, **Change**: {change:+.4f}\n"
                       f"- **Min**: {min_val:.4f}, **Max**: {max_val:.4f}\n"
                       f"- **Mean**: {mean_val:.4f}, **Median**: {median_val:.4f}, **Std Dev**: {std_val:.4f}\n"
                       f"- **Avg Change per Period**: {avg_change:+.4f}\n"
                       f"- **Trend Reversals**: {len(reversals)} times\n")

    return "\n".join(summary)