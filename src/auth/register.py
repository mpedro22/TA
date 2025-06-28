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

    # MENGGUNAKAN CSS YANG SAMA DENGAN HALAMAN LOGIN
    st.markdown("""
    <style>
    /* Hide sidebar completely on this page */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
    }
    .main .block-container {
        margin-left: 0 !important;
        padding-left: 1rem !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Background hijau lembut untuk seluruh halaman */
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }

    header { visibility: hidden; display: none; }
    
    /* HILANGKAN IKON COPY, LINK, DAN TOOLTIP */
    button[title*="Copy"], 
    [data-testid="stCopyButton"], 
    .stMarkdown a[href^="#"],
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    
    /* Wrapper untuk menata elemen secara vertikal di tengah */
    .form-content-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 3rem; /* Beri sedikit jarak dari atas */
    }
    
    /* MENATA st.form MENJADI KARTU PUTIH (SAMA SEPERTI LOGIN) */
    [data-testid="stForm"] {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0,0,0,0.06);
        animation: fadeIn 0.7s ease-out;
        width: 100%; /* Form mengisi lebar kolom tengah */
        /* max-width: 420px; Dihapus agar form mengisi kolom tengah */
    }

    /* Judul di dalam form */
    [data-testid="stForm"] h3 {
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.5rem;
        color: #374151;
        margin-top: -1rem;
        margin-bottom: 1.5rem; 
    }
    
    /* Styling Input Field (SAMA SEPERTI LOGIN) */
    .stTextInput > label {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 0.85rem !important;
        font-family: 'Poppins', sans-serif !important;
        margin-bottom: 0.3rem !important;
    }
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
        background-color: #f9fafb !important;
        transition: all 0.2s ease-in-out;
        font-family: 'Poppins', sans-serif !important;
        height: 42px;
    }
    .stTextInput input:focus {
        border-color: #059669 !important;
        background-color: white !important;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15) !important;
        outline: none !important;
    }

    /* Kontainer untuk dua tombol */
    .button-container {
        display: flex;
        gap: 0.75rem; /* Jarak antar tombol */
        margin-top: 1.5rem;
    }

    /* Styling Tombol (SAMA SEPERTI LOGIN & FORM LAINNYA) */
    .stForm button[type="submit"] {
        border-radius: 8px;
        padding: 0.8rem;
        font-weight: 600;
        font-size: 1rem;
        font-family: 'Poppins', sans-serif !important;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        border: none;
    }
    
    .stForm button[type="submit"]:hover {
        transform: translateY(-2px);
    }
    
    /* Tombol Primary (Tambahkan) */
    .stForm button[type="submit"][kind="primary"] {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
    }
    .stForm button[type="submit"][kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
    }

    /* Tombol Secondary (Kembali) */
    .stForm button[type="submit"]:not([kind="primary"]) {
        background-color: #f3f4f6 !important;
        color: #4b5563 !important;
        border: 1px solid #e5e7eb !important;
    }
    .stForm button[type="submit"]:not([kind="primary"]):hover {
        background-color: #e5e7eb !important;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Menggunakan st.columns untuk memusatkan seluruh konten (SAMA SEPERTI LOGIN)
    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        st.markdown('<div class="form-content-wrapper">', unsafe_allow_html=True)

        # Form Pendaftaran dengan style baru
        with st.form("register_form"):
            st.markdown("<h3>Tambah Akun Baru</h3>", unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Masukkan username baru")
            email = st.text_input("Email", placeholder="Masukkan email pengguna")
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")

            # Layout tombol di dalam kontainer custom
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                back_clicked = st.form_submit_button("Kembali", use_container_width=True)
            with btn_col2:
                submit_clicked = st.form_submit_button("Tambahkan", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

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