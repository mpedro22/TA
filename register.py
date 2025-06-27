# register.py
import streamlit as st
from auth import create_user, is_admin
import time

def show():
    if not is_admin():
        st.error("Akses ditolak! Hanya admin yang dapat menambah akun baru.")
        return

    # CSS untuk design register sesuai Figma
    st.markdown("""
    <style>
        /* CLEAN REGISTER BACKGROUND */
        .register-container {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%) !important;
            z-index: -1 !important;
        }
        
        /* Main content container override */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
            max-width: none !important;
            min-height: 100vh !important;
        }
        
        /* Register Form - Integrated white container */
        .register-form {
            background: #ffffff !important;
            border: 1px solid rgba(229, 231, 235, 0.6) !important;
            border-radius: 20px !important;
            padding: 2rem 2.5rem !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
            position: relative !important;
            z-index: 10 !important;
            margin: 2rem auto !important;
            animation: slideInUp 0.6s ease-out !important;
            max-width: 450px !important;
        }
        
        .form-title {
            text-align: center !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 1.5rem !important;
            margin-top: 0rem !important;
            font-family: 'Poppins', sans-serif !important;
        }
        
        .register-logo .logo-text {
            color: white !important;
            font-family: 'Poppins', sans-serif !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            line-height: 0.8 !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
        }
        
        /* Form inputs styling - NO RED BORDER */
        .stTextInput > div > div > input {
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            font-family: 'Poppins', sans-serif !important;
            transition: all 0.3s ease !important;
            background: #ffffff !important;
            height: 44px !important;
            box-sizing: border-box !important;
            width: 100% !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #059669 !important;
            box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.1) !important;
            outline: none !important;
            background: #ffffff !important;
        }
        
        .stTextInput > div > div > input:hover {
            border-color: #9ca3af !important;
            background: #ffffff !important;
        }
        
        /* Fix input container */
        .stTextInput > div {
            width: 100% !important;
        }
        
        .stTextInput > div > div {
            width: 100% !important;
        }
        
        .stTextInput > label {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 600 !important;
            color: #374151 !important;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }
        
        /* Button styling */
        .button-row {
            display: flex !important;
            gap: 12px !important;
            margin-top: 1.5rem !important;
        }
        
        .stButton > button[key="back_btn"] {
            background: #f8f9fa !important;
            color: #6c757d !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            font-family: 'Poppins', sans-serif !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            height: 44px !important;
            flex: 1 !important;
            cursor: pointer !important;
        }
        
        .stButton > button[key="back_btn"]:hover {
            background: #e9ecef !important;
            color: #495057 !important;
            border-color: #adb5bd !important;
            transform: translateY(-1px) !important;
        }
        
        .stForm button[type="submit"] {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            font-family: 'Poppins', sans-serif !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            height: 44px !important;
            flex: 1 !important;
            cursor: pointer !important;
        }
        
        .stForm button[type="submit"]:hover {
            background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3) !important;
        }
        
        /* Hide copy buttons */
        .stMarkdown [data-testid="stCopyButton"],
        .stMarkdown button[aria-label*="Copy"],
        .stMarkdown .copy-button,
        [data-testid="copyButton"],
        button[title*="copy" i] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Custom button container */
        .custom-button-container {
            display: flex !important;
            gap: 12px !important;
            margin-top: 1.5rem !important;
            width: 100% !important;
        }
        
        .custom-button-container > div {
            flex: 1 !important;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .register-form {
                padding: 1.5rem !important;
                margin: 1rem !important;
                max-width: 95% !important;
            }
            
            .form-title {
                font-size: 1.5rem !important;
            }
            
            .button-row, .custom-button-container {
                flex-direction: column !important;
                gap: 8px !important;
            }
            
            .main .block-container {
                padding-top: 1rem !important;
            }
        }
        
        /* Animation */
        @keyframes slideInUp {
            from {
                transform: translateY(30px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Background
    st.markdown('<div class="register-container"></div>', unsafe_allow_html=True)

    # Main container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Register form container
        st.markdown('<div class="register-form">', unsafe_allow_html=True)
        
        # Form title
        st.markdown('<h2 class="form-title">Tambah Akun</h2>', unsafe_allow_html=True)
        
        # Register form
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Masukkan username")
            email = st.text_input("Email", placeholder="Masukkan email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Konfirmasi password")
            
            # Custom button layout
            st.markdown('<div class="custom-button-container">', unsafe_allow_html=True)
            
            col_back, col_submit = st.columns(2)
            
            with col_back:
                back_clicked = st.form_submit_button("Kembali", use_container_width=True)
            
            with col_submit:
                submit_clicked = st.form_submit_button("Tambahkan", use_container_width=True, type="primary")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Handle back button
        if back_clicked:
            st.query_params["page"] = "overview"
            st.rerun()

        # Handle form submission
        if submit_clicked:
            if username and email and password and confirm_password:
                if password == confirm_password:
                    if len(password) >= 6:
                        try:
                            success = create_user(email, username, password)
                            if success:
                                st.success(f"Akun '{username}' berhasil dibuat!")
                                time.sleep(2)
                                st.query_params["page"] = "overview"
                                st.rerun()
                            else:
                                st.error("Gagal membuat akun. Username atau email mungkin sudah ada.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.error("Password minimal 6 karakter!")
                else:
                    st.error("Password dan konfirmasi password tidak sama!")
            else:
                st.error("Mohon isi semua field!")
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
                ITB Carbon Dashboard - Kampus Ganesha
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)