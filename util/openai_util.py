import pandas as pd
import openai
import streamlit as st
# from dotenv import load_dotenv
# import os

# Load API key
# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = st.secrets["api_keys"]["openai"]

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
    "TI0001M_Ask Price": "TIBOR 1M",
    "TI0003M_Ask Price": "TIBOR 3M",
    "TI0006M_Ask Price": "TIBOR 6M",
    "TI0012M_Ask Price": "TIBOR 12M",
    "JYSOC_Close": "JPY OIS 1Y",
    "JYSO2_Close": "JPY OIS 2Y",
    "JYSO5_Close": "JPY OIS 5Y",
    "JYSO10_Close": "JPY OIS 10Y",
    "JYSO30_Close": "JPY OIS 30Y",
    "CCSWOC_Close": "CNY IRS 1Y (7D Repo)",
    "CCSWO2_Close": "CNY IRS 2Y (7D Repo)",
    "CCSWO5_Close": "CNY IRS 5Y (7D Repo)",
    "CCSWO10_Close": "CNY IRS 10Y (7D Repo)",
    "CHLRLPR1_Last Price": "LPR 1Y",
    "CHLRLPR5_Last Price": "LPR 5Y",
    "SHIF1Y_Close": "SHIBOR 1Y",
    "SHIF3M_Close": "SHIBOR 3M",
    "ADSWAP2_Close": "AUD IRS 2Y (6M Benchmark)",
    "ADSWAP5_Close": "AUD IRS 5Y (6M Benchmark)",
    "ADSWAP10_Close": "AUD IRS 10Y (6M Benchmark)",
    "ADSWAP30_Close": "AUD IRS 30Y (6M Benchmark)"
}

# 1. Summarize basic trends
def summarize_basic_trends(df_filtered, start_date, end_date, title, show_bps=False):
    # Ensure Date is the index and filter for the given period
    if start_date and end_date:
        df_filtered = df_filtered.loc[start_date:end_date]

        # Drop columns containing "SMAVG" (if applicable)
        df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains("SMAVG")]

    # Handle empty data
    if df_filtered.empty:
        return "No data to analyze."

    summary = [f"📊 **{title} Summary:**\n"]

    # Generate full summary
    for col in df_filtered.columns:
        if not pd.api.types.is_numeric_dtype(df_filtered[col]):
            continue  # Skip non-numeric columns like 'Date'
        series = df_filtered[col].dropna()

        if series.empty:
            summary.append(f"📈 **{col}**: No available data.")
            continue

        if len(series) == 1:
            date_str = series.index[0].strftime('%d/%m/%Y')
            summary.append(f"📈 {ticker_mapping.get(col, '')} on {date_str}: {series.iloc[0]:.2f}")
            continue

        # Get first and last values
        start = series.iloc[0]
        end = series.iloc[-1]
        change = end - start
        percent_change = (change / start) * 100 if start != 0 else "N/A"

        # Determine overall trend direction
        trend = "⬆️ Increased" if end > start else "⬇️ Decreased" if end < start else "➡️ Stable"

        if col in ticker_mapping:
            col = ticker_mapping[col]

        if show_bps:
            bps_change = change / 0.01
            if isinstance(percent_change, str):  # e.g. "N/A"
                summary.append(f"{col} {trend} ({start:.3f} → {end:.3f}, Change: {change:+.3f}, {bps_change:+.0f} bps).\n")
            else:
                summary.append(f"{col} {trend} ({start:.3f} → {end:.3f}, Change: {change:+.3f}, {percent_change:+.3f}%, {bps_change:+.0f} bps).\n")
        else:
            if isinstance(percent_change, str):
                summary.append(f"{col} {trend} ({start:.3f} → {end:.3f}, Change: {change:+.3f}).\n")
            else:
                summary.append(f"{col} {trend} ({start:.3f} → {end:.3f}, Change: {change:+.3f}, {percent_change:+.3f}%).\n")

    
    return "\n".join(summary)

# 2. Generate prompt for yield curve of the selected prompt
def generate_prompt_for_a_single_day(df, selected_date, country):
    if df.empty:
        return ""
    
    prompt = []

    title = f"Yield Curve Summary for {country} on {selected_date.strftime('%d/%m/%Y')}\n"
    prompt.append(title)

    for col in df.columns:
        prompt.append(f"- {ticker_mapping[col]}: {df[col].values[0]:.4f}%")

    # Add analysis questions
    prompt.append("""
        Analysis Questions (answer shortly):
        1. What is the shape of this yield curve?  
        - Is it upward-sloping (normal), downward-sloping (inverted), or humped?  
        2. What does this shape indicate about the economy? 
        - Does it suggest economic expansion, slowdown, or uncertainty?
        """)

    return "\n".join(prompt)

# 3. Generate prompt for yield curve of a period
def generate_yield_curve_trend_prompt(country, start_date, end_date, trend_summary):
    prompt = f"""
    Yield Curve Trend Analysis for {country} ({start_date} - {end_date})**

    {trend_summary}

    Analysis Questions (answer shortly in bullet points):
    1. How does the yield curve evolve over this period?
    - Are there any significant/abnormal trends?  
    - Differences in movement between short-term, medium-term, and long-term maturities? 
    - What does this movement suggest about monetary policy shifts?  

    2. What does this yield curve trend suggest about {country}'s economy?  
    - How do investor expectations seem to shift over time?  

    3. What key global or domestic events during this period could have impacted the yield curve, if you know?   
    """

    return prompt

# 4. Generated prompt for additional data
def generate_multi_data_prompt(country, start_date, end_date, summary_for_prompt):
    # Yield Curve Summary (First Element)
    yield_curve_summary = summary_for_prompt[0]

    # Additional Insights (If Any)
    additional_summaries = summary_for_prompt[1:]

    prompt = f"""
    # Macroeconomic & Yield Curve Analysis for {country} ({start_date} - {end_date})

    ## Yield Curve Key Trends:
    {yield_curve_summary}

    """

    if additional_summaries:
        prompt += "## **Additional Insights & Impact Analysis:**\n"
        for summary in additional_summaries:
            prompt += f"""
            🔍 **Data Summary:**
            {summary}

            - How has this indicator evolved over the period?
            - What does this trend suggest about {country}'s economy?
            - Could this data have influenced the yield curve? If so, how?
            """

    prompt += "\n**Please provide a concise, structured response.**"
    
    return prompt

# 5. Generate prompt for prediction
def generate_prediction_prompt(input_metadata, summary_for_prompt):
    """
    Create a descriptive prompt for interpreting input and predicted trends,
    based on metadata and the input/output summaries.
    """
    country = input_metadata.get("country", "Unknown Country")
    maturities = input_metadata.get("maturities", [])
    lookback_window = input_metadata.get("lookback_window", "N/A")
    input_mode = input_metadata.get("input_mode", "Unknown")
    quarter_year_mapping = input_metadata.get("quarter_year_mapping", {})
    noise_level = input_metadata.get("noise_level", 0)
    prompt = ""

    # Start building the prompt
    prompt += f"The user selected the following maturities: {', '.join(maturities)} for {country}.\n"
    prompt += f"The prediction window is: **{lookback_window}**.\n"

    if input_mode == "Generate synthetic data":
        prompt += f"The data was synthetically generated to resemble historical conditions.\n"
        if quarter_year_mapping:
            prompt += "Each maturity was conditioned on a specific time period:\n"
            for maturity, period in quarter_year_mapping.items():
                prompt += f"  • {maturity}: {period}\n"
        if noise_level > 0:
            prompt += f"A Gaussian noise level of {noise_level * 10000:.0f} basis points (bps) was added to simulate market volatility.\n"
    else:
        prompt += "The input data was uploaded directly by the user.\n"

    prompt += "\n---\n"
    prompt += "Summary of Trends\n"
    for section in summary_for_prompt:
        prompt += section + "\n"

    prompt += "\n---\n"
    prompt += "Interpretation Tasks\n"
    prompt += (
        "1. What is the overall trend in the input yields across maturities?\n"
        "2. What trends can you observe in the predicted yields?\n"
        "3. Are there any sudden changes, large basis point shifts, or maturity segments that behave unusually?\n"
        "4. Do the predictions follow or deviate from the input trend?\n"
        "5. Based on the yield movements, what could be implied about the market outlook or yield curve shape?"
    )

    return prompt



# 6. Given any prompt, generate OpenAI's response
def get_openai_response(prompt, basic=False):
    """
    basic (bool): If True, use GPT-3.5 for a cheaper response; otherwise, use GPT-4o.
    """
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        model = "gpt-3.5-turbo" if basic else "gpt-4o"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst specializing in bond markets, monetary policy, and macroeconomics. "
                        "Summarize your analysis clearly and concisely within the given token limit. "
                        "Prioritize key insights, avoid excessive details, and structure responses effectively."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.2  # More factual responses
        )

        # ✅ Extract and return the response text
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ Error: {str(e)}"