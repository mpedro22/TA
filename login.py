# login.py
import streamlit as st
from auth import authenticate
import time

def show():
    # CSS FINAL: LAYOUT RAPAT, PADAT, DAN KONSISTEN
    st.markdown("""
    <style>
        /* Mengatur background hijau lembut untuk seluruh halaman */
        [data-testid="stAppViewContainer"] > .main {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        }

        /* Sembunyikan header bawaan Streamlit */
        header { visibility: hidden; display: none; }
        
        /* HILANGKAN IKON COPY, LINK, DAN TOOLTIP "PRESS ENTER" */
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
            margin-top: 2rem; /* Jarak dari atas DIKURANGI */
            margin-bottom: 1.5rem;
            animation: fadeIn 0.5s ease-out;
        }
        .login-logo .logo-circle {
            width: 80px; height: 80px;
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
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
            font-size: 1.8rem; /* Ukuran font DIKECILKAN */
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        }
        .welcome-subtitle {
            font-family: 'Poppins', sans-serif;
            font-size: 0.9rem; /* Ukuran font DIKECILKAN */
            color: #64748b;
            margin-top: 0.25rem;
        }

        /* MENATA st.form MENJADI KARTU PUTIH */
        [data-testid="stForm"] {
            background: white;
            padding: 2.5rem;
            border-radius: 20px;
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
            margin-top: -4;
            margin-bottom: 0rem; /* Jarak ke input DIKURANGI */
        }
        
        /* Styling Input Field */
        .stTextInput > label {
            font-weight: 600 !important;
            color: #374151 !important;
            font-size: 0.5rem !important;
            font-family: 'Poppins', sans-serif !important;
            margin-bottom: 0.3rem !important;
        }
        .stTextInput > div > div > input {
            border-radius: 8px !important;
            border: 1px solid #d1d5db !important;
            background-color: #f9fafb !important;
            transition: all 0.2s ease-in-out;
            font-family: 'Poppins', sans-serif !important;
            height: 40px;
        }
        /* SOLUSI FINAL UNTUK BORDER MERAH/BIRU */
        .stTextInput input:focus {
            border-color: #059669 !important;
            background-color: white !important;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15) !important;
            outline: none !important;
        }

        /* Styling Tombol Masuk (DI RAPATKAN) */
        .stForm button[type="submit"] {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.8rem;
            margin-top: 1rem; /* Jarak dari input password DIKURANGI */
            font-weight: 600;
            font-size: 1rem;
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

    # Menggunakan st.columns untuk memusatkan seluruh konten secara horizontal
    _, center_col, _ = st.columns([1, 1.5, 1])

    with center_col:
        st.markdown('<div class="login-content">', unsafe_allow_html=True)
        
        # 1. Logo
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
        
        # 2. Teks Sambutan
        st.markdown("""
        <div class="welcome-text">
            <h1 class="welcome-title">Selamat Datang</h1>
        </div>
        """, unsafe_allow_html=True)

        # 3. Form Login
        with st.form("login_form"):
            st.markdown("<h3>Masuk</h3>", unsafe_allow_html=True)
            username = st.text_input("Username atau Email", placeholder="Masukkan username atau email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            submit = st.form_submit_button("Masuk", use_container_width=True)

        if submit:
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.query_params["logged_in"] = "true"
                    st.query_params["user"] = user["username"]
                    st.query_params["page"] = "overview"
                    st.success("Login berhasil! Mengalihkan...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Username/email atau password salah!")
            else:
                st.error("Mohon isi semua field!")

        st.markdown('</div>', unsafe_allow_html=True)