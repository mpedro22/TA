# login.py
import streamlit as st
from auth import authenticate
import time

def show():
    # CSS untuk design login sesuai Figma
    st.markdown("""
    <style>
        /* CLEAN LOGIN BACKGROUND */
        .login-container {
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
        
        /* Login Form - Integrated white container */
        .login-form {
            background: #ffffff !important;
            border: 1px solid rgba(229, 231, 235, 0.6) !important;
            border-radius: 20px !important;
            padding: 2rem 2.5rem !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
            position: relative !important;
            z-index: 10 !important;
            margin: 0 auto !important;
            animation: slideInUp 0.6s ease-out !important;
            max-width: 400px !important;
            margin-top: -1rem !important;
        }
        
        .form-title {
            text-align: center !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 1.5rem !important;
            margin-top: 0rem !important;
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Logo styling - Outside form */
        .login-logo {
            text-align: center !important;
            margin-bottom: 1rem !important;
            margin-top: 1rem !important;
        }
        
        .login-logo .logo-circle {
            width: 100px !important;
            height: 100px !important;
            margin: 0 auto !important;
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 12px 30px rgba(5, 150, 105, 0.3) !important;
        }
        
        .login-logo .logo-text {
            color: white !important;
            font-family: 'Poppins', sans-serif !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            line-height: 0.8 !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
        }
        
        .login-logo .logo-text-main {
            font-size: 1.6rem !important;
            font-weight: 900 !important;
        }
        
        .login-logo .logo-text-sub {
            font-size: 0.5rem !important;
            font-weight: 700 !important;
            white-space: nowrap !important;
        }
        
        /* Welcome message - Between logo and form */
        .welcome-message {
            text-align: center !important;
            margin-bottom: 1.5rem !important;
            margin-top: 1rem !important;
        }
        
        .welcome-title {
            font-size: 2rem !important;
            font-weight: 800 !important;
            color: #1e293b !important;
            font-family: 'Poppins', sans-serif !important;
            margin-bottom: 0rem !important;
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
        
        /* Submit Button */
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
        
        /* Responsive */
        @media (max-width: 768px) {
            .login-form {
                padding: 1.5rem !important;
                margin: 1rem !important;
                max-width: 95% !important;
            }
            
            .welcome-title {
                font-size: 1.8rem !important;
            }
            
            .form-title {
                font-size: 1.4rem !important;
            }
            
            .login-logo .logo-circle {
                width: 80px !important;
                height: 80px !important;
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
    st.markdown('<div class="login-container"></div>', unsafe_allow_html=True)

    # Main container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo at the top
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
        
        # Welcome message
        st.markdown("""
        <div class="welcome-message">
            <h1 class="welcome-title">Selamat Datang!</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form container - ALL FORM CONTENT INSIDE
        st.markdown('<div class="login-form">', unsafe_allow_html=True)
        
        # Form title
        st.markdown('<h2 class="form-title">Masuk</h2>', unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Masukkan username atau email")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Masuk", use_container_width=True, type="primary")

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
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 0.9rem; font-family: 'Poppins', sans-serif;">
                ITB Carbon Dashboard - Kampus Ganesha
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # CLOSE the form container
        st.markdown('</div>', unsafe_allow_html=True)