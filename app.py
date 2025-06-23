import streamlit as st
from auth import is_logged_in, is_admin, get_current_user, logout, load_users
import time

# Page config
st.set_page_config(
    page_title="ITB Carbon Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
)

with open("style.css", encoding="utf-8") as f:
    css_content = f.read()
    st.markdown(f"""
    <style>
    /* Timestamp: {time.time()} */
    {css_content}
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    with st.sidebar:
        current_user = get_current_user()
        if current_user:
            user_indicator = "Halo, Admin!" if is_admin() else f"Halo, {current_user['username']}!"
            st.markdown(f"""<div style="font-size: 1rem; font-weight: 750; color: #059669; margin-top: -2.5rem; font-family: 'Poppins', sans-serif; padding-left: 0.5rem;">{user_indicator}</div>""", unsafe_allow_html=True)
        
        st.markdown("""<div class="sidebar-header"><div class="logo-wrapper"><div class="logo-container"><div class="logo-circle"><span class="logo-text"><span class="logo-text-main">ITB</span><span class="logo-text-sub">CARBON DASHBOARD</span></span></div></div></div><h2 class="sidebar-title">Kampus Ganesha</h2></div>""", unsafe_allow_html=True)
        st.markdown('<div class="nav-menu">', unsafe_allow_html=True)

        menu_items = [
            ("", "Dashboard Utama", "overview"),
            ("", "Transportasi", "transportation"),
            ("", "Elektronik", "electronic"),
            ("", "Sampah", "sampah"),
            ("", "Tentang Dashboard", "about")
        ]
        
        current_page_from_url = st.query_params.get('page', 'overview')

        for icon, label, page_id in menu_items:
            is_active = current_page_from_url == page_id
            st.markdown('<div class="nav-item-wrapper">', unsafe_allow_html=True)
            if is_active:
                st.markdown(f'<div class="nav-item-active">{label}</div>', unsafe_allow_html=True)
            else:
                if st.button(f"{label}", key=f"nav_{page_id}", use_container_width=True):
                    st.query_params["page"] = page_id
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="flex-grow: 1; min-height: 2rem;"></div>', unsafe_allow_html=True)

        if is_admin():
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Tambah Akun", key="sidebar_add_account", use_container_width=True):
                    st.query_params['page'] = 'register'
                    st.rerun()
            with col2:
                if st.button("Keluar", key="sidebar_logout_admin", use_container_width=True):
                    logout()
                    st.rerun()
        else:
            if st.button("Keluar", key="sidebar_logout_user", use_container_width=True):
                logout()
                st.rerun()

def main():
    # === LOGIKA OTENTIKASI FINAL ===

    # 1. Jika pengguna belum login (tidak ada flag di URL), tampilkan halaman login.
    if st.query_params.get("logged_in") != "true":
        import login
        login.show()
        return

    # 2. Jika flag login ada, tapi sesi di server kosong (terjadi saat refresh),
    #    maka "hidrasi" atau buat ulang sesi dari URL.
    if not is_logged_in():
        username_from_url = st.query_params.get("user")
        if username_from_url:
            all_users = load_users()
            user_data = all_users.get(username_from_url)
            
            if user_data:
                # Berhasil menemukan data user, pulihkan sesi
                st.session_state.user = user_data
                # Paksa rerun agar seluruh UI digambar dengan sesi yang sudah pulih
                st.rerun()
                return 
            else:
                # User di URL tidak valid, paksa logout
                st.error("Sesi tidak valid. Harap login kembali.")
                logout()
                st.rerun()
                return
        else:
            # Flag login ada tapi username tidak, paksa logout
            st.error("Sesi tidak valid. Harap login kembali.")
            logout()
            st.rerun()
            return
            
    # 3. Jika kode sampai di sini, sesi dijamin valid dan sudah siap.
    #    Lanjutkan untuk menggambar UI.
    page = st.query_params.get("page", "overview")

    if page != 'register':
        create_sidebar()

    # Routing Halaman
    if page == 'overview':
        import overview
        overview.show()
    elif page == 'transportation':
        import transportation
        transportation.show()
    elif page == 'electronic':
        import electronic
        electronic.show()
    elif page == 'sampah':
        import food_drink_waste
        food_drink_waste.show()
    elif page == 'about':
        import about
        about.show()
    elif page == 'register':
        if is_admin():
            import register
            register.show()
        else:
            st.error("Akses ditolak!")
            st.query_params["page"] = "overview"
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    main()