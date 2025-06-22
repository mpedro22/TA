import streamlit as st
from auth import authenticate
import time

def show():
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 2.5rem;
            margin-top: 4rem;
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
            <h2 style="color: #1f2937; font-family: 'Poppins', sans-serif; margin: 0; font-size: 1.5rem;">Dashboard Emisi Karbon</h2>
            <p style="color: #6b7280; font-family: 'Poppins', sans-serif; font-size: 0.875rem; margin-top: 0.25rem;">Kampus Ganesha</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username / Email", placeholder="Masukkan username atau email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("Masuk", use_container_width=True, type="primary")
        
        if submit:
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    if 'current_page' not in st.session_state:
                        st.session_state.current_page = "overview"
                    st.success(f"Selamat datang, {user['username']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Username/email atau password salah!")
            else:
                st.error("Mohon isi semua field!")
        
        st.markdown("</div>", unsafe_allow_html=True)