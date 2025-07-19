# src/main.py

import streamlit as st
import sys
import os
import time
import importlib
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import supabase client dari db_connector, bukan auth
from src.utils.db_connector import init_supabase_connection # Ini akan memicu inisialisasi supabase client
from src.auth.auth import is_logged_in, get_current_user, is_admin, logout # Hapus supabase dari sini

# Initial check for supabase client, it will be initialized by db_connector import
_initial_supabase_client = init_supabase_connection() 

def main():
    # Inisialisasi session state untuk pelacakan halaman
    if 'last_loaded_page' not in st.session_state:
        st.session_state.last_loaded_page = None
    if 'is_initial_page_load' not in st.session_state:
        st.session_state.is_initial_page_load = True 
    if 'is_app_offline' not in st.session_state: 
        st.session_state.is_app_offline = False # Ini harus direset setiap kali reload browser

    start_main_time = time.time()

    st.set_page_config(
        page_title="ITB Carbon Dashboard", 
        layout="wide", 
        initial_sidebar_state="expanded",
    )

    css_file_path = "assets/css/style.css"
    if os.path.exists(css_file_path):
        with open(css_file_path, encoding="utf-8") as f:
            css_content = f.read()
            st.markdown(f'<style>/* Cache Buster: {time.time()} */\n{css_content}</style>', unsafe_allow_html=True)
    else:
        st.error("Error: style.css not found!")

    # Cek apakah client supabase berhasil diinisialisasi
    if _initial_supabase_client is None:
        st.error("Dashboard tidak dapat beroperasi. Gagal menginisialisasi koneksi ke Supabase. Periksa konfigurasi atau kredensial Anda.")
        st.stop()

    # --- START REHYDRATION LOGIC (FOR AUTH SESSION) ---
    # Attempt to rehydrate Supabase session from client storage on every rerun
    # This is crucial for staying logged in after a page refresh/reload
    try:
        # Panggil get_session() dari objek supabase yang sudah diinisialisasi
        current_session = _initial_supabase_client.auth.get_session() 
        if current_session:
            st.session_state.supabase_session = current_session
            st.session_state.supabase_user = current_session.user
            st.session_state.user_metadata = current_session.user.user_metadata if current_session.user else {}
            # Jika berhasil rehydrate, pastikan flag offline direset
            if st.session_state.is_app_offline:
                st.session_state.is_app_offline = False
                logging.info("Supabase session re-established. App is back online.")
                st.experimental_rerun() # Trigger rerun to clear offline message
        else:
            st.session_state.pop("supabase_session", None)
            st.session_state.pop("supabase_user", None)
            st.session_state.pop("user_metadata", None)
    except Exception as e:
        logging.error(f"Error rehydrating Supabase session: {e}")
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("supabase_user", None)
        st.session_state.pop("user_metadata", None)
        # Jika rehidrasi gagal karena masalah koneksi, set offline flag
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, socket.gaierror)):
            st.session_state.is_app_offline = True
            logging.warning("App set to offline mode due to rehydration network error.")
    # --- END REHYDRATION LOGIC ---

    # Fungsi untuk menampilkan pesan offline terpusat
    def render_offline_message():
        st.empty() # Clear all previous content
        st.markdown("""
            <style>
                .offline-container {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 80vh; 
                    text-align: center;
                    padding: 20px;
                    background-color: #f0fdf4; 
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    margin: 20px;
                }
                .offline-icon {
                    font-size: 3rem;
                    color: #ef4444; 
                    margin-bottom: 15px;
                }
                .offline-title {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 10px;
                }
                .offline-message {
                    font-size: 1rem;
                    color: #4b5563;
                    max-width: 600px;
                }
                .offline-button {
                    margin-top: 20px;
                }
            </style>
            <div class="offline-container">
                <div class="offline-icon">⚠️</div>
                <div class="offline-title">Koneksi Internet Terputus</div>
                <div class="offline-message">
                    Dashboard tidak dapat memuat data karena tidak ada koneksi ke server Supabase. 
                    Mohon periksa koneksi internet Anda atau coba lagi nanti.
                </div>
                <div class="offline-button">
                    <!-- Tombol untuk mencoba kembali -->
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tombol coba lagi
        if st.button("Coba Lagi", key="reconnect_button"):
            st.session_state.is_app_offline = False 
            st.experimental_rerun() 

        # Hapus sidebar saat offline
        st.markdown('<style>section[data-testid="stSidebar"] { display: none !important; }</style>', unsafe_allow_html=True)

    # --- Cek Status Offline Global ---
    if st.session_state.is_app_offline:
        render_offline_message()
        st.stop() # Hentikan eksekusi script lebih awal

    # === AUTH LOGIC ===
    if not is_logged_in():
        from src.auth.login import show as show_login_page 
        show_login_page()
        end_main_time_login = time.time()
        elapsed_main_time_login = end_main_time_login - start_main_time
        logging.info(f"MAIN: Login page rendered/rerun in: {elapsed_main_time_login:.2f} seconds")
        st.stop() 
            
    current_page_id = st.query_params.get("page", "overview")

    # Tentukan apakah ini navigasi halaman baru atau rerun filter di halaman yang sama
    if st.session_state.last_loaded_page != current_page_id:
        st.session_state.is_initial_page_load = True 
        st.session_state.last_loaded_page = current_page_id
    else:
        st.session_state.is_initial_page_load = False 
        
    create_sidebar()

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

    end_main_time = time.time()
    elapsed_main_time = end_main_time - start_main_time
    logging.info(f"MAIN: Total script execution for '{current_page_id}' rerun: {elapsed_main_time:.2f} seconds")


if __name__ == "__main__":
    main()