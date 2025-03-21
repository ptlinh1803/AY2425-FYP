import pandas as pd
import streamlit as st

pred_window_mapping = {
    "5 past days → Predict next 1 day": 5,
    "30 past days → Predict next 5 days": 30,
    "60 past days → Predict next 7 days": 60,
    "90 past days → Predict next 30 days": 90
}

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
        st.warning(f"Only {len(df)} rows available, which is less than the required {input_days}.")
        return None

    return df