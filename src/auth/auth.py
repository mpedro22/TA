# src/auth/auth.py

import streamlit as st
from supabase import create_client, Client
import os
from typing import Dict, Optional
from dotenv import load_dotenv # Tetap impor untuk kompatibilitas lokal via .env

# load_dotenv() # Hapus atau komentari ini jika Anda tidak ingin memuat dari .env di awal
              # Jika Anda tetap ingin ini untuk development lokal dengan .env saja, biarkan.
              # Tapi untuk Streamlit Cloud, ini tidak relevan.

SUPABASE_URL: Optional[str] = None
SUPABASE_KEY: Optional[str] = None

# Prioritaskan mengambil dari st.secrets (untuk Streamlit Cloud dan secrets.toml lokal)
# Jika tidak ada di st.secrets, coba dari environment variables (untuk lokal dengan .env saja)
try:
    if "supabase" in st.secrets:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
except AttributeError:
    # st.secrets mungkin tidak tersedia jika dijalankan di luar Streamlit environment
    # Fallback ke os.getenv() jika st.secrets tidak ada atau tidak memiliki 'supabase'
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
except KeyError:
    # Jika st.secrets["supabase"] ada tapi isinya tidak lengkap
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    

if not SUPABASE_URL or not SUPABASE_KEY:
    supabase: Optional[Client] = None
    # Ganti pesan error agar lebih jelas asal masalahnya
    st.error("Dashboard tidak dapat beroperasi. Kredensial Supabase (URL/KEY) tidak ditemukan.")
    st.error("Pastikan Anda sudah mengonfigurasi `secrets.toml` di folder `.streamlit/` Anda (lokal) atau di Streamlit Cloud Dashboard (deployment).")
    # Tidak perlu st.stop() di sini, karena error akan ditangani di main.py
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase: Optional[Client] = None
        st.error(f"ERROR: Gagal menginisialisasi klien Supabase dengan kredensial yang ditemukan: {e}.")
        st.error("Periksa format URL/KEY Supabase Anda atau status database.")