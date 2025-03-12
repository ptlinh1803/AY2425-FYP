import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Homepage",
        page_icon="👋",
    )

    st.write("# Welcome to Streamlit! 👋")

    st.sidebar.success("Select a page above.")

    st.markdown("""
    ### 📈 What is a Yield Curve?
    The **yield curve** is a graphical representation of **bond yields** across different maturities.  
    It helps investors and economists understand **interest rate expectations**, **inflation outlook**, and **economic growth trends**.

    ### 🔎 How to Interpret the Yield Curve?
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


if __name__ == "__main__":
    run()