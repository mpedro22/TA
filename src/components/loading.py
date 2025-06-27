import streamlit as st
import time
from contextlib import contextmanager
import functools

@contextmanager
def loading():
    """
    Loading general untuk semua keperluan desktop
    """
    container = st.empty()
    
    container.markdown("""
    <div class="loading-overlay">
        <div class="loading-spinner"></div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        yield
    finally:
        container.empty()

def loading_decorator(func=None):
    """
    Decorator untuk fungsi yang butuh loading
    Bisa dipake dengan atau tanpa kurung:
    @loading_decorator
    @loading_decorator()
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with loading():
                time.sleep(0.05)  # Lebih cepat untuk smoothness
                return f(*args, **kwargs)
        return wrapper
    
    if func is None:
        # Dipanggil dengan kurung: @loading_decorator()
        return decorator
    else:
        # Dipanggil tanpa kurung: @loading_decorator
        return decorator(func)