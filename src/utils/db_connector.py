# src/utils/db_connector.py

import streamlit as st
import pandas as pd
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

@st.cache_resource
def init_supabase_connection() -> Client:
    """Initializes a connection to the Supabase client."""
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Gagal terhubung ke Supabase: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def run_query(table_name: str) -> pd.DataFrame:
    """Runs a SELECT * query on the specified Supabase table and returns a DataFrame."""
    logging.info(f"Running SELECT * on table: {table_name}")
    supabase = init_supabase_connection()
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error saat mengambil data dari tabel '{table_name}': {e}")
        return pd.DataFrame()

# --- FUNGSI BARU UNTUK OPTIMASI (TAMBAHKAN INI) ---
@st.cache_data(ttl=3600)
def run_sql(sql_query: str) -> pd.DataFrame:
    """
    Runs a raw SQL query using Supabase's PostgREST RPC function.
    NOTE: Requires a `public.exec_sql` function in your Supabase DB.
    
    Args:
        sql_query (str): The raw SQL query to execute.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the query results.
    """
    logging.info(f"Executing raw SQL query: {sql_query[:150]}...") # Log 150 char pertama
    supabase = init_supabase_connection()
    try:
        # Panggil Remote Procedure Call (RPC) 'exec_sql'
        response = supabase.rpc('exec_sql', {'query': sql_query}).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Gagal menjalankan query SQL: {e}. Pastikan fungsi 'exec_sql' sudah dibuat di database Supabase Anda.")
        logging.error(f"SQL Query failed: {sql_query}\nError: {e}")
        return pd.DataFrame()