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

from src.auth.auth import is_logged_in, get_current_user, is_admin, logout, supabase 

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
            st.markdown(f'<style>/* Cache Buster: {time.time()} */\n{css_content}</style>', unsafe_allow_html=True)
    else:
        st.error("Error: style.css not found!")

    if supabase is None:
        st.error("Dashboard tidak dapat beroperasi. Gagal menginisialisasi koneksi ke Supabase. Periksa konfigurasi .env Anda.")
        return 
    
    # --- START REHYDRATION LOGIC (MOVED UP) ---
    # Attempt to rehydrate Supabase session from client storage on every rerun
    # This is crucial for staying logged in after a page refresh/reload
    if supabase: # Only attempt if supabase client is initialized
        try:
            current_session = supabase.auth.get_session() # This reads from localStorage
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
        from src.auth.login import show as show_login_page 
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