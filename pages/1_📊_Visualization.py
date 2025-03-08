import streamlit as st

# VISUALIZATION PAGE
st.set_page_config(
    page_title="Visualization",
    page_icon="📊",
)

# Dropdown to select country
country = st.sidebar.selectbox("Select country", ["Japan", "China", "Australia"])

# Main page content-------------------------------------
st.title(country)  # Display selected country as the main title