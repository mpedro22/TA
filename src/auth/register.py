import streamlit as st
from src.auth.auth import create_user, is_admin
import time

from src.components.loading import loading

def show():
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        st.query_params["page"] = "overview" 
        time.sleep(1.5)
        st.rerun()
        return

    with loading():
        st.markdown("""
        <div class="wow-header">
            <div class="header-bg-pattern"></div>
            <div class="header-float-1"></div>
            <div class="header-float-2"></div>
            <div class="header-float-3"></div>
            <div class="header-float-4"></div>  
            <div class="header-float-5"></div>              
            <div class="header-content">
                <h1 class="header-title">Tambah Akun Baru</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.25)

    st.markdown("""
    <style>
        /* Mengatur agar form di tengah */
        .st-emotion-cache-r421ms {
            display: flex;
            justify-content: center;
        }

        /* Menargetkan kontainer form */
        div[data-testid="stForm"] {
            width: 100%;
            max-width: 700px; /* Lebar form disesuaikan agar tidak terlalu lebar */
            background: white !important;
            border-radius: 20px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0,0,0,0.06);
            padding: 2.5rem;
            margin: 0 auto;
        }

        div[data-testid="stForm"] > form {
            padding: 0 !important;
        }

        /* Styling Judul di dalam form */
        div[data-testid="stForm"] h3 {
            text-align: center;
            color: #1e293b;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 1.6rem;
            margin-top: -1rem;
            margin-bottom: 2rem;
        }

        /* Menghilangkan tooltip "Press Enter to submit" */
        [data-testid="InputInstructions"] {
            display: none !important;
        }

        /* Merapatkan ikon password */
        div[data-testid="stTextInput"] [data-baseweb="input"] > div {
            padding-right: -3rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        with st.form("register_form", clear_on_submit=True):
            st.markdown(
                "<h3>Silahkan Mengisi Form Berikut</h3>",
                unsafe_allow_html=True
            )
            
            username = st.text_input("Username (opsional)", placeholder="Contoh: koped")
            email = st.text_input("Email", placeholder="Contoh: nama@example.com")
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
            
            is_new_admin = st.checkbox("Jadikan akun ini Admin?", value=False, key="make_admin_checkbox")


            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                back_clicked = st.form_submit_button("Kembali", use_container_width=True)
            with btn_col2:
                submit_clicked = st.form_submit_button("Tambahkan", use_container_width=True, type="primary")

    if back_clicked:
        st.query_params["page"] = "overview"
        st.rerun()

    if submit_clicked:
        if not all([email, password, confirm_password]): 
            st.error("Mohon isi Email, Password, dan Konfirmasi Password!")
        elif password != confirm_password:
            st.error("Password dan konfirmasi password tidak cocok!")
        elif len(password) < 6:
            st.error("Password minimal harus 6 karakter!")
        else:
            success = create_user(email, password, is_admin=is_new_admin, username=username if username.strip() else None)
            if success:
                st.success(f"Akun '{email}' berhasil dibuat! Mengalihkan...")
                time.sleep(2)
                st.query_params["page"] = "overview"
                st.rerun() 
            else:
                pass
        time.sleep(0.15)