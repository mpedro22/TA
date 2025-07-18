import streamlit as st
import time
from contextlib import contextmanager
import functools
import logging # Import modul logging

# Setup logging (opsional, bisa juga di main.py atau db_connector.py)
# Jika sudah diinisialisasi di main.py, baris ini bisa dihapus atau dikomentari.
# logging.basicConfig(level=logging.INFO) 

@contextmanager
def loading():
    """
    Loading general untuk semua keperluan desktop.
    Sekarang juga mencatat durasi loading ke terminal.
    """
    start_time = time.time() # Mulai pengukuran waktu
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
        end_time = time.time() # Akhiri pengukuran waktu
        elapsed_time = end_time - start_time
        # Log durasi loading
        logging.info(f"LOADING_SPINNER: Operation took {elapsed_time:.2f} seconds")


def loading_decorator(func=None):
    """
    Decorator untuk fungsi yang butuh loading.
    Bisa dipake dengan atau tanpa kurung:
    @loading_decorator
    @loading_decorator()
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with loading(): # Panggilan ini sekarang akan otomatis memicu log timing
                # time.sleep(0.05)  # Anda bisa biarkan ini jika ingin spinner terlihat lebih lama (UX)
                                  # atau hapus jika ingin mengukur waktu murni operasi.
                                  # Log akan mencakup waktu sleep ini.
                return f(*args, **kwargs)
        return wrapper
    
    if func is None:
        # Dipanggil dengan kurung: @loading_decorator()
        return decorator
    else:
        # Dipanggil tanpa kurung: @loading_decorator
        return decorator(func)