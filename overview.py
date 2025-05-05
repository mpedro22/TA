import streamlit as st

def show():
    st.title("Welcome to the Overview")
    st.write("This dashboard provides insight into various sources of carbon emissions on ITB campus, including transportation, electronics, food waste, and more.")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Emissions", "1.52 Tons CO₂")
    with col2:
        st.metric("Survey Respondents", "157 Students")
    with col3:
        st.metric("Areas Covered", "18 Buildings")

    st.subheader("Emissions by Category")
    st.image("https://via.placeholder.com/400x200")

    st.subheader("Weekly Emission Trend")
    st.image("https://via.placeholder.com/400x200")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("© 2025 ITB Carbon Emission Monitoring")
