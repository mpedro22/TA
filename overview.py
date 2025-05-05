import streamlit as st
import plotly.express as px
from PIL import Image

st.markdown("""
    <div style='margin-top:-60px; padding-bottom: 20px'>
        <h1 style='margin-bottom:0;'>Welcome to the Overview</h1>
        <p style='margin-top:0; color: gray;'>
            This dashboard provides insight into various sources of carbon emissions on ITB campus,
            including transportation, electronics, food waste, and more.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style="background-color:#f0f9ff; padding: 20px; border-radius: 10px;">
                <h5>Total Emissions</h5>
                <h2>1.52 Tons CO₂</h2>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style="background-color:#f0f9ff; padding: 20px; border-radius: 10px;">
                <h5>Survey Respondents</h5>
                <h2>157 Students</h2>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style="background-color:#f0f9ff; padding: 20px; border-radius: 10px;">
                <h5>Areas Covered</h5>
                <h2>18 Buildings</h2>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
        <div style="background-color:#fdfdfd; padding: 25px; border-radius: 10px; box-shadow: 0px 2px 6px rgba(0,0,0,0.05);">
            <h4>Emissions by Category</h4>
    """, unsafe_allow_html=True)

    fig1 = px.pie(
        names=["Transportation", "Electronic", "Food Waste", "Other"],
        values=[123, 78, 45, 32],
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    st.markdown("""
        <div style="background-color:#fdfdfd; padding: 25px; border-radius: 10px; box-shadow: 0px 2px 6px rgba(0,0,0,0.05);">
            <h4>Weekly Emission Trend</h4>
    """, unsafe_allow_html=True)

    import pandas as pd
    df = pd.DataFrame({
        "Date": pd.date_range(start="2025-05-01", periods=7),
        "Emission (kg CO₂)": [40, 35, 50, 38, 60, 55, 48]
    })
    fig2 = px.line(df, x="Date", y="Emission (kg CO₂)", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
