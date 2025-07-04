# src/pages/transportation.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
from src.utils.db_connector import run_query


# CONSISTENT COLOR PALETTE
MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

# Transport mode colors - grouped by emission level using main palette
TRANSPORT_COLORS = {
    # Eco-friendly - greens from palette
    'Sepeda': '#66c2a5', 'Jalan kaki': '#abdda4', 'Bike': '#66c2a5', 'Walk': '#abdda4',
    # Low emission - blue-greens  
    'Bus': '#3288bd', 'Kereta': '#5e4fa2', 'Angkot': '#66c2a5', 'Angkutan Umum': '#3288bd',
    'Ojek Online': '#5e4fa2', 'TransJakarta': '#3288bd',
    # Medium emission - oranges
    'Motor': '#fdae61', 'Sepeda Motor': '#f46d43', 'Motorcycle': '#fdae61', 'Ojek': '#f46d43',
    # High emission - reds
    'Mobil': '#d53e4f', 'Mobil Pribadi': '#9e0142', 'Car': '#d53e4f', 'Taksi': '#9e0142', 'Taxi': '#9e0142'
}

MODEBAR_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,  
    'modeBarButtonsToRemove': [
        'pan2d', 'pan3d',
        'select2d', 'lasso2d', 
        'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 
        'autoScale2d', 'resetScale2d', 'resetScale3d',
        'hoverClosestCartesian', 'hoverCompareCartesian',
        'toggleSpikelines', 'hoverClosest3d',
        'orbitRotation', 'tableRotation',
        'resetCameraDefault3d', 'resetCameraLastSave3d'
    ],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'carbon_emission_chart',
        'height': 600,
        'width': 800,
        'scale': 2
    }
}

@st.cache_data(ttl=1)
@loading_decorator()
def load_data():
    """Load transportation data from Supabase"""
    try:
        time.sleep(0.3)
        return run_query("transportasi") 
    except Exception as e:
        st.error(f"Error loading transportation data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1)
@loading_decorator()
def load_responden_data():
    """Load responden data for fakultas information from Supabase"""
    try:
        time.sleep(0.2)
        return run_query("informasi_responden") 
    except Exception as e:
        return pd.DataFrame()

def categorize_emission_level(transport_mode):
    """Categorize transportation mode by emission level"""
    eco_modes = ['Sepeda', 'Jalan Kaki', 'Bike', 'Walk']
    low_modes = ['Bus', 'Kereta', 'Angkot', 'Angkutan Umum', 'Ojek Online', 'TransJakarta']
    medium_modes = ['Motor', 'Sepeda Motor', 'Motorcycle', 'Ojek']
    high_modes = ['Mobil', 'Mobil Pribadi', 'Car', 'Taksi', 'Taxi']
    
    if transport_mode in eco_modes:
        return 'Eco-friendly'
    elif transport_mode in low_modes:
        return 'Low Emission'
    elif transport_mode in medium_modes:
        return 'Medium Emission'
    elif transport_mode in high_modes:
        return 'High Emission'
    else:
        return 'Unknown'

def get_fakultas_mapping():
    """Mapping program_studi ke fakultas ITB"""
    return {
        'Meteorologi': 'FITB', 'Oseanografi': 'FITB', 'Teknik Geodesi dan Geomatika': 'FITB', 'Teknik Geologi': 'FITB',
        'Aktuaria': 'FMIPA', 'Astronomi': 'FMIPA', 'Fisika': 'FMIPA', 'Kimia': 'FMIPA', 'Matematika': 'FMIPA',
        'Desain Interior': 'FSRD', 'Desain Komunikasi Visual': 'FSRD', 'Desain Produk': 'FSRD', 'Kriya': 'FSRD', 'Seni Rupa': 'FSRD',
        'Manajemen Rekayasa Industri': 'FTI', 'Teknik Fisika': 'FTI', 'Teknik Industri': 'FTI', 'Teknik Kimia': 'FTI',
        'Teknik Geofisika': 'FTTM', 'Teknik Metalurgi': 'FTTM', 'Teknik Perminyakan': 'FTTM', 'Teknik Pertambangan': 'FTTM',
        'Teknik Dirgantara': 'FTMD', 'Teknik Material': 'FTMD', 'Teknik Mesin': 'FTMD',
        'Teknik Kelautan': 'FTSL', 'Teknik Lingkungan': 'FTSL', 'Teknik Sipil': 'FTSL',
        'Arsitektur': 'SAPPK', 'Perencanaan Wilayah dan Kota': 'SAPPK',
        'Kewirausahaan': 'SBM', 'Manajemen': 'SBM',
        'Farmasi Klinik dan Komunitas': 'SF', 'Sains dan Teknologi Farmasi': 'SF',
        'Biologi': 'SITH', 'Mikrobiologi': 'SITH',
        'Sistem dan Teknologi Informasi': 'STEI', 'Teknik Biomedis': 'STEI', 'Teknik Elektro': 'STEI', 
        'Teknik Informatika': 'STEI', 'Teknik Telekomunikasi': 'STEI', 'Teknik Tenaga Listrik': 'STEI'
    }

@loading_decorator()
def apply_filters(df, selected_days, selected_modes, selected_fakultas, df_responden=None):
    """Apply filters to the dataframe with loading"""
    filtered_df = df.copy()
    
    # Filter by day (using daily emission columns if available)
    if selected_days:
        day_cols = []
        for day in selected_days:
            day_col = f'emisi_transportasi_{day.lower()}'
            if day_col in filtered_df.columns:
                day_cols.append(day_col)
        
        if day_cols:
            mask = filtered_df[day_cols].sum(axis=1) > 0
            filtered_df = filtered_df[mask]
    
    # Filter by transport mode
    if selected_modes:
        filtered_df = filtered_df[filtered_df['transportasi'].isin(selected_modes)]
    
    # Filter by fakultas
    if selected_fakultas and df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        if 'program_studi' in df_responden.columns:
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            fakultas_students = df_responden[df_responden['fakultas'].isin(selected_fakultas)]
            if 'id_responden' in fakultas_students.columns and 'id_responden' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['id_responden'].isin(fakultas_students['id_responden'])]
    
    time.sleep(0.1) 
    return filtered_df

# Ganti seluruh fungsi generate_pdf_report() dengan kode ini

# Ganti seluruh fungsi generate_pdf_report() dengan kode ini

@loading_decorator()
def generate_pdf_report(filtered_df, df_responden=None):
    """
    REVISED to generate a professional HTML report with distinct, actionable insights 
    and realistic recommendations for university management.
    """
    from datetime import datetime
    import pandas as pd
    time.sleep(0.6)

    if filtered_df.empty:
        return "<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"

    # --- 1. DATA PREPARATION & INSIGHT GENERATION ---
    total_emisi = filtered_df['emisi_mingguan'].sum()
    avg_emisi = filtered_df['emisi_mingguan'].mean()

    # --- Insight 1: Analisis Ritme Mingguan Kampus ---
    hari_cols = [c for c in filtered_df.columns if 'emisi_transportasi_' in c and c != 'emisi_transportasi_mingguan']
    daily_trend_table_html = "<tr><td colspan='2'>Data emisi harian tidak tersedia.</td></tr>"
    trend_conclusion = "Pola mobilitas mingguan belum dapat dipetakan."
    trend_recommendation = "Lengkapi data perjalanan harian untuk analisis ritme kampus yang lebih akurat."
    if hari_cols:
        daily_totals = {col.replace('emisi_transportasi_', '').capitalize(): filtered_df[col].sum() for col in hari_cols}
        if any(daily_totals.values()):
            daily_df = pd.DataFrame(list(daily_totals.items()), columns=['Hari', 'Total Emisi (kg CO₂)']).sort_values(by='Total Emisi (kg CO₂)', ascending=False)
            if not daily_df.empty:
                daily_trend_table_html = "".join([f"<tr><td>{row['Hari']}</td><td style='text-align:right;'>{row['Total Emisi (kg CO₂)']:.1f}</td></tr>" for _, row in daily_df.iterrows()])
                peak_day = daily_df.iloc[0]['Hari']
                low_day = daily_df.iloc[-1]['Hari']
                weekend_emissions = daily_df[daily_df['Hari'].isin(['Sabtu', 'Minggu'])]['Total Emisi (kg CO₂)'].sum()
                weekday_emissions = daily_df[~daily_df['Hari'].isin(['Sabtu', 'Minggu'])]['Total Emisi (kg CO₂)'].sum()
                trend_conclusion = f"Terdapat disparitas emisi yang jelas antara hari kerja dan akhir pekan. Puncak mobilitas terjadi pada <strong>{peak_day}</strong>, menunjukkan bahwa mayoritas perjalanan terkait aktivitas akademik dan operasional kampus."
                trend_recommendation = f"Fokuskan kebijakan transportasi pada hari kerja (Senin-Jumat). Pertimbangkan untuk mengkaji kemungkinan penerapan 'flexible working/studying day' (misal: satu hari dalam sebulan) sebagai studi kasus untuk melihat dampaknya terhadap pengurangan emisi puncak."

    # --- Insight 2: Analisis Demografi Spasial (Fakultas) ---
    fakultas_table_html = "<tr><td colspan='3'>Data fakultas tidak tersedia.</td></tr>"
    fakultas_conclusion = "Profil emisi berdasarkan fakultas tidak dapat dibuat."
    fakultas_recommendation = "Data demografi responden diperlukan untuk analisis kebijakan yang lebih tertarget."
    if df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        if not df_with_fakultas.empty and 'fakultas' in df_with_fakultas.columns:
            fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_mingguan'].agg(['mean', 'sum', 'count']).round(2)
            fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 1].sort_values('mean', ascending=False)
            if not fakultas_stats.empty:
                fakultas_table_html = "".join([f"<tr><td>{fakultas}</td><td style='text-align:right;'>{row['mean']:.2f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for fakultas, row in fakultas_stats.head(10).iterrows()])
                highest_fakultas = fakultas_stats.index[0]
                fakultas_conclusion = f"Mahasiswa dari fakultas <strong>{highest_fakultas}</strong> secara rata-rata memiliki jejak karbon transportasi tertinggi. Hal ini bisa mengindikasikan bahwa komunitas fakultas ini cenderung tinggal lebih jauh atau lebih bergantung pada kendaraan pribadi."
                fakultas_recommendation = f"Alih-alih kebijakan umum, terapkan intervensi berbasis lokasi. Prioritaskan penambahan atau perbaikan fasilitas parkir sepeda dan shelter 'drop-off' ojek online di sekitar gedung fakultas <strong>{highest_fakultas}</strong>."

    # --- Insight 3: Analisis Preferensi Moda Transportasi ---
    mode_stats = filtered_df.groupby('transportasi')['emisi_mingguan'].agg(['count', 'mean']).round(2).sort_values('count', ascending=False)
    mode_table_html = "".join([f"<tr><td>{mode}</td><td style='text-align:center;'>{int(row['count'])}</td><td style='text-align:right;'>{row['mean']:.2f}</td></tr>" for mode, row in mode_stats.iterrows()])
    dominant_mode = mode_stats.index[0]
    dominant_mode_emission_cat = categorize_emission_level(dominant_mode)
    mode_conclusion = f"<strong>{dominant_mode}</strong> (kategori: {dominant_mode_emission_cat}) adalah moda transportasi pilihan utama komunitas kampus. Ini mencerminkan infrastruktur dan kondisi eksisting yang paling mendukung moda tersebut."
    rec_text = f"Penggunaan <strong>{dominant_mode}</strong> yang tinggi menunjukkan keberhasilan. Kebijakan selanjutnya adalah meningkatkan 'user experience', seperti menambah jumlah unit 'bike sharing' atau memperluas cakupan jalur pejalan kaki yang teduh." if dominant_mode_emission_cat in ['Eco-friendly', 'Low Emission'] else f"Ketergantungan tinggi pada <strong>{dominant_mode}</strong> adalah tantangan utama. Kebijakan 'mode shifting' diperlukan, contohnya dengan mempertimbangkan pembatasan akses kendaraan pribadi di zona tertentu kampus (Low Emission Zone)."
    mode_recommendation = rec_text

    # --- Insight 4: Analisis Pola Perilaku Harian ---
    heatmap_table_html = "<tr><td colspan='7'>Data penggunaan harian tidak tersedia.</td></tr>"
    heatmap_header_html = "<tr><th>Hari</th><th>Moda Populer 1</th><th>Moda Populer 2</th></tr>"
    heatmap_conclusion = "Pola perilaku spesifik harian belum teridentifikasi."
    heatmap_recommendation = "Data yang lebih detail akan membantu merumuskan kampanye perilaku yang lebih efektif."
    if hari_cols:
        transport_day_data = []
        for mode in filtered_df['transportasi'].unique():
            mode_data = filtered_df[filtered_df['transportasi'] == mode]
            for col in hari_cols:
                day = col.replace('emisi_transportasi_', '').capitalize()
                users_count = (mode_data[col] > 0).sum()
                transport_day_data.append({'transportasi': mode, 'hari': day, 'pengguna': users_count})
        if transport_day_data:
            heatmap_df = pd.DataFrame(transport_day_data)
            day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            pivot_df = heatmap_df.pivot(index='hari', columns='transportasi', values='pengguna').fillna(0).reindex(index=day_order, fill_value=0)
            top_modes = pivot_df.sum(axis=0).nlargest(6).index
            pivot_df_filtered = pivot_df[top_modes]
            if not pivot_df_filtered.empty:
                header_cells_html = "<th>Hari</th>" + "".join([f"<th>{mode}</th>" for mode in pivot_df_filtered.columns])
                heatmap_header_html = f"<tr>{header_cells_html}</tr>"
                body_rows_list = []
                for day, row in pivot_df_filtered.iterrows():
                    cells_html = "".join([f"<td style='text-align:center;'>{int(count)}</td>" for count in row])
                    body_rows_list.append(f"<tr><td><strong>{day}</strong></td>{cells_html}</tr>")
                heatmap_table_html = "".join(body_rows_list)
                
                peak_usage_day = pivot_df_filtered.sum(axis=1).idxmax()
                peak_usage_mode = pivot_df_filtered.loc[peak_usage_day].idxmax()
                heatmap_conclusion = f"Teridentifikasi sebuah kebiasaan kuat (strong habit): penggunaan <strong>{peak_usage_mode}</strong> secara masif pada hari <strong>{peak_usage_day}</strong>."
                heatmap_recommendation = f"Fokus pada intervensi perilaku. Usulkan program 'Tantangan <strong>{peak_usage_day}</strong> Hijau': ajak komunitas untuk tidak menggunakan <strong>{peak_usage_mode}</strong> pada hari itu dan berbagi pengalamannya di media sosial dengan tagar resmi. Berikan apresiasi (bukan hadiah) bagi partisipan terbaik."

    # --- Insight 5: Analisis Geografis Asal Perjalanan ---
    kecamatan_table_html = "<tr><td colspan='3'>Data kecamatan tidak tersedia.</td></tr>"
    kecamatan_conclusion = "Analisis 'hotspot' geografis belum dapat dilakukan."
    rec_kecamatan = "Sertakan data asal perjalanan untuk merumuskan kebijakan berbasis kewilayahan."
    if 'kecamatan' in filtered_df.columns and not filtered_df['kecamatan'].isnull().all():
        kecamatan_stats = filtered_df.groupby('kecamatan')['emisi_mingguan'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        if not kecamatan_stats.empty:
            kecamatan_table_html = "".join([f"<tr><td>{kecamatan}</td><td style='text-align:right;'>{row['sum']:.1f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for kecamatan, row in kecamatan_stats.head(10).iterrows()])
            hottest_spot = kecamatan_stats.index[0]
            student_count = int(kecamatan_stats.iloc[0]['count'])
            kecamatan_conclusion = f"Kecamatan <strong>{hottest_spot}</strong> merupakan 'feeder' utama komuter ke kampus, sekaligus menjadi sumber emisi terbesar. Ini adalah titik intervensi paling strategis di luar kampus."
            rec_kecamatan = f"Gunakan data ini sebagai dasar proposal ke pemerintah daerah (Dishub) untuk pembukaan atau optimalisasi rute angkutan umum dari <strong>{hottest_spot}</strong>. Di level kampus, pertimbangkan untuk menjadikan <strong>{hottest_spot}</strong> sebagai titik jemput utama untuk layanan shuttle."
    
    # --- HTML Generation ---
    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Transportasi</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Poppins', sans-serif; color: #333; line-height: 1.6; font-size: 11px; }}
        .page {{ padding: 25px; max-width: 800px; margin: auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #059669; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ color: #059669; margin: 0; }} h2 {{ color: #065f46; border-bottom: 1px solid #d1fae5; padding-bottom: 8px; margin-top: 30px; margin-bottom: 15px;}}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
        .card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .card.primary {{ border-left: 4px solid #10b981; }} .card.primary strong {{ color: #059669; }}
        .card.secondary {{ border-left: 4px solid #3b82f6; }} .card.secondary strong {{ color: #3b82f6; }}
        .card strong {{ font-size: 1.5em; display: block; }}
        .conclusion, .recommendation {{ padding: 12px 15px; margin-top: 10px; border-radius: 6px; }}
        .conclusion {{ background: #f0fdf4; border-left: 4px solid #10b981; }}
        .recommendation {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        ul {{ padding-left: 20px; margin-top: 8px; margin-bottom: 0; }} li {{ margin-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th, td {{ padding: 8px; text-align: left; border: 1px solid #e5e7eb; }}
        th {{ background-color: #f3f4f6; font-weight: 600; text-align: center; }}
        td:first-child {{ font-weight: 500; }}
    </style></head>
    <body><div class="page">
        <div class="header"><h1>Laporan Emisi Transportasi</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO₂</strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO₂</strong>Rata-rata/Mahasiswa</div>
        </div>

        <h2>1. Ritme Mobilitas Mingguan</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        
        <h2>2. Profil Demografi Spasial (Fakultas)</h2>
        <table><thead><tr><th>Fakultas</th><th>Rata-rata Emisi (kg CO₂)</th><th>Jumlah Responden</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        
        <h2>3. Preferensi Moda Transportasi</h2>
        <table><thead><tr><th>Moda Transportasi</th><th>Jumlah Pengguna</th><th>Rata-rata Emisi (kg CO₂)</th></tr></thead><tbody>{mode_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {mode_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {mode_recommendation}</div>

        <h2>4. Analisis Pola Perilaku Harian</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>

        <h2>5. Hotspot Geografis Asal Perjalanan</h2>
        <table><thead><tr><th>Kecamatan</th><th>Total Emisi (kg CO₂)</th><th>Jumlah Responden</th></tr></thead><tbody>{kecamatan_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {kecamatan_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {rec_kecamatan}</div>
    </div></body></html>
    """
    return html_content

def show():
    with loading():
        st.markdown("""
        <div class="wow-header">
            <div class="header-bg-pattern"></div>
            <div class="header-float-1"></div>
            <div class="header-float-2"></div>
            <div class="header-float-3"></div>
            <div class="header-content">
                <h1 class="header-title">Emisi Transportasi</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.2) 

    df = load_data()
    df_responden = load_responden_data()
    
    if df.empty:
        st.error("Data transportasi tidak tersedia")
        return

    with loading():
        df['emisi_transportasi'] = pd.to_numeric(df['emisi_transportasi'], errors='coerce').fillna(0)
        # Kolom hari datang, pastikan string dan handle nilai null
        df['hari_datang'] = df['hari_datang'].astype(str).fillna('')
        df['jumlah_hari_datang'] = df['hari_datang'].str.split(',').str.len()
        df['emisi_mingguan'] = df['emisi_transportasi'] * df['jumlah_hari_datang']
        days_of_week = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
        for day in days_of_week:
            col_name = f'emisi_transportasi_{day}'
            df[col_name] = np.where(df['hari_datang'].str.contains(day.capitalize(), na=False), df['emisi_transportasi'], 0)
        
        df = df.dropna(subset=['transportasi'])
        df['emission_category'] = df['transportasi'].apply(categorize_emission_level)
        time.sleep(0.1)
    
    # Filter
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:",
            options=day_options,
            placeholder="Pilih Opsi",
            key='transport_day_filter'
        )
    
    with filter_col2:
        available_modes = sorted(df['transportasi'].unique())
        selected_modes = st.multiselect(
            "Moda Transportasi:",
            options=available_modes,
            placeholder="Pilih Opsi",
            key='transport_mode_filter'
        )
    
    with filter_col3:
        if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
            fakultas_mapping = get_fakultas_mapping()
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            available_fakultas = sorted(df_responden['fakultas'].unique())
            selected_fakultas = st.multiselect(
                "Fakultas:",
                options=available_fakultas,
                placeholder="Pilih Opsi",
                key='transport_fakultas_filter'
            )
        else:
            selected_fakultas = []

    # Apply filters with loading
    filtered_df = apply_filters(df, selected_days, selected_modes, selected_fakultas, df_responden)
    
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return
    

    
    # Calculate metrics for export
    total_emisi = filtered_df['emisi_mingguan'].sum()
    avg_emisi = filtered_df['emisi_mingguan'].mean()
    total_users = len(filtered_df)
    eco_friendly_users = len(filtered_df[filtered_df['emission_category'] == 'Eco-friendly'])
    eco_percentage = (eco_friendly_users / total_users * 100) if total_users > 0 else 0

    # Export buttons
    with export_col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Raw Data",
            data=csv_data,
            file_name=f"transport_{len(filtered_df)}.csv",
            mime="text/csv",
            use_container_width=True,
            key="transport_export_csv"
        )

    with export_col2:
        try:
            pdf_content = generate_pdf_report(filtered_df, df_responden)
            
            st.download_button(
                "Laporan",
                data=pdf_content,
                file_name=f"transport_report_{len(filtered_df)}.html",
                mime="text/html",
                use_container_width=True,
                key="transport_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    # Charts with loading animations
    with loading():
        # Row 1: Main Charts
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Chart 1: Tren Emisi Harian
            hari_cols = [c for c in filtered_df.columns if 'emisi_transportasi_' in c and c != 'emisi_transportasi_mingguan']
            
            if hari_cols:
                daily_data = []
                for col in hari_cols:
                    day = col.replace('emisi_transportasi_', '').capitalize()
                    total_emisi = filtered_df[col].sum()
                    daily_data.append({'hari': day, 'emisi': total_emisi})
                
                daily_df = pd.DataFrame(daily_data)
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                daily_df['order'] = daily_df['hari'].map({day: i for i, day in enumerate(day_order)})
                daily_df = daily_df.sort_values('order')
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=daily_df['hari'], y=daily_df['emisi'],
                    fill='tonexty', mode='lines+markers',
                    line=dict(color='#3288bd', width=2, shape='spline'), 
                    marker=dict(size=6, color='#3288bd', line=dict(color='white', width=1)),
                    fillcolor="rgba(102, 194, 165, 0.3)",
                    hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>',
                    showlegend=False
                ))
                
                fig_trend.update_layout(
                    height=270, margin=dict(t=30, b=0, l=0, r=10),
                    xaxis_title="", yaxis_title="Emisi (kg CO₂)",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                              font=dict(size=12, color="#000000")),
                    xaxis=dict(showgrid=False, tickfont=dict(size=10), title=dict(text="Hari", font=dict(size=10))),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=10), title=dict(text="Total Emisi (Kg CO₂)", font=dict(size=10)))
                )
                st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Data tren harian tidak tersedia")

        with col2:
            # Chart 2: Emisi per Fakultas
            if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
                fakultas_mapping = get_fakultas_mapping()
                df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
                
                if 'id_responden' in df_responden.columns and 'id_responden' in filtered_df.columns:
                    df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                    fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_mingguan'].agg(['sum', 'count']).reset_index()
                    fakultas_stats.columns = ['fakultas', 'total_emisi', 'count']
                    fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 0].sort_values('total_emisi', ascending=True).tail(13)
                    
                    if not fakultas_stats.empty:
                        fig_fakultas = go.Figure()
                        
                        max_emisi = fakultas_stats['total_emisi'].max()
                        min_emisi = fakultas_stats['total_emisi'].min()
                        
                        for i, (_, row) in enumerate(fakultas_stats.iterrows()):
                            if max_emisi > min_emisi:
                                ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                                color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                                color_idx = int(ratio * (len(color_palette) - 1))
                                color = color_palette[color_idx]
                            else:
                                color = MAIN_PALETTE[i % len(MAIN_PALETTE)]
                            
                            fig_fakultas.add_trace(go.Bar(
                                x=[row['total_emisi']], 
                                y=[row['fakultas']], 
                                orientation='h',
                                marker=dict(color=color), 
                                showlegend=False,
                                text=[f"{row['total_emisi']:.1f}"], 
                                textposition='inside',
                                textfont=dict(color='white', size=10, weight='bold'),
                                hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["count"]}<extra></extra>'
                            ))
                        
                        fig_fakultas.update_layout(
                            height=270, margin=dict(t=30, b=0, l=0, r=20),
                            title=dict(text="<b>Emisi per Fakultas</b>", x=0.4, y=0.95,
                                      font=dict(size=12, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=10), title=dict(text="Total Emisi (kg CO₂)", font=dict(size=10))),
                            yaxis=dict(tickfont=dict(size=10), title=dict(text="Fakultas/Sekolah", font=dict(size=10)))
                        )
                        
                        st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
                    else:
                        st.info("Data fakultas tidak cukup (min 2 mahasiswa)")
                else:
                    st.info("Data fakultas tidak dapat digabungkan")

        with col3:
            # Chart 3: Proporsi Emisi per Moda Transportasi
            transport_counts = filtered_df['transportasi'].value_counts()
            colors = [TRANSPORT_COLORS.get(mode, MAIN_PALETTE[i % len(MAIN_PALETTE)]) 
                     for i, mode in enumerate(transport_counts.index)]
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=transport_counts.index,
                values=transport_counts.values,
                hole=0.45,
                marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=10, family="Poppins"),
                hovertemplate='<b>%{label}</b><br>%{value:.2f} kg CO₂ (%{percent})<extra></extra>'
            )])
            
            total_emisi_chart = filtered_df['emisi_mingguan'].sum()
            center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
            fig_donut.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)

            fig_donut.update_layout(
                height=270, margin=dict(t=30, b=5, l=5, r=5), showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="<b>Komposisi Moda Transportasi</b>", x=0.3, y=0.95, 
                          font=dict(size=12, color="#000000"))
            )
            st.plotly_chart(fig_donut, config=MODEBAR_CONFIG, use_container_width=True)

        time.sleep(0.2)  

    # Row 2: Secondary Charts with loading
    with loading():
        col1, col2 = st.columns([1, 1])

        with col1:
            # Chart 4: Heatmap Hari vs Moda Transportasi
            hari_cols = [c for c in filtered_df.columns if 'emisi_transportasi_' in c and c != 'emisi_transportasi_mingguan']
            
            if hari_cols:
                transport_day_data = []
                for mode in filtered_df['transportasi'].unique():
                    mode_data = filtered_df[filtered_df['transportasi'] == mode]
                    for col in hari_cols:
                        day = col.replace('emisi_transportasi_', '').capitalize()
                        users_count = (mode_data[col] > 0).sum()
                        transport_day_data.append({
                            'transportasi': mode,
                            'hari': day, 
                            'pengguna': users_count
                        })
                
                heatmap_df = pd.DataFrame(transport_day_data)
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                
                pivot_df = heatmap_df.pivot(index='hari', columns='transportasi', values='pengguna').fillna(0)
                pivot_df = pivot_df.reindex(index=day_order, fill_value=0)
                
                top_modes = pivot_df.sum(axis=0).nlargest(6).index
                pivot_df_filtered = pivot_df[top_modes]
                
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=pivot_df_filtered.values,
                    x=pivot_df_filtered.columns,
                    y=pivot_df_filtered.index,   
                    colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                    hoverongaps=False,
                    hovertemplate='<b>%{x}</b><br>%{y}: %{z} pengguna<extra></extra>',
                    colorbar=dict(
                        title=dict(text="Pengguna", font=dict(size=9)),
                        tickfont=dict(size=10),
                        thickness=15,
                        len=0.7
                    ),
                    xgap=1, ygap=1,  
                    zmin=0
                ))
                
                fig_heatmap.update_layout(
                    height=270, margin=dict(t=30, b=0, l=0, r=0),
                    title=dict(text="<b>Heatmap Penggunaan Moda Transportasi per Hari</b>", x=0.3, y=0.95, 
                            font=dict(size=12, color="#000000")),
                    xaxis=dict(tickfont=dict(size=10), tickangle=0, title=dict(text="Moda Transportasi", font=dict(size=10))),
                    yaxis=dict(tickfont=dict(size=10), title=dict(text="Hari", font=dict(size=10))),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Data pola harian tidak tersedia")

        with col2:
            if 'kecamatan' in filtered_df.columns:
                kecamatan_stats = filtered_df.groupby('kecamatan')['emisi_mingguan'].agg(['mean', 'count', 'sum']).reset_index()
                kecamatan_stats.columns = ['kecamatan', 'rata_rata_emisi', 'jumlah_mahasiswa', 'total_emisi']
                
                kecamatan_filtered = kecamatan_stats[kecamatan_stats['jumlah_mahasiswa'] >= 0].sort_values('rata_rata_emisi', ascending=False)
                
                if not kecamatan_filtered.empty:
                    kecamatan_display = kecamatan_filtered.nlargest(8, 'jumlah_mahasiswa').sort_values('rata_rata_emisi', ascending=False)
                    
                    fig_kecamatan = go.Figure()
                    
                    max_emisi = kecamatan_display['rata_rata_emisi'].max()
                    min_emisi = kecamatan_display['rata_rata_emisi'].min()
                    
                    for i, (_, row) in enumerate(kecamatan_display.iterrows()):
                        if max_emisi > min_emisi:
                            ratio = (row['rata_rata_emisi'] - min_emisi) / (max_emisi - min_emisi)
                            sequential_warm = ['#fee08b', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                            color_idx = int(ratio * (len(sequential_warm) - 1))
                            color = sequential_warm[color_idx]
                        else:
                            color = MAIN_PALETTE[i % len(MAIN_PALETTE)]
                        
                        display_name = row['kecamatan'] if len(row['kecamatan']) <= 10 else row['kecamatan'][:8] + '..'
                        
                        fig_kecamatan.add_trace(go.Bar(
                            x=[display_name], 
                            y=[row['rata_rata_emisi']], 
                            marker=dict(color=color, line=dict(color='white', width=1)), 
                            showlegend=False,
                            text=[f"{row['rata_rata_emisi']:.1f}"], 
                            textposition='inside',
                            textfont=dict(color='#2d3748', size=10, weight='bold'),
                            hovertemplate=f'<b>{row["kecamatan"]}</b><br>Rata-rata: {row["rata_rata_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["jumlah_mahasiswa"]}<br>Total: {row["total_emisi"]:.1f} kg CO₂<extra></extra>',
                            name=row['kecamatan']
                        ))
                    
                    avg_emisi = kecamatan_display['rata_rata_emisi'].mean()
                    fig_kecamatan.add_hline(
                        y=avg_emisi,
                        line_dash="dash",
                        line_color="#5e4fa2",
                        line_width=2,
                        annotation_text=f"Rata-rata: {avg_emisi:.1f}",
                        annotation_position="top right",
                        annotation=dict(
                            bgcolor="white", 
                            bordercolor="#5e4fa2", 
                            borderwidth=1,
                            font=dict(size=10)
                        )
                    )
                    
                    fig_kecamatan.update_layout(
                        height=270, margin=dict(t=30, b=0, l=0, r=10),
                        title=dict(text="<b>Emisi per Kecamatan</b>", x=0.4, y=0.95, 
                                  font=dict(size=12, color="#000000")),
                        xaxis=dict(
                            title=dict(text="Kecamatan", font=dict(size=10)), 
                            showgrid=False, 
                            tickfont=dict(size=10),
                        ),
                        yaxis=dict(
                            title=dict(text="Rata-Rata Emisi (kg CO₂)", font=dict(size=10)), 
                            showgrid=True, 
                            gridcolor='rgba(0,0,0,0.1)', 
                            tickfont=dict(size=10)
                        ),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=False
                    )
                    st.plotly_chart(fig_kecamatan, config=MODEBAR_CONFIG, use_container_width=True)
                else:
                    st.info("Data kecamatan tidak mencukupi untuk analisis")
            else:
                st.info("Data kecamatan tidak tersedia")

        time.sleep(0.2) 

if __name__ == "__main__":
    show()