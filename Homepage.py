import streamlit as st
from streamlit.logger import get_logger
import plotly.graph_objects as go

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Homepage",
        page_icon="🏠",
    )

    st.markdown("# 🌐 Yield Curve Explorer App")

    st.sidebar.success("Select a page above.")

    st.markdown("""
      As the name suggests, this app is designed to **explore and forecast government bond yield curves** using machine learning models.

      - 📊 Visualize historical trends of **bond yields** and **macroeconomic indicators** from 2000 to 2024  
      - 🌍 Explore yield curve dynamics for **Japan**, **China**, and **Australia**  
      - 🧠 Forecast future curves with **LSTM models** using your own data or sample datasets  
      - ⏳ Experiment with different **forecast windows**  
      - 🤖 Get **AI-generated summaries** of historical yield patterns and future predictions from **GPT-4o**
      """)
    
    st.warning("⚠️ *This app is purely for educational purposes and does not provide financial or investment advice.*")


    st.markdown("""
      ### 📈 What is a Yield Curve?
      The **yield curve** is a graphical representation of **bond yields** across different maturities.  
      It helps investors and economists understand **interest rate expectations**, **inflation outlook**, and **economic growth trends**.
      """
    )

    # --- Plotly Yield Curve ---
    maturities = ["3M", "2Y", "5Y", "10Y", "30Y"]
    yields = [0.02, 0.446, 0.586, 0.952, 2.221]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=maturities,
        y=yields,
        mode='lines+markers',
        marker=dict(size=8)
    ))

    fig.update_layout(
        xaxis_title="Bond Maturity",
        yaxis_title="Yield (%)",
        showlegend=False,
        margin=dict(l=40, r=40, t=10, b=40),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Caption ---
    st.caption("Example: Japan Government Bond Yield Curve on 31/10/2024")


    with st.expander("🔎 How to Interpret the Yield Curve?"):
      st.markdown("""
      The shape of the yield curve provides **insights into market expectations**:

      - **🔼 Upward-Sloping (Normal Curve)**
        - Short-term yields **lower** than long-term yields.
        - Indicates **economic growth** and **inflation expectations**.
        - Investors expect **higher interest rates** in the future.
        - Common during economic **expansion**.

      - **🔽 Downward-Sloping (Inverted Curve)**
        - Short-term yields **higher** than long-term yields.
        - Often a **recession indicator**.
        - Suggests **interest rate cuts** or economic slowdown.
        - Common before an economic **downturn**.

      - **〰️ Flat Curve**
        - Short-term and long-term yields **almost equal**.
        - Signals **economic uncertainty**.
        - Often occurs during **transitions** (before recession or recovery).

      - **🔄 Humped Curve**
        - Middle-term yields **higher** than both short-term and long-term.
        - Suggests **short-term uncertainty** but **long-term stability**.
        - Can indicate **monetary policy shifts**.
                  
      - **🔄 Reverse Humped Curve**  
        - Middle-term yields **lower** than both short-term and long-term.  
        - Suggests **tight short-term monetary policy** but **long-term inflation concerns**.  
        - Often occurs when **central banks raise short-term rates aggressively**, while markets **expect future rate cuts** due to economic slowdown.  
        - Can signal **policy transitions, economic uncertainty, or concerns about long-term debt sustainability**.

      ### 💡 Why Does the Yield Curve Matter?
      - **📊 Investors** use it to predict **stock market trends**.
      - **🏦 Central banks** monitor it to guide **interest rate decisions**.
      - **📉 Businesses** use it for **borrowing cost forecasts**.
      """)

    # --- APAC BOND MARKETS ---
    st.markdown("## APAC Bond Markets")

    st.markdown("""
    The bond market is a major part of the global financial system. While the U.S. and Europe dominate in terms of advanced analytics, Asia-Pacific (APAC) markets — especially **China**, **Japan**, and **Australia** — are rapidly growing but still underexplored in terms of predictive modeling.

    By focusing on APAC yield curve forecasting, this app helps bridge the gap and offers valuable insights for both regional and global investors.
    """)

    st.markdown("##### Bond Market Size (2023 Estimates)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 🌏")
        st.markdown("### **$140.7T**")
        st.markdown("**Worldwide**")
        st.caption("Larger than global equity")

    with col2:
        st.markdown("#### 🇨🇳")
        st.markdown("### **$20T**")
        st.markdown("**China**")
        st.caption("2nd largest bond market")

    with col3:
        st.markdown("#### 🇯🇵")
        st.markdown("### **$9T**")
        st.markdown("**Japan**")
        st.caption("Highly developed market")

    with col4:
        st.markdown("#### 🇦🇺")
        st.markdown("### **$1T**")
        st.markdown("**Australia**")
        st.caption("Known for higher yields")
    
    # --- APP FEATURES ---
    st.markdown("## 🔍 App Features")
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # --- Row 1: Visualization ---
    row1_col1, row1_col2 = st.columns([1, 1.2])  # Slightly wider for text

    with row1_col1:
        st.image("assets/visualization_preview.png", caption="Visualization Preview", use_container_width=True)
        if st.button("Go to Visualization Page"):
            st.switch_page("pages/1_📊_Visualization.py")

    with row1_col2:
        st.markdown("#### 📊 Visualization")
        st.markdown("""
        - View the full yield curve for a specific day  
        - Track how the curve evolves over a selected time period  
        - Explore key macroeconomic indicators like **CPI**, **interest rates**, etc.
        - Get AI-generated insights into the yield curve and its relationship with macro factors  
        """)

    # Spacer
    st.markdown("---")

    # --- Row 2: Prediction ---
    row2_col1, row2_col2 = st.columns([1.2, 1])

    with row2_col1:
        st.markdown("#### 📈 Prediction")
        st.markdown("""
        - Upload your own data or use synthetic sample data  
        - Select different lookback/prediction windows (e.g. 5→1, 30→5, 60→7, 90→30 days)  
        - Predict one or multiple yield maturities at once  
        - Receive AI-generated summaries of forecast results  
        """)

    with row2_col2:
        st.image("assets/prediction_preview.png", caption="Prediction Preview", use_container_width=True)
        if st.button("Go to Prediction Page"):
            st.switch_page("pages/2_📈_Prediction.py")





if __name__ == "__main__":
    run()