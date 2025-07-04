import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
import warnings
warnings.filterwarnings('ignore')

# CONSISTENT COLOR PALETTE
MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

# Palet Warna
CATEGORY_COLORS = {'Transportasi': '#d53e4f', 'Elektronik': '#3288bd', 'Sampah Makanan': '#66c2a5'}
CLUSTER_COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
FACULTY_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5']

# K-MEANS CLUSTER COLORS
CLUSTER_COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']

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
    """Load all data sources for overview dashboard"""
    # Transportation data
    transport_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    
    # Electronic data
    electronic_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=622151341"
    
    # Daily activities data (for food waste)
    activities_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    
    # Responden data
    responden_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    
    try:
        time.sleep(0.4) 
        df_transport = pd.read_csv(transport_url)
        df_electronic = pd.read_csv(electronic_url)
        df_activities = pd.read_csv(activities_url)
        df_responden = pd.read_csv(responden_url)
        
        return df_transport, df_electronic, df_activities, df_responden
    except Exception as e:
        st.error(f"Error loading data: {e}")
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
    """Parse food waste activities from daily activities data"""
    food_activities = []
    
    if df_activities.empty:
        return pd.DataFrame()
    
    # Filter untuk kegiatan Makan atau Minum
    meal_df = df_activities[df_activities['kegiatan'].str.contains('Makan|Minum', case=False, na=False)] if 'kegiatan' in df_activities.columns else df_activities
    
    for _, row in meal_df.iterrows():
        # Parse hari column (format: senin_1012)
        hari_value = str(row.get('hari', ''))
        if '_' in hari_value:
            parts = hari_value.split('_')
            if len(parts) == 2:
                day_name = parts[0].capitalize()
                
                food_activities.append({
                    'id_responden': row.get('id_responden', ''),
                    'day': day_name,
                    'emisi_makanan': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce'),
                    'kategori': 'Sampah Makanan'
                })
    
    time.sleep(0.1)
    return pd.DataFrame(food_activities)

@loading_decorator()
def create_unified_dataset(df_transport, df_electronic, df_food, df_responden):
    """Create unified dataset for overview analysis"""
    unified_data = []
    
    # Add fakultas mapping
    fakultas_mapping = get_fakultas_mapping()
    if not df_responden.empty and 'program_studi' in df_responden.columns:
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
    
    # Process all respondents
    all_respondents = set()
    if not df_transport.empty and 'id_responden' in df_transport.columns:
        all_respondents.update(df_transport['id_responden'].dropna())
    if not df_electronic.empty and 'id_responden' in df_electronic.columns:
        all_respondents.update(df_electronic['id_responden'].dropna())
    if not df_food.empty and 'id_responden' in df_food.columns:
        all_respondents.update(df_food['id_responden'].dropna())
    
    for resp_id in all_respondents:
        if pd.isna(resp_id) or resp_id == '' or resp_id == 0:
            continue
            
        # Get responden info
        fakultas = 'Unknown'
        if not df_responden.empty and 'id_responden' in df_responden.columns:
            resp_info = df_responden[df_responden['id_responden'] == resp_id]
            if not resp_info.empty:
                fakultas = resp_info.iloc[0].get('fakultas', 'Unknown')
        
        # Transport emissions
        transport_emisi = 0
        if not df_transport.empty and 'id_responden' in df_transport.columns:
            transport_data = df_transport[df_transport['id_responden'] == resp_id]
            if not transport_data.empty and 'emisi_mingguan' in transport_data.columns:
                transport_emisi = transport_data['emisi_mingguan'].fillna(0).sum()
        
        # Electronic emissions
        electronic_emisi = 0
        if not df_electronic.empty and 'id_responden' in df_electronic.columns:
            electronic_data = df_electronic[df_electronic['id_responden'] == resp_id]
            if not electronic_data.empty and 'emisi_elektronik_mingguan' in electronic_data.columns:
                electronic_emisi = electronic_data['emisi_elektronik_mingguan'].fillna(0).sum()
        
        # Food emissions
        food_emisi = 0
        if not df_food.empty and 'id_responden' in df_food.columns:
            food_data = df_food[df_food['id_responden'] == resp_id]
            if not food_data.empty:
                food_emisi = food_data['emisi_makanan'].fillna(0).sum()
        
        total_emisi = transport_emisi + electronic_emisi + food_emisi
        
        if total_emisi > 0:  
            unified_data.append({
                'id_responden': resp_id,
                'fakultas': fakultas,
                'transportasi': transport_emisi,
                'elektronik': electronic_emisi,
                'sampah_makanan': food_emisi,
                'total_emisi': total_emisi
            })
    
    time.sleep(0.15)
    return pd.DataFrame(unified_data)

@loading_decorator()
def apply_overview_filters(df_unified, df_transport, df_electronic, df_food, selected_days, selected_categories, selected_fakultas):
    """Apply filters to all datasets - FIXED to work with all filters"""
    filtered_unified = df_unified.copy()
    
    # Filter by fakultas first
    if selected_fakultas:
        filtered_unified = filtered_unified[filtered_unified['fakultas'].isin(selected_fakultas)]
    
    # Filter by category - zero out non-selected categories
    if selected_categories:
        if 'Transportasi' not in selected_categories:
            filtered_unified['transportasi'] = 0
        if 'Elektronik' not in selected_categories:
            filtered_unified['elektronik'] = 0
        if 'Sampah Makanan' not in selected_categories:
            filtered_unified['sampah_makanan'] = 0
        
        # Recalculate total after category filtering
        filtered_unified['total_emisi'] = (
            filtered_unified['transportasi'] + 
            filtered_unified['elektronik'] + 
            filtered_unified['sampah_makanan']
        )
        
        # Remove rows with zero total emission after category filtering
        filtered_unified = filtered_unified[filtered_unified['total_emisi'] > 0]
    
    # Filter by days - complex logic to filter based on daily data
    if selected_days:
        valid_respondents = set(filtered_unified['id_responden'])
        day_filtered_respondents = set()
        
        # Check transport daily data
        if not df_transport.empty and 'Transportasi' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah Makanan']):
            for day in selected_days:
                day_col = f'emisi_transportasi_{day.lower()}'
                if day_col in df_transport.columns:
                    day_users = df_transport[df_transport[day_col] > 0]['id_responden'].dropna()
                    day_filtered_respondents.update(day_users)
        
        # Check food daily data
        if not df_food.empty and 'Sampah Makanan' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah Makanan']):
            day_food_users = df_food[df_food['day'].isin(selected_days)]['id_responden'].dropna()
            day_filtered_respondents.update(day_food_users)
        
        # For electronic, include all since it doesn't have daily breakdown
        if 'Elektronik' in (selected_categories or ['Transportasi', 'Elektronik', 'Sampah Makanan']):
            if not df_electronic.empty:
                electronic_users = df_electronic['id_responden'].dropna()
                day_filtered_respondents.update(electronic_users)
        
        # Apply day filter only for relevant respondents
        if day_filtered_respondents:
            valid_respondents = valid_respondents.intersection(day_filtered_respondents)
            filtered_unified = filtered_unified[filtered_unified['id_responden'].isin(valid_respondents)]
    
    time.sleep(0.1)
    return filtered_unified

@loading_decorator()
def calculate_gini_coefficient(emissions):
    """Calculate Gini coefficient for emission inequality"""
    emissions = np.array(emissions)
    emissions = emissions[emissions > 0]  
    
    if len(emissions) == 0:
        return 0
    
    # Sort emissions
    sorted_emissions = np.sort(emissions)
    n = len(sorted_emissions)
    
    # Calculate Gini coefficient
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_emissions)) / (n * np.sum(sorted_emissions)) - (n + 1) / n
    
    time.sleep(0.05)
    return gini


@loading_decorator()
def perform_kmeans_clustering(df_unified):
    """
    Perform K-means clustering on emission patterns.
    Revised to use 3 clusters and exclude total_emisi from features.
    """
    if df_unified.empty or len(df_unified) < 3:
        # Tidak cukup data untuk clustering
        return pd.DataFrame(), 0, pd.DataFrame()
    
    # Fitur yang digunakan untuk clustering
    features = ['transportasi', 'elektronik', 'sampah_makanan']
    X = df_unified[features].fillna(0)
    
    # Selalu coba 3 klaster jika data mencukupi
    n_clusters = 3
    
    # Standarisasi data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Lakukan K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    
    # Buat salinan DataFrame untuk menambahkan label klaster
    df_clustered = df_unified.copy()
    df_clustered['kmeans_cluster'] = kmeans.fit_predict(X_scaled)
    
    # Hitung pusat klaster dalam skala asli
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    centers_df = pd.DataFrame(cluster_centers, columns=features)
    
    # Tambahkan total emisi untuk sorting
    centers_df['total_emisi'] = centers_df.sum(axis=1)
    
    return df_clustered, n_clusters, centers_df

@loading_decorator()
def perform_kmeans_clustering(df_unified):
    """
    Perform K-means clustering on emission patterns.
    Revised to use 3 clusters and exclude total_emisi from features.
    """
    # Butuh setidaknya 3 data untuk 3 klaster, jika kurang, jangan lakukan clustering
    if df_unified.empty or len(df_unified) < 3:
        return df_unified, 0, pd.DataFrame()
    
    # Fitur untuk clustering, total_emisi dihilangkan agar tidak bias
    features = ['transportasi', 'elektronik', 'sampah_makanan']
    X = df_unified[features].fillna(0)
    
    # Tetapkan jumlah klaster menjadi 3 untuk analisis yang jelas
    # Atau 2 jika data sangat sedikit
    n_clusters = 3 if len(df_unified) >= 3 else 2

    # Lakukan standarisasi dan clustering
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    
    df_unified_copy = df_unified.copy()
    df_unified_copy['kmeans_cluster'] = kmeans.fit_predict(X_scaled)
    
    # Hitung pusat klaster dan kembalikan ke skala asli
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    centers_df = pd.DataFrame(cluster_centers, columns=features)
    
    # Hitung total emisi rata-rata per klaster untuk analisis
    centers_df['total_emisi'] = centers_df.sum(axis=1)
    
    return df_unified_copy, n_clusters, centers_df

@loading_decorator()
def perform_hierarchical_clustering(df_unified):
    """Perform Hierarchical clustering on emission patterns"""
    if df_unified.empty or len(df_unified) < 4:
        return df_unified, 0, []
    
    # Prepare data for clustering
    features = ['transportasi', 'elektronik', 'sampah_makanan', 'total_emisi']
    X = df_unified[features].fillna(0)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Determine optimal number of clusters (2-4)
    n_clusters = min(4, max(2, len(df_unified) // 4))
    
    # Perform hierarchical clustering
    hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    df_unified_copy = df_unified.copy()
    df_unified_copy['hierarchical_cluster'] = hierarchical.fit_predict(X_scaled)
    
    # Calculate cluster centers manually
    cluster_centers = []
    for i in range(n_clusters):
        cluster_data = X[df_unified_copy['hierarchical_cluster'] == i]
        center = cluster_data.mean()
        cluster_centers.append(center)
    
    centers_df = pd.DataFrame(cluster_centers, columns=features)
    
    time.sleep(0.1)
    return df_unified_copy, n_clusters, centers_df

@loading_decorator()
def categorize_emission_level(total_emisi):
    """Categorize respondents by emission level"""
    if total_emisi <= 5:
        return 'Emisi Rendah'
    elif total_emisi <= 15:
        return 'Emisi Sedang'
    elif total_emisi <= 30:
        return 'Emisi Tinggi'
    else:
        return 'Emisi Sangat Tinggi'

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

    # --- 1. Data Preparation & Insight Generation (Bagian lain tetap sama) ---
    total_emisi = filtered_df['total_emisi'].sum()
    avg_emisi = filtered_df['total_emisi'].mean()
    
    # Komposisi
    composition_data = {'Transportasi': filtered_df['transportasi'].sum(), 'Elektronik': filtered_df['elektronik'].sum(), 'Sampah Makanan': filtered_df['sampah_makanan'].sum()}
    dominant_cat = max(composition_data, key=composition_data.get) if total_emisi > 0 else "N/A"
    dominant_pct = (composition_data.get(dominant_cat, 0) / total_emisi * 100) if total_emisi > 0 else 0
    composition_conclusion = f"Sumber emisi utama adalah <strong>{dominant_cat}</strong>, menyumbang <strong>{dominant_pct:.1f}%</strong> dari total jejak karbon yang dianalisis."
    rec_map_cat = {'Transportasi': "Prioritaskan kebijakan transportasi ramah lingkungan.", 'Elektronik': "Implementasikan kebijakan hemat energi di seluruh kampus.", 'Sampah Makanan': "Luncurkan program komprehensif untuk manajemen limbah makanan."}
    composition_recommendation = rec_map_cat.get(dominant_cat, "Analisis lebih lanjut diperlukan.")

    # Tren Harian
    peak_day = "N/A"
    if not daily_df.empty:
        daily_totals = daily_df.set_index('day').sum(axis=1)
        peak_day = daily_totals.idxmax() if not daily_totals.empty else "N/A"
    trend_conclusion = f"Aktivitas emisi memuncak pada hari <strong>{peak_day}</strong>."
    trend_recommendation = f"Selidiki aktivitas spesifik pada hari <strong>{peak_day}</strong> yang menyebabkan lonjakan emisi. Pertimbangkan untuk mengadakan kampanye hemat energi pada hari tersebut."

    # Fakultas
    fakultas_report = pd.DataFrame()
    fakultas_conclusion = "Data fakultas tidak cukup untuk dianalisis."
    fakultas_recommendation = ""
    if not fakultas_stats_full.empty and len(fakultas_stats_full) > 1:
        fakultas_report = fakultas_stats_full.sort_values('total_emisi', ascending=False)
        highest_fakultas_row = fakultas_report.iloc[0]
        lowest_fakultas_row = fakultas_report.iloc[-1]
        fakultas_conclusion = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> menunjukkan total emisi tertinggi, sementara <strong>{lowest_fakultas_row['fakultas']}</strong> mencatat yang terendah."
        fakultas_recommendation = f"Bentuk tim studi banding antara fakultas <strong>{highest_fakultas_row['fakultas']}</strong> dan <strong>{lowest_fakultas_row['fakultas']}</strong> untuk mengidentifikasi praktik terbaik dan area perbaikan."

    # --- Insight 4: Segmentasi Perilaku (REVISI BESAR DI SINI) ---
    df_clustered, n_clusters, centers_df = perform_kmeans_clustering(filtered_df.copy())
    
    segmentation_table_html = "<tr><td colspan='5'>Data tidak cukup untuk segmentasi (minimal 3 responden).</td></tr>"
    segmentation_conclusion = "Data tidak mencukupi untuk membuat profil segmen mahasiswa yang bermakna."
    segmentation_recommendation = "Diperlukan lebih banyak data responden untuk analisis segmentasi yang valid."

    if n_clusters == 3:
        # Menghitung jumlah anggota di setiap klaster
        cluster_counts = df_clustered['kmeans_cluster'].value_counts()
        centers_df['count'] = centers_df.index.map(cluster_counts)
        
        # Mengurutkan pusat klaster berdasarkan total emisi untuk konsistensi
        centers_df = centers_df.sort_values('total_emisi', ascending=True)
        
        # Mendefinisikan nama profil dan rekomendasi secara eksplisit
        profile_names = ["Profil 1: Emitor Rendah", "Profil 2: Emitor Sedang", "Profil 3: Emitor Tinggi"]
        recommendations_map = {
            "Profil 1: Emitor Rendah": "Kelompok ini adalah contoh baik. Berikan apresiasi atau gamifikasi untuk mempertahankan perilaku rendah karbon mereka.",
            "Profil 2: Emitor Sedang": "Fokus pada edukasi mengenai area emisi dominan mereka (misalnya, transportasi atau elektronik) untuk membantu mereka mengurangi jejak karbon.",
            "Profil 3: Emitor Tinggi": "Klaster ini adalah prioritas utama. Intervensi harus intensif dan mungkin personal untuk mendorong perubahan perilaku yang signifikan."
        }
        
        # Membuat tabel HTML dari data yang sudah diurutkan
        table_rows = []
        for i, (original_idx, row) in enumerate(centers_df.iterrows()):
            table_rows.append(f"""
            <tr>
                <td><strong>{profile_names[i]}</strong></td>
                <td style='text-align:center;'>{int(row.get('count', 0))}</td>
                <td style='text-align:right;'>{row['transportasi']:.1f}</td>
                <td style='text-align:right;'>{row['elektronik']:.1f}</td>
                <td style='text-align:right;'>{row['sampah_makanan']:.1f}</td>
                <td style='text-align:right;'><strong>{row['total_emisi']:.1f}</strong></td>
            </tr>""")
        segmentation_table_html = "".join(table_rows)
        
        # Membuat Kesimpulan & Rekomendasi
        segmentation_conclusion = (
            f"Analisis berhasil mengidentifikasi <strong>3 segmen perilaku</strong> yang berbeda. "
            f"Segmen 'Emitor Tinggi' ({int(centers_df.iloc[2].get('count', 0))} mahasiswa) memiliki dampak emisi terbesar, "
            f"sementara segmen 'Emitor Rendah' ({int(centers_df.iloc[0].get('count', 0))} mahasiswa) menunjukkan perilaku paling ideal."
        )
        
        recs_list = [f"<li><strong>{name}:</strong> {recommendations_map[name]}</li>" for name in profile_names]
        segmentation_recommendation = f"Alih-alih pendekatan 'satu untuk semua', alokasikan sumber daya sesuai profil segmen: <ul>{''.join(recs_list)}</ul>"

    # --- HTML Generation ---
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
    # Header with loading
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

    # Load all data with loading
    df_transport, df_electronic, df_activities, df_responden = load_all_data()
    
    if df_transport.empty and df_electronic.empty and df_activities.empty:
        st.error("Data tidak tersedia")
        return

    # Parse food data and create unified dataset with loading
    with loading():
        df_food = parse_food_activities(df_activities)
        df_unified = create_unified_dataset(df_transport, df_electronic, df_food, df_responden)
        time.sleep(0.2)
    
    if df_unified.empty:
        st.error("Tidak ada data unified yang tersedia")
        return

    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])
    with filter_col1:
        selected_days = st.multiselect("Hari:", ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'], key='overview_day_filter')
    with filter_col2:
        selected_categories = st.multiselect("Jenis:", ['Transportasi', 'Elektronik', 'Sampah Makanan'], key='overview_category_filter')
    with filter_col3:
        available_fakultas = sorted(df_unified['fakultas'].unique())
        selected_fakultas = st.multiselect("Fakultas:", available_fakultas, key='overview_fakultas_filter')

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
    # --- AKHIR DARI BLOK KALKULASI DATA ---

    # 5. Tampilkan tombol Export
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
        # --- KOLOM 1: KPI & FAKULTAS ---
        total_emisi = filtered_df['total_emisi'].sum()
        avg_emisi = filtered_df['total_emisi'].mean()
        st.markdown(f'<div class="kpi-card primary" style="margin-bottom: 1rem;"><div class="kpi-value">{total_emisi:.1f}</div><div class="kpi-label">Total Emisi (kg CO₂)</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card secondary" style="margin-bottom: 1.5rem;"><div class="kpi-value">{avg_emisi:.2f}</div><div class="kpi-label">Rata-rata/Mahasiswa</div></div>', unsafe_allow_html=True)
        
        fakultas_stats = filtered_df.groupby('fakultas')['total_emisi'].sum().reset_index().sort_values('total_emisi', ascending=False)
        color_palette = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5']
        n_fakultas = len(fakultas_stats)
        colors = [color_palette[int(i / (n_fakultas - 1) * (len(color_palette) - 1))] if n_fakultas > 1 else color_palette[0] for i in range(n_fakultas)]
        fakultas_stats['color'] = colors
        fakultas_stats = fakultas_stats.sort_values('total_emisi', ascending=True)

        fig_fakultas = go.Figure(go.Bar(
            x=fakultas_stats['total_emisi'], y=fakultas_stats['fakultas'],
            orientation='h', marker_color=fakultas_stats['color']
        ))
        fig_fakultas.update_layout(height=382, title_text="<b>Emisi per Fakultas</b>", title_x=0.32,
            margin=dict(t=40, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, showlegend=False)
        st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
        

    with col2:
        # --- KOLOM 2: TREN & KOMPOSISI ---
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

        
        categories_data = {'Transportasi': filtered_df['transportasi'].sum(), 'Elektronik': filtered_df['elektronik'].sum(), 'Sampah Makanan': filtered_df['sampah_makanan'].sum()}
        data_pie = {k: v for k, v in categories_data.items() if v > 0}
        
        if data_pie:
            fig_composition = go.Figure(go.Pie(
                labels=list(data_pie.keys()), values=list(data_pie.values()), hole=0.5,
                marker_colors=[CATEGORY_COLORS.get(cat) for cat in data_pie.keys()]
            ))
            fig_composition.update_layout(height=280, title_text="<b>Komposisi Emisi</b>", title_x=0.32, title_y=0.95,
                margin=dict(t=40, b=0, l=0, r=0), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(size=9))
            )
            st.plotly_chart(fig_composition, config=MODEBAR_CONFIG, use_container_width=True)
    
    with col3:
        # --- KOLOM 3: CLUSTERING 3D (REVISED FOR 3 PROFILES) ---
        if len(filtered_df) >= 3:
            df_clustered, n_clusters, centers_df = perform_kmeans_clustering(filtered_df.copy())
            
            fig_3d = go.Figure()

            if n_clusters == 3:
                # --- Logika Penamaan & Pewarnaan Klaster Baru ---
                # 1. Urutkan pusat klaster berdasarkan total emisi
                centers_df = centers_df.sort_values('total_emisi')
                
                # 2. Definisikan nama dan warna secara eksplisit
                profile_names = ["Profil 1: Emitor Rendah", "Profil 2: Emitor Sedang", "Profil 3: Emitor Tinggi"]
                profile_colors = ['#4daf4a', '#ff7f00', '#e41a1c'] # Hijau, Oren, Merah

                # 3. Buat pemetaan dari ID klaster asli ke profil baru
                name_map = {original_idx: name for original_idx, name in zip(centers_df.index, profile_names)}
                color_map = {original_idx: color for original_idx, color in zip(centers_df.index, profile_colors)}
                
                # 4. Tambahkan trace ke plot dengan urutan yang benar (Rendah -> Sedang -> Tinggi)
                for original_idx in centers_df.index:
                    cluster_data = df_clustered[df_clustered['kmeans_cluster'] == original_idx]
                    fig_3d.add_trace(go.Scatter3d(
                        x=cluster_data['transportasi'],
                        y=cluster_data['elektronik'],
                        z=cluster_data['sampah_makanan'],
                        mode='markers', 
                        name=name_map.get(original_idx),
                        marker=dict(size=5, color=color_map.get(original_idx))
                    ))
            
            # Update layout figur
            fig_3d.update_layout(
                height=570, 
                title_text="<b>Segmentasi Perilaku Emisi</b>", 
                title_x=0.5,
                margin=dict(l=0, r=0, b=0, t=40),
                scene=dict(
                    xaxis_title='Transportasi', yaxis_title='Elektronik', zaxis_title='Sampah',
                    xaxis_title_font=dict(size=9), yaxis_title_font=dict(size=9), zaxis_title_font=dict(size=9),
                    aspectratio=dict(x=1, y=1, z=0.8)),
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, 
                    font_size=9, itemsizing='constant'
                )
            )
            st.plotly_chart(fig_3d, use_container_width=True, config=MODEBAR_CONFIG)
        else:
            st.info("Data tidak cukup untuk clustering (minimal 3 data).")

            
        time.sleep(0.15)

if __name__ == "__main__":
    show()