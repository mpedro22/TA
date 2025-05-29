import streamlit as st
from PIL import Image
import base64
import io

# Page config
st.set_page_config(
    page_title="ITB Carbon Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="🌱"
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
        
        # Navigation Menu
        st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
        
        # Menu items
        menu_items = [
            ("", "Overview", "overview"),
            ("", "Transportation", "transportation"),
            ("", "Electronic", "electronic"),
            ("", "Food & Waste", "food"),
            ("", "Analytics", "analytics"),
            ("", "Heatmap", "heatmap"),
            ("", "About", "about")
        ]
        
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'overview'
        
        # Create navigation
        for icon, label, page_id in menu_items:
            active_class = "nav-active" if st.session_state.current_page == page_id else ""
            
            # Custom navigation button
            if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sidebar footer
        st.markdown("""
        <div class="sidebar-footer">
            <p class="footer-text">© 2025 ITB Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

# Main content routing
def main():
    create_sidebar()
    
    # Page routing
    if st.session_state.current_page == 'overview':
        import overview
        overview.show()
    elif st.session_state.current_page == 'transportation':
        import transportation
        transportation.show()
    elif st.session_state.current_page == 'electronic':
        import electronic
        electronic.show()
    elif st.session_state.current_page == 'food':
        import food_drink_waste
        food_drink_waste.show()
    elif st.session_state.current_page == 'analytics':
        show_analytics()
    elif st.session_state.current_page == 'heatmap':
        show_heatmap()
    elif st.session_state.current_page == 'about':
        import about
        about.show()

def show_analytics():
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📊 Analytics & Insights</h1>
        <p class="page-subtitle">Advanced analysis of carbon emission patterns</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Placeholder for analytics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3>Trend Analysis</h3>
            <p>Analyze emission trends over time</p>
            <span class="coming-soon">Coming Soon</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Goal Tracking</h3>
            <p>Monitor emission reduction goals</p>
            <span class="coming-soon">Coming Soon</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💡</div>
            <h3>Recommendations</h3>
            <p>AI-powered reduction suggestions</p>
            <span class="coming-soon">Coming Soon</span>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()