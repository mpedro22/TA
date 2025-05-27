import streamlit as st
from PIL import Image

st.set_page_config(page_title="ITB Carbon Dashboard", layout="wide", initial_sidebar_state="expanded")

# Load logo
logo = Image.open("assets/logo_itb.png")

# Sidebar - Custom
with st.sidebar:
    st.image(logo, width=75)
    st.markdown("### ITB Carbon Dashboard")
    st.markdown("Monitoring campus carbon emissions using dynamic visualizations.")
    st.markdown("---")
    selected_page = st.radio("Menu", [
        "Overview", "Transportation", "Electronic", "Food Waste", "About"
    ])

# Page Routing
if selected_page == "Overview":
    import overview
    overview.show()

elif selected_page == "Transportation":
    import transportation
    transportation.show()

elif selected_page == "Electronic":
    import electronic
    electronic.show()

elif selected_page == "Food Waste":
    import food_drink_waste
    food_drink_waste.show()

elif selected_page == "About":
    import about
    about.show()
