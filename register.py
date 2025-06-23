# register.py

import streamlit as st
from auth import create_user, is_admin
import time

def show():
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="padding: 2.5rem; margin-top: 2rem;">', unsafe_allow_html=True)

        with st.form("register_form"):
            email = st.text_input("Email", placeholder="Masukkan email")
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Konfirmasi password")
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                back = st.form_submit_button("Kembali", use_container_width=True)
            with col_btn2:
                submit = st.form_submit_button("Tambah Akun", use_container_width=True, type="primary")

        if back:
            # Sederhana: cukup kembali ke halaman overview.
            # Flag 'logged_in=true' sudah ada di URL.
            st.query_params["page"] = "overview"
            st.rerun()

        if submit:
            if username and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Password dan konfirmasi password tidak sama!")
                elif len(password) < 6:
                    st.error("Password minimal 6 karakter!")
                else:
                    if create_user(email, username, password):
                        st.success(f"Akun {username} berhasil dibuat!")
                        time.sleep(1)
                        # Kembali ke overview setelah berhasil
                        st.query_params["page"] = "overview"
                        st.rerun()
                    else:
                        st.error("Username atau email sudah digunakan!")
            else:
                st.error("Mohon isi semua field!")

        st.markdown("</div>", unsafe_allow_html=True)