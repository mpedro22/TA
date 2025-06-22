import streamlit as st
from auth import create_user, is_admin
import time

def show():
    # Check if user is admin
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        return
    
    st.markdown("""
    <div class="wow-header">
        <div class="header-bg-pattern"></div>
        <div class="header-float-1"></div>
        <div class="header-float-2"></div>
        <div class="header-float-3"></div>
        <div class="header-float-4"></div>  
        <div class="header-float-5"></div>              
        <div class="header-content">
            <h1 class="header-title">Tambah Akun</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the register form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 2.5rem;
            margin-top: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        ">
        """, unsafe_allow_html=True)
        
        # Logo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem auto;
                box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2);
            ">
                <span style="color: white; font-size: 1.5rem; font-weight: 700; font-family: 'Poppins', sans-serif;">ITB</span>
            </div>
            <h2 style="color: #1f2937; font-family: 'Poppins', sans-serif; margin: 0; font-size: 1.5rem;">Tambah Akun Baru</h2>
            <p style="color: #6b7280; font-family: 'Poppins', sans-serif; font-size: 0.875rem; margin-top: 0.25rem;">Hanya untuk Admin</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Register form
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Masukkan username")
            email = st.text_input("Email", placeholder="Masukkan email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Konfirmasi password")
            
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                back = st.form_submit_button("Kembali", use_container_width=True)
            with col_btn2:
                submit = st.form_submit_button("Tambah Akun", use_container_width=True, type="primary")
        
        if back:
            st.session_state.current_page = "overview"
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
                        st.session_state.current_page = "overview"
                        st.rerun()
                    else:
                        st.error("Username atau email sudah digunakan!")
            else:
                st.error("Mohon isi semua field!")
        
        st.markdown("</div>", unsafe_allow_html=True)