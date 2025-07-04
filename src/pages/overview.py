import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
import warnings
warnings.filterwarnings('ignore')
from src.utils.db_connector import run_query


# color pallete
MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']
CATEGORY_COLORS = {'Transportasi': '#d53e4f', 'Elektronik': '#3288bd', 'Sampah': '#66c2a5'}
CLUSTER_COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
FACULTY_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5']


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

@st.cache_data(ttl=3600)
@loading_decorator()
def load_all_data():
    """Load all data sources for overview dashboard from Supabase"""
    try:
        time.sleep(0.4) 
        df_transport_raw = run_query("transportasi")
        df_electronic_raw = run_query("elektronik")
        df_activities_raw = run_query("aktivitas_harian")
        df_responden_raw = run_query("informasi_responden")
        
        return df_transport_raw, df_electronic_raw, df_activities_raw, df_responden_raw
    except Exception as e:
        st.error(f"Error loading data from Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
def parse_food_activities(df_activities):
    """Parse food waste activities from Supabase daily activities data"""
    food_activities = []
    if df_activities.empty:
        return pd.DataFrame()

    meal_df = df_activities[
        df_activities['kegiatan'].str.contains('Makan|Minum', case=False, na=False) &
        (pd.to_numeric(df_activities['emisi_makanminum'], errors='coerce').fillna(0) > 0)
    ].copy()

    if meal_df.empty:
        return pd.DataFrame()

    for _, row in meal_df.iterrows():
        day_name = str(row.get('hari', '')).capitalize()
        if day_name:
            food_activities.append({
                'id_responden': row.get('id_responden', ''),
                'day': day_name,
                'emisi_makanan': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce'),
                'kategori': 'Sampah'
            })
            
    time.sleep(0.1)
    return pd.DataFrame(food_activities)

@loading_decorator()
def create_unified_dataset(df_transport, df_electronic, df_food, df_responden):
    """Create unified dataset for overview analysis"""
    unified_data = []
    
    fakultas_mapping = get_fakultas_mapping()
    if not df_responden.empty and 'program_studi' in df_responden.columns:
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
    
    all_respondents = set(df_responden['id_responden'].dropna())

    for resp_id in all_respondents:
        if pd.isna(resp_id) or resp_id == '':
            continue
            
        resp_info = df_responden[df_responden['id_responden'] == resp_id]
        fakultas = resp_info.iloc[0].get('fakultas', 'Unknown') if not resp_info.empty else 'Unknown'
        
        # Ambil emisi mingguan yang sudah dihitung sebelumnya
        transport_emisi = df_transport.loc[df_transport['id_responden'] == resp_id, 'emisi_mingguan'].sum()
        electronic_emisi = df_electronic.loc[df_electronic['id_responden'] == resp_id, 'emisi_elektronik_mingguan'].sum()
        
        # Emisi makanan adalah total dari semua aktivitas makan per responden
        food_emisi = df_food.loc[df_food['id_responden'] == resp_id, 'emisi_makanan'].sum()
        
        total_emisi = transport_emisi + electronic_emisi + food_emisi
        
        if total_emisi > 0:  
            unified_data.append({
                'id_responden': resp_id, 'fakultas': fakultas,
                'transportasi': transport_emisi, 'elektronik': electronic_emisi,
                'sampah_makanan': food_emisi, 'total_emisi': total_emisi
            })
    
    time.sleep(0.15)
    return pd.DataFrame(unified_data)

@loading_decorator()
def apply_overview_filters(df_unified, df_transport, df_electronic, df_food, selected_days, selected_categories, selected_fakultas):
    """Apply filters to all datasets - FIXED to work with all filters"""
    filtered_unified = df_unified.copy()
    
    if selected_fakultas:
        filtered_unified = filtered_unified[filtered_unified['fakultas'].isin(selected_fakultas)]
    
    if selected_categories:
        if 'Transportasi' not in selected_categories:
            filtered_unified['transportasi'] = 0
        if 'Elektronik' not in selected_categories:
            filtered_unified['elektronik'] = 0
        if 'Sampah' not in selected_categories:
            filtered_unified['sampah_makanan'] = 0
        
        filtered_unified['total_emisi'] = (
            filtered_unified['transportasi'] + 
            filtered_unified['elektronik'] + 
            filtered_unified['sampah_makanan']
        )
        
        filtered_unified = filtered_unified[filtered_unified['total_emisi'] > 0]
    
    if selected_days:
        valid_respondents = set(filtered_unified['id_responden'])
        day_filtered_respondents = set()
        
        if not df_transport.empty and 'Transportasi' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah']):
            for day in selected_days:
                day_col = f'emisi_transportasi_{day.lower()}'
                if day_col in df_transport.columns:
                    day_users = df_transport[df_transport[day_col] > 0]['id_responden'].dropna()
                    day_filtered_respondents.update(day_users)
        
        if not df_food.empty and 'Sampah' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah']):
            day_food_users = df_food[df_food['day'].isin(selected_days)]['id_responden'].dropna()
            day_filtered_respondents.update(day_food_users)
        
        if 'Elektronik' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah']):
            if not df_electronic.empty:
                electronic_users = df_electronic['id_responden'].dropna()
                day_filtered_respondents.update(electronic_users)
        
        if day_filtered_respondents:
            valid_respondents = valid_respondents.intersection(day_filtered_respondents)
            filtered_unified = filtered_unified[filtered_unified['id_responden'].isin(valid_respondents)]
    
    time.sleep(0.1)
    return filtered_unified

# Menentukan profil perilaku mahasiswa berdasarkan emisi
def create_behavior_profile(row, thresholds):
    """Membuat nama profil perilaku dalam Bahasa Indonesia."""
    t_level = "Tinggi" if row['transportasi'] > thresholds['transportasi'] else "Rendah"
    e_level = "Tinggi" if row['elektronik'] > thresholds['elektronik'] else "Rendah"
    f_level = "Tinggi" if row['sampah_makanan'] > thresholds['sampah_makanan'] else "Rendah"
    
    if t_level == "Tinggi" and e_level == "Tinggi" and f_level == "Tinggi":
        return "Kontributor Utama"
    elif t_level == "Rendah" and e_level == "Rendah" and f_level == "Rendah":
        return "Sangat Sadar Lingkungan"
    elif t_level == "Tinggi" and e_level == "Tinggi":
        return "Komuter & Digital"
    elif t_level == "Tinggi" and f_level == "Tinggi":
        return "Komuter & Boros Pangan"
    elif e_level == "Tinggi" and f_level == "Tinggi":
        return "Digital & Boros Pangan"
    elif t_level == "Tinggi":
        return "Komuter Berat"
    elif e_level == "Tinggi":
        return "Pengguna Elektronik Berat"
    elif f_level == "Tinggi":
        return "Boros Pangan"
    else:
        return "Profil Campuran"

@loading_decorator()
def generate_overview_pdf_report(filtered_df, daily_df, fakultas_stats_full):
    """
    Generate comprehensive and insightful overview PDF report.
    REVISED with detailed clustering analysis, table, and recommendations.
    """
    from datetime import datetime
    time.sleep(0.6)

    if filtered_df.empty:
        return "<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda dan coba lagi.</p></body></html>"

    total_emisi = filtered_df['total_emisi'].sum()
    avg_emisi = filtered_df['total_emisi'].mean()
    
    composition_data = {'Transportasi': filtered_df['transportasi'].sum(), 'Elektronik': filtered_df['elektronik'].sum(), 'Sampah': filtered_df['sampah_makanan'].sum()}
    dominant_cat = max(composition_data, key=composition_data.get) if total_emisi > 0 else "N/A"
    dominant_pct = (composition_data.get(dominant_cat, 0) / total_emisi * 100) if total_emisi > 0 else 0
    composition_conclusion = f"Sumber emisi utama adalah <strong>{dominant_cat}</strong>, menyumbang <strong>{dominant_pct:.1f}%</strong> dari total jejak karbon yang dianalisis."
    rec_map_cat = {'Transportasi': "Prioritaskan kebijakan transportasi ramah lingkungan.", 'Elektronik': "Implementasikan kebijakan hemat energi di seluruh kampus.", 'Sampah': "Luncurkan program komprehensif untuk manajemen limbah makanan."}
    composition_recommendation = rec_map_cat.get(dominant_cat, "Analisis lebih lanjut diperlukan.")

    peak_day = "N/A"
    if not daily_df.empty:
        daily_totals = daily_df.set_index('day').sum(axis=1)
        peak_day = daily_totals.idxmax() if not daily_totals.empty else "N/A"
    trend_conclusion = f"Aktivitas emisi memuncak pada hari <strong>{peak_day}</strong>."
    trend_recommendation = f"Selidiki aktivitas spesifik pada hari <strong>{peak_day}</strong> yang menyebabkan lonjakan emisi. Pertimbangkan untuk mengadakan kampanye hemat energi pada hari tersebut."

    fakultas_report = pd.DataFrame()
    fakultas_conclusion = "Data fakultas tidak cukup untuk dianalisis."
    fakultas_recommendation = ""
    if not fakultas_stats_full.empty and len(fakultas_stats_full) > 1:
        fakultas_report = fakultas_stats_full.sort_values('total_emisi', ascending=False)
        highest_fakultas_row = fakultas_report.iloc[0]
        lowest_fakultas_row = fakultas_report.iloc[-1]
        fakultas_conclusion = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> menunjukkan total emisi tertinggi, sementara <strong>{lowest_fakultas_row['fakultas']}</strong> mencatat yang terendah."
        fakultas_recommendation = f"Bentuk tim studi banding antara fakultas <strong>{highest_fakultas_row['fakultas']}</strong> dan <strong>{lowest_fakultas_row['fakultas']}</strong> untuk mengidentifikasi praktik terbaik dan area perbaikan."

    segmentation_table_html = "<tr><td colspan='2'>Data tidak cukup untuk segmentasi.</td></tr>"
    segmentation_conclusion = "Tidak dapat membuat profil perilaku mahasiswa karena data terbatas."
    segmentation_recommendation = "Diperlukan lebih banyak data responden untuk analisis segmentasi yang valid."

    if len(filtered_df) > 1:
        thresholds = {
            'transportasi': filtered_df['transportasi'].median(),
            'elektronik': filtered_df['elektronik'].median(),
            'sampah_makanan': filtered_df['sampah_makanan'].median()
        }
        df_with_profile = filtered_df.copy()
        df_with_profile['profil_perilaku'] = df_with_profile.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
        
        profile_stats = df_with_profile.groupby('profil_perilaku').agg(
            jumlah_mahasiswa=('id_responden', 'count'),
            avg_emisi=('total_emisi', 'mean')
        ).sort_values('jumlah_mahasiswa', ascending=False).reset_index()

        if not profile_stats.empty:
            segmentation_table_html = "".join([f"<tr><td><strong>{row['profil_perilaku']}</strong></td><td style='text-align:center;'>{row['jumlah_mahasiswa']}</td><td style='text-align:right;'>{row['avg_emisi']:.2f}</td></tr>" for _, row in profile_stats.iterrows()])
            
            dominant_profile = profile_stats.iloc[0]['profil_perilaku']
            dominant_count = profile_stats.iloc[0]['jumlah_mahasiswa']
            
            segmentation_conclusion = f"Segmentasi berbasis perilaku menunjukkan bahwa profil dominan di antara mahasiswa adalah '<strong>{dominant_profile}</strong>', yang mencakup <strong>{dominant_count}</strong> orang. Mengidentifikasi profil dominan adalah kunci untuk intervensi yang efektif."
            
            rec_map = {
                "Kontributor Utama": "Kelompok ini adalah prioritas tertinggi. Intervensi harus bersifat holistik mencakup transportasi, energi, dan pangan.",
                "Komuter Berat": "Fokus pada kebijakan 'mode shifting' seperti peningkatan layanan shuttle atau insentif untuk carpooling.",
                "Pengguna Elektronik Berat": "Targetkan kampanye hemat energi dan audit penggunaan fasilitas di gedung-gedung yang sering mereka gunakan.",
                "Boros Pangan": "Kolaborasi dengan vendor kantin untuk program reduksi sisa makanan adalah langkah yang paling berdampak.",
                "Sangat Sadar Lingkungan": "Jadikan kelompok ini sebagai 'champion' atau duta lingkungan. Wawancara mereka untuk mendapatkan insight praktik terbaik.",
                "Profil Campuran": "Edukasi umum mengenai sumber-sumber emisi utama di kampus akan efektif untuk kelompok ini."
            }
            rekomendasi_utama = rec_map.get(dominant_profile, rec_map["Profil Campuran"])
            segmentation_recommendation = f"Kebijakan kampus harus diprioritaskan untuk menargetkan profil '<strong>{dominant_profile}</strong>'. Rekomendasi: {rekomendasi_utama}"

    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Overview</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
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
        <div class="header"><h1>Laporan Overview Emisi Karbon</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO₂</strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO₂</strong>Rata-rata/Mahasiswa</div>
        </div>

        <h2>1. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>
        {''.join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for idx, row in fakultas_report.head(10).iterrows()]) if not fakultas_report.empty else "<tr><td colspan='2'>Data tidak tersedia.</td></tr>"}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>

        <h2>2. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>
        {''.join([f"<tr><td>{row['day']}</td><td style='text-align:right;'>{row.drop('day').sum():.1f}</td></tr>" for idx, row in daily_df.iterrows()]) if not daily_df.empty else "<tr><td colspan='2'>Data tidak tersedia.</td></tr>"}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        
        <h2>3. Komposisi Emisi</h2>
        <table><thead><tr><th>Kategori</th><th>Total Emisi (kg CO₂)</th><th>Persentase</th></tr></thead><tbody>
        {''.join([f"<tr><td>{cat}</td><td style='text-align:right;'>{val:.1f}</td><td style='text-align:right;'>{(val/total_emisi*100 if total_emisi>0 else 0):.1f}%</td></tr>" for cat, val in composition_data.items()])}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {composition_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {composition_recommendation}</div>

        <h2>4. Segmentasi Perilaku</h2>
        <table><thead>
            <tr><th>Profil Klaster</th><th>Jumlah Mahasiswa</th><th>Rata-rata Emisi Transportasi</th><th>Rata-rata Emisi Elektronik</th><th>Rata-rata Emisi Makanan</th></tr>
        </thead><tbody>
            {segmentation_table_html}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {segmentation_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {segmentation_recommendation}</div>
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
            <div class="header-float-4"></div>  
            <div class="header-float-5"></div>              
            <div class="header-content">
                <h1 class="header-title">Dashboard Utama</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.25)

    df_transport_raw, df_electronic_raw, df_activities_raw, df_responden = load_all_data()
    
    if df_transport_raw.empty or df_electronic_raw.empty or df_activities_raw.empty:
        st.error("Satu atau lebih sumber data tidak tersedia.")
        return

    with loading():
        df_transport = df_transport_raw.copy()
        df_transport['emisi_transportasi'] = pd.to_numeric(df_transport['emisi_transportasi'], errors='coerce').fillna(0)
        df_transport['hari_datang'] = df_transport['hari_datang'].astype(str).fillna('')
        df_transport['jumlah_hari_datang'] = df_transport['hari_datang'].str.split(',').str.len()
        df_transport['emisi_mingguan'] = df_transport['emisi_transportasi'] * df_transport['jumlah_hari_datang']
        days_of_week = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
        for day in days_of_week:
            col_name = f'emisi_transportasi_{day}'
            df_transport[col_name] = np.where(df_transport['hari_datang'].str.contains(day.capitalize(), na=False), df_transport['emisi_transportasi'], 0)

        df_electronic = df_electronic_raw.copy()
        if 'emisi_elektronik' in df_electronic.columns:
            df_electronic = df_electronic.rename(columns={'emisi_elektronik': 'emisi_elektronik_mingguan'})
        df_electronic['emisi_elektronik_mingguan'] = pd.to_numeric(df_electronic['emisi_elektronik_mingguan'], errors='coerce').fillna(0)
        df_electronic['hari_datang'] = df_electronic['hari_datang'].astype(str).fillna('')
        df_electronic['jumlah_hari_datang'] = df_electronic['hari_datang'].str.split(',').str.len()
        df_electronic['emisi_harian'] = df_electronic['emisi_elektronik_mingguan'] / (df_electronic['jumlah_hari_datang'] + 1e-9)
        for day in days_of_week:
            col_name = f'emisi_elektronik_{day}'
            df_electronic[col_name] = np.where(df_electronic['hari_datang'].str.contains(day.capitalize(), na=False), df_electronic['emisi_harian'], 0)

        df_food = parse_food_activities(df_activities_raw)
        
        df_unified = create_unified_dataset(df_transport, df_electronic, df_food, df_responden)
        time.sleep(0.2)
    
    if df_unified.empty:
        st.warning("Tidak ada data gabungan yang dapat ditampilkan. Periksa sumber data.")
        return

    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])
    with filter_col1:
        selected_days = st.multiselect("Hari:", ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'], placeholder="Pilih Opsi", key='overview_day_filter')
    with filter_col2:
        selected_categories = st.multiselect("Jenis:", ['Transportasi', 'Elektronik', 'Sampah'], placeholder="Pilih Opsi", key='overview_category_filter')
    with filter_col3:
        available_fakultas = sorted(df_unified['fakultas'].unique())
        selected_fakultas = st.multiselect("Fakultas:", available_fakultas, placeholder="Pilih Opsi", key='overview_fakultas_filter')

    # 3. Terapkan filter ke data
    filtered_df = apply_overview_filters(df_unified, df_transport, df_electronic, df_food, selected_days, selected_categories, selected_fakultas)
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter."); return

    # Data untuk chart Fakultas
    fakultas_stats = filtered_df.groupby('fakultas')['total_emisi'].sum().reset_index()
    
    # Data untuk chart Tren Harian
    ids = filtered_df['id_responden']
    days_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    daily_data = []
    for day in days_order:
        row = {'day': day}
        for cat, df_source, col_prefix in [('transportasi', df_transport, 'emisi_transportasi_'), ('elektronik', df_electronic, 'emisi_elektronik_')]:
            col = f"{col_prefix}{day.lower()}"
            row[cat] = df_source.loc[df_source['id_responden'].isin(ids), col].sum() if not df_source.empty and col in df_source.columns else 0
        row['sampah_makanan'] = df_food.loc[(df_food['id_responden'].isin(ids)) & (df_food['day'] == day), 'emisi_makanan'].sum() if not df_food.empty else 0
        daily_data.append(row)
    daily_df = pd.DataFrame(daily_data)

    with export_col1:
        st.download_button(
            "Raw Data",
            filtered_df.to_csv(index=False),
            f"overview_filtered_{len(filtered_df)}.csv",
            "text/csv",
            use_container_width=True,
            key="overview_export_csv"
        )
    with export_col2:
        try:
            pdf_content = generate_overview_pdf_report(filtered_df, daily_df, fakultas_stats)
            st.download_button(
                "Laporan",
                pdf_content,
                f"overview_report_{len(filtered_df)}.html",
                "text/html",
                use_container_width=True,
                key="overview_export_pdf_final"
            )
        except Exception as e:
            st.error(f"Error generating PDF report: {e}")

    col1, col2, col3 = st.columns([1, 1, 1.5], gap="small")

    with col1:
        # KPI
        total_emisi = filtered_df['total_emisi'].sum()
        avg_emisi = filtered_df['total_emisi'].mean()
        st.markdown(f'<div class="kpi-card primary" style="margin-bottom: 1rem;"><div class="kpi-value">{total_emisi:.1f}</div><div class="kpi-label">Total Emisi (kg CO₂)</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card secondary" style="margin-bottom: 1.5rem;"><div class="kpi-value">{avg_emisi:.2f}</div><div class="kpi-label">Rata-rata/Mahasiswa</div></div>', unsafe_allow_html=True)
        
        fakultas_stats = filtered_df.groupby('fakultas')['total_emisi'].agg(['sum', 'count']).reset_index()
        fakultas_stats.columns = ['fakultas', 'total_emisi', 'count']
        fakultas_stats = fakultas_stats.sort_values('total_emisi', ascending=False)
        
        fakultas_stats_display = fakultas_stats.head(13).sort_values('total_emisi', ascending=True)

        fig_fakultas = go.Figure()

        for _, row in fakultas_stats_display.iterrows():
            max_emisi = fakultas_stats_display['total_emisi'].max()
            min_emisi = fakultas_stats_display['total_emisi'].min()
            if max_emisi > min_emisi:
                ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                color_idx = int(ratio * (len(color_palette) - 1))
                color = color_palette[color_idx]
            else:
                color = MAIN_PALETTE[0]

            fig_fakultas.add_trace(go.Bar(
                x=[row['total_emisi']], 
                y=[row['fakultas']], 
                orientation='h',
                marker=dict(color=color), 
                showlegend=False,
                text=[f"{row['total_emisi']:.1f}"], 
                textposition='inside',
                textfont=dict(color='white', size=10, weight='bold'),
                hovertemplate=f'<b>{row["fakultas"]}</b><br>Total Emisi: {row["total_emisi"]:.1f} kg CO₂<br>Jumlah Mahasiswa: {row["count"]}<extra></extra>'
            ))

        fig_fakultas.update_layout(
            height=382, 
            title_text="<b>Emisi per Fakultas</b>", 
            title_x=0.32,
            margin=dict(t=40, b=0, l=0, r=20), 
            xaxis_title="Total Emisi (kg CO₂)", 
            yaxis_title=None, 
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            yaxis=dict(showgrid=False)
        )        
        st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
        

    with col2:
        # Tren Emisi Harian dan Komposisi Emisi
        ids = filtered_df['id_responden']
        daily_data = []
        days_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        for day in days_order:
            day_data_row = {'day': day, 'transportasi': 0, 'elektronik': 0, 'sampah_makanan': 0}
            transport_col = f'emisi_transportasi_{day.lower()}'
            day_data_row['transportasi'] = df_transport[df_transport['id_responden'].isin(ids)][transport_col].sum() if not df_transport.empty and transport_col in df_transport.columns else 0
            electronic_col = f'emisi_elektronik_{day.lower()}'
            day_data_row['elektronik'] = df_electronic[df_electronic['id_responden'].isin(ids)][electronic_col].sum() if not df_electronic.empty and electronic_col in df_electronic.columns else 0
            day_data_row['sampah_makanan'] = df_food[(df_food['id_responden'].isin(ids)) & (df_food['day'] == day)]['emisi_makanan'].sum() if not df_food.empty else 0
            daily_data.append(day_data_row)
        daily_df = pd.DataFrame(daily_data)
        
        fig_trend = go.Figure()
        for cat in (selected_categories or list(CATEGORY_COLORS.keys())):
            col_name = cat.lower().replace(' ', '_')
            if col_name in daily_df.columns:
                fig_trend.add_trace(go.Scatter(x=daily_df['day'], y=daily_df[col_name], name=cat, mode='lines+markers', line=dict(color=CATEGORY_COLORS[cat])))
        
        fig_trend.update_layout(height=265, title_text="<b>Tren Emisi Harian</b>", title_x=0.32,
            margin=dict(t=40, b=0, l=0, r=0), legend_title_text='', yaxis_title="Emisi (kg CO₂)", xaxis_title=None,
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font_size=9))
        st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)

        
        categories_data = {'Transportasi': filtered_df['transportasi'].sum(), 'Elektronik': filtered_df['elektronik'].sum(), 'Sampah': filtered_df['sampah_makanan'].sum()}
        data_pie = {k: v for k, v in categories_data.items() if v > 0}
        
        if data_pie:
            fig_composition = go.Figure(go.Pie(
                labels=list(data_pie.keys()), 
                values=list(data_pie.values()), 
                hole=0.45, 
                marker=dict(
                    colors=[CATEGORY_COLORS.get(cat) for cat in data_pie.keys()],
                    line=dict(color='#FFFFFF', width=2) 
                ),
                textposition='outside', 
                textinfo='label+percent', 
                textfont=dict(size=10, family="Poppins"),
                hovertemplate='<b>%{label}</b><br>Emisi: %{value:.1f} kg CO₂ (%{percent})<extra></extra>' 
            ))

            total_emisi_pie = sum(data_pie.values())
            center_text = f"<b style='font-size:14px'>{total_emisi_pie:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
            fig_composition.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
            
            fig_composition.update_layout(
                height=280, 
                title_text="<b>Komposisi Emisi</b>", 
                title_x=0.32, 
                title_y=0.95,
                margin=dict(t=65, b=30, l=0, r=0), 
                showlegend=False 
            )

            st.plotly_chart(fig_composition, config=MODEBAR_CONFIG, use_container_width=True)
    
    with col3:
        # Segmentasi Profil Perilaku        
        if len(filtered_df) > 1:
            thresholds = {
                'transportasi': filtered_df['transportasi'].median(),
                'elektronik': filtered_df['elektronik'].median(),
                'sampah_makanan': filtered_df['sampah_makanan'].median()
            }
            
            filtered_df['profil_perilaku'] = filtered_df.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
            
            profile_counts = filtered_df['profil_perilaku'].value_counts().reset_index()
            profile_counts.columns = ['profil', 'jumlah']

            profile_color_map = {
                "Kontributor Utama": "#9e0142",       
                "Komuter & Digital": "#d53e4f",       
                "Komuter & Boros Pangan": "#f46d43",   
                "Digital & Boros Pangan": "#fdae61",   
                "Komuter Berat": "#fee08b",         
                "Pengguna Elektronik Berat": "#e6f598",
                "Boros Pangan": "#abdda4",            
                "Sangat Sadar Lingkungan": "#66c2a5", 
                "Profil Campuran": "#3288bd"          
            }

            fig_treemap = px.treemap(
                profile_counts,
                path=[px.Constant("Semua Profil"), 'profil'],
                values='jumlah',
                color='profil',
                color_discrete_map=profile_color_map,
                custom_data=['jumlah']
            )
            
            fig_treemap.update_traces(
                texttemplate="<b>%{label}</b><br>%{value} Mahasiswa",
                hovertemplate="<b>%{label}</b><br>Jumlah: %{customdata[0]} mahasiswa<extra></extra>",
                textfont=dict(size=14),
                insidetextfont=dict(size=16, color='black'), 
                marker=dict(line=dict(width=2, color='white'))
            )
            
            fig_treemap.update_layout(
                height=570,
                title_text="<b>Segmentasi Profil Perilaku</b>",
                title_x=0.33,
                margin = dict(t=30, l=5, r=5, b=10)
            )
            
            st.plotly_chart(fig_treemap, use_container_width=True, config=MODEBAR_CONFIG)

        else:
            st.info("Data tidak cukup untuk membuat segmentasi perilaku.")
            
        time.sleep(0.15)

if __name__ == "__main__":
    show()