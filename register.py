# register.py
import streamlit as st
from auth import create_user, is_admin
import time

def show():
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        return

    # CSS BARU UNTUK DESAIN REGISTER YANG KONSISTEN DENGAN LOGIN
    st.markdown("""
    <style>
        /* Mengatur background hijau untuk seluruh halaman */
        [data-testid="stAppViewContainer"] > .main {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        }

        /* Sembunyikan header bawaan Streamlit */
        header {
            visibility: hidden;
            display: none;
        }

        /* Kontainer utama untuk kartu form putih */
        .form-container {
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
            border: 1px solid rgba(0,0,0,0.05);
            max-width: 450px;
            margin: 3rem auto;
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Header di dalam form (Judul + Subjudul) */
        .form-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .form-title {
            font-family: 'Poppins', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }

        .form-subtitle {
            font-family: 'Poppins', sans-serif;
            font-size: 1rem;
            color: #64748b;
        }

        /* Styling untuk Input Field */
        .stTextInput > label {
            font-weight: 600 !important;
            color: #374151 !important;
            font-size: 0.9rem !important;
            font-family: 'Poppins', sans-serif !important;
        }

        .stTextInput > div > div > input {
            border-radius: 8px !important;
            border: 1px solid #d1d5db !important;
            background-color: #f9fafb !important;
            transition: all 0.2s ease-in-out;
            font-family: 'Poppins', sans-serif !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #059669 !important;
            background-color: white !important;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15) !important;
        }

        /* Kontainer untuk dua tombol */
        .button-container {
            display: flex;
            gap: 0.75rem; /* Jarak antar tombol */
            margin-top: 1.5rem;
        }

        /* Styling Tombol Primary (Tambahkan) */
        .stForm button[type="submit"][kind="primary"] {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            color: white !important;
            border: none !important;
            transition: all 0.2s ease-in-out;
        }

        .stForm button[type="submit"][kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
        }
        
        /* Styling Tombol Secondary (Kembali) */
        .stForm button[type="submit"]:not([kind="primary"]) {
            background-color: white !important;
            color: #4b5563 !important;
            border: 1px solid #d1d5db !important;
        }

        .stForm button[type="submit"]:not([kind="primary"]):hover {
            background-color: #f3f4f6 !important;
            border-color: #9ca3af !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }
        
        /* Universal button styles */
        .stForm button[type="submit"] {
            border-radius: 8px;
            padding: 0.75rem;
            font-weight: 600;
            font-size: 1rem;
            font-family: 'Poppins', sans-serif !important;
            width: 100%;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    # Layout utama untuk memusatkan form
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        st.markdown("""
        <div class="form-header">
            <h1 class="form-title">Tambah Akun Baru</h1>
            <p class="form-subtitle">Isi detail di bawah untuk mendaftarkan pengguna.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Masukkan username baru")
            email = st.text_input("Email", placeholder="Masukkan email pengguna")
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")

            # Spasi sebelum tombol
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            # Layout tombol
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                back_clicked = st.form_submit_button("Kembali", use_container_width=True)
            with btn_col2:
                submit_clicked = st.form_submit_button("Tambahkan", use_container_width=True, type="primary")

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

        st.markdown('</div>', unsafe_allow_html=True)