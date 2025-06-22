import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from loading import loading, loading_decorator
import time
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
import warnings
warnings.filterwarnings('ignore')

# CONSISTENT COLOR PALETTE
MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

CATEGORY_COLORS = {
    'Transportasi': '#d53e4f',
    'Elektronik': '#3288bd', 
    'Sampah Makanan': '#66c2a5'
}

# K-MEANS CLUSTER COLORS
CLUSTER_COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']

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
        time.sleep(0.4)  # Simulate loading time
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
        'Informatika': 'STEI', 'Teknik Telekomunikasi': 'STEI', 'Teknik Tenaga Listrik': 'STEI'
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
        
        if total_emisi > 0:  # Only include if there's actual emission data
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
        
        # Apply day filter only if we found relevant respondents
        if day_filtered_respondents:
            valid_respondents = valid_respondents.intersection(day_filtered_respondents)
            filtered_unified = filtered_unified[filtered_unified['id_responden'].isin(valid_respondents)]
    
    time.sleep(0.1)
    return filtered_unified

@loading_decorator()
def calculate_gini_coefficient(emissions):
    """Calculate Gini coefficient for emission inequality"""
    emissions = np.array(emissions)
    emissions = emissions[emissions > 0]  # Remove zero emissions
    
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
    """Perform K-means clustering on emission patterns"""
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
    
    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df_unified_copy = df_unified.copy()
    df_unified_copy['kmeans_cluster'] = kmeans.fit_predict(X_scaled)
    
    # Calculate cluster centers in original scale
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    centers_df = pd.DataFrame(cluster_centers, columns=features)
    
    time.sleep(0.1)
    return df_unified_copy, n_clusters, centers_df

@loading_decorator()
def perform_pairwise_kmeans_clustering(df_unified, feature1, feature2):
    """Perform K-means clustering specifically for two emission categories"""
    if df_unified.empty or len(df_unified) < 4:
        return df_unified, 0, []
    
    # Prepare data for clustering with just two features
    features = [feature1, feature2]
    X = df_unified[features].fillna(0)
    
    # Remove rows where both features are zero
    X = X[(X[feature1] > 0) | (X[feature2] > 0)]
    if len(X) < 4:
        return df_unified, 0, []
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Determine optimal number of clusters using elbow method
    wcss_values = []
    k_range = range(1, min(6, len(X)))
    
    for k in k_range:
        if k == 1:
            wcss_values.append(np.sum((X_scaled - X_scaled.mean(axis=0))**2))
        else:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X_scaled)
            wcss_values.append(kmeans.inertia_)
    
    # Find elbow point (simplified method)
    if len(wcss_values) >= 3:
        # Calculate rate of change
        deltas = [wcss_values[i-1] - wcss_values[i] for i in range(1, len(wcss_values))]
        # Find point where improvement starts to slow down significantly
        optimal_k = 2
        if len(deltas) >= 2:
            for i in range(1, len(deltas)):
                if deltas[i] < deltas[i-1] * 0.3:  # Less than 30% improvement
                    optimal_k = i + 1
                    break
            optimal_k = min(optimal_k, 4)  # Cap at 4 clusters
    else:
        optimal_k = min(3, len(X) // 2)
    
    # Perform final clustering
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    # Create result dataframe
    df_result = df_unified.copy()
    df_result['pairwise_cluster'] = -1  # Initialize with -1 for non-clustered points
    
    # Map cluster labels back to original dataframe
    valid_indices = X.index
    df_result.loc[valid_indices, 'pairwise_cluster'] = cluster_labels
    
    # Calculate cluster centers in original scale
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    centers_df = pd.DataFrame(cluster_centers, columns=features)
    
    time.sleep(0.05)
    return df_result, optimal_k, centers_df

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
def generate_overview_pdf_report(filtered_df, selected_days, selected_categories, selected_fakultas):
    """Generate comprehensive overview PDF report based on FILTERED data"""
    from datetime import datetime
    
    time.sleep(0.6)  # Complex report generation
    
    # Calculate metrics from FILTERED data
    total_emisi = filtered_df['total_emisi'].sum()
    avg_emisi = filtered_df['total_emisi'].mean()
    total_responden = len(filtered_df)
    transport_total = filtered_df['transportasi'].sum()
    electronic_total = filtered_df['elektronik'].sum()
    food_total = filtered_df['sampah_makanan'].sum()
    
    transport_pct = (transport_total / total_emisi * 100) if total_emisi > 0 else 0
    electronic_pct = (electronic_total / total_emisi * 100) if total_emisi > 0 else 0
    food_pct = (food_total / total_emisi * 100) if total_emisi > 0 else 0
    
    # Calculate Gini coefficient from filtered data
    gini_coeff = calculate_gini_coefficient(filtered_df['total_emisi'])
    
    # Faculty analysis from filtered data
    fakultas_stats = filtered_df.groupby('fakultas')['total_emisi'].agg(['sum', 'mean', 'count']).round(2)
    fakultas_stats.columns = ['total_emisi', 'rata_rata_emisi', 'jumlah_mahasiswa']
    fakultas_stats = fakultas_stats.sort_values('rata_rata_emisi', ascending=False)
    
    # Applied filters summary
    filter_summary = []
    if selected_days:
        filter_summary.append(f"Hari: {', '.join(selected_days)}")
    if selected_categories:
        filter_summary.append(f"Kategori: {', '.join(selected_categories)}")
    if selected_fakultas:
        filter_summary.append(f"Fakultas: {', '.join(selected_fakultas)}")
    
    filter_text = "; ".join(filter_summary) if filter_summary else "Semua data"
    
    # Clustering on filtered data - hanya untuk laporan
    df_kmeans, n_clusters_kmeans, _ = perform_kmeans_clustering(filtered_df)
    df_hierarchical, n_clusters_hierarchical, _ = perform_hierarchical_clustering(filtered_df)
    
    cluster_stats_kmeans = df_kmeans.groupby('kmeans_cluster')['total_emisi'].agg(['count', 'mean']).round(2) if n_clusters_kmeans > 0 else pd.DataFrame()
    cluster_stats_hierarchical = df_hierarchical.groupby('hierarchical_cluster')['total_emisi'].agg(['count', 'mean']).round(2) if n_clusters_hierarchical > 0 else pd.DataFrame()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Overview Emisi Karbon ITB</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            @page {{
                size: A4;
                margin: 15mm;
            }}
            
            @media print {{
                body {{
                    -webkit-print-color-adjust: exact !important;
                    color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }}
                
                .no-print {{
                    display: none !important;
                }}
                
                .page-break {{
                    page-break-before: always;
                }}
                
                .avoid-break {{
                    page-break-inside: avoid;
                }}
            }}
            
            body {{
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
                line-height: 1.4;
                color: #1f2937;
                margin: 0;
                padding: 0;
                font-size: 11px;
                background: white;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 25px;
                padding: 20px 0;
                border-bottom: 2px solid #16a34a;
            }}
            
            .header h1 {{
                font-size: 20px;
                font-weight: 600;
                color: #16a34a;
                margin: 0 0 8px 0;
            }}
            
            .header .subtitle {{
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 5px;
                font-weight: 400;
            }}
            
            .header .timestamp {{
                font-size: 9px;
                color: #9ca3af;
                font-weight: 300;
            }}
            
            .print-instruction {{
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 20px;
                text-align: center;
                font-weight: 500;
                color: #16a34a;
                font-size: 10px;
            }}
            
            .filter-summary {{
                background: #e0f2fe;
                border: 1px solid #0288d1;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 20px;
                font-size: 10px;
                color: #01579b;
            }}
            
            .executive-summary {{
                background: #fafafa;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 20px;
                margin-bottom: 25px;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-bottom: 10px;
            }}
            
            .metric-card {{
                background: white;
                border: 1px solid #16a34a;
                border-radius: 6px;
                padding: 15px;
                text-align: center;
            }}
            
            .metric-value {{
                font-size: 20px;
                font-weight: 600;
                color: #16a34a;
                margin-bottom: 4px;
                display: block;
            }}
            
            .metric-label {{
                font-size: 9px;
                color: #6b7280;
                font-weight: 400;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .section {{
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
            
            .section-title {{
                font-size: 13px;
                font-weight: 600;
                color: #16a34a;
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid #16a34a;
            }}
            
            .section-content {{
                background: #fafafa;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 15px;
            }}
            
            .conclusion {{
                background: #f0fdf4;
                border-left: 3px solid #16a34a;
                padding: 10px;
                margin-top: 10px;
                font-style: italic;
                color: #374151;
                font-size: 10px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
                background: white;
                font-size: 9px;
            }}
            
            th {{
                background: #16a34a !important;
                color: white !important;
                padding: 8px 5px;
                text-align: center;
                font-weight: 500;
                border: 1px solid #16a34a;
                font-size: 8px;
            }}
            
            td {{
                padding: 6px 5px;
                text-align: center;
                border: 1px solid #e5e7eb;
                font-size: 8px;
            }}
            
            tr:nth-child(even) {{
                background: #f9fafb !important;
            }}
            
            .footer {{
                margin-top: 25px;
                padding-top: 15px;
                border-top: 1px solid #16a34a;
                text-align: center;
                font-size: 9px;
                color: #6b7280;
                page-break-inside: avoid;
            }}
        </style>
    </head>
    <body>
        <div class="print-instruction no-print">
            <strong>Export PDF:</strong> Tekan Ctrl+P (Windows) atau Cmd+P (Mac), pilih "Save as PDF", lalu klik Save
        </div>
        
        <div class="header">
            <h1>LAPORAN OVERVIEW EMISI KARBON ITB</h1>
            <div class="subtitle">Institut Teknologi Bandung - Dashboard Utama</div>
            <div class="timestamp">Dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M WIB')}</div>
        </div>
        
        <div class="filter-summary">
            <strong>Filter Aktif:</strong> {filter_text}
        </div>
        
        <div class="executive-summary avoid-break">
            <h2 style="margin-top: 0; color: #16a34a; font-size: 14px; font-weight: 600;">Ringkasan Eksekutif</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{total_emisi:.1f}</span>
                    <div class="metric-label">Total Emisi Kampus (kg CO₂)</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{avg_emisi:.2f}</span>
                    <div class="metric-label">Rata-rata per Mahasiswa</div>
                </div>
            </div>
            <p style="margin-top: 15px; font-size: 10px; color: #6b7280; text-align: center;">
                Analisis berdasarkan {total_responden} mahasiswa dengan filter yang diterapkan
            </p>
        </div>
        
        <!-- 1. Komposisi Emisi per Kategori -->
        <div class="section avoid-break">
            <h2 class="section-title">1. Komposisi Emisi per Kategori</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Kategori</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Persentase (%)</th>
                            <th>Rata-rata per Mahasiswa</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Transportasi</td>
                            <td>{transport_total:.1f}</td>
                            <td>{transport_pct:.1f}%</td>
                            <td>{(transport_total/total_responden):.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Elektronik</td>
                            <td>{electronic_total:.1f}</td>
                            <td>{electronic_pct:.1f}%</td>
                            <td>{(electronic_total/total_responden):.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Sampah Makanan</td>
                            <td>{food_total:.1f}</td>
                            <td>{food_pct:.1f}%</td>
                            <td>{(food_total/total_responden):.2f}</td>
                        </tr>
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> Berdasarkan filter yang diterapkan, kategori dengan kontribusi terbesar adalah {'Transportasi' if transport_pct > electronic_pct and transport_pct > food_pct else 'Elektronik' if electronic_pct > food_pct else 'Sampah Makanan'} ({max(transport_pct, electronic_pct, food_pct):.1f}% dari total emisi).
                </div>
            </div>
        </div>
        
        <!-- 2. Ranking Fakultas -->
        <div class="section avoid-break">
            <h2 class="section-title">2. Ranking Emisi per Fakultas</h2>
            <div class="section-content">
    """
    
    if not fakultas_stats.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Fakultas</th>
                            <th>Mahasiswa</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Rata-rata Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (fakultas, row) in enumerate(fakultas_stats.head(10).iterrows(), 1):
            html_content += f"""
                            <tr>
                                <td><strong>#{idx}</strong></td>
                                <td style="text-align: left; font-weight: 500;">{fakultas}</td>
                                <td>{row['jumlah_mahasiswa']}</td>
                                <td>{row['total_emisi']:.1f}</td>
                                <td>{row['rata_rata_emisi']:.2f}</td>
                            </tr>
            """
        
        html_content += "</tbody></table>"
        
        highest_fakultas = fakultas_stats.index[0]
        lowest_fakultas = fakultas_stats.index[-1]
        fakultas_conclusion = f"{highest_fakultas} memiliki rata-rata emisi tertinggi ({fakultas_stats.iloc[0]['rata_rata_emisi']:.2f} kg CO₂), sedangkan {lowest_fakultas} terendah ({fakultas_stats.iloc[-1]['rata_rata_emisi']:.2f} kg CO₂)."
    else:
        html_content += "<p>Data fakultas tidak tersedia dengan filter yang diterapkan.</p>"
        fakultas_conclusion = "Data fakultas tidak tersedia dengan filter yang diterapkan."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {fakultas_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 3. Analisis Distribusi dan Ketimpangan -->
        <div class="section avoid-break">
            <h2 class="section-title">3. Analisis Distribusi dan Ketimpangan (Gini Coefficient)</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Metrik</th>
                            <th>Nilai</th>
                            <th>Interpretasi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Gini Coefficient</td>
                            <td>{gini_coeff:.3f}</td>
                            <td>{'Rendah (merata)' if gini_coeff < 0.3 else 'Sedang' if gini_coeff < 0.5 else 'Tinggi (timpang)'}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Total Responden</td>
                            <td>{total_responden} mahasiswa</td>
                            <td>Data setelah filtering</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Range Emisi</td>
                            <td>{filtered_df['total_emisi'].min():.1f} - {filtered_df['total_emisi'].max():.1f} kg CO₂</td>
                            <td>Minimum hingga maksimum</td>
                        </tr>
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> Berdasarkan data yang difilter, distribusi emisi menunjukkan tingkat ketimpangan {'rendah' if gini_coeff < 0.3 else 'sedang' if gini_coeff < 0.5 else 'tinggi'} (Gini = {gini_coeff:.3f}).
                </div>
            </div>
        </div>
    """
    
    # Add clustering sections
    if n_clusters_kmeans > 0 and not cluster_stats_kmeans.empty:
        html_content += f"""
        <!-- 4. K-Means Clustering Responden -->
        <div class="section avoid-break">
            <h2 class="section-title">4. K-Means Clustering Pola Emisi Responden</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Klaster</th>
                            <th>Jumlah Responden</th>
                            <th>Rata-rata Emisi</th>
                            <th>Kategori</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        cluster_stats_kmeans.columns = ['jumlah_responden', 'rata_rata_emisi']
        for cluster_id, row in cluster_stats_kmeans.iterrows():
            category = categorize_emission_level(row['rata_rata_emisi'])
            html_content += f"""
                            <tr>
                                <td><strong>Klaster {cluster_id + 1}</strong></td>
                                <td>{row['jumlah_responden']}</td>
                                <td>{row['rata_rata_emisi']:.2f}</td>
                                <td>{category}</td>
                            </tr>
            """
        
        html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> K-Means berhasil mengidentifikasi {n_clusters_kmeans} klaster dengan pola emisi yang berbeda pada data yang difilter.
                </div>
            </div>
        </div>
        """
    
    if n_clusters_hierarchical > 0 and not cluster_stats_hierarchical.empty:
        html_content += f"""
        <!-- 5. Hierarchical Clustering Responden -->
        <div class="section avoid-break">
            <h2 class="section-title">5. Hierarchical Clustering Pola Emisi Responden</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Klaster</th>
                            <th>Jumlah Responden</th>
                            <th>Rata-rata Emisi</th>
                            <th>Kategori</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        cluster_stats_hierarchical.columns = ['jumlah_responden', 'rata_rata_emisi']
        for cluster_id, row in cluster_stats_hierarchical.iterrows():
            category = categorize_emission_level(row['rata_rata_emisi'])
            html_content += f"""
                            <tr>
                                <td><strong>Klaster {cluster_id + 1}</strong></td>
                                <td>{row['jumlah_responden']}</td>
                                <td>{row['rata_rata_emisi']:.2f}</td>
                                <td>{category}</td>
                            </tr>
            """
        
        html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> Hierarchical clustering berhasil mengidentifikasi {n_clusters_hierarchical} klaster dengan pola emisi yang berbeda, memberikan perspektif alternatif dalam segmentasi responden.
                </div>
            </div>
        </div>
        """
    
    html_content += """
        <div class="footer">
            <p><strong>Institut Teknologi Bandung</strong></p>
            <p>Carbon Emission Dashboard - Overview Report</p>
        </div>
    </body>
    </html>
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

    # Filters - UPDATED: periode -> jenis
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:", 
            options=day_options, 
            placeholder="Pilih Opsi", 
            key='overview_day_filter'
        )
    
    with filter_col2:
        # CHANGED: periode -> jenis/kategori
        category_options = ['Transportasi', 'Elektronik', 'Sampah Makanan']
        selected_categories = st.multiselect(
            "Jenis:", 
            options=category_options, 
            placeholder="Pilih Opsi", 
            key='overview_category_filter'
        )
    
    with filter_col3:
        if not df_responden.empty and 'program_studi' in df_responden.columns:
            fakultas_mapping = get_fakultas_mapping()
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            available_fakultas = sorted(df_responden['fakultas'].unique())
            selected_fakultas = st.multiselect(
                "Fakultas:", 
                options=available_fakultas, 
                placeholder="Pilih Opsi", 
                key='overview_fakultas_filter'
            )
        else:
            selected_fakultas = []

    # Apply filters with loading - FIXED function call
    filtered_df = apply_overview_filters(df_unified, df_transport, df_electronic, df_food, selected_days, selected_categories, selected_fakultas)

    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return

    # Export buttons - FIXED to use filtered data
    with export_col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Raw Data", 
            data=csv_data, 
            file_name=f"overview_filtered_{len(filtered_df)}.csv", 
            mime="text/csv", 
            use_container_width=True, 
            key="overview_export_csv"
        )
    
    with export_col2:
        try:
            pdf_content = generate_overview_pdf_report(filtered_df, selected_days, selected_categories, selected_fakultas)
            st.download_button(
                "Laporan", 
                data=pdf_content, 
                file_name=f"overview_filtered_{len(filtered_df)}.html", 
                mime="text/html", 
                use_container_width=True, 
                key="overview_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    # Calculate metrics from FILTERED data
    total_emisi = filtered_df['total_emisi'].sum()
    avg_emisi = filtered_df['total_emisi'].mean()
    gini_coeff = calculate_gini_coefficient(filtered_df['total_emisi'])

    # KPI Cards with loading - using FILTERED data
    with loading():
        kpi_col1, kpi_col2 = st.columns([1, 1])
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card primary">
                <div class="kpi-value">{total_emisi:.1f}</div>
                <div class="kpi-label">Total Emisi Kampus (kg CO₂)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card secondary">
                <div class="kpi-value">{avg_emisi:.2f}</div>
                <div class="kpi-label">Rata-rata Emisi per Mahasiswa</div>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(0.15)

    # Row 1: Main Charts with loading - ALL using FILTERED data
    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 1. Tren Emisi Harian - using FILTERED data
            daily_data = []
            days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            
            # If days filter is applied, only show selected days
            if selected_days:
                days_to_show = selected_days
            else:
                days_to_show = days
            
            # Calculate daily emissions from filtered transport data
            filtered_transport_ids = set(filtered_df['id_responden'])
            filtered_transport = df_transport[df_transport['id_responden'].isin(filtered_transport_ids)] if not df_transport.empty else pd.DataFrame()
            filtered_food = df_food[df_food['id_responden'].isin(filtered_transport_ids)] if not df_food.empty else pd.DataFrame()
            
            for day in days_to_show:
                day_transport = 0
                day_col = f'emisi_transportasi_{day.lower()}'
                if not filtered_transport.empty and day_col in filtered_transport.columns:
                    day_transport = filtered_transport[day_col].sum()
                
                # Electronic - distribute weekly evenly for filtered responden
                day_electronic = filtered_df['elektronik'].sum() / 7
                
                # Food for specific day
                day_food = 0
                if not filtered_food.empty:
                    day_food_data = filtered_food[filtered_food['day'] == day]
                    day_food = day_food_data['emisi_makanan'].sum()
                
                # Apply category filter
                if selected_categories:
                    if 'Transportasi' not in selected_categories:
                        day_transport = 0
                    if 'Elektronik' not in selected_categories:
                        day_electronic = 0
                    if 'Sampah Makanan' not in selected_categories:
                        day_food = 0
                
                daily_data.append({
                    'day': day,
                    'transportasi': day_transport,
                    'elektronik': day_electronic,
                    'sampah_makanan': day_food,
                    'total': day_transport + day_electronic + day_food
                })
            
            daily_df = pd.DataFrame(daily_data)
            
            fig_trend = go.Figure()
            
            # Only add traces for selected categories (or all if none selected)
            categories_to_show = selected_categories if selected_categories else ['Transportasi', 'Elektronik', 'Sampah Makanan']
            
            if 'Transportasi' in categories_to_show:
                fig_trend.add_trace(go.Scatter(
                    x=daily_df['day'], y=daily_df['transportasi'],
                    mode='lines+markers', name='Transportasi',
                    line=dict(color=CATEGORY_COLORS['Transportasi'], width=2),
                    marker=dict(size=6)
                ))
            
            if 'Elektronik' in categories_to_show:
                fig_trend.add_trace(go.Scatter(
                    x=daily_df['day'], y=daily_df['elektronik'],
                    mode='lines+markers', name='Elektronik',
                    line=dict(color=CATEGORY_COLORS['Elektronik'], width=2),
                    marker=dict(size=6)
                ))
            
            if 'Sampah Makanan' in categories_to_show:
                fig_trend.add_trace(go.Scatter(
                    x=daily_df['day'], y=daily_df['sampah_makanan'],
                    mode='lines+markers', name='Sampah Makanan',
                    line=dict(color=CATEGORY_COLORS['Sampah Makanan'], width=2),
                    marker=dict(size=6)
                ))
            
            fig_trend.update_layout(
                height=235, margin=dict(t=25, b=0, l=0, r=20),
                title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                          font=dict(size=11, color="#000000")),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10))),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (kg CO₂)", font=dict(size=10))),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=8)),
                showlegend=True
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

        with col2:
            # 2. Emisi per Fakultas - using FILTERED data
            fakultas_stats = filtered_df.groupby('fakultas')['total_emisi'].agg(['sum', 'count']).reset_index()
            fakultas_stats.columns = ['fakultas', 'total_emisi', 'count']
            fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 1].sort_values('total_emisi', ascending=True).tail(13)
            
            if not fakultas_stats.empty:
                fig_fakultas = go.Figure()
                
                # Use color gradient
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
                        textfont=dict(color='white', size=7, weight='bold'),
                        hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["count"]}<extra></extra>'
                    ))
                
                fig_fakultas.update_layout(
                    height=235, margin=dict(t=25, b=0, l=0, r=20),
                    title=dict(text="<b>Emisi per Fakultas</b>", x=0.35, y=0.95,
                              font=dict(size=11, color="#000000")),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Total Emisi (kg CO₂)", font=dict(size=10))),
                    yaxis=dict(tickfont=dict(size=8), title=dict(text="Fakultas/Sekolah", font=dict(size=10)))
                )
                
                st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data fakultas tidak tersedia dengan filter yang diterapkan")

        with col3:
            # 3. Komposisi Emisi per Kategori - using FILTERED data
            categories = ['Transportasi', 'Elektronik', 'Sampah Makanan']
            category_totals = [
                filtered_df['transportasi'].sum(),
                filtered_df['elektronik'].sum(),
                filtered_df['sampah_makanan'].sum()
            ]
            
            # Filter out categories with zero emission
            filtered_categories = []
            filtered_totals = []
            filtered_colors = []
            
            for i, (cat, total) in enumerate(zip(categories, category_totals)):
                if total > 0:
                    filtered_categories.append(cat)
                    filtered_totals.append(total)
                    filtered_colors.append(CATEGORY_COLORS[cat])
            
            if filtered_totals:
                fig_composition = go.Figure(data=[go.Pie(
                    labels=filtered_categories,
                    values=filtered_totals,
                    hole=0.45,
                    marker=dict(colors=filtered_colors, line=dict(color='#FFFFFF', width=2)),
                    textposition='outside',
                    textinfo='label+percent',
                    textfont=dict(size=8, family="Poppins"),
                    hovertemplate='<b>%{label}</b><br>%{value:.1f} kg CO₂ (%{percent})<extra></extra>'
                )])
                
                total_emisi_chart = sum(filtered_totals)
                center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                fig_composition.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                
                fig_composition.update_layout(
                    height=235, margin=dict(t=25, b=5, l=5, r=5), showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text="<b>Komposisi Emisi per Kategori</b>", x=0.27, y=0.95, 
                              font=dict(size=11, color="#000000"))
                )
                
                st.plotly_chart(fig_composition, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Tidak ada data emisi dengan filter yang diterapkan")

        time.sleep(0.2)

    # Row 2: K-Means Clustering for Emission Category Pairs - IMPLEMENTATION AS REQUESTED
    with loading():
        cluster_pairs = [
            ('transportasi', 'elektronik', 'Transportasi vs Elektronik'),
            ('transportasi', 'sampah_makanan', 'Transportasi vs Sampah Makanan'),
            ('elektronik', 'sampah_makanan', 'Elektronik vs Sampah Makanan')
        ]
        
        col1, col2, col3 = st.columns([1, 1, 1])
        columns = [col1, col2, col3]
        
        for idx, (feature1, feature2, title) in enumerate(cluster_pairs):
            with columns[idx]:
                # Perform K-means clustering for this pair
                df_pairwise, n_clusters_pair, centers_pair = perform_pairwise_kmeans_clustering(filtered_df, feature1, feature2)
                
                if not df_pairwise.empty and n_clusters_pair > 1:
                    fig_pair = go.Figure()
                    
                    # Get cluster colors
                    pair_colors = CLUSTER_COLORS[:n_clusters_pair]
                    
                    # Add data points with cluster colors
                    for i in range(n_clusters_pair):
                        cluster_data = df_pairwise[df_pairwise['pairwise_cluster'] == i]
                        
                        if not cluster_data.empty:
                            # Categorize emission levels for this cluster
                            cluster_data_copy = cluster_data.copy()
                            cluster_data_copy['emission_level'] = cluster_data_copy['total_emisi'].apply(categorize_emission_level)
                            
                            # Calculate average emission level for cluster
                            avg_emission = cluster_data_copy['total_emisi'].mean()
                            cluster_category = categorize_emission_level(avg_emission)
                            
                            fig_pair.add_trace(go.Scatter(
                                x=cluster_data[feature1],
                                y=cluster_data[feature2],
                                mode='markers',
                                marker=dict(
                                    size=8,  # Same size for all markers
                                    color=pair_colors[i],
                                    opacity=0.7,
                                    line=dict(color='white', width=1)
                                ),
                                name=f'Klaster {i+1} ({cluster_category})',
                                hovertemplate=f'<b>Klaster {i+1}</b><br>' +
                                            f'{feature1.replace("sampah_makanan", "Sampah Makanan").replace("transportasi", "Transportasi").replace("elektronik", "Elektronik")}: %{{x:.1f}} kg CO₂<br>' +
                                            f'{feature2.replace("sampah_makanan", "Sampah Makanan").replace("transportasi", "Transportasi").replace("elektronik", "Elektronik")}: %{{y:.1f}} kg CO₂<br>' +
                                            'Total Emisi: %{customdata:.1f} kg CO₂<br>' +
                                            f'Kategori: {cluster_category}<br>' +
                                            '<extra></extra>',
                                customdata=cluster_data['total_emisi']
                            ))
                    
                    # Add cluster centers
                    if not centers_pair.empty:
                        fig_pair.add_trace(go.Scatter(
                            x=centers_pair[feature1],
                            y=centers_pair[feature2],
                            mode='markers',
                            marker=dict(
                                size=15,
                                color='black',
                                symbol='x',
                                line=dict(color='white', width=2)
                            ),
                            name='Pusat Klaster',
                            hovertemplate='<b>Pusat Klaster</b><br>' +
                                        f'{feature1.replace("sampah_makanan", "Sampah Makanan").replace("transportasi", "Transportasi").replace("elektronik", "Elektronik")}: %{{x:.1f}}<br>' +
                                        f'{feature2.replace("sampah_makanan", "Sampah Makanan").replace("transportasi", "Transportasi").replace("elektronik", "Elektronik")}: %{{y:.1f}}<br>' +
                                        '<extra></extra>'
                        ))
                    
                    # Calculate WCSS for this clustering
                    if n_clusters_pair > 0:
                        wcss_total = 0
                        for i in range(n_clusters_pair):
                            cluster_data = df_pairwise[df_pairwise['pairwise_cluster'] == i]
                            if not cluster_data.empty and not centers_pair.empty:
                                center = centers_pair.iloc[i]
                                wcss_cluster = ((cluster_data[feature1] - center[feature1])**2 + 
                                              (cluster_data[feature2] - center[feature2])**2).sum()
                                wcss_total += wcss_cluster
                    
                    fig_pair.update_layout(
                        height=240, margin=dict(t=40, b=0, l=0, r=0),
                        title=dict(text=f"<b>{title}</b>", 
                                  x=0.35, y=0.95, font=dict(size=10, color="#000000")),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), 
                                  title=dict(text=f"{feature1.replace('sampah_makanan', 'Sampah Makanan').replace('transportasi', 'Transportasi').replace('elektronik', 'Elektronik')} (kg CO₂)", font=dict(size=8))),
                        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), 
                                  title=dict(text=f"{feature2.replace('sampah_makanan', 'Sampah Makanan').replace('transportasi', 'Transportasi').replace('elektronik', 'Elektronik')} (kg CO₂)", font=dict(size=8))),
                        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=7)),
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig_pair, use_container_width=True, config={'displayModeBar': False})
                    
                else:
                    st.info(f"Klasterisasi tidak dapat dilakukan untuk {title}")
        
        time.sleep(0.15)

if __name__ == "__main__":
    show()