import streamlit as st
from supabase import create_client, Client
import os
from typing import Dict, Optional

# Perbaikan: Hapus dotenv untuk Streamlit Cloud
# from dotenv import load_dotenv
# load_dotenv()

# Perbaikan: Gunakan st.secrets dengan benar
try:
    # Untuk Streamlit Cloud
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError:
    # Fallback untuk development local
    try:
        from dotenv import load_dotenv
        load_dotenv()
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    except ImportError:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    supabase: Optional[Client] = None
    st.error("ERROR: SUPABASE_URL atau SUPABASE_KEY tidak ditemukan. Pastikan secrets sudah dikonfigurasi.")
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase: Optional[Client] = None
        st.error(f"ERROR: Gagal menginisialisasi klien Supabase: {e}. Pastikan URL dan KEY benar.")

def authenticate(email: str, password: str) -> Optional[Dict]:
    """
    Mengautentikasi pengguna menggunakan Supabase Auth (email/password).
    Menyimpan sesi dan objek pengguna Supabase di st.session_state.
    Mengembalikan metadata pengguna jika autentikasi berhasil.
    """
    if not supabase:
        st.error("Sistem tidak terhubung ke Supabase. Periksa konfigurasi.")
        return None
    try:
        response = supabase.auth.sign_in_with_password({
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
    Peran admin dan username (opsional) disimpan di user_metadata.
    """
    if not supabase:
        st.error("Sistem tidak terhubung ke Supabase. Pendaftaran gagal.")
        return False
    try:
        user_metadata = {"is_admin": is_admin}
        if username:
            user_metadata["username"] = username
        
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": user_metadata 
            }
        })
        
        if response.user:
            st.success(f"Pengguna '{email}' berhasil didaftarkan di Supabase. User ID: {response.user.id}")
            return True
        return False
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        st.error(f"Gagal mendaftarkan pengguna: {error_message}")
        return False

def is_logged_in() -> bool:
    """Mengecek apakah pengguna sedang login berdasarkan sesi Supabase di st.session_state."""
    return st.session_state.get("supabase_session") is not None

def is_admin() -> bool:
    """Mengecek apakah pengguna yang sedang login memiliki peran admin dari metadata."""
    if not is_logged_in():
        return False
    user_metadata = st.session_state.get("user_metadata", {}) 
    return user_metadata.get("is_admin", False)

def get_current_user() -> Optional[Dict]:
    """Mengembalikan metadata pengguna yang sedang login."""
    if is_logged_in():
        return st.session_state.get("user_metadata")
    return None

def logout():
    """Melakukan logout pengguna dari Supabase dan membersihkan state terkait."""
    if not supabase:
        st.error("Sistem tidak terhubung ke Supabase. Logout gagal.")
        return
    try:
        supabase.auth.sign_out()
        keys_to_clear = ["supabase_session", "supabase_user", "user_metadata"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.query_params.clear() 
        st.success("Logout berhasil dari Supabase.")
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        st.error(f"Gagal logout: {error_message}")