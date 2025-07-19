# src/utils/db_connector.py

import streamlit as st
import pandas as pd
from supabase import create_client, Client # Pastikan Client diimpor
import logging
import psycopg2 
import requests 
from requests.exceptions import ConnectionError, Timeout 
import socket 
from postgrest.exceptions import APIError

logging.basicConfig(level=logging.INFO)

# --- TIDAK ADA GLOBAL SUPABASE CLIENT DI SINI UNTUK MENGHINDARI CIRCULAR IMPORT ---
# Objek Client akan diinisialisasi dan di-cache oleh @st.cache_resource

# Fungsi helper untuk menangani error jaringan
def _handle_network_error(e: Exception, context: str):
    logging.error(f"Network error in {context}: {e}")
    if 'is_app_offline' not in st.session_state:
        st.session_state.is_app_offline = False 

    if not st.session_state.is_app_offline:
        st.session_state.is_app_offline = True
        st.rerun() 

@st.cache_resource
def init_supabase_connection() -> Client:
    """
    Initializes a connection to the Supabase client using st.secrets.
    This function is cached to ensure only one client is created per session.
    """
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        
        # Reset offline flag jika koneksi berhasil diinisialisasi
        if 'is_app_offline' in st.session_state and st.session_state.is_app_offline:
            st.session_state.is_app_offline = False
            logging.info("Supabase connection re-established. App is back online.")
            # st.rerun() # Tidak perlu reruns di sini, karena client sudah diinisialisasi dan akan dipakai

        return create_client(supabase_url, supabase_key)

    except Exception as e:
        if isinstance(e, (ConnectionError, Timeout, socket.gaierror)):
            _handle_network_error(e, "init_supabase_connection")
            st.stop() # Hentikan proses jika network error di awal
        elif isinstance(e, KeyError) and "supabase" in str(e): 
            st.error("Kredensial Supabase tidak ditemukan. Pastikan 'secrets.toml' Anda terkonfigurasi dengan benar.")
            st.exception(e)
            st.stop() # Hentikan jika kredensial tidak ada
        else:
            st.error(f"Inisialisasi Supabase Gagal: {e}. Periksa konfigurasi atau kredensial Anda.")
            st.exception(e) 
            st.stop()
        return None 

# run_query dan run_sql akan memanggil init_supabase_connection() secara internal

@st.cache_data(ttl=3600)
def run_query(table_name: str) -> pd.DataFrame:
    logging.info(f"Running SELECT * on table: {table_name}")
    if 'is_app_offline' in st.session_state and st.session_state.is_app_offline:
        return pd.DataFrame() 

    # Dapatkan client dari cache
    local_supabase_client = init_supabase_connection() 
    if local_supabase_client is None: # Jika inisialisasi gagal (sudah st.stop() di init_supabase_connection)
        return pd.DataFrame()

    try:
        response = local_supabase_client.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        if isinstance(e, (psycopg2.OperationalError, ConnectionError, Timeout, socket.gaierror)):
            _handle_network_error(e, f"run_query for {table_name}")
        elif isinstance(e, APIError) and "exec_sql" in str(e): 
             st.error(f"Gagal menjalankan query: Pastikan fungsi 'exec_sql' sudah dibuat di database Supabase Anda.")
             st.exception(e) 
        else:
            st.error(f"Error saat mengambil data dari tabel '{table_name}': {e}.")
            st.exception(e) 
        logging.error(f"Error fetching data from '{table_name}': {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def run_sql(sql_query: str) -> pd.DataFrame:
    logging.info(f"Executing raw SQL query: {sql_query[:150]}...") 
    if 'is_app_offline' in st.session_state and st.session_state.is_app_offline:
        return pd.DataFrame()

    local_supabase_client = init_supabase_connection()
    if local_supabase_client is None: # Jika inisialisasi gagal
        return pd.DataFrame()

    try:
        response = local_supabase_client.rpc('exec_sql', {'query': sql_query}).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        if isinstance(e, (psycopg2.OperationalError, ConnectionError, Timeout, socket.gaierror)):
            _handle_network_error(e, "run_sql")
        elif isinstance(e, APIError) and "exec_sql" in str(e):
             st.error(f"Gagal menjalankan query: Pastikan fungsi 'exec_sql' sudah dibuat di database Supabase Anda.")
             st.exception(e) 
        else:
            st.error(f"Gagal menjalankan query SQL: {e}. Pastikan query tidak ada syntax error.")
            st.exception(e)
        logging.error(f"SQL Query failed: {sql_query}\nError: {e}")
        return pd.DataFrame()