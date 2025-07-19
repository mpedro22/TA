# src/auth/auth.py

import streamlit as st
from supabase import Client # Pastikan Client diimpor
from typing import Dict, Optional

# Impor fungsi init_supabase_connection untuk mendapatkan client Supabase
from src.utils.db_connector import init_supabase_connection

# Objek supabase client tidak lagi diimpor global.
# Ini akan didapatkan secara on-demand melalui init_supabase_connection()

def authenticate(email: str, password: str) -> Optional[Dict]:
    """
    Mengautentikasi pengguna menggunakan Supabase Auth (email/password).
    """
    # Dapatkan objek client Supabase (dari cache atau inisialisasi baru)
    local_supabase_client = init_supabase_connection()
    if local_supabase_client is None: 
        st.error("Sistem tidak terhubung ke Supabase. Autentikasi tidak dapat dilakukan.")
        return None
    
    try:
        response = local_supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        
        if response.user and response.session:
            st.session_state.supabase_session = response.session 
            st.session_state.supabase_user = response.user      
            st.session_state.user_metadata = response.user.user_metadata 
            return response.user.user_metadata
        else:
            st.error("Autentikasi gagal: Respons Supabase tidak lengkap atau user/sesi tidak ditemukan.")
            return None
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        st.error(f"Autentikasi gagal: {error_message}")
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("supabase_user", None)
        st.session_state.pop("user_metadata", None)
        return None

def create_user(email: str, password: str, is_admin: bool = False, username: Optional[str] = None) -> bool:
    """
    Mendaftarkan pengguna baru via Supabase Auth.
    """
    local_supabase_client = init_supabase_connection()
    if local_supabase_client is None: 
        st.error("Sistem tidak terhubung ke Supabase. Pendaftaran gagal.")
        return False
    try:
        user_metadata = {"is_admin": is_admin}
        if username:
            user_metadata["username"] = username
        
        response = local_supabase_client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": user_metadata 
            }
        })
        
        if response.user:
            print(f"Pengguna '{email}' berhasil didaftarkan di Supabase. User ID: {response.user.id}")
            return True
        return False
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        st.error(f"Gagal mendaftarkan pengguna: {error_message}")
        return False

def is_logged_in() -> bool:
    """Mengecek apakah pengguna sedang login berdasarkan sesi Supabase di st.session_state."""
    # is_logged_in tidak membutuhkan objek supabase client secara langsung
    return st.session_state.get("supabase_session") is not None

def is_admin() -> bool:
    """Mengecek apakah pengguna yang sedang login memiliki peran admin dari metadata."""
    # is_admin tidak membutuhkan objek supabase client secara langsung
    if not is_logged_in():
        return False
    user_metadata = st.session_state.get("user_metadata", {}) 
    return user_metadata.get("is_admin", False)

def get_current_user() -> Optional[Dict]:
    """Mengembalikan metadata pengguna yang sedang login."""
    # get_current_user tidak membutuhkan objek supabase client secara langsung
    if is_logged_in():
        return st.session_state.get("user_metadata")
    return None

def logout():
    """Melakukan logout pengguna dari Supabase dan membersihkan state terkait."""
    local_supabase_client = init_supabase_connection()
    if local_supabase_client is None: 
        st.error("Sistem tidak terhubung ke Supabase. Logout gagal.")
        return
    try:
        local_supabase_client.auth.sign_out()
        keys_to_clear = ["supabase_session", "supabase_user", "user_metadata"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.query_params.clear() 
        print("Logout berhasil dari Supabase.")
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        st.error(f"Gagal logout: {error_message}")