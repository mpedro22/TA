# src/auth/login.py

import streamlit as st
# Hapus 'supabase' dari impor ini
from src.auth.auth import authenticate 
import time

# Impor init_supabase_connection untuk melakukan pengecekan di halaman login saja
from src.utils.db_connector import init_supabase_connection

def show():
    # Lakukan pengecekan koneksi di sini agar pesan muncul sebelum form login
    # init_supabase_connection() akan memicu st.error dan st.stop() jika ada masalah
    local_supabase_client = init_supabase_connection()
    if local_supabase_client is None:
        # Pesan error sudah ditangani oleh init_supabase_connection() di db_connector.py
        # dan sudah st.stop(), jadi kode di bawah ini seharusnya tidak dieksekusi.
        # Namun, ini sebagai fallback keamanan.
        st.error("Dashboard tidak dapat beroperasi. Gagal menginisialisasi koneksi ke Supabase.")
        return

    st.markdown("""
    <style>
    /* Hide sidebar completely on login page */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }
    
    /* Make main content full width on login */
    .main .block-container {
        margin-left: 0 !important;
        padding-left: 1rem !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Mengatur background hijau lembut untuk seluruh halaman */
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }

    /* Sembunyikan header bawaan Streamlit */
    header { visibility: hidden; display: none; }
    
    button[title*="Copy"], 
    [data-testid="stCopyButton"], 
    .stMarkdown a[href^="#"],
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    
    /* Wrapper di dalam kolom tengah untuk menata elemen secara vertikal */
    .login-content {
        display: flex;
        flex-direction: column;
        align-items: center; /* Memusatkan semua konten */
    }
    
    /* Styling untuk Logo */
    .login-logo {
        margin-top: 1rem; /* Jarak dari atas DIKURANGI */
        margin-bottom: 1.5rem;
        animation: fadeIn 0.5s ease-out;
    }
    .login-logo .logo-circle {
        width: 80px; height: 80px;
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        border-radius: 50%;
        box-shadow: 0 10px 25px rgba(5, 150, 105, 0.2);
    }
    .login-logo .logo-text {
        color: white; font-family: 'Poppins', sans-serif;
        display: flex; flex-direction: column; align-items: center;
        line-height: 0.85; text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .login-logo .logo-text-main { font-size: 1.6rem; font-weight: 800; }
    .login-logo .logo-text-sub {
        font-size: 0.4rem; font-weight: 600; white-space: nowrap;
        letter-spacing: 0.05em; text-transform: uppercase;
    }
    
    /* Styling Teks Sambutan (DIKECILKAN) */
    .welcome-text {
        text-align: center;
        margin-bottom: 1.5rem; /* Jarak ke form DIKURANGI */
        animation: fadeIn 0.7s ease-out;
    }
    .welcome-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.5rem;
        font-weight: 620;
        color: #1e293b;
    }
    .welcome-subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: 0.5rem; /* Ukuran font DIKECILKAN */
        color: #64748b;
        margin-top: 0.5rem;
    }

    [data-testid="stForm"] {
        background: white;
        padding: 2.5rem;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0,0,0,0.06);
        animation: fadeIn 0.9s ease-out;
    }

    /* Judul "Masuk" di dalam form (DI RAPATKAN) */
    [data-testid="stForm"] h3 {
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #374151;
        margin-top: -1.5rem;
        margin-bottom: 0.5rem; /* Jarak ke input DIKURANGI */
    }
    
    /* Styling Input Field */
    .stTextInput > label {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 1rem !important;
        font-family: 'Poppins', sans-serif !important;
        margin-bottom: 0.3rem !important;
    }
    .stTextInput > div > div > input {
        transition: all 0.2s ease-in-out;
        font-family: 'Poppins', sans-serif !important;
        height: 40px;
    }
    .stTextInput input:focus {
        background-color: white !important;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15) !important;
    }

    /* Styling Tombol Masuk (DI RAPATKAN) */
    .stForm button[type="submit"] {
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 1rem; /* Jarak dari input password DIKURANGI */
        font-weight: 600;
        font-size: 2rem;
        font-family: 'Poppins', sans-serif !important;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .stForm button[type="submit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.5, 1])

    with center_col:
        st.markdown('<div class="login-content">', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="login-logo">
            <div class="logo-circle">
                <div class="logo-text">
                    <div class="logo-text-main">ITB</div>
                    <div class="logo-text-sub">CARBON DASHBOARD</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="welcome-text">
            <div class="welcome-title">Selamat Datang, Silahkan Isi Untuk Memasuki Dashboard</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Masukkan email Anda") 
            password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Masuk", use_container_width=True)

        if submit:
            if email and password:
                # Panggil authenticate
                user_metadata = authenticate(email, password) 
                if user_metadata:
                    st.query_params["logged_in"] = "true" 
                    st.query_params["user_email"] = email 
                    st.query_params["page"] = "overview" 
                    st.success("Login berhasil! Mengalihkan...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Login gagal. Periksa kembali email dan password Anda.")
            else:
                st.error("Mohon isi semua field!")

        st.markdown('</div>', unsafe_allow_html=True)