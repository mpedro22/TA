import streamlit as st
import pandas as pd
from supabase import create_client, Client

@st.cache_resource
def init_supabase_connection() -> Client:
    """
    Initializes a connection to the Supabase client.
    Uses Streamlit's secrets for credentials.
    """
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Gagal terhubung ke Supabase: {e}")
        st.stop()

@st.cache_data(ttl=3600) 
def run_query(table_name: str) -> pd.DataFrame:
    """
    Runs a SELECT * query on the specified Supabase table and returns a DataFrame.
    
    Args:
        table_name (str): The name of the table to query.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the query results.
    """
    supabase = init_supabase_connection()
    try:
        response = supabase.table(table_name).select("*").execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Error saat mengambil data dari tabel '{table_name}': {e}")
        return pd.DataFrame()