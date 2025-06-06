import streamlit as st
from PIL import Image
import base64
import io

# Page config
st.set_page_config(
    page_title="ITB Carbon Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar Navigation
def create_sidebar():
    with st.sidebar:
        # Logo and Header
        st.markdown("""
        <div class="sidebar-header">
            <div class="logo-container">
                <div class="logo-circle">
                    <span class="logo-text">ITB</span>
                </div>
            </div>
            <h2 class="sidebar-title">Dashboard Emisi Karbon</h2>
            <p class="sidebar-subtitle">Kampus Ganesha</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu Container
        st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
        
        # Menu items
        menu_items = [
            ("", "Ringkasan", "overview"),
            ("", "Transportasi", "transportation"),
            ("", "Elektronik", "electronic"),
            ("", "Sampah", "sampah"),
            ("", "Tentang Kami", "about")
        ]
        
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'
        
        # Create navigation items
        for icon, label, page_id in menu_items:
            is_active = st.session_state.current_page == page_id
            
            # Navigation item wrapper
            st.markdown('<div class="nav-item-wrapper">', unsafe_allow_html=True)
            
            if is_active:
                # Active state - styled div
                st.markdown(f"""
                <div class="nav-item-active">{label}</div>
                """, unsafe_allow_html=True)
            else:
                # Inactive state - clickable button
                if st.button(f"{label}", key=f"nav_{page_id}", use_container_width=True):
                    st.session_state.current_page = page_id
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Close navigation menu container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sidebar footer
        st.markdown("""
        <div class="sidebar-footer">
            <p class="footer-text">© ITB 2025</p>
        </div>
        """, unsafe_allow_html=True)

# Main content routing
def main():
    create_sidebar()
    
    # Page routing based on session state
    if st.session_state.current_page == 'overview':
        import overview
        overview.show()
    elif st.session_state.current_page == 'transportation':
        import transportation
        transportation.show()
    elif st.session_state.current_page == 'electronic':
        import electronic
        electronic.show()
    elif st.session_state.current_page == 'sampah':
        import food_drink_waste
        food_drink_waste.show()
    elif st.session_state.current_page == 'about':
        import about
        about.show()

if __name__ == "__main__":
    main()