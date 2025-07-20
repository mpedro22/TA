# src/main.py

import streamlit as st
import sys
import os
import time
import importlib
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Perbaikan: Sesuaikan path import untuk memastikan modul ditemukan
# Menambahkan folder utama proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Perbaikan: Import modul secara terpusat dari src/
try:
    from src.auth.auth import is_logged_in, get_current_user, is_admin, logout
    from src.utils.db_connector import init_supabase_connection # Import fungsi ini
    auth_available = True
except ImportError as e:
    logging.error(f"Initial import error: {e}. Trying fallback path.")
    try:
        # Fallback jika struktur folder atau PYTHONPATH berbeda
        from auth.auth import is_logged_in, get_current_user, is_admin, logout
        from utils.db_connector import init_supabase_connection # Fallback import
        auth_available = True
    except ImportError as e_fallback:
        st.error(f"Error: Tidak dapat mengimport modul auth atau db_connector. Periksa struktur folder dan PYTHONPATH Anda.")
        logging.critical(f"Critical import error: {e_fallback}")
        auth_available = False

def check_supabase_connection():
    """
    Check if Supabase connection is working by attempting to get the client.
    This uses the cached init_supabase_connection function.
    """
    if not auth_available:
        return False # Jika modul dasar tidak bisa diimport, koneksi pasti gagal
    try:
        # Memanggil fungsi init_supabase_connection yang di-cache
        # Ini akan menginisialisasi atau mengambil klien Supabase yang sudah ada
        supabase_client = init_supabase_connection()
        return supabase_client is not None
    except Exception as e:
        # init_supabase_connection sudah menangani st.error dan st.stop()
        # di sini kita hanya log dan kembalikan False jika ada pengecualian
        logging.error(f"Error during check_supabase_connection: {e}")
        return False

def main():
    # Inisialisasi session state untuk pelacakan halaman jika belum ada
    if 'last_loaded_page' not in st.session_state:
        st.session_state.last_loaded_page = None
    if 'is_initial_page_load' not in st.session_state:
        st.session_state.is_initial_page_load = True 

    start_main_time = time.time()

    st.set_page_config(
        page_title="ITB Carbon Dashboard", 
        layout="wide", 
        initial_sidebar_state="expanded",
    )

    # Load CSS
    css_file_path = "assets/css/style.css"
    if os.path.exists(css_file_path):
        with open(css_file_path, encoding="utf-8") as f:
            css_content = f.read()
            # Cache Buster ditambahkan agar CSS selalu di-reload saat aplikasi di-deploy/di-update
            st.markdown(f'<style>/* Cache Buster: {time.time()} */\n{css_content}</style>', unsafe_allow_html=True)
    else:
        st.warning("Warning: style.css not found! Using default styling.")

    # Perbaikan: Pengecekan koneksi Supabase yang lebih robust
    if not auth_available:
        st.error("Dashboard tidak dapat beroperasi. Modul auth atau db_connector tidak dapat diimport.")
        return
    
    # Panggil fungsi check_supabase_connection yang baru
    if not check_supabase_connection():
        # Pesan error sudah ditampilkan oleh check_supabase_connection
        # Tampilkan panduan konfigurasi jika koneksi gagal
        st.write("### 📋 Panduan Konfigurasi Secrets")
        st.write("Di Streamlit Cloud > Settings > Secrets, tambahkan:")
        st.code("""
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
        """)
        return 
    
    # --- START REHYDRATION LOGIC (MOVED UP) ---
    # Attempt to rehydrate Supabase session from client storage on every rerun
    # This is crucial for staying logged in after a page refresh/reload
    
    # Ambil instance Supabase yang sudah diinisialisasi/di-cache
    supabase = None
    try:
        supabase = init_supabase_connection()
    except Exception as e:
        logging.error(f"Could not get Supabase client for rehydration: {e}")
        # Error handling sudah dilakukan di init_supabase_connection, jadi ini fallback log saja.
        
    if supabase: # Hanya lakukan rehidrasi jika klien supabase tersedia
        try:
            current_session = supabase.auth.get_session() # Ini membaca dari localStorage
            if current_session:
                st.session_state.supabase_session = current_session
                st.session_state.supabase_user = current_session.user
                st.session_state.user_metadata = current_session.user.user_metadata if current_session.user else {}
                # logging.info("Supabase session rehydrated from client storage.") # Optional logging
            else:
                # If get_session() returns None, ensure session_state is clear
                st.session_state.pop("supabase_session", None)
                st.session_state.pop("supabase_user", None)
                st.session_state.pop("user_metadata", None)
                # logging.info("No active Supabase session found in client storage after rehydration attempt.") # Optional logging
        except Exception as e:
            # Handle errors during rehydration (e.g., network issues preventing communication with Supabase Auth)
            logging.error(f"Error rehydrating Supabase session: {e}")
            st.session_state.pop("supabase_session", None)
            st.session_state.pop("supabase_user", None)
            st.session_state.pop("user_metadata", None)
    # --- END REHYDRATION LOGIC ---

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

    # === AUTH LOGIC ===
    # This check now relies on the rehydration logic above
    if not is_logged_in():
        try:
            from src.auth.login import show as show_login_page 
        except ImportError:
            from auth.login import show as show_login_page
        show_login_page()
        end_main_time_login = time.time()
        elapsed_main_time_login = end_main_time_login - start_main_time
        logging.info(f"MAIN: Login page rendered/rerun in: {elapsed_main_time_login:.2f} seconds")
        return 
            
    current_page_id = st.query_params.get("page", "overview")

    # Tentukan apakah ini navigasi halaman baru atau rerun filter di halaman yang sama
    if st.session_state.last_loaded_page != current_page_id:
        st.session_state.is_initial_page_load = True 
        st.session_state.last_loaded_page = current_page_id
    else:
        st.session_state.is_initial_page_load = False 
        
    create_sidebar()

    # Perbaikan: Handle import error untuk setiap page
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
        else: # Halaman tidak dikenal, arahkan ke overview
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