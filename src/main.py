# src/main.py

import streamlit as st
import sys
import os # Tetap import untuk penggunaan lain jika ada, tapi tidak untuk sys.path.append
import time
import importlib
import logging
import requests 
import socket 

# --- HAPUS BARIS INI KARENA INI PENYEBAB ERROR 'ModuleNotFoundError' DI STREAMLIT CLOUD ---
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# --- PENTING: PASTIKAN SEMUA IMPOR BERASAL DARI ROOT PROYEK (misal 'src.utils...') ---
from src.utils.db_connector import init_supabase_connection 
from src.auth.auth import is_logged_in, get_current_user, is_admin, logout 

# Setup logging
logging.basicConfig(level=logging.INFO)

def main():
    # Inisialisasi session state untuk pelacakan halaman
    if 'last_loaded_page' not in st.session_state:
        st.session_state.last_loaded_page = None
    if 'is_initial_page_load' not in st.session_state:
        st.session_state.is_initial_page_load = True 
    if 'is_app_offline' not in st.session_state: 
        st.session_state.is_app_offline = False

    start_main_time = time.time()

    st.set_page_config(
        page_title="ITB Carbon Dashboard", 
        layout="wide", 
        initial_sidebar_state="expanded",
    )

    css_file_path = "assets/css/style.css" # Path ini relatif ke root main.py
    if os.path.exists(css_file_path):
        with open(css_file_path, encoding="utf-8") as f:
            css_content = f.read()
            st.markdown(f'<style>/* Cache Buster: {time.time()} */\n{css_content}</style>', unsafe_allow_html=True)
    else:
        st.error("Error: style.css not found! Pastikan file berada di 'assets/css/style.css'.") # Pesan lebih detail

    # --- Cek Status Offline Global ---
    if st.session_state.is_app_offline:
        render_offline_message()
        st.stop() 

    try:
        init_supabase_connection() 
    except Exception as e:
        st.error(f"Kesalahan Fatal: Aplikasi tidak dapat memulai koneksi ke Supabase. {e}")
        st.stop()
    
    # --- START REHYDRATION LOGIC (FOR AUTH SESSION) ---
    try:
        current_client = init_supabase_connection() 
        if current_client is None: 
            st.error("Sistem tidak dapat memproses sesi login karena koneksi Supabase tidak aktif.")
            st.stop()

        current_session = current_client.auth.get_session() 
        if current_session:
            st.session_state.supabase_session = current_session
            st.session_state.supabase_user = current_session.user
            st.session_state.user_metadata = current_session.user.user_metadata if current_session.user else {}
            if st.session_state.is_app_offline:
                st.session_state.is_app_offline = False
                logging.info("Supabase session re-established. App is back online.")
                st.experimental_rerun() 
        else:
            st.session_state.pop("supabase_session", None)
            st.session_state.pop("supabase_user", None)
            st.session_state.pop("user_metadata", None)
    except Exception as e:
        logging.error(f"Error rehydrating Supabase session: {e}")
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("supabase_user", None)
        st.session_state.pop("user_metadata", None)
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, socket.gaierror)):
            st.session_state.is_app_offline = True
            logging.warning("App set to offline mode due to rehydration network error.")
            st.experimental_rerun() 
    # --- END REHYDRATION LOGIC ---

    # Fungsi untuk menampilkan pesan offline terpusat (didefinisikan setelah cek offline utama)
    def render_offline_message():
        st.empty() 
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
        
        if st.button("Coba Lagi", key="reconnect_button"):
            st.session_state.is_app_offline = False 
            st.experimental_rerun() 

        st.markdown('<style>section[data-testid="stSidebar"] { display: none !important; }</style>', unsafe_allow_html=True)


    # === AUTH LOGIC ===
    if not is_logged_in():
        from src.auth.login import show as show_login_page 
        importlib.reload(show_login_page) # Reload login page on error/re-entry
        show_login_page()
        end_main_time_login = time.time()
        elapsed_main_time_login = end_main_time_login - start_main_time
        logging.info(f"MAIN: Login page rendered/rerun in: {elapsed_main_time_login:.2f} seconds")
        st.stop() 
            
    current_page_id = st.query_params.get("page", "overview")

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