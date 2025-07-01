# src/utils/charts.py

import streamlit as st
import plotly.graph_objects as go

def get_default_plotly_config():
    """
    Mengembalikan dictionary konfigurasi standar untuk semua chart Plotly.
    Ini memastikan konsistensi dan kemudahan dalam pengelolaan.
    """
    # Tentukan tombol-tombol yang ingin ditampilkan di modebar
    # Grup 1: Download
    # Grup 2: Zoom, Pan, Reset
    custom_modebar_buttons = [
        ['toImage'],
        ['zoomIn2d', 'zoomOut2d', 'pan2d', 'resetScale']
    ]

    config = {
        'displaylogo': False,
        'modeBarButtons': custom_modebar_buttons,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'itb_carbon_dashboard_chart', # Nama file default
            'height': 600,
            'width': 1000,
            'scale': 2  # Resolusi 2x lebih tinggi
        }
    }
    return config

def display_plotly_chart(
    fig: go.Figure,
    use_container_width: bool = True,
    filename: str = 'itb_carbon_dashboard_chart',
    **kwargs
):
    """
    Fungsi pembungkus (wrapper) untuk st.plotly_chart.
    
    Menerapkan konfigurasi default dan memungkinkan kustomisasi lebih lanjut.
    
    Args:
        fig (go.Figure): Objek figur Plotly yang akan ditampilkan.
        use_container_width (bool): Sama seperti argumen di st.plotly_chart.
        filename (str): Nama file default untuk diekspor (tanpa ekstensi).
        **kwargs: Argumen tambahan untuk st.plotly_chart.
    """
    # Ambil konfigurasi default
    config = get_default_plotly_config()
    
    # Perbarui nama file jika disediakan secara spesifik
    config['toImageButtonOptions']['filename'] = filename
    
    # Panggil fungsi streamlit yang sebenarnya dengan figur dan config
    st.plotly_chart(fig, use_container_width=use_container_width, config=config, **kwargs)