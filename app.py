import streamlit as st
from PIL import Image
import base64
import io
from auth import is_logged_in, is_admin, get_current_user, logout

# Page config
st.set_page_config(
    page_title="ITB Carbon Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Check authentication
def check_auth():
    if not is_logged_in():
        import login
        login.show()
        return False
    return True

# Sidebar Navigation
def create_sidebar():
    with st.sidebar:
        # User info and Header
        current_user = get_current_user()
        if current_user:
            if is_admin():
                user_indicator = "Admin"
            else:
                user_indicator = current_user["username"]
            
            st.markdown(f"""
            <div style="
                font-size: 0.75rem;
                color: #64748b;
                margin-bottom: 0.5rem;
                font-family: 'Poppins', sans-serif;
                padding-left: 1rem;
            ">
                {user_indicator}
            </div>
            """, unsafe_allow_html=True)
        
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
            ("", "Dashboard Utama", "overview"),
            ("", "Transportasi", "transportation"),
            ("", "Elektronik", "electronic"),
            ("", "Sampah", "sampah"),
            ("", "Tentang Dashboard", "about")
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Spacer to push buttons to bottom
        st.markdown('<div style="flex-grow: 1; min-height: 2rem;"></div>', unsafe_allow_html=True)
        
        # Admin controls and logout
        if is_admin():
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Tambah Akun", key="add_account", use_container_width=True):
                    st.session_state.current_page = 'register'
                    st.rerun()
            with col2:
                if st.button("Keluar", key="logout", use_container_width=True):
                    logout()
                    st.rerun()
        else:
            # Regular user only gets logout
            if st.button("Keluar", key="logout_user", use_container_width=True):
                logout()
                st.rerun()

# Main content routing
def main():
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'overview'
    
    # Check authentication first
    if not check_auth():
        return
    
    # Check for register page (admin only)
    if st.session_state.get('current_page') == 'register':
        if is_admin():
            import register
            register.show()
        else:
            st.error("Akses ditolak!")
            st.session_state.current_page = 'overview'
            st.rerun()
        return
    
    # Create sidebar for authenticated users
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

    # Spacer to push buttons to bottom
    st.markdown('<div style="flex-grow: 1; min-height: 2rem;"></div>', unsafe_allow_html=True)

    # Admin controls and logout
    if is_admin():
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Tambah Akun", key="add_account", use_container_width=True):
                st.session_state.current_page = 'register'
                st.rerun()
        with col2:
            if st.button("Keluar", key="logout", use_container_width=True):
                logout()
                st.rerun()
    else:
        # Regular user only gets logout
        if st.button("Keluar", key="logout_user", use_container_width=True):
            logout()
            st.rerun()

if __name__ == "__main__":
    main()