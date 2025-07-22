import streamlit as st
import sys
import os
import time
import importlib
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.auth.auth import is_logged_in, get_current_user, is_admin, logout
    from src.utils.db_connector import init_supabase_connection 
    auth_available = True
except ImportError as e:
    logging.error(f"Initial import error: {e}. Trying fallback path.")
    try:
        from auth.auth import is_logged_in, get_current_user, is_admin, logout
        from utils.db_connector import init_supabase_connection
        auth_available = True
    except ImportError as e_fallback:
        st.error(f"Error: Tidak dapat mengimport modul auth atau db_connector. Periksa struktur folder dan PYTHONPATH Anda.")
        logging.critical(f"Critical import error: {e_fallback}")
        auth_available = False

def check_supabase_connection():
    if not auth_available:
        return False
    try:
        supabase_client = init_supabase_connection()
        return supabase_client is not None
    except Exception as e:
        logging.error(f"Error during check_supabase_connection: {e}")
        return False

def main():
    if 'last_loaded_page' not in st.session_state:
        st.session_state.last_loaded_page = None
    if 'is_initial_page_load' not in st.session_state:
        st.session_state.is_initial_page_load = True 

    start_main_time = time.time()

    # KUNCI: Ubah initial_sidebar_state menjadi "collapsed"
    st.set_page_config(
        page_title="ITB Carbon Dashboard", 
        layout="wide", 
        initial_sidebar_state="collapsed", 
    )

    css_file_path = "assets/css/style.css"
    if os.path.exists(css_file_path):
        with open(css_file_path, encoding="utf-8") as f:
            css_content = f.read()
            st.markdown(f'<style>/* Cache Buster: {time.time()} */\n{css_content}</style>', unsafe_allow_html=True)
    else:
        st.warning("Warning: style.css not found! Using default styling.")

    if not auth_available:
        st.error("Dashboard tidak dapat beroperasi. Modul auth atau db_connector tidak dapat diimport.")
        return
    
    if not check_supabase_connection():
        st.write("### 📋 Panduan Konfigurasi Secrets")
        st.write("Di Streamlit Cloud > Settings > Secrets, tambahkan:")
        st.code("""
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
        """)
        return 
    
    supabase = None
    try:
        supabase = init_supabase_connection()
    except Exception as e:
        logging.error(f"Could not get Supabase client for rehydration: {e}")
        
    if supabase:
        try:
            current_session = supabase.auth.get_session()
            if current_session:
                st.session_state.supabase_session = current_session
                st.session_state.supabase_user = current_session.user
                st.session_state.user_metadata = current_session.user.user_metadata if current_session.user else {}
            else:
                st.session_state.pop("supabase_session", None)
                st.session_state.pop("supabase_user", None)
                st.session_state.pop("user_metadata", None)
        except Exception as e:
            logging.error(f"Error rehydrating Supabase session: {e}")
            st.session_state.pop("supabase_session", None)
            st.session_state.pop("supabase_user", None)
            st.session_state.pop("user_metadata", None)

    def create_sidebar():
        with st.sidebar:
            current_user_metadata = get_current_user() 
            if current_user_metadata:
                display_name = current_user_metadata.get("username", current_user_metadata.get("email", "Pengguna"))
                user_indicator = "Halo, Admin!" if is_admin() else f"Halo, {display_name}!"
                st.markdown(f"""<div style="font-size: 1rem; font-weight: 750; color: #059669; margin-top: 0rem; font-family: 'Poppins', sans-serif; padding-left: 0.5rem;">{user_indicator}</div>""", unsafe_allow_html=True)
            
            st.markdown("""<div class="sidebar-header"><div class="logo-wrapper"><div class="logo-container"><div class="logo-circle"><span class="logo-text"><span class="logo-text-main">ITB</span><span class="logo-text-sub">CARBON DASHBOARD</span></span></div></div></div><h2 class="sidebar-title">Kampus Ganesha</h2></div>""", unsafe_allow_html=True)
            
            st.markdown('<div class="nav-menu">', unsafe_allow_html=True)

            menu_items = [
                ("Dashboard Utama", "overview"),
                ("Transportasi", "transportation"),
                ("Elektronik", "electronic"),
                ("Sampah", "sampah"),
                ("Tentang Dashboard", "about")
            ]
            
            current_page_from_url = st.query_params.get('page', 'overview')

            for label, page_id in menu_items:
                st.markdown('<div class="nav-item-wrapper">', unsafe_allow_html=True)
                if current_page_from_url == page_id:
                    st.markdown(f'<div class="nav-item-active">{label}</div>', unsafe_allow_html=True)
                else:
                    if st.button(label, key=f"nav_{page_id}", use_container_width=True):
                        st.query_params["page"] = page_id
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            if is_admin():
                st.markdown('<div class="nav-item-wrapper">', unsafe_allow_html=True)
                if current_page_from_url == 'register':
                    st.markdown('<div class="nav-item-active">Tambah Akun</div>', unsafe_allow_html=True)
                else:
                    if st.button("Tambah Akun", key="nav_register", use_container_width=True):
                        st.query_params["page"] = "register"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="nav-item-wrapper">', unsafe_allow_html=True)
            if st.button("Keluar", key="nav_logout", use_container_width=True):
                logout()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    if not is_logged_in():
        try:
            from src.auth.login import show as show_login_page 
        except ImportError:
            from auth.login import show as show_login_page
        show_login_page() # Panggil halaman login untuk menangani autentikasi
        end_main_time_login = time.time()
        elapsed_main_time_login = end_main_time_login - start_main_time
        logging.info(f"MAIN: Login page rendered/rerun in: {elapsed_main_time_login:.2f} seconds")
        return # PENTING: Hentikan eksekusi jika belum login
            
    current_page_id = st.query_params.get("page", "overview")

    if st.session_state.last_loaded_page != current_page_id:
        st.session_state.is_initial_page_load = True 
        st.session_state.last_loaded_page = current_page_id
    else:
        st.session_state.is_initial_page_load = False 
        
    create_sidebar() # Sidebar dibuat hanya jika user sudah login

    try:
        if current_page_id == 'overview':
            from src.pages import overview
            importlib.reload(overview)
            overview.show()
        elif current_page_id == 'transportation':
            from src.pages import transportation
            importlib.reload(transportation)
            transportation.show()
        elif current_page_id == 'electronic':
            from src.pages import electronic
            importlib.reload(electronic)
            electronic.show()
        elif current_page_id == 'sampah':
            from src.pages import food_drink_waste
            importlib.reload(food_drink_waste)
            food_drink_waste.show()
        elif current_page_id == 'about':
            from src.pages import about
            importlib.reload(about)
            about.show()
        elif current_page_id == 'register':
            if is_admin():
                from src.auth import register
                importlib.reload(register)
                register.show()
            else:
                st.error("Akses ditolak!")
                st.query_params["page"] = "overview"
                time.sleep(1)
                st.rerun()
        else:
            st.warning("Halaman tidak ditemukan. Mengalihkan ke Dashboard Utama.")
            st.query_params["page"] = "overview"
            st.rerun()

    except ImportError as e:
        st.error(f"Error mengimport page '{current_page_id}': {e}")
        st.write("Periksa struktur folder dan nama file.")

    end_main_time = time.time()
    elapsed_main_time = end_main_time - start_main_time
    logging.info(f"MAIN: Total script execution for '{current_page_id}' rerun: {elapsed_main_time:.2f} seconds")

if __name__ == "__main__":
    main()