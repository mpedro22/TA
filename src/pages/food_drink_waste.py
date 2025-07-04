import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time

MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

PERIOD_COLORS = {
    'Pagi': '#66c2a5',         
    'Siang': '#fdae61',       
    'Sore': '#f46d43',         
    'Malam': '#5e4fa2'         
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

@st.cache_data(ttl=3600)
@loading_decorator()
def load_daily_activities_data():
    """Load daily activities data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    try:
        time.sleep(0.35)  
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
        time.sleep(0.2)  
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
        'Teknik Informatika': 'STEI', 'Teknik Telekomunikasi': 'STEI', 'Teknik Tenaga Listrik': 'STEI'
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
    
    time.sleep(0.12)  
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
    
    time.sleep(0.08)  
    return filtered_df


@loading_decorator()
def generate_pdf_report(filtered_df, df_responden=None):
    """
    REVISED to generate a professional HTML report with tables, insights, and recommendations,
    matching the latest design.
    """
    from datetime import datetime
    import pandas as pd
    time.sleep(0.6)

    if filtered_df.empty:
        return "<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"

    total_emisi = filtered_df['emisi_makanminum'].sum()
    avg_emisi = filtered_df['emisi_makanminum'].mean()
    
    # Insight 1: Daily Trend
    daily_stats = filtered_df.groupby('day')['emisi_makanminum'].sum().reset_index()
    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    daily_stats['day_order'] = daily_stats['day'].map({day: i for i, day in enumerate(day_order)})
    daily_stats = daily_stats.sort_values('day_order').drop(columns=['day_order'])
    daily_trend_table_html = "".join([f"<tr><td>{row['day']}</td><td style='text-align:right;'>{row['emisi_makanminum']:.1f}</td></tr>" for _, row in daily_stats.iterrows()])
    peak_day = daily_stats.sort_values('emisi_makanminum', ascending=False).iloc[0]['day']
    trend_conclusion = f"Puncak emisi dari sampah makanan & minuman terjadi pada hari <strong>{peak_day}</strong>."
    trend_recommendation = f"Fokuskan kampanye 'zero food waste' atau 'habiskan makananmu' pada hari <strong>{peak_day}</strong>, terutama di kantin-kantin populer."

    # Insight 2: Faculty Analysis
    fakultas_table_html = "<tr><td colspan='3'>Data fakultas tidak tersedia.</td></tr>"
    fakultas_conclusion = "Tidak dapat melakukan analisis per fakultas."
    fakultas_recommendation = "Integrasikan data responden untuk mendapatkan wawasan per fakultas."
    if df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        if not df_with_fakultas.empty and 'fakultas' in df_with_fakultas.columns:
            fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_makanminum'].agg(['sum', 'count']).round(2)
            fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 1].sort_values('sum', ascending=False)
            if not fakultas_stats.empty:
                fakultas_table_html = "".join([f"<tr><td>{fakultas}</td><td style='text-align:right;'>{row['sum']:.2f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for fakultas, row in fakultas_stats.head(10).iterrows()])
                highest_fakultas = fakultas_stats.index[0]
                fakultas_conclusion = f"Total emisi sampah makanan tertinggi berasal dari fakultas <strong>{highest_fakultas}</strong>."
                fakultas_recommendation = f"Lakukan program edukasi limbah makanan yang ditargetkan untuk fakultas <strong>{highest_fakultas}</strong>, possibly di kantin terdekat mereka."

    # Insight 3: Meal Period Distribution
    period_stats = filtered_df.groupby('meal_period')['emisi_makanminum'].agg(['count', 'sum']).round(2).sort_values('count', ascending=False)
    period_table_html = "".join([f"<tr><td>{period}</td><td style='text-align:center;'>{int(row['count'])}</td><td style='text-align:right;'>{row['sum']:.1f}</td></tr>" for period, row in period_stats.iterrows()])
    peak_period = period_stats.index[0]
    period_conclusion = f"Aktivitas makan & minum paling banyak terjadi pada periode <strong>{peak_period}</strong>."
    period_recommendation = f"Pastikan ketersediaan pilihan makanan porsi kecil/sedang selama periode <strong>{peak_period}</strong> untuk mengurangi potensi sisa makanan."

    # Insight 4: Location vs. Time Heatmap
    heatmap_conclusion = "Pola emisi menunjukkan adanya kombinasi waktu dan lokasi tertentu dengan emisi sangat tinggi."
    heatmap_recommendation = "Gunakan data heatmap untuk mengidentifikasi 'hotspot' (misal: kantin tertentu di jam makan siang) dan tempatkan intervensi (seperti poster atau petugas) di sana."

    # Insight 5: Canteen/Location Emissions
    canteen_stats = filtered_df.groupby('lokasi')['emisi_makanminum'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    canteen_table_html = "".join([f"<tr><td>{loc}</td><td style='text-align:right;'>{row['sum']:.1f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for loc, row in canteen_stats.head(10).iterrows()])
    hottest_canteen = canteen_stats.index[0]
    canteen_conclusion = f"Lokasi/kantin <strong>{hottest_canteen}</strong> menjadi sumber emisi sampah makanan terbesar."
    canteen_recommendation = f"Prioritaskan program intervensi di <strong>{hottest_canteen}</strong>. Opsi: perkenalkan sistem penimbangan sisa makanan, tawarkan diskon untuk yang menghabiskan makanan, atau perbaiki manajemen porsi."

    # --- HTML Generation ---
    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Sampah Makanan</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Poppins', sans-serif; color: #333; line-height: 1.6; font-size: 11px; }}
        .page {{ padding: 25px; max-width: 800px; margin: auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #059669; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ color: #059669; margin: 0; }} h2 {{ color: #065f46; border-bottom: 1px solid #d1fae5; padding-bottom: 8px; margin-top: 30px; margin-bottom: 15px;}}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
        .card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .card.primary {{ border-left: 4px solid #10b981; }} .card.primary strong {{ color: #059669; }}
        .card.secondary {{ border-left: 4px solid #34d399; }} .card.secondary strong {{ color: #10b981; }}
        .card strong {{ font-size: 1.5em; display: block; }}
        .conclusion, .recommendation {{ padding: 12px 15px; margin-top: 10px; border-radius: 6px; }}
        .conclusion {{ background: #f0fdf4; border-left: 4px solid #10b981; }}
        .recommendation {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th, td {{ padding: 8px; text-align: left; border: 1px solid #e5e7eb; }}
        th {{ background-color: #d1fae5; font-weight: 600; text-align: center; }}
        td:first-child {{ font-weight: 500; }}
    </style></head>
    <body><div class="page">
        <div class="header"><h1>Laporan Emisi Sampah Makanan</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO₂</strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO₂</strong>Rata-rata/Aktivitas</div>
        </div>

        <h2>1. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>

        <h2>2. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO₂)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>

        <h2>3. Distribusi per Periode Waktu</h2>
        <table><thead><tr><th>Periode</th><th>Jumlah Aktivitas</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>{period_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {period_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {period_recommendation}</div>

        <h2>4. Pola Emisi (Lokasi & Waktu)</h2>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>

        <h2>5. Hotspot Emisi per Lokasi/Kantin</h2>
        <table><thead><tr><th>Lokasi/Kantin</th><th>Total Emisi (kg CO₂)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{canteen_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {canteen_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {canteen_recommendation}</div>
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
                <h1 class="header-title">Emisi Sampah Makanan & Minuman</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.25)  

    df_activities = load_daily_activities_data()
    df_responden = load_responden_data()
    
    if df_activities.empty:
        st.error("Data aktivitas harian tidak tersedia")
        return

    meal_data = parse_meal_activities(df_activities)
    
    if meal_data.empty:
        st.error("Data aktivitas makanan & minuman tidak ditemukan")
        return
    
    with loading():
        meal_data = meal_data.dropna(subset=['emisi_makanminum'])
        meal_data = meal_data[meal_data['emisi_makanminum'] > 0] 
        time.sleep(0.1)  

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
            pdf_content = generate_pdf_report(filtered_df, df_responden)
            
            st.download_button(
                "Laporan", 
                data=pdf_content, 
                file_name=f"food_waste_report_{len(filtered_df)}.html", 
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
                height=270, margin=dict(t=30, b=0, l=0, r=20),
                xaxis_title="", yaxis_title="Emisi (kg CO₂)",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                          font=dict(size=12, color="#000000")),
                xaxis=dict(showgrid=False, tickfont=dict(size=10), title=dict(text="Hari", font=dict(size=10))),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=10), title=dict(text="Emisi (Kg CO₂)", font=dict(size=10)))
            )
            
            st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)

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
                                textfont=dict(color='white', size=10, weight='bold'),
                                hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Aktivitas: {row["count"]}<extra></extra>'
                            ))
                        
                        fig_fakultas.update_layout(
                            height=270, margin=dict(t=30, b=0, l=0, r=20),
                            title=dict(text="<b>Emisi per Fakultas</b>", x=0.35, y=0.95,
                                      font=dict(size=12, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=10), title=dict(text="Rata-Rata Emisi (kg CO₂)", font=dict(size=10))),
                            yaxis=dict(tickfont=dict(size=10), title=dict(text="Fakultas/Sekolah", font=dict(size=10)))
                        )
                        
                        st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
                    else:
                        st.info("Data fakultas tidak cukup (min 3 aktivitas)")
                else:
                    st.info("Data fakultas tidak dapat digabungkan")
            else:
                st.info("Data fakultas tidak tersedia")

        with col3:
            # 3. Distribusi Periode Waktu - Diagram Lingkaran
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
                textfont=dict(size=10, family="Poppins"),
                hovertemplate='<b>%{label}</b><br>%{value} aktivitas (%{percent})<extra></extra>'
            )])
            
            total_emisi_chart = filtered_df['emisi_makanminum'].sum()
            center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
            fig_period.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
            
            fig_period.update_layout(
                height=270, margin=dict(t=30, b=5, l=5, r=5), showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="<b>Distribusi Periode Waktu</b>", x=0.27, y=0.95, 
                          font=dict(size=12, color="#000000"))
            )
            
            st.plotly_chart(fig_period, config=MODEBAR_CONFIG, use_container_width=True)

        time.sleep(0.18)  

    # Row 2 with loading
    with loading():
        col1, col2 = st.columns([1, 1])

        with col1:
            # 1. Heatmap Lokasi vs Waktu 
            heatmap_data = filtered_df.groupby(['lokasi', 'time_slot'])['emisi_makanminum'].sum().reset_index()
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
                        tickfont=dict(size=10),
                        thickness=15,
                        len=0.7
                    ),
                    xgap=1, ygap=1,
                    zmin=0
                ))
                
                fig_heatmap.update_layout(
                    height=270, margin=dict(t=30, b=20, l=20, r=40),
                    title=dict(text="<b>Heatmap Lokasi vs Waktu</b>", x=0.15, y=0.95, 
                            font=dict(size=12, color="#000000")),
                    xaxis=dict(tickfont=dict(size=10), title=dict(text="Lokasi", font=dict(size=10))),
                    yaxis=dict(tickfont=dict(size=10)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Data heatmap tidak tersedia")

        with col2:
            # 2. Emisi per Kantin
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
                                    colors.append('#66c2a5')  
                                elif ratio < 0.4:
                                    colors.append('#abdda4')  
                                elif ratio < 0.6:
                                    colors.append('#fdae61')  
                                elif ratio < 0.8:
                                    colors.append('#f46d43')  
                                else:
                                    colors.append('#d53e4f') 
                            else:
                                colors.append('#3288bd')  
                        
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
                                textfont=dict(size=10, color='#2d3748', weight='bold'),
                                hovertemplate=f'<b>{row["lokasi"]}</b><br>Total Emisi: {row["total_emisi"]:.2f} kg CO₂<br>Rata-rata: {row["avg_emisi"]:.2f} kg CO₂<br>Aktivitas: {row["activity_count"]}<br><i>Total emisi makanan & minuman</i><extra></extra>',
                                name=row['lokasi']
                            ))
                        
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
                                font=dict(size=10)
                            )
                        )
                        
                        fig_canteen.update_layout(
                            height=270,
                            margin=dict(t=30, b=0, l=0, r=0),
                            title=dict(text=f"<b>{canteen_title}</b>", x=0.35, y=0.95,
                                      font=dict(size=12, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(
                                showgrid=False, 
                                tickfont=dict(size=10), 
                                title=dict(text="Lokasi", font=dict(size=10))
                            ),
                            yaxis=dict(
                                showgrid=True, 
                                gridcolor='rgba(0,0,0,0.1)', 
                                tickfont=dict(size=10),
                                title=dict(text="Total Emisi (kg CO₂)", font=dict(size=9))
                            ),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_canteen, config=MODEBAR_CONFIG, use_container_width=True)
                    else:
                        st.info("Data kantin tidak cukup untuk analisis")
                else:
                    st.info("Data lokasi kantin tidak tersedia")
            else:
                st.info("Data lokasi tidak tersedia")

        time.sleep(0.18)  

if __name__ == "__main__":
    show()