import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from loading import loading, loading_decorator
import time

MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

PERIOD_COLORS = {
    'Pagi': '#66c2a5',         
    'Siang': '#fdae61',       
    'Sore': '#f46d43',         
    'Malam': '#5e4fa2'         
}

@st.cache_data(ttl=3600)
@loading_decorator()
def load_daily_activities_data():
    """Load daily activities data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    try:
        time.sleep(0.35)  # Food data loading time
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading daily activities data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
@loading_decorator()
def load_responden_data():
    """Load responden data for fakultas information"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    try:
        time.sleep(0.2)  # Responden data loading time
        return pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

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
def parse_meal_activities(df):
    """Parse meal activities from daily activities data - filter kegiatan Makan/Minum"""
    meal_activities = []
    
    if df.empty:
        return pd.DataFrame()
    
    # Filter untuk kegiatan Makan atau Minum
    meal_df = df[df['kegiatan'].str.contains('Makan|Minum', case=False, na=False)] if 'kegiatan' in df.columns else df
    
    for _, row in meal_df.iterrows():
        # Parse hari column (format: senin_1012)
        hari_value = str(row.get('hari', ''))
        if '_' in hari_value:
            parts = hari_value.split('_')
            if len(parts) == 2:
                day_name = parts[0].capitalize()
                time_str = parts[1]
                
                if len(time_str) == 4:  
                    start_hour = int(time_str[:2])
                    end_hour = int(time_str[2:])
                    
                    # Categorize meal periods - 4 periods
                    if 6 <= start_hour < 11:
                        meal_period = 'Pagi'
                    elif 11 <= start_hour < 15:
                        meal_period = 'Siang'
                    elif 15 <= start_hour < 18:
                        meal_period = 'Sore'
                    elif 18 <= start_hour < 22:
                        meal_period = 'Malam'
                    else:
                        meal_period = 'Lainnya'
                    
                    # Keep original location without categorization
                    lokasi = str(row.get('lokasi', ''))
                    if not lokasi or lokasi == 'nan':
                        lokasi = 'Unknown'
                    
                    # Determine meal type
                    kegiatan = str(row.get('kegiatan', '')).lower()
                    meal_type = 'Makan' if 'makan' in kegiatan else 'Minum' if 'minum' in kegiatan else 'Lainnya'
                    
                    meal_activities.append({
                        'id_responden': row.get('id_responden', ''),
                        'day': day_name,
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                        'duration': end_hour - start_hour,
                        'time_slot': f"{start_hour:02d}:00-{end_hour:02d}:00",
                        'meal_period': meal_period,
                        'meal_type': meal_type,
                        'lokasi': lokasi,
                        'emisi_makanminum': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce'),
                        'day_order': {'Senin': 1, 'Selasa': 2, 'Rabu': 3, 'Kamis': 4, 'Jumat': 5, 'Sabtu': 6, 'Minggu': 7}.get(day_name, 0),
                        'is_weekend': day_name in ['Sabtu', 'Minggu']
                    })
    
    time.sleep(0.12)  # Meal activity parsing time
    return pd.DataFrame(meal_activities)

@loading_decorator()
def apply_filters(df, selected_days, selected_periods, selected_fakultas, df_responden=None):
    """Apply filters to the meal dataframe - 3 filters only"""
    filtered_df = df.copy()
    
    # Filter by day
    if selected_days:
        filtered_df = filtered_df[filtered_df['day'].isin(selected_days)]
    
    # Filter by meal period
    if selected_periods:
        filtered_df = filtered_df[filtered_df['meal_period'].isin(selected_periods)]
    
    # Filter by fakultas
    if selected_fakultas and df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        if 'program_studi' in df_responden.columns:
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            fakultas_students = df_responden[df_responden['fakultas'].isin(selected_fakultas)]
            if 'id_responden' in fakultas_students.columns and 'id_responden' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['id_responden'].isin(fakultas_students['id_responden'])]
    
    time.sleep(0.08)  # Filter processing time
    return filtered_df

@loading_decorator()
def generate_pdf_report(filtered_df, total_emisi, avg_emisi, df_responden=None):
    """Generate professional HTML report optimized for PDF printing - Updated to match 6 visualizations"""
    from datetime import datetime
    import pandas as pd
    
    # Simulate complex report generation
    time.sleep(0.55)
    
    def get_fakultas_mapping():
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
    
    # Data calculations
    valid_df = filtered_df[filtered_df['id_responden'].notna() & (filtered_df['id_responden'] != '') & (filtered_df['id_responden'] != 0)]
    total_responden = len(valid_df['id_responden'].unique()) if not valid_df.empty else 0
    
    # 1. Daily trend analysis
    daily_stats = valid_df.groupby('day')['emisi_makanminum'].sum().reset_index()
    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    daily_stats['day_order'] = daily_stats['day'].map({day: i for i, day in enumerate(day_order)})
    daily_stats = daily_stats.sort_values('day_order')
    highest_day = daily_stats.loc[daily_stats['emisi_makanminum'].idxmax()] if not daily_stats.empty else None
    lowest_day = daily_stats.loc[daily_stats['emisi_makanminum'].idxmin()] if not daily_stats.empty else None
    
    # 2. Faculty analysis
    fakultas_data = pd.DataFrame()
    fakultas_conclusion = "Data fakultas tidak tersedia."
    if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        df_with_fakultas = valid_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        
        if not df_with_fakultas.empty:
            fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_makanminum'].agg(['sum', 'count']).round(2)
            fakultas_stats.columns = ['total_emisi', 'jumlah_aktivitas']
            fakultas_data = fakultas_stats[fakultas_stats['jumlah_aktivitas'] >= 3].sort_values('total_emisi', ascending=False).head(6)
            
            if not fakultas_data.empty:
                highest = fakultas_data.index[0]
                highest_emisi = fakultas_data.iloc[0]['total_emisi']
                fakultas_conclusion = f"Fakultas {highest} memiliki total emisi makanan tertinggi sebesar {highest_emisi:.2f} kg CO₂."

    # 3. Period analysis  
    period_stats = valid_df.groupby('meal_period')['emisi_makanminum'].agg(['count', 'mean', 'sum']).round(2)
    period_stats.columns = ['jumlah_aktivitas', 'rata_rata_emisi', 'total_emisi']
    period_stats = period_stats.reset_index().sort_values('total_emisi', ascending=False)
    peak_period = period_stats.iloc[0] if not period_stats.empty else None

    # 4. Heatmap analysis (Time-Location patterns)
    heatmap_conclusion = "Data pola waktu-lokasi tidak tersedia."
    peak_time_location = "N/A"
    if not valid_df.empty and 'time_slot' in valid_df.columns and 'lokasi' in valid_df.columns:
        top_locations = valid_df.groupby('lokasi')['emisi_makanminum'].sum().nlargest(6).index.tolist()
        heatmap_filtered = valid_df[valid_df['lokasi'].isin(top_locations)]
        
        if not heatmap_filtered.empty:
            heatmap_data = heatmap_filtered.groupby(['lokasi', 'time_slot'])['emisi_makanminum'].sum().reset_index()
            if not heatmap_data.empty:
                peak_combo = heatmap_data.loc[heatmap_data['emisi_makanminum'].idxmax()]
                peak_time_location = f"{peak_combo['lokasi']} pada jam {peak_combo['time_slot']}"
                heatmap_conclusion = f"Kombinasi lokasi-waktu dengan emisi tertinggi adalah {peak_time_location} dengan {peak_combo['emisi_makanminum']:.2f} kg CO₂."

    # 5. Location popularity analysis
    location_stats = valid_df.groupby('lokasi').agg({
        'emisi_makanminum': ['sum', 'mean'],
        'lokasi': 'count'
    }).reset_index()
    location_stats.columns = ['lokasi', 'total_emisi', 'avg_emisi', 'session_count']
    location_stats = location_stats[location_stats['session_count'] >= 2].sort_values('session_count', ascending=False).head(10)
    most_popular_location = location_stats.iloc[0] if not location_stats.empty else None

    # 6. Box plot distribution analysis (sesuai visualisasi)
    box_plot_analysis = pd.DataFrame()
    box_plot_conclusion = "Data distribusi emisi per lokasi tidak tersedia."
    
    if not valid_df.empty and 'id_responden' in valid_df.columns and 'lokasi' in valid_df.columns:
        # Aggregate per responden per lokasi (sama seperti di visualisasi)
        responden_lokasi_agg = valid_df.groupby(['id_responden', 'lokasi']).agg({
            'emisi_makanminum': 'sum'
        }).reset_index()
        
        # Group by location untuk analisis distribusi
        location_distribution = responden_lokasi_agg.groupby('lokasi').agg({
            'emisi_makanminum': ['count', 'mean', 'median', 'std', 'min', 'max']
        }).reset_index()
        location_distribution.columns = ['lokasi', 'responden_count', 'mean_emisi', 'median_emisi', 'std_emisi', 'min_emisi', 'max_emisi']
        
        # Filter lokasi dengan minimal 3 responden
        significant_locations = location_distribution[location_distribution['responden_count'] >= 3]
        
        if not significant_locations.empty:
            # Analisis outliers per lokasi
            outlier_analysis = []
            for _, loc_row in significant_locations.iterrows():
                lokasi = loc_row['lokasi']
                location_emissions = responden_lokasi_agg[responden_lokasi_agg['lokasi'] == lokasi]['emisi_makanminum']
                
                q1 = location_emissions.quantile(0.25)
                q3 = location_emissions.quantile(0.75)
                iqr = q3 - q1
                lower_fence = q1 - 1.5 * iqr
                upper_fence = q3 + 1.5 * iqr
                
                outliers = len(location_emissions[(location_emissions > upper_fence) | (location_emissions < lower_fence)])
                
                outlier_analysis.append({
                    'lokasi': lokasi,
                    'responden': int(loc_row['responden_count']),
                    'median': loc_row['median_emisi'],
                    'iqr': q3 - q1,
                    'outliers': outliers,
                    'variabilitas': 'Tinggi' if loc_row['std_emisi'] > loc_row['mean_emisi'] * 0.5 else 'Rendah'
                })
            
            box_plot_analysis = pd.DataFrame(outlier_analysis).sort_values('median', ascending=False)
            
            if not box_plot_analysis.empty:
                highest_median = box_plot_analysis.iloc[0]
                most_outliers = box_plot_analysis.loc[box_plot_analysis['outliers'].idxmax()]
                most_variable = box_plot_analysis.loc[box_plot_analysis['iqr'].idxmax()]
                total_outliers = box_plot_analysis['outliers'].sum()
                
                box_plot_conclusion = f"Distribusi emisi menunjukkan {total_outliers} responden outlier total. {highest_median['lokasi']} memiliki median tertinggi ({highest_median['median']:.2f} kg CO₂), {most_outliers['lokasi']} memiliki outlier terbanyak ({most_outliers['outliers']} responden), dan {most_variable['lokasi']} paling bervariasi (IQR: {most_variable['iqr']:.2f})."

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Emisi Sampah Makanan ITB</title>
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
            <h1>LAPORAN EMISI SAMPAH MAKANAN ITB</h1>
            <div class="subtitle">Institut Teknologi Bandung</div>
            <div class="timestamp">Dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M WIB')}</div>
        </div>
        
        <div class="executive-summary avoid-break">
            <h2 style="margin-top: 0; color: #16a34a; font-size: 14px; font-weight: 600;">Ringkasan Eksekutif</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{total_emisi:.1f}</span>
                    <div class="metric-label">Total Emisi (kg CO₂)</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{avg_emisi:.2f}</span>
                    <div class="metric-label">Rata-rata per Aktivitas</div>
                </div>
            </div>
        </div>
        
        <!-- 1. Tren Emisi Harian -->
        <div class="section avoid-break">
            <h2 class="section-title">1. Tren Emisi Harian</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Hari</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for _, row in daily_stats.iterrows():
        # Determine status based on comparison to mean
        avg_daily = daily_stats['emisi_makanminum'].mean()
        if row['emisi_makanminum'] > avg_daily * 1.2:
            status = 'Tinggi'
        elif row['emisi_makanminum'] < avg_daily * 0.8:
            status = 'Rendah'
        else:
            status = 'Normal'
            
        html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{row['day']}</td>
                            <td>{row['emisi_makanminum']:.2f}</td>
                            <td>{status}</td>
                        </tr>
        """
    
    daily_conclusion = f"Hari {highest_day['day']} mencatat emisi tertinggi ({highest_day['emisi_makanminum']:.1f} kg CO₂), sedangkan {lowest_day['day']} terendah ({lowest_day['emisi_makanminum']:.1f} kg CO₂)." if highest_day is not None and lowest_day is not None else "Data tren harian tidak tersedia."
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {daily_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 2. Emisi per Fakultas -->
        <div class="section avoid-break">
            <h2 class="section-title">2. Emisi per Fakultas</h2>
            <div class="section-content">
    """
    
    if not fakultas_data.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Fakultas</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Jumlah Aktivitas</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for idx, (fakultas, row) in enumerate(fakultas_data.iterrows(), 1):
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{fakultas}</td>
                            <td>{row['total_emisi']:.2f}</td>
                            <td>{row['jumlah_aktivitas']}</td>
                        </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data fakultas tidak tersedia.</p>"
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {fakultas_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 3. Distribusi Emisi per Periode Waktu -->
        <div class="section avoid-break">
            <h2 class="section-title">3. Distribusi Emisi per Periode Waktu</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Periode</th>
                            <th>Aktivitas</th>
                            <th>Rata-rata Emisi</th>
                            <th>Total Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for _, row in period_stats.iterrows():
        html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{row['meal_period']}</td>
                            <td>{row['jumlah_aktivitas']}</td>
                            <td>{row['rata_rata_emisi']:.2f}</td>
                            <td>{row['total_emisi']:.1f}</td>
                        </tr>
        """
    
    period_conclusion = f"Periode {peak_period['meal_period']} menghasilkan emisi tertinggi sebesar {peak_period['total_emisi']:.1f} kg CO₂." if peak_period is not None else "Data periode tidak tersedia."
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {period_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 4. Analisis Pola Waktu dan Lokasi -->
        <div class="section avoid-break">
            <h2 class="section-title">4. Analisis Pola Waktu dan Lokasi</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Metrik</th>
                            <th>Nilai</th>
                            <th>Keterangan</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Kombinasi Puncak</td>
                            <td>{peak_time_location}</td>
                            <td>Lokasi-waktu dengan emisi tertinggi</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Top Lokasi Analisis</td>
                            <td>{len(top_locations) if 'top_locations' in locals() else 0}</td>
                            <td>Lokasi yang dianalisis dalam heatmap</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Total Slot Waktu</td>
                            <td>{len(valid_df['time_slot'].unique()) if 'time_slot' in valid_df.columns else 0}</td>
                            <td>Variasi waktu aktivitas makan</td>
                        </tr>
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {heatmap_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 5. Distribusi Emisi per Lokasi Makan -->
        <div class="section avoid-break">
            <h2 class="section-title">5. Distribusi Emisi per Lokasi Makan</h2>
            <div class="section-content">
    """
    
    if not box_plot_analysis.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Lokasi</th>
                            <th>Responden</th>
                            <th>Median (kg CO₂)</th>
                            <th>IQR</th>
                            <th>Outlier</th>
                            <th>Variabilitas</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (_, row) in enumerate(box_plot_analysis.iterrows(), 1):
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{row['lokasi']}</td>
                            <td>{row['responden']}</td>
                            <td>{row['median']:.2f}</td>
                            <td>{row['iqr']:.2f}</td>
                            <td>{row['outliers']} responden</td>
                            <td>{row['variabilitas']}</td>
                        </tr>
            """
        
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data distribusi emisi per lokasi tidak tersedia.</p>"
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {box_plot_conclusion}
                </div>
            </div>

        <!-- 6. Lokasi Makan Terpopuler -->
        <div class="section avoid-break">
            <h2 class="section-title">6. Lokasi Makan Terpopuler</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Lokasi</th>
                            <th>Jumlah Sesi</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Emisi per Sesi</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for idx, (_, row) in enumerate(location_stats.iterrows(), 1):
        emisi_per_sesi = row['total_emisi'] / row['session_count']
        html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{row['lokasi']}</td>
                            <td>{row['session_count']}</td>
                            <td>{row['total_emisi']:.2f}</td>
                            <td>{emisi_per_sesi:.2f}</td>
                        </tr>
        """
    
    location_conclusion = f"Lokasi {most_popular_location['lokasi']} merupakan yang terpopuler dengan {most_popular_location['session_count']} sesi dan total emisi {most_popular_location['total_emisi']:.2f} kg CO₂." if most_popular_location is not None else "Data lokasi tidak tersedia."
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {location_conclusion}
                </div>
            </div>
        </div>
        </div>
        
        <div class="footer">
            <p><strong>Institut Teknologi Bandung</strong></p>
            <p>Carbon Emission Dashboard - Food Waste Report</p>
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
                <h1 class="header-title">Emisi Sampah Makanan & Minuman</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.25)  # Header animation time

    # Load data with loading decorators
    df_activities = load_daily_activities_data()
    df_responden = load_responden_data()
    
    if df_activities.empty:
        st.error("Data aktivitas harian tidak tersedia")
        return

    # Parse meal activities with loading
    meal_data = parse_meal_activities(df_activities)
    
    if meal_data.empty:
        st.error("Data aktivitas makanan & minuman tidak ditemukan")
        return
    
    # Clean data with loading
    with loading():
        meal_data = meal_data.dropna(subset=['emisi_makanminum'])
        meal_data = meal_data[meal_data['emisi_makanminum'] > 0]  # Remove zero emissions
        time.sleep(0.1)  # Data cleaning time

    # Filters
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:", 
            options=day_options, 
            placeholder="Pilih Opsi", 
            key='food_day_filter'
        )
    
    with filter_col2:
        period_options = ['Pagi', 'Siang', 'Sore', 'Malam']
        selected_periods = st.multiselect(
            "Periode:", 
            options=period_options, 
            placeholder="Pilih Opsi", 
            key='food_period_filter'
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
                key='food_fakultas_filter'
            )
        else:
            selected_fakultas = []

    # Apply filters with loading
    filtered_df = apply_filters(meal_data, selected_days, selected_periods, selected_fakultas, df_responden)

    # Calculate metrics for export
    total_emisi = filtered_df['emisi_makanminum'].sum()
    avg_emisi = filtered_df['emisi_makanminum'].mean()

    # Export buttons
    with export_col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Raw Data", 
            data=csv_data, 
            file_name=f"food_drink_waste_{len(filtered_df)}.csv", 
            mime="text/csv", 
            use_container_width=True, 
            key="food_export_csv"
        )
    
    with export_col2:
        try:
            pdf_content = generate_pdf_report(filtered_df, total_emisi, avg_emisi, df_responden)
            st.download_button(
                "Laporan", 
                data=pdf_content, 
                file_name=f"food_drink_waste_{len(filtered_df)}.html", 
                mime="text/html", 
                use_container_width=True, 
                key="food_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return

    # Charts with loading animations - Row 1
    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 1. Tren Emisi Harian - Grafik Garis
            daily_trend = filtered_df.groupby('day')['emisi_makanminum'].sum().reset_index()
            day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            daily_trend['day_order'] = daily_trend['day'].map({day: i for i, day in enumerate(day_order)})
            daily_trend = daily_trend.sort_values('day_order')
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_trend['day'], y=daily_trend['emisi_makanminum'],
                fill='tonexty', mode='lines+markers',
                line=dict(color='#3288bd', width=2, shape='spline'),
                marker=dict(size=6, color='#3288bd', line=dict(color='white', width=1)),
                fillcolor="rgba(102, 194, 165, 0.3)",
                hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>',
                showlegend=False
            ))
            
            fig_trend.update_layout(
                height=235, margin=dict(t=25, b=0, l=0, r=20),
                xaxis_title="", yaxis_title="Emisi (kg CO₂)",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                          font=dict(size=11, color="#000000")),
                xaxis=dict(showgrid=False, tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10))),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (Kg CO₂)", font=dict(size=10)))
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

        with col2:
            # 2. Emisi per Fakultas
            if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
                fakultas_mapping = get_fakultas_mapping()
                df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
                df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                
                if not df_with_fakultas.empty:
                    fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_makanminum'].agg(['sum', 'count']).reset_index()
                    fakultas_stats.columns = ['fakultas', 'total_emisi', 'count']
                    fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 1].sort_values('total_emisi', ascending=True).tail(13)
                    
                    if not fakultas_stats.empty:
                        fig_fakultas = go.Figure()
                        
                        # Use color gradient based on emission level
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
                                hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Aktivitas: {row["count"]}<extra></extra>'
                            ))
                        
                        fig_fakultas.update_layout(
                            height=235, margin=dict(t=25, b=0, l=0, r=20),
                            title=dict(text="<b>Emisi per Fakultas</b>", x=0.35, y=0.95,
                                      font=dict(size=11, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Rata-Rata Emisi (kg CO₂)", font=dict(size=10))),
                            yaxis=dict(tickfont=dict(size=8), title=dict(text="Fakultas/Sekolah", font=dict(size=10)))
                        )
                        
                        st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.info("Data fakultas tidak cukup (min 3 aktivitas)")
                else:
                    st.info("Data fakultas tidak dapat digabungkan")
            else:
                st.info("Data fakultas tidak tersedia")

        with col3:
            # 3. Distribusi Periode Waktu - Diagram Lingkaran - DIPERBAIKI CENTER TEXT
            period_data = filtered_df['meal_period'].value_counts()
            colors = [PERIOD_COLORS.get(period, MAIN_PALETTE[i % len(MAIN_PALETTE)]) 
                     for i, period in enumerate(period_data.index)]
            
            fig_period = go.Figure(data=[go.Pie(
                labels=period_data.index,
                values=period_data.values,
                hole=0.45,
                marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=7, family="Poppins"),
                hovertemplate='<b>%{label}</b><br>%{value} aktivitas (%{percent})<extra></extra>'
            )])
            
            # DIPERBAIKI: Center text menampilkan total emisi, bukan total aktivitas
            total_emisi_chart = filtered_df['emisi_makanminum'].sum()
            center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
            fig_period.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
            
            fig_period.update_layout(
                height=235, margin=dict(t=25, b=5, l=5, r=5), showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="<b>Distribusi Periode Waktu</b>", x=0.27, y=0.95, 
                          font=dict(size=11, color="#000000"))
            )
            
            st.plotly_chart(fig_period, use_container_width=True, config={'displayModeBar': False})

        time.sleep(0.18)  # Row 1 charts loading time

    # Row 2 with loading
    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 1. Heatmap Top Lokasi vs Waktu 
            top_locations = filtered_df.groupby('lokasi')['emisi_makanminum'].sum().nlargest().index.tolist()
            heatmap_filtered = filtered_df[filtered_df['lokasi'].isin(top_locations)]
            
            heatmap_data = heatmap_filtered.groupby(['lokasi', 'time_slot'])['emisi_makanminum'].sum().reset_index()
            heatmap_pivot = heatmap_data.pivot(index='time_slot', columns='lokasi', values='emisi_makanminum').fillna(0)
            
            if not heatmap_pivot.empty:
                truncated_columns = [col[:15] + '...' if len(col) > 15 else col for col in heatmap_pivot.columns]
                
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=heatmap_pivot.values,
                    x=truncated_columns,
                    y=heatmap_pivot.index,
                    colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                    hoverongaps=False,
                    hovertemplate='<b>%{customdata}</b><br>Waktu: %{y}<br>Emisi: %{z:.2f} kg CO₂<extra></extra>',
                    customdata=np.array([list(heatmap_pivot.columns)] * len(heatmap_pivot.index)),
                    colorbar=dict(
                        title=dict(text="Emisi", font=dict(size=9)),
                        tickfont=dict(size=8),
                        thickness=15,
                        len=0.7
                    ),
                    xgap=1, ygap=1,
                    zmin=0
                ))
                
                fig_heatmap.update_layout(
                    height=235, margin=dict(t=25, b=20, l=20, r=40),
                    title=dict(text="<b>Heatmap Top Lokasi vs Waktu</b>", x=0.15, y=0.95, 
                            font=dict(size=11, color="#000000")),
                    xaxis=dict(tickfont=dict(size=7), tickangle=-45, title=dict(text="Lokasi", font=dict(size=10))),
                    yaxis=dict(tickfont=dict(size=7)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data heatmap tidak tersedia")

        with col2:
            # 2. Box Plot Distribusi Emisi per Kantin - DIPERBAIKI DENGAN AGREGASI
            if not filtered_df.empty and 'lokasi' in filtered_df.columns:
                # Filter data valid
                valid_data = filtered_df[
                    (filtered_df['emisi_makanminum'].notna()) & 
                    (filtered_df['emisi_makanminum'] > 0) &
                    (filtered_df['lokasi'].notna()) &
                    (filtered_df['lokasi'] != '') &
                    (filtered_df['id_responden'].notna()) &
                    (filtered_df['id_responden'] != '')
                ]
                
                if len(valid_data) > 0:
                    # KUNCI: Aggregate emisi per responden per lokasi (sum multiple visits)
                    responden_lokasi_agg = valid_data.groupby(['id_responden', 'lokasi']).agg({
                        'emisi_makanminum': 'sum'  # Sum all eating sessions per person per location
                    }).reset_index()
                    
                    # Group by location untuk melihat distribusi
                    location_stats = responden_lokasi_agg.groupby('lokasi').agg({
                        'emisi_makanminum': ['count', 'mean', 'std', 'min', 'max']
                    }).reset_index()
                    location_stats.columns = ['lokasi', 'responden_count', 'mean_emisi', 'std_emisi', 'min_emisi', 'max_emisi']
                    
                    # Filter lokasi dengan minimal 3 responden untuk box plot yang meaningful
                    valid_locations_data = location_stats[location_stats['responden_count'] >= 3]
                    
                    if len(valid_locations_data) >= 2:
                        # Ambil top 6 lokasi berdasarkan jumlah responden
                        top_locations = valid_locations_data.nlargest(6, 'responden_count')['lokasi'].tolist()
                        
                        # Filter aggregated data untuk lokasi-lokasi ini
                        box_data = responden_lokasi_agg[responden_lokasi_agg['lokasi'].isin(top_locations)]
                        
                        if not box_data.empty:
                            fig_canteen_boxplot = go.Figure()
                            
                            # Color palette
                            colors = ['#66c2a5', '#fdae61', '#f46d43', '#d53e4f', '#5e4fa2', '#9e0142']
                            
                            for i, location in enumerate(top_locations):
                                # Ambil total emisi per responden untuk lokasi ini
                                location_emissions = box_data[box_data['lokasi'] == location]['emisi_makanminum']
                                
                                if len(location_emissions) >= 3:
                                    color = colors[i % len(colors)]
                                    
                                    # Calculate statistics
                                    q1 = location_emissions.quantile(0.25)
                                    q3 = location_emissions.quantile(0.75)
                                    iqr = q3 - q1
                                    lower_fence = q1 - 1.5 * iqr
                                    upper_fence = q3 + 1.5 * iqr
                                    outliers_count = len(location_emissions[
                                        (location_emissions > upper_fence) | 
                                        (location_emissions < lower_fence)
                                    ])
                                    
                                    # Convert hex to rgba
                                    hex_color = color[1:]
                                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                                    rgba_fill = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.4)"
                                    
                                    # Short name for display
                                    display_name = location if len(location) <= 10 else location[:8] + '..'
                                    
                                    fig_canteen_boxplot.add_trace(go.Box(
                                        y=location_emissions,
                                        name=display_name,
                                        marker_color=color,
                                        boxpoints='outliers',
                                        pointpos=-1.8,
                                        marker=dict(
                                            size=6,
                                            line=dict(width=1, color='white'),
                                            opacity=0.9
                                        ),
                                        line=dict(width=2),
                                        fillcolor=rgba_fill,
                                        hovertemplate=f'<b>{location}</b><br>' +
                                                    'Median: %{median:.2f} kg CO₂<br>' +
                                                    f'Outlier: {outliers_count}<br>' +
                                                    'Total Emisi: %{y:.2f} kg CO₂<br>' +
                                                    f'Responden: {len(location_emissions)}<extra></extra>'
                                    ))
                            
                            fig_canteen_boxplot.update_layout(
                                height=235, margin=dict(t=25, b=5, l=5, r=5),
                                title=dict(text="<b>Distribusi Total Emisi per Responden</b>", x=0.20, y=0.95, 
                                          font=dict(size=11, color="#000000")),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(
                                    showgrid=False, 
                                    tickfont=dict(size=7), 
                                    title=dict(text="Lokasi Makan", font=dict(size=9))
                                ),
                                yaxis=dict(
                                    showgrid=True, 
                                    gridcolor='rgba(0,0,0,0.1)', 
                                    tickfont=dict(size=7), 
                                    title=dict(text="Total Emisi per Responden (kg CO₂)", font=dict(size=9))
                                ),
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_canteen_boxplot, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.info("Data lokasi makan kosong setelah agregasi")
                    else:
                        # Show debug info yang lebih detail
                        st.info(f"Tidak cukup lokasi dengan responden memadai. Ditemukan {len(valid_locations_data)} lokasi.")
                        
                        # Tampilkan debug info untuk troubleshooting
                        if not location_stats.empty:
                            st.write("**Statistik per lokasi (setelah agregasi):**")
                            st.dataframe(location_stats.head(10))
                else:
                    st.info("Tidak ada data aktivitas makan yang valid")
                    
                    # Debug info yang lebih detail
                    st.write("**Debug Info:**")
                    st.write(f"- Total data: {len(filtered_df)}")
                    if len(filtered_df) > 0:
                        st.write(f"- Data dengan emisi > 0: {len(filtered_df[filtered_df['emisi_makanminum'] > 0])}")
                        st.write(f"- Data dengan lokasi valid: {len(filtered_df[filtered_df['lokasi'].notna()])}")
                        st.write(f"- Lokasi unique: {filtered_df['lokasi'].nunique()}")
                        st.write(f"- Sample lokasi: {filtered_df['lokasi'].value_counts().head()}")
            else:
                st.info("Data tidak tersedia")

        with col3:
            # 3. Emisi per Kantin
            if not filtered_df.empty and 'lokasi' in filtered_df.columns:
                # Filter for canteen-like locations (containing 'kantin', 'cafeteria', 'cafe', etc.)
                canteen_keywords = ['kantin', 'cafeteria', 'cafe', 'kafe', 'food', 'makan', 'warung', 'resto', 'restaurant']
                
                # First try to find locations with canteen keywords
                canteen_df = filtered_df[
                    filtered_df['lokasi'].str.contains('|'.join(canteen_keywords), case=False, na=False)
                ]
                
                # If no canteen-specific locations found, use top locations by activity count
                if canteen_df.empty:
                    canteen_df = filtered_df.copy()
                    canteen_title = "Lokasi Makan Teratas"
                else:
                    canteen_title = "Emisi per Kantin"
                
                if not canteen_df.empty:
                    canteen_stats = canteen_df.groupby('lokasi').agg({
                        'emisi_makanminum': ['sum', 'mean', 'count']
                    }).reset_index()
                    canteen_stats.columns = ['lokasi', 'total_emisi', 'avg_emisi', 'activity_count']
                    
                    # Filter locations with at least 2 activities and take top 8
                    canteen_stats = canteen_stats[canteen_stats['activity_count'] >= 2]
                    canteen_stats = canteen_stats.sort_values('total_emisi', ascending=False).head(8)
                    
                    if not canteen_stats.empty:
                        fig_canteen = go.Figure()
                        
                        # Color gradient based on emission level
                        max_emisi = canteen_stats['total_emisi'].max()
                        min_emisi = canteen_stats['total_emisi'].min()
                        
                        colors = []
                        for _, row in canteen_stats.iterrows():
                            if max_emisi > min_emisi:
                                ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                                if ratio < 0.2:
                                    colors.append('#66c2a5')  # Low emission - green
                                elif ratio < 0.4:
                                    colors.append('#abdda4')  
                                elif ratio < 0.6:
                                    colors.append('#fdae61')  # Medium emission - orange
                                elif ratio < 0.8:
                                    colors.append('#f46d43')  
                                else:
                                    colors.append('#d53e4f')  # High emission - red
                            else:
                                colors.append('#3288bd')  # Default blue
                        
                        for i, (_, row) in enumerate(canteen_stats.iterrows()):
                            # Shorten location names for display
                            display_name = row['lokasi'] if len(row['lokasi']) <= 12 else row['lokasi'][:10] + '..'
                            
                            fig_canteen.add_trace(go.Bar(
                                x=[display_name],
                                y=[row['total_emisi']],
                                marker=dict(
                                    color=colors[i],
                                    line=dict(color='white', width=1.5),
                                    opacity=0.85
                                ),
                                showlegend=False,
                                text=[f"{row['total_emisi']:.1f}"],
                                textposition='outside',
                                textfont=dict(size=8, color='#2d3748', weight='bold'),
                                hovertemplate=f'<b>{row["lokasi"]}</b><br>Total Emisi: {row["total_emisi"]:.2f} kg CO₂<br>Rata-rata: {row["avg_emisi"]:.2f} kg CO₂<br>Aktivitas: {row["activity_count"]}<br><i>Total emisi makanan & minuman</i><extra></extra>',
                                name=row['lokasi']
                            ))
                        
                        # Add average line for reference
                        avg_emisi = canteen_stats['total_emisi'].mean()
                        fig_canteen.add_hline(
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
                                font=dict(size=8)
                            )
                        )
                        
                        fig_canteen.update_layout(
                            height=235,
                            margin=dict(t=25, b=0, l=0, r=0),
                            title=dict(text=f"<b>{canteen_title}</b>", x=0.35, y=0.95,
                                      font=dict(size=11, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(
                                showgrid=False, 
                                tickfont=dict(size=7), 
                                tickangle=-45,
                                title=dict(text="Lokasi", font=dict(size=9))
                            ),
                            yaxis=dict(
                                showgrid=True, 
                                gridcolor='rgba(0,0,0,0.1)', 
                                tickfont=dict(size=8),
                                title=dict(text="Total Emisi (kg CO₂)", font=dict(size=9))
                            ),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_canteen, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.info("Data kantin tidak cukup untuk analisis")
                else:
                    st.info("Data lokasi kantin tidak tersedia")
            else:
                st.info("Data lokasi tidak tersedia")

        time.sleep(0.18)  # Row 2 charts loading time

if __name__ == "__main__":
    show()