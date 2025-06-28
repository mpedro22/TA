# register.py
import streamlit as st
from src.auth.auth import create_user, is_admin
import time

def show():
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        st.query_params["page"] = "overview"
        time.sleep(1.5)
        st.rerun()
        return

    # CSS BARU: HANYA UNTUK MENATA FORM, TIDAK MENYEMBUNYIKAN SIDEBAR
    st.markdown("""
    <style>
        /* Kontainer untuk menengahkan form di area konten utama */
        .register-container {
            display: flex;
            justify-content: center;
            align-items: flex-start; /* Rata atas */
            padding-top: 2rem;
        }

        /* Kartu Form Pendaftaran */
        .register-form-card {
            background: white;
            padding: 2rem 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
            border: 1px solid rgba(0,0,0,0.05);
            width: 100%;
            max-width: 500px; /* Lebar maksimum form */
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Judul di dalam form */
        .register-form-card h3 {
            text-align: center;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 1.6rem;
            color: #1e293b;
            margin-top: 0;
            margin-bottom: 1.5rem;
        }

        /* Styling Input Field */
        .register-form-card .stTextInput > label {
            font-weight: 500 !important; /* Sedikit lebih tipis */
            color: #374151 !important;
            font-size: 0.9rem !important;
        }
        .register-form-card .stTextInput input {
            height: 44px;
        }
        
        /* Kontainer untuk dua tombol */
        .register-form-card .button-container {
            display: flex;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header halaman tetap sama seperti halaman lainnya
    st.markdown("""
    <div class="wow-header">
        <div class="header-bg-pattern"></div>
        <div class="header-float-1"></div>
        <div class="header-content">
            <h1 class="header-title">Manajemen Akun</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Layout utama untuk memusatkan form
    st.markdown('<div class="register-container">', unsafe_allow_html=True)
    st.markdown('<div class="register-form-card">', unsafe_allow_html=True)

    with st.form("register_form"):
        st.markdown("<h3>Tambah Akun Baru</h3>", unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Masukkan username baru")
        email = st.text_input("Email", placeholder="Masukkan email pengguna")
        password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
        confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")

        # Layout tombol di dalam kontainer
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            back_clicked = st.form_submit_button("Kembali", use_container_width=True)
        with btn_col2:
            submit_clicked = st.form_submit_button("Tambahkan", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # close .register-form-card
    st.markdown('</div>', unsafe_allow_html=True) # close .register-container

    if back_clicked:
        st.query_params["page"] = "overview"
        st.rerun()

    if submit_clicked:
        if username and email and password and confirm_password:
            if password == confirm_password:
                if len(password) >= 6:
                    success = create_user(email, username, password)
                    if success:
                        st.success(f"Akun '{username}' berhasil dibuat!")
                        time.sleep(2)
                        st.query_params["page"] = "overview"
                        st.rerun()
                    else:
                        st.error("Gagal membuat akun. Username atau email mungkin sudah terdaftar.")
                else:
                    st.error("Password minimal harus 6 karakter!")
            else:
                st.error("Password dan konfirmasi password tidak cocok!")
        else:
            st.error("Mohon isi semua field yang tersedia!")