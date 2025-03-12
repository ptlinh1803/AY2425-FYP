import pandas as pd
import openai
from dotenv import load_dotenv
import os
# Load API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

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
def summarize_basic_trends(df_filtered, start_date, end_date, title):
    # Ensure Date is the index and filter for the given period
    df_filtered = df_filtered.loc[start_date:end_date]

    # Drop columns containing "SMAVG" (if applicable)
    df_filtered = df_filtered.loc[:, ~df_filtered.columns.str.contains("SMAVG")]

    # Handle empty data
    if df_filtered.empty:
        return "No data to analyze."

    summary = [f"📊 **{title} Summary:**\n"]

    # Generate full summary
    for col in df_filtered.columns:
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

        # Detect significant fluctuations (if max-min difference is large)
        fluctuation = series.max() - series.min()
        volatility = "⚠️ High fluctuations" if fluctuation > (0.1 * abs(start)) else "🔹 Relatively stable"

        if col in ticker_mapping:
            col = ticker_mapping[col]
        else:
            col = ""

        # Format the summary
        summary.append(f"{col} {trend} ({start:.2f} → {end:.2f}, Change: {change:+.2f}, {percent_change:+.2f}%). {volatility}.\n")
    
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



# Given any prompt, generate OpenAI's response
def get_openai_response(prompt):
    try:
        client = openai.OpenAI(api_key=openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
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