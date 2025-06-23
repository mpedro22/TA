# login.py

import streamlit as st
from auth import authenticate
import time

def show():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="
            border-radius: 16px;
            padding: 2.5rem;
            margin-top: 0rem;
        ">
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-header" style="border-bottom: none;">
            <div class="logo-wrapper">
                <div class="logo-particles">
                    <span class="particle" style="top: 10%; left: 10%; animation-delay: 0s;"></span>
                    <span class="particle" style="top: 20%; right: 15%; animation-delay: 0.5s;"></span>
                    <span class="particle" style="bottom: 20%; left: 20%; animation-delay: 1s;"></span>
                    <span class="particle" style="bottom: 10%; right: 10%; animation-delay: 1.5s;"></span>
                </div>
                <div class="logo-container" style="margin-top: 0;">
                    <div class="logo-ring"></div>
                    <div class="logo-circle">
                        <span class="logo-text">
                            <span class="logo-text-main">ITB</span>
                            <span class="logo-text-sub">CARBON DASHBOARD</span>
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 0rem;'></div>", unsafe_allow_html=True)

        st.markdown("""
        <h2 style="
            text-align: center;
            color: #333;
            margin-top: 1rem;
            margin-bottom: 2rem;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
        ">Masuk</h2>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username_input = st.text_input("Username / Email", placeholder="Masukkan username atau email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Masuk", use_container_width=True, type="primary")

        if submit:
            if username_input and password:
                user = authenticate(username_input, password)
                if user:
                    st.session_state.user = user
                    
                    # --- PERUBAHAN PENTING ---
                    # Tambahkan username ke URL
                    st.query_params.update({
                        "page": "overview",
                        "logged_in": "true",
                        "user": user['username'] # <-- BARIS KUNCI
                    })
                    
                    st.success(f"Selamat datang, {user['username']}!")
                    time.sleep(1)
                    st.rerun() 
                else:
                    st.error("Username/email atau password salah!")
            else:
                st.error("Mohon isi semua field!")

        st.markdown("</div>", unsafe_allow_html=True)