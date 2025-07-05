import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
from src.utils.db_connector import run_query


MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

DEVICE_COLORS = {
    'Smartphone': '#d53e4f',  
    'Laptop': '#3288bd',      
    'Tablet': '#66c2a5',     
    'AC': '#f46d43',         
    'Lampu': '#fdae61'        
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
def load_electronic_data():
    """Load electronic data from Supabase"""
    try:
        time.sleep(0.3)  
        return run_query("elektronik")
    except Exception as e:
        st.error(f"Error loading electronic data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
@loading_decorator()
def load_daily_activities():
    """Load daily activities data from Supabase"""
    try:
        time.sleep(0.25) 
        return run_query("aktivitas_harian")
    except Exception as e:
        st.error(f"Error loading daily activities data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
@loading_decorator()
def load_responden_data():
    """Load responden data for fakultas information from Supabase"""
    try:
        time.sleep(0.2) 
        return run_query("informasi_responden")
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
def parse_time_activities(df_activities):
    """Parse time and location data from daily activities (Supabase format)"""
    parsed_data = []
    if df_activities.empty:
        return pd.DataFrame()
    
    # Loop melalui setiap baris data aktivitas harian dari Supabase
    for _, row in df_activities.iterrows():
        day = row.get('hari', '').capitalize()
        waktu_str = str(row.get('waktu', ''))

        # Pastikan kolom hari dan waktu tidak kosong dan formatnya benar (contoh: "10-12")
        if day and '-' in waktu_str:
            try:
                # Pisahkan jam mulai dan selesai dari string "10-12"
                start_hour_str, end_hour_str = waktu_str.split('-')
                start_hour = int(start_hour_str)
                end_hour = int(end_hour_str)
                
                # Buat time_range yang konsisten dengan format lama
                time_range = f"{start_hour:02d}:00-{end_hour:02d}:00"
                
                # Tambahkan data yang sudah diparsing ke list
                parsed_data.append({
                    'id_responden': row.get('id_responden', ''),
                    'day': day,
                    'start_hour': start_hour,
                    'end_hour': end_hour,
                    'time_range': time_range,
                    'duration': end_hour - start_hour,
                    'lokasi': row.get('lokasi', ''),
                    'kegiatan': row.get('kegiatan', ''),
                    'ac': row.get('penggunaan_ac', ''), # Sesuaikan jika nama kolom berbeda
                    'emisi_ac': pd.to_numeric(row.get('emisi_ac', 0), errors='coerce'),
                    'emisi_lampu': pd.to_numeric(row.get('emisi_lampu', 0), errors='coerce'),
                    'emisi_makanminum': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce')
                })
            except (ValueError, IndexError):
                # Lewati baris jika format 'waktu' tidak valid
                continue
    
    time.sleep(0.1)
    return pd.DataFrame(parsed_data)

@loading_decorator()
def apply_electronic_filters(df, selected_days, selected_devices, selected_fakultas, df_responden=None):
    """Apply filters to the electronic dataframe with loading"""
    filtered_df = df.copy()
    
    # Filter by day
    if selected_days and 'hari_datang' in filtered_df.columns:
        day_mask = pd.Series(False, index=filtered_df.index)
        for day in selected_days:
            # Menggunakan .str.contains() aman karena hari_datang adalah string
            day_mask |= filtered_df['hari_datang'].str.contains(day, case=False, na=False)
        filtered_df = filtered_df[day_mask]
    
    # Filter by device usage
    if selected_devices:
        device_mask = pd.Series(False, index=filtered_df.index)
        
        for device in selected_devices:
            # Logika filter diubah untuk menangani boolean (TRUE/FALSE)
            if device == 'Smartphone' and 'penggunaan_hp' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_hp'] == True)
            elif device == 'Laptop' and 'penggunaan_laptop' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_laptop'] == True)
            elif device == 'Tablet' and 'penggunaan_tab' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_tab'] == True)
            # Logika untuk AC dan Lampu tetap sama
            elif device == 'AC':
                device_mask |= pd.Series(True, index=filtered_df.index)
            elif device == 'Lampu':
                device_mask |= pd.Series(True, index=filtered_df.index)
        
        if device_mask.any():
            filtered_df = filtered_df[device_mask]
    
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

@loading_decorator()
def calculate_device_emissions(df, activities_df):
    """Calculate emissions for each device type based on actual data with loading"""
    device_emissions = {}
    
    # Personal devices
    if 'durasi_hp' in df.columns:
        device_emissions['Smartphone'] = (df['durasi_hp'] * 0.02 * 0.5).sum()
    if 'durasi_laptop' in df.columns:
        device_emissions['Laptop'] = (df['durasi_laptop'] * 0.08 * 0.5).sum()
    if 'durasi_tab' in df.columns:
        device_emissions['Tablet'] = (df['durasi_tab'] * 0.03 * 0.5).sum()
    
    # Infrastructure from activities
    if not activities_df.empty:
        device_emissions['AC'] = activities_df['emisi_ac'].sum()
        device_emissions['Lampu'] = activities_df['emisi_lampu'].sum()
    
    time.sleep(0.15)  
    return device_emissions

# Ganti seluruh fungsi generate_electronic_pdf_report() dengan kode ini

# Ganti seluruh fungsi generate_electronic_pdf_report() dengan kode ini

@loading_decorator()
def generate_electronic_pdf_report(filtered_df, activities_df, device_emissions, df_responden=None):
    """
    REVISED to generate a professional HTML report with actionable insights 
    and realistic recommendations for university management.
    """
    from datetime import datetime
    import pandas as pd
    time.sleep(0.6)

    if filtered_df.empty or activities_df.empty:
        return "<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"

    # --- 1. DATA PREPARATION & INSIGHT GENERATION ---
    total_emisi = filtered_df['emisi_elektronik_mingguan'].sum()
    avg_emisi = total_emisi / len(filtered_df) if not filtered_df.empty else 0
    
    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    # Insight 1: Daily Trend
    days_of_week = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
    daily_cols = [f'emisi_elektronik_{day}' for day in days_of_week if f'emisi_elektronik_{day}' in filtered_df.columns]
    daily_trend_table_html = "<tr><td colspan='2'>Data emisi harian tidak tersedia.</td></tr>"
    trend_conclusion = "Data tren emisi harian tidak dapat dianalisis."
    trend_recommendation = "Lengkapi data aktivitas harian untuk mendapatkan wawasan tren mingguan."
    if daily_cols:
        daily_totals = {col.replace('emisi_elektronik_', '').capitalize(): filtered_df[col].sum() for col in daily_cols}
        if any(daily_totals.values()):
            daily_df = pd.DataFrame(list(daily_totals.items()), columns=['Hari', 'Total Emisi (kg CO₂)'])
            daily_df['order'] = daily_df['Hari'].map({day: i for i, day in enumerate(day_order)})
            daily_df = daily_df.sort_values('order').drop(columns='order')
            if not daily_df.empty:
                daily_trend_table_html = "".join([f"<tr><td>{row['Hari']}</td><td style='text-align:right;'>{row['Total Emisi (kg CO₂)']:.1f}</td></tr>" for _, row in daily_df.iterrows()])
                peak_day_df = daily_df.sort_values(by='Total Emisi (kg CO₂)', ascending=False)
                peak_day = peak_day_df.iloc[0]['Hari']
                low_day = peak_day_df.iloc[-1]['Hari']
                trend_conclusion = f"Pola penggunaan elektronik menunjukkan puncak pada hari <strong>{peak_day}</strong> dan menurun signifikan pada <strong>{low_day}</strong>, menandakan adanya korelasi kuat dengan aktivitas akademik."
                trend_recommendation = f"Pengelola kampus dapat menjadwalkan kampanye komunikasi (misal: email, konten media sosial) mengenai hemat energi pada hari <strong>{peak_day}</strong> atau sehari sebelumnya untuk dampak maksimal."

    # Insight 2: Faculty Analysis
    fakultas_table_html = "<tr><td colspan='3'>Data fakultas tidak tersedia.</td></tr>"
    fakultas_conclusion = "Tidak dapat melakukan analisis emisi per fakultas."
    fakultas_recommendation = "Integrasikan data responden untuk wawasan per fakultas."
    if df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        if not df_with_fakultas.empty and 'fakultas' in df_with_fakultas.columns:
            fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_elektronik_mingguan'].agg(['sum', 'count']).round(2)
            fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 1].sort_values('sum', ascending=False)
            if not fakultas_stats.empty:
                fakultas_table_html = "".join([f"<tr><td>{fakultas}</td><td style='text-align:right;'>{row['sum']:.2f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for fakultas, row in fakultas_stats.head(10).iterrows()])
                highest_fakultas = fakultas_stats.index[0]
                fakultas_conclusion = f"Total emisi elektronik tertinggi berasal dari mahasiswa fakultas <strong>{highest_fakultas}</strong>. Ini bisa disebabkan oleh durasi penggunaan perangkat pribadi yang lebih lama atau fasilitas kampus yang intensif digunakan."
                fakultas_recommendation = f"Jadikan gedung-gedung utama fakultas <strong>{highest_fakultas}</strong> sebagai prioritas untuk program 'walk-through audit' energi. Audit ini bertujuan untuk mengidentifikasi potensi penghematan sederhana seperti mematikan lampu/AC di ruang kosong."

    # Insight 3: Device Proportion
    total_device_emission = sum(device_emissions.values())
    device_table_html = "".join([f"<tr><td>{device}</td><td style='text-align:right;'>{emisi:.2f}</td><td style='text-align:right;'>{(emisi/total_device_emission*100 if total_device_emission > 0 else 0):.1f}%</td></tr>" for device, emisi in sorted(device_emissions.items(), key=lambda item: item[1], reverse=True)])
    dominant_device = max(device_emissions, key=device_emissions.get) if device_emissions else "N/A"
    dominant_percentage = (device_emissions.get(dominant_device, 0) / total_device_emission * 100) if total_device_emission > 0 else 0
    device_conclusion = f"Perangkat <strong>{dominant_device}</strong> adalah penyumbang emisi terbesar dari sektor elektronik, mencakup <strong>{dominant_percentage:.1f}%</strong> dari total."
    rec_text = f"Pengelola kampus dapat mempertimbangkan kebijakan pengadaan perangkat <strong>{dominant_device}</strong> hemat energi (label bintang 4 atau 5) untuk penggantian atau pengadaan baru di masa depan." if dominant_device in ['AC', 'Lampu'] else "Pengelola dapat mempromosikan kebiasaan hemat energi untuk perangkat pribadi melalui materi edukasi di website atau layar informasi digital kampus."
    device_recommendation = rec_text

    # Insight 4: Daily Activity Heatmap
    heatmap_header_html = "<tr><th>Waktu</th><th>Senin</th><th>Selasa</th><th>Rabu</th><th>Kamis</th><th>Jumat</th><th>Sabtu</th><th>Minggu</th></tr>"
    heatmap_body_html = "<tr><td colspan='8'>Data aktivitas tidak cukup untuk membuat heatmap.</td></tr>"
    heatmap_conclusion = "Pola penggunaan fasilitas (AC & Lampu) belum dapat diidentifikasi secara detail."
    heatmap_recommendation = "Tingkatkan kelengkapan data aktivitas harian untuk analisis jam-jam sibuk yang lebih akurat."
    if not activities_df.empty:
        heatmap_df = activities_df.groupby(['day', 'time_range']).agg(emisi_ac_sum=('emisi_ac', 'sum'), emisi_lampu_sum=('emisi_lampu', 'sum')).reset_index()
        heatmap_df['total_emisi'] = heatmap_df['emisi_ac_sum'] + heatmap_df['emisi_lampu_sum']
        if not heatmap_df.empty:
            pivot_df = heatmap_df.pivot_table(index='time_range', columns='day', values='total_emisi', fill_value=0)
            pivot_df = pivot_df.reindex(columns=day_order, fill_value=0) 
            try:
                pivot_df.index = sorted(pivot_df.index, key=lambda x: int(x.split(':')[0]))
            except (ValueError, IndexError):
                pass 
            body_rows_list = []
            for time_slot, row in pivot_df.iterrows():
                cells = "".join([f"<td style='text-align:center;'>{val:.2f}</td>" for val in row])
                body_rows_list.append(f"<tr><td><strong>{time_slot}</strong></td>{cells}</tr>")
            heatmap_body_html = "".join(body_rows_list)
            peak_time_emissions = pivot_df.sum(axis=1)
            if not peak_time_emissions.empty:
                peak_time_slot = peak_time_emissions.idxmax()
                heatmap_conclusion = f"Emisi dari fasilitas kampus (AC/Lampu) mencapai puncaknya pada jam <strong>{peak_time_slot}</strong>, menunjukkan waktu penggunaan fasilitas paling intensif."
                heatmap_recommendation = f"Jadikan jam <strong>{peak_time_slot}</strong> sebagai referensi untuk kebijakan operasional, seperti menyetel timer AC untuk mati otomatis setelah jam tersebut di area-area umum atau ruang kelas yang tidak terjadwal."

    # Insight 5: Popular Classrooms
    class_activities = activities_df[activities_df['kegiatan'].str.contains('kelas', case=False, na=False)] if not activities_df.empty else pd.DataFrame()
    location_table_html = "<tr><td colspan='3'>Data aktivitas kelas tidak tersedia.</td></tr>"
    location_conclusion = "Tidak dapat mengidentifikasi gedung kelas yang paling sering digunakan."
    location_recommendation = "Lengkapi data aktivitas harian untuk analisis penggunaan fasilitas yang lebih baik."
    if not class_activities.empty:
        location_stats = class_activities.groupby('lokasi')['duration'].agg(['sum', 'count']).sort_values('count', ascending=False)
        location_stats.columns = ['Total Jam Pakai', 'Jumlah Sesi']
        if not location_stats.empty:
            location_table_html = "".join([f"<tr><td>{loc}</td><td style='text-align:center;'>{int(row['Jumlah Sesi'])}</td><td style='text-align:right;'>{row['Total Jam Pakai']:.1f}</td></tr>" for loc, row in location_stats.head(10).iterrows()])
            popular_building = location_stats.index[0]
            sessions = int(location_stats.iloc[0]['Jumlah Sesi'])
            location_conclusion = f"Gedung <strong>{popular_building}</strong> adalah yang paling sering digunakan untuk aktivitas kelas, dengan tercatat <strong>{sessions}</strong> sesi. Ini menjadikannya target yang efisien untuk intervensi."
            location_recommendation = f"Usulkan pemasangan sensor gerak untuk lampu dan AC di gedung <strong>{popular_building}</strong> sebagai proyek percontohan 'Smart Building'. Keberhasilan di lokasi ini dapat menjadi justifikasi untuk ekspansi ke gedung lain."

    # --- HTML Generation --- (Tidak ada perubahan di sini)
    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Elektronik</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
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
        <div class="header"><h1>Laporan Emisi Elektronik</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO₂</strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO₂</strong>Rata-rata/Mahasiswa</div>
        </div>
        <h2>1. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO₂)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        <h2>2. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO₂)</th><th>Jumlah Responden</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        <h2>3. Proporsi Emisi per Perangkat</h2>
        <table><thead><tr><th>Perangkat</th><th>Total Emisi (kg CO₂)</th><th>Persentase</th></tr></thead><tbody>{device_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {device_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {device_recommendation}</div>
        <h2>4. Pola Penggunaan Fasilitas Kampus</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>
        <h2>5. Gedung Kelas Paling Populer</h2>
        <table><thead><tr><th>Gedung</th><th>Jumlah Sesi</th><th>Total Jam Pakai</th></tr></thead><tbody>{location_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {location_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {location_recommendation}</div>
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
                <h1 class="header-title">Emisi Elektronik</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.2)  # Small delay for header animation

    # Load data with loading decorators
    df_electronic = load_electronic_data()
    df_activities = load_daily_activities()
    df_responden = load_responden_data()
    
    if df_electronic.empty:
        st.error("Data elektronik tidak tersedia")
        return

    # Data processing with loading
    with loading():
        # Rename 'emisi_elektronik' -> 'emisi_elektronik_mingguan' for consistency
        if 'emisi_elektronik' in df_electronic.columns:
            df_electronic = df_electronic.rename(columns={'emisi_elektronik': 'emisi_elektronik_mingguan'})

        df_electronic['emisi_elektronik_mingguan'] = pd.to_numeric(df_electronic['emisi_elektronik_mingguan'], errors='coerce')
        df_electronic = df_electronic.dropna(subset=['emisi_elektronik_mingguan'])
        
        # Konversi durasi ke numerik, isi NaN dengan 0
        df_electronic['durasi_hp'] = pd.to_numeric(df_electronic['durasi_hp'], errors='coerce').fillna(0)
        df_electronic['durasi_laptop'] = pd.to_numeric(df_electronic['durasi_laptop'], errors='coerce').fillna(0)
        df_electronic['durasi_tab'] = pd.to_numeric(df_electronic['durasi_tab'], errors='coerce').fillna(0)
        
        # Buat kolom emisi harian yang tidak ada di Supabase
        df_electronic['hari_datang'] = df_electronic['hari_datang'].astype(str).fillna('')
        df_electronic['jumlah_hari_datang'] = df_electronic['hari_datang'].str.split(',').str.len()
        
        # Emisi harian adalah emisi mingguan dibagi jumlah hari datang
        # Tambah 1e-9 untuk menghindari pembagian dengan nol
        df_electronic['emisi_harian'] = df_electronic['emisi_elektronik_mingguan'] / (df_electronic['jumlah_hari_datang'] + 1e-9)

        days_of_week = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
        for day in days_of_week:
            col_name = f'emisi_elektronik_{day}'
            df_electronic[col_name] = np.where(
                df_electronic['hari_datang'].str.contains(day.capitalize(), na=False), 
                df_electronic['emisi_harian'], 
                0
            )
        
        time.sleep(0.15)
    
    activities_parsed = parse_time_activities(df_activities)

    # Filters
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:", 
            options=day_options, 
            placeholder="Pilih Opsi", 
            key='electronic_day_filter'
        )
    
    with filter_col2:
        device_options = ['Smartphone', 'Laptop', 'Tablet', 'AC', 'Lampu']
        selected_devices = st.multiselect(
            "Perangkat:", 
            options=device_options, 
            placeholder="Pilih Opsi", 
            key='electronic_device_filter'
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
                key='electronic_fakultas_filter'
            )
        else:
            selected_fakultas = []

    # Apply filters with loading
    filtered_df = apply_electronic_filters(df_electronic, selected_days, selected_devices, selected_fakultas, df_responden)

    # Export buttons
    with export_col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Raw Data", 
            data=csv_data, 
            file_name=f"electronic_{len(filtered_df)}.csv", 
            mime="text/csv", 
            use_container_width=True, 
            key="electronic_export_csv"
        )
    
    with export_col2:
        try:
            filtered_activities = activities_parsed[activities_parsed['id_responden'].isin(filtered_df['id_responden'])] if not activities_parsed.empty else pd.DataFrame()
            device_emissions = calculate_device_emissions(filtered_df, filtered_activities)
            pdf_content = generate_electronic_pdf_report(filtered_df, filtered_activities, device_emissions, df_responden)
            st.download_button(
                "Laporan", 
                data=pdf_content, 
                file_name=f"electronic_report_{len(filtered_df)}.html", 
                mime="text/html", 
                use_container_width=True, 
                key="electronic_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")


    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return
    
    # Calculate emissions with loading
    with loading():
        filtered_activities = activities_parsed[activities_parsed['id_responden'].isin(filtered_df['id_responden'])] if not activities_parsed.empty else pd.DataFrame()
        device_emissions = calculate_device_emissions(filtered_df, filtered_activities)
        time.sleep(0.1)

    # Charts with loading animations - Row 1
    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # 1. Tren Harian - Line chart 
            days_of_week = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
            daily_cols = [f'emisi_elektronik_{day}' for day in days_of_week if f'emisi_elektronik_{day}' in filtered_df.columns]            
            if daily_cols:
                daily_data = []
                for col in daily_cols:
                    day = col.replace('emisi_elektronik_', '').capitalize()
                    if not selected_days or day in selected_days:
                        total_emisi = filtered_df[col].sum()
                        daily_data.append({'Hari': day, 'Emisi': total_emisi})
                
                if daily_data:
                    daily_df = pd.DataFrame(daily_data)
                    
                    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                    daily_df['Order'] = daily_df['Hari'].map({day: i for i, day in enumerate(day_order)})
                    daily_df = daily_df.sort_values('Order')
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=daily_df['Hari'], y=daily_df['Emisi'],
                        fill='tonexty', mode='lines+markers',
                        line=dict(color='#3288bd', width=2, shape='spline'),
                        marker=dict(size=6, color='#3288bd', line=dict(color='white', width=1)),
                        fillcolor="rgba(102, 194, 165, 0.3)",
                        hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>',
                        showlegend=False
                    ))
                    
                    fig_trend.update_layout(
                        height=270, margin=dict(t=25, b=0, l=0, r=20),
                        xaxis_title="", yaxis_title="Emisi (kg CO₂)",
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                                  font=dict(size=12, color="#000000")),
                        xaxis=dict(showgrid=False, tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10))),
                        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (Kg CO₂)", font=dict(size=10)))
                    )
                    
                    st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)

        with col2:
            # 2. Emisi per Fakultas - Horizontal Bar (SAME AS TRANSPORTATION)
            if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
                fakultas_mapping = get_fakultas_mapping()
                df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            

                if 'id_responden' in df_responden.columns and 'id_responden' in filtered_df.columns:
                    df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                    fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_elektronik_mingguan'].agg(['sum', 'count']).reset_index()
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
                                textfont=dict(color='white', size=7, weight='bold'),
                                hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["count"]}<extra></extra>'
                            ))
                        
                        fig_fakultas.update_layout(
                            height=270, margin=dict(t=25, b=0, l=0, r=20),
                            title=dict(text="<b>Emisi per Fakultas</b>", x=0.4, y=0.95,
                                      font=dict(size=12, color="#000000")),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Total Emisi (kg CO₂)", font=dict(size=10))),
                            yaxis=dict(tickfont=dict(size=8), title=dict(text="Fakultas/Sekolah", font=dict(size=10)))
                        )
                        
                        st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
                    else:
                        st.info("Data fakultas tidak cukup (min 2 mahasiswa)")
                else:
                    st.info("Data fakultas tidak dapat digabungkan")

        with col3:
            # 3. Proporsi Emisi per Perangkat - DONUT CHART
            if device_emissions:
                filtered_device_emissions = device_emissions.copy()
                if selected_devices:
                    filtered_device_emissions = {k: v for k, v in device_emissions.items() 
                                               if k in selected_devices or k in ['AC', 'Lampu']}
                
                devices = list(filtered_device_emissions.keys())
                emissions = list(filtered_device_emissions.values())
                
                if devices and emissions:
                    colors = [DEVICE_COLORS.get(device, MAIN_PALETTE[i % len(MAIN_PALETTE)]) for i, device in enumerate(devices)]
                    
                    fig_devices = go.Figure(data=[go.Pie(
                        labels=devices,
                        values=emissions,
                        hole=0.45,
                        marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
                        textposition='outside',
                        textinfo='label+percent',
                        textfont=dict(size=8, family="Poppins"),
                        hovertemplate='<b>%{label}</b><br>%{value:.2f} kg CO₂ (%{percent})<extra></extra>'
                    )])
                    
                    total_emisi = sum(emissions)
                    center_text = f"<b style='font-size:14px'>{total_emisi:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                    fig_devices.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                    
                    fig_devices.update_layout(
                        height=270, margin=dict(t=40, b=10, l=0, r=0), showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        title=dict(text="<b>Proporsi Emisi per Perangkat</b>", x=0.32, y=0.95, 
                                  font=dict(size=12, color="#000000"))
                    )  
                    st.plotly_chart(fig_devices, config=MODEBAR_CONFIG, use_container_width=True)

        time.sleep(0.2) 

    # Row 2: Second 3 visualizations with loading
    with loading():
        col1, col2 = st.columns([1, 1])

        with col1:
            # 4. Heatmap Hari dan Jam
            if not filtered_activities.empty:
                activities_for_heatmap = filtered_activities.copy()
                if selected_days:
                    activities_for_heatmap = activities_for_heatmap[activities_for_heatmap['day'].isin(selected_days)]
                
                if not activities_for_heatmap.empty:
                    heatmap_df = activities_for_heatmap.groupby(['day', 'time_range']).agg({
                        'emisi_ac': 'sum',
                        'emisi_lampu': 'sum'
                    }).reset_index()
                    heatmap_df['total_emisi'] = heatmap_df['emisi_ac'] + heatmap_df['emisi_lampu']
                    
                    heatmap_data = heatmap_df.pivot(index='day', columns='time_range', values='total_emisi')
                    heatmap_data = heatmap_data.fillna(0)
                    
                    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                    heatmap_data = heatmap_data.reindex([day for day in day_order if day in heatmap_data.index])
                    
                    if not heatmap_data.empty and len(heatmap_data.columns) > 0:
                        time_columns = heatmap_data.columns.tolist()
                        time_columns.sort(key=lambda x: int(x.split(':')[0]) if ':' in str(x) else 0)
                        heatmap_data = heatmap_data[time_columns]
                        
                        fig_heatmap = go.Figure(data=go.Heatmap(
                            z=heatmap_data.values,
                            x=heatmap_data.columns,
                            y=heatmap_data.index,
                            colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                            hoverongaps=False,
                            hovertemplate='<b>%{y}</b><br>Jam: %{x}<br>Emisi: %{z:.2f} kg CO₂<br><extra></extra>',
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
                            height=270, margin=dict(t=30, b=0, l=0, r=0),
                            title=dict(text="<b>Heatmap Emisi Harian Per Jam</b>", x=0.4, y=0.95, 
                                    font=dict(size=12, color="#000000")),
                            xaxis=dict(tickfont=dict(size=8), tickangle=-25, title=dict(text="Jam", font=dict(size=10))),
                            yaxis=dict(tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10))),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)

        with col2:
            # 5. Gedung Kelas Terpopuler
            if not filtered_activities.empty and 'lokasi' in filtered_activities.columns:
                activities_for_location = filtered_activities.copy()
                if selected_days:
                    activities_for_location = activities_for_location[activities_for_location['day'].isin(selected_days)]
                
                class_activities = activities_for_location[activities_for_location['kegiatan'].str.contains('kelas', case=False, na=False)]
                
                if not class_activities.empty:
                    location_stats = class_activities.groupby('lokasi').agg({
                        'emisi_ac': 'sum',
                        'emisi_lampu': 'sum',
                        'duration': 'sum'
                    }).reset_index()
                    location_stats['total_emisi'] = location_stats['emisi_ac'] + location_stats['emisi_lampu']
                    location_stats['session_count'] = class_activities.groupby('lokasi').size().values
                    location_stats['avg_emisi_per_session'] = location_stats['total_emisi'] / location_stats['session_count']
                    
                    location_stats = location_stats.sort_values('session_count', ascending=False).head(10)
                    
                    fig_location = go.Figure()
                    
                    max_sessions = location_stats['session_count'].max()
                    min_sessions = location_stats['session_count'].min()
                    
                    colors = []
                    for _, row in location_stats.iterrows():
                        if max_sessions > min_sessions:
                            ratio = (row['session_count'] - min_sessions) / (max_sessions - min_sessions)
                            if ratio < 0.2:
                                colors.append('#e6f598') 
                            elif ratio < 0.4:
                                colors.append('#abdda4') 
                            elif ratio < 0.6:
                                colors.append('#66c2a5')  
                            elif ratio < 0.8:
                                colors.append('#3288bd') 
                            else:
                                colors.append('#d53e4f') 
                        else:
                            colors.append('#3288bd')  
                    
                    # Add bars
                    for i, (_, row) in enumerate(location_stats.iterrows()):
                        fig_location.add_trace(go.Bar(
                            x=[row['lokasi']],
                            y=[row['session_count']],
                            marker=dict(
                                color=colors[i],
                                line=dict(color='white', width=1.5),
                                opacity=0.85
                            ),
                            showlegend=False,
                            text=[f"{row['session_count']}"],
                            textposition='inside',
                            textfont=dict(size=8, color='#2d3748', weight='bold'),
                            hovertemplate=f'<b>{row["lokasi"]}</b><br>Jumlah Sesi: {row["session_count"]}<br>Total Emisi: {row["total_emisi"]:.2f} kg CO₂<br>Emisi per Sesi: {row["avg_emisi_per_session"]:.2f} kg CO₂<br><i>Frekuensi penggunaan gedung</i><extra></extra>',
                            name=row['lokasi']
                        ))
                    
                    avg_sessions = location_stats['session_count'].mean()
                    fig_location.add_hline(
                        y=avg_sessions,
                        line_dash="dash",
                        line_color="#5e4fa2",  
                        line_width=2,
                        annotation_text=f"Rata-rata: {avg_sessions:.1f}",
                        annotation_position="top right",
                        annotation=dict(
                            bgcolor="white", 
                            bordercolor="#5e4fa2", 
                            borderwidth=1,
                            font=dict(size=8)
                        )
                    )
                    
                    fig_location.update_layout(
                        height=270,
                        margin=dict(t=25, b=0, l=0, r=0),
                        title=dict(text="<b>Emisi Per Lokasi</b>", x=0.45, y=0.95,
                                  font=dict(size=12, color="#000000")),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=False, 
                            tickfont=dict(size=8), 
                            tickangle=-45,
                            title=dict(text="Gedung Kelas", font=dict(size=10))
                        ),
                        yaxis=dict(
                            showgrid=True, 
                            gridcolor='rgba(0,0,0,0.1)', 
                            tickfont=dict(size=8),
                            title=dict(text="Jumlah Sesi", font=dict(size=10))
                        ),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_location, config=MODEBAR_CONFIG, use_container_width=True)
                else:
                    st.info("Data aktivitas kelas tidak tersedia")
            else:
                st.info("Data lokasi kelas tidak tersedia")

        time.sleep(0.2)  # Final delay for row 2 charts

if __name__ == "__main__":
    show()