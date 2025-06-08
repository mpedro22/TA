import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

DEVICE_COLORS = {
    'Smartphone': '#d53e4f',  
    'Laptop': '#3288bd',      
    'Tablet': '#66c2a5',     
    'AC': '#f46d43',         
    'Lampu': '#fdae61'        
}

@st.cache_data(ttl=3600)
def load_electronic_data():
    """Load electronic data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=622151341"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading electronic data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_daily_activities():
    """Load daily activities data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading daily activities data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_responden_data():
    """Load responden data for fakultas information"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    try:
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

def parse_time_activities(df_activities):
    """Parse time and location data from daily activities"""
    parsed_data = []
    if df_activities.empty or 'hari' not in df_activities.columns:
        return pd.DataFrame()
    
    for _, row in df_activities.iterrows():
        hari_value = str(row['hari'])
        if '_' in hari_value:
            parts = hari_value.split('_')
            if len(parts) == 2:
                day = parts[0].capitalize()
                time_str = parts[1]
                if len(time_str) == 4:
                    start_hour = int(time_str[:2])
                    end_hour = int(time_str[2:])
                    
                    # Create time range label
                    time_range = f"{start_hour:02d}:00-{end_hour:02d}:00"
                    
                    parsed_data.append({
                        'id_responden': row.get('id_responden', ''),
                        'day': day,
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                        'time_range': time_range,
                        'duration': end_hour - start_hour,
                        'lokasi': row.get('lokasi', ''),
                        'kegiatan': row.get('kegiatan', ''),
                        'ac': row.get('ac', ''),
                        'emisi_ac': pd.to_numeric(row.get('emisi_ac', 0), errors='coerce'),
                        'emisi_lampu': pd.to_numeric(row.get('emisi_lampu', 0), errors='coerce'),
                        'emisi_makanminum': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce')
                    })
    
    return pd.DataFrame(parsed_data)

def apply_electronic_filters(df, selected_days, selected_devices, selected_fakultas, df_responden=None):
    """Apply filters to the electronic dataframe"""
    filtered_df = df.copy()
    
    # Filter by day (using hari_datang)
    if selected_days and 'hari_datang' in filtered_df.columns:
        day_mask = pd.Series(False, index=filtered_df.index)
        for day in selected_days:
            day_mask |= filtered_df['hari_datang'].str.contains(day, case=False, na=False)
        filtered_df = filtered_df[day_mask]
    
    # Filter by device usage
    if selected_devices:
        device_mask = pd.Series(False, index=filtered_df.index)
        
        for device in selected_devices:
            if device == 'Smartphone' and 'penggunaan_hp' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_hp'].str.contains('Ya', case=False, na=False))
            elif device == 'Laptop' and 'penggunaan_laptop' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_laptop'].str.contains('Ya', case=False, na=False))
            elif device == 'Tablet' and 'penggunaan_tab' in filtered_df.columns:
                device_mask |= (filtered_df['penggunaan_tab'].str.contains('Ya', case=False, na=False))
        
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
    
    return filtered_df

def calculate_device_emissions(df, activities_df):
    """Calculate emissions for each device type based on actual data"""
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
    
    return device_emissions

def generate_electronic_pdf_report(filtered_df, activities_df, device_emissions, df_responden=None):
    """Generate professional HTML report optimized for PDF printing"""
    from datetime import datetime
    import pandas as pd
    
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
    
    total_emisi = sum(device_emissions.values()) if device_emissions else 0
    
    valid_responden = filtered_df[filtered_df['id_responden'].notna() & (filtered_df['id_responden'] != '') & (filtered_df['id_responden'] != 0)]
    total_responden = len(valid_responden)
    
    avg_emisi_per_person = total_emisi / total_responden if total_responden > 0 else 0
    
    smartphone_users = len(valid_responden[valid_responden['penggunaan_hp'].str.contains('Ya', case=False, na=False)]) if 'penggunaan_hp' in valid_responden.columns else 0
    laptop_users = len(valid_responden[valid_responden['penggunaan_laptop'].str.contains('Ya', case=False, na=False)]) if 'penggunaan_laptop' in valid_responden.columns else 0
    tablet_users = len(valid_responden[valid_responden['penggunaan_tab'].str.contains('Ya', case=False, na=False)]) if 'penggunaan_tab' in valid_responden.columns else 0
    
    expected_daily_cols = [
        'emisi_elektronik_senin', 'emisi_elektronik_selasa', 'emisi_elektronik_rabu',
        'emisi_elektronik_kamis', 'emisi_elektronik_jumat', 'emisi_elektronik_sabtu', 
        'emisi_elektronik_minggu'
    ]
    daily_cols = [col for col in expected_daily_cols if col in valid_responden.columns]
    daily_analysis = []
    
    for col in daily_cols:
        day = col.replace('emisi_elektronik_', '').capitalize()
        total_day_emisi = valid_responden[col].sum()
        daily_analysis.append({'day': day, 'emission': total_day_emisi})
    
    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    daily_analysis = sorted(daily_analysis, key=lambda x: day_order.index(x['day']) if x['day'] in day_order else 999)
    
    if daily_analysis:
        highest_day = max(daily_analysis, key=lambda x: x['emission'])
        lowest_day = min(daily_analysis, key=lambda x: x['emission'])
        weekday_emissions = [d['emission'] for d in daily_analysis[:5]]  # Mon-Fri
        weekend_emissions = [d['emission'] for d in daily_analysis[5:]]  # Sat-Sun
        avg_weekday = sum(weekday_emissions) / len(weekday_emissions) if weekday_emissions else 0
        avg_weekend = sum(weekend_emissions) / len(weekend_emissions) if weekend_emissions else 0
    else:
        highest_day = {'day': 'N/A', 'emission': 0}
        lowest_day = {'day': 'N/A', 'emission': 0}
        avg_weekday = 0
        avg_weekend = 0
    
    # Top 3 fakultas with highest average emissions
    if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        
        # Merge with valid responden
        df_with_fakultas = valid_responden.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        
        if not df_with_fakultas.empty and 'emisi_elektronik_mingguan' in df_with_fakultas.columns:
            fakultas_emissions = df_with_fakultas.groupby('fakultas').agg({
                'emisi_elektronik_mingguan': ['mean', 'count']
            }).reset_index()
            fakultas_emissions.columns = ['fakultas', 'avg_emission', 'student_count']
            fakultas_emissions = fakultas_emissions[fakultas_emissions['student_count'] >= 2]  # At least 2 students
            top_fakultas = fakultas_emissions.nlargest(3, 'avg_emission')
        else:
            top_fakultas = pd.DataFrame()
    else:
        top_fakultas = pd.DataFrame()
    
    # Usage duration analysis - use valid responden
    avg_smartphone_duration = valid_responden['durasi_hp'].mean() if 'durasi_hp' in valid_responden.columns else 0
    avg_laptop_duration = valid_responden['durasi_laptop'].mean() if 'durasi_laptop' in valid_responden.columns else 0
    avg_tablet_duration = valid_responden['durasi_tab'].mean() if 'durasi_tab' in valid_responden.columns else 0
    
    # Duration distribution analysis
    duration_stats = {}
    if 'durasi_hp' in valid_responden.columns:
        smartphone_data = valid_responden[valid_responden['durasi_hp'] > 0]['durasi_hp']
        if not smartphone_data.empty:
            duration_stats['Smartphone'] = {
                'median': smartphone_data.median(),
                'q75': smartphone_data.quantile(0.75),
                'q25': smartphone_data.quantile(0.25),
                'max': smartphone_data.max(),
                'users': len(smartphone_data)
            }
    
    if 'durasi_laptop' in valid_responden.columns:
        laptop_data = valid_responden[valid_responden['durasi_laptop'] > 0]['durasi_laptop']
        if not laptop_data.empty:
            duration_stats['Laptop'] = {
                'median': laptop_data.median(),
                'q75': laptop_data.quantile(0.75),
                'q25': laptop_data.quantile(0.25),
                'max': laptop_data.max(),
                'users': len(laptop_data)
            }
    
    if 'durasi_tab' in valid_responden.columns:
        tablet_data = valid_responden[valid_responden['durasi_tab'] > 0]['durasi_tab']
        if not tablet_data.empty:
            duration_stats['Tablet'] = {
                'median': tablet_data.median(),
                'q75': tablet_data.quantile(0.75),
                'q25': tablet_data.quantile(0.25),
                'max': tablet_data.max(),
                'users': len(tablet_data)
            }
    
    # Heatmap analysis
    heatmap_conclusion = "Data aktivitas harian tidak tersedia."
    peak_time_range = "N/A"
    peak_day = "N/A"
    if not activities_df.empty:
        # Find peak emission time and day
        activities_df['total_emisi_activity'] = activities_df['emisi_ac'] + activities_df['emisi_lampu']
        if not activities_df.empty:
            peak_activity = activities_df.loc[activities_df['total_emisi_activity'].idxmax()]
            peak_time_range = peak_activity.get('time_range', 'N/A')
            peak_day = peak_activity.get('day', 'N/A')
            heatmap_conclusion = f"Aktivitas tertinggi terjadi pada hari {peak_day} di jam {peak_time_range} dengan emisi {peak_activity['total_emisi_activity']:.2f} kg CO₂."
    
    # Device emissions analysis for insights
    if device_emissions:
        dominant_device = max(device_emissions.items(), key=lambda x: x[1])
        dominant_percentage = (dominant_device[1] / total_emisi * 100) if total_emisi > 0 else 0
        
        # Infrastructure vs Personal devices
        infrastructure_devices = ['AC', 'Lampu']
        personal_devices = ['Smartphone', 'Laptop', 'Tablet']
        
        infrastructure_total = sum([device_emissions.get(device, 0) for device in infrastructure_devices])
        personal_total = sum([device_emissions.get(device, 0) for device in personal_devices])
        
        infrastructure_percentage = (infrastructure_total / total_emisi * 100) if total_emisi > 0 else 0
        personal_percentage = (personal_total / total_emisi * 100) if total_emisi > 0 else 0
    else:
        dominant_device = ('N/A', 0)
        dominant_percentage = 0
        infrastructure_percentage = 0
        personal_percentage = 0
    
    # CONSISTENT WITH TRANSPORTATION REPORT STYLING
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Emisi Elektronik ITB</title>
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
            <h1>LAPORAN EMISI ELEKTRONIK</h1>
            <div class="subtitle">Institut Teknologi Bandung</div>
            <div class="timestamp">Dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M WIB')}</div>
        </div>
        
        <div class="executive-summary avoid-break">
            <h2 style="margin-top: 0; color: #16a34a; font-size: 14px; font-weight: 600;">Ringkasan</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{total_emisi:.1f}</span>
                    <div class="metric-label">Total Emisi (kg CO₂)</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{avg_emisi_per_person:.2f}</span>
                    <div class="metric-label">Rata-rata per Mahasiswa</div>
                </div>
            </div>
        </div>
        
        <!-- 1. Komposisi Emisi per Perangkat -->
        <div class="section avoid-break">
            <h2 class="section-title">1. Komposisi Emisi per Perangkat</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Perangkat</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Persentase (%)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add device emissions data
    for device, emisi in device_emissions.items():
        percentage = (emisi / total_emisi * 100) if total_emisi > 0 else 0
        if percentage > 30:
            status = 'Tinggi'
        elif percentage > 15:
            status = 'Sedang'
        else:
            status = 'Rendah'
        
        html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{device}</td>
                            <td>{emisi:.2f}</td>
                            <td>{percentage:.1f}%</td>
                            <td>{status}</td>
                        </tr>
        """
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {dominant_device[0]} mendominasi dengan {dominant_percentage:.1f}% total emisi perangkat elektronik.
                </div>
            </div>
        </div>
        
        <!-- 2. Tren Emisi Harian -->
        <div class="section avoid-break">
            <h2 class="section-title">2. Tren Emisi Harian</h2>
            <div class="section-content">
    """
    
    if daily_analysis:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Hari</th>
                            <th>Total Emisi (kg CO₂)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for day_data in daily_analysis:
            html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{day_data['day']}</td>
                            <td>{day_data['emission']:.2f}</td>
                        </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data emisi harian tidak tersedia.</p>"
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> Hari {highest_day['day']} mencatat emisi tertinggi ({highest_day['emission']:.1f} kg CO₂), hari {lowest_day['day']} terendah ({lowest_day['emission']:.1f} kg CO₂).
                </div>
            </div>
        </div>
        
        <!-- 3. Emisi per Fakultas -->
        <div class="section avoid-break">
            <h2 class="section-title">3. Emisi per Fakultas</h2>
            <div class="section-content">
    """
    
    if not top_fakultas.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Fakultas</th>
                            <th>Rata-rata Emisi (kg CO₂/minggu)</th>
                            <th>Jumlah Mahasiswa</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (_, row) in enumerate(top_fakultas.iterrows(), 1):
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{row['fakultas']}</td>
                            <td>{row['avg_emission']:.2f}</td>
                            <td>{row['student_count']} mahasiswa</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
        """
        fakultas_conclusion = f"{top_fakultas.iloc[0]['fakultas']} memiliki rata-rata emisi elektronik tertinggi sebesar {top_fakultas.iloc[0]['avg_emission']:.2f} kg CO₂ per minggu."
    else:
        html_content += "<p>Data fakultas tidak tersedia.</p>"
        fakultas_conclusion = "Data fakultas tidak tersedia."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {fakultas_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 4. Analisis Waktu dan Ruang (Heatmap) -->
        <div class="section avoid-break">
            <h2 class="section-title">4. Analisis Waktu dan Ruang</h2>
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
                            <td style="text-align: left; font-weight: 500;">Waktu Puncak</td>
                            <td>{peak_time_range}</td>
                            <td>Jam dengan aktivitas tertinggi</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Hari Puncak</td>
                            <td>{peak_day}</td>
                            <td>Hari dengan aktivitas tertinggi</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Total Aktivitas</td>
                            <td>{len(activities_df)} sesi</td>
                            <td>Jumlah sesi pembelajaran</td>
                        </tr>
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {heatmap_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 5. Pola Emisi per Responden -->
        <div class="section avoid-break">
            <h2 class="section-title">5. Pola Emisi per Responden</h2>
            <div class="section-content">
    """
    
    # Calculate user categorization for report
    if not filtered_df.empty:
        user_emissions_report = filtered_df[['id_responden', 'emisi_elektronik_mingguan']].copy()
        Q1 = user_emissions_report['emisi_elektronik_mingguan'].quantile(0.25)
        Q3 = user_emissions_report['emisi_elektronik_mingguan'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        median_val = user_emissions_report['emisi_elektronik_mingguan'].median()
        
        # Count categories
        heavy_users = len(user_emissions_report[user_emissions_report['emisi_elektronik_mingguan'] > upper_bound])
        light_users = len(user_emissions_report[user_emissions_report['emisi_elektronik_mingguan'] < lower_bound])
        eco_users = len(user_emissions_report[user_emissions_report['emisi_elektronik_mingguan'] < median_val * 0.5])
        high_users = len(user_emissions_report[user_emissions_report['emisi_elektronik_mingguan'] > median_val * 1.5])
        normal_users = total_responden - heavy_users - light_users - eco_users - high_users
        
        html_content += f"""
                <table>
                    <thead>
                        <tr>
                            <th>Kategori Pengguna</th>
                            <th>Jumlah</th>
                            <th>Persentase</th>
                            <th>Range Emisi (kg CO₂)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Eco User</td>
                            <td>{eco_users}</td>
                            <td>{eco_users/total_responden*100:.1f}%</td>
                            <td>< {median_val * 0.5:.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Light User</td>
                            <td>{light_users}</td>
                            <td>{light_users/total_responden*100:.1f}%</td>
                            <td>< {lower_bound:.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Normal User</td>
                            <td>{normal_users}</td>
                            <td>{normal_users/total_responden*100:.1f}%</td>
                            <td>{lower_bound:.2f} - {upper_bound:.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">High User</td>
                            <td>{high_users}</td>
                            <td>{high_users/total_responden*100:.1f}%</td>
                            <td>> {median_val * 1.5:.2f}</td>
                        </tr>
                        <tr>
                            <td style="text-align: left; font-weight: 500;">Heavy User</td>
                            <td>{heavy_users}</td>
                            <td>{heavy_users/total_responden*100:.1f}%</td>
                            <td>> {upper_bound:.2f}</td>
                        </tr>
                    </tbody>
                </table>
        """
        
        # Find dominant user category
        categories = [
            ('Eco User', eco_users),
            ('Light User', light_users), 
            ('Normal User', normal_users),
            ('High User', high_users),
            ('Heavy User', heavy_users)
        ]
        dominant_category = max(categories, key=lambda x: x[1])
        user_pattern_conclusion = f"Kategori {dominant_category[0]} mendominasi dengan {dominant_category[1]} mahasiswa ({dominant_category[1]/total_responden*100:.1f}%), menunjukkan pola penggunaan yang {dominant_category[0].lower().replace(' user', '')}."
    else:
        html_content += "<p>Data pola emisi per responden tidak tersedia.</p>"
        user_pattern_conclusion = "Data pola emisi per responden tidak tersedia."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {user_pattern_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 6. Gedung Kelas Terpopuler -->
        <div class="section avoid-break">
            <h2 class="section-title">6. Gedung Kelas Terpopuler</h2>
            <div class="section-content">
    """
    
    # Calculate location stats for report
    if not activities_df.empty and 'lokasi' in activities_df.columns:
        class_activities_report = activities_df[activities_df['kegiatan'].str.contains('kelas', case=False, na=False)]
        
        if not class_activities_report.empty:
            location_stats_report = class_activities_report.groupby('lokasi').agg({
                'emisi_ac': 'sum',
                'emisi_lampu': 'sum',
                'duration': 'sum'
            }).reset_index()
            location_stats_report['total_emisi'] = location_stats_report['emisi_ac'] + location_stats_report['emisi_lampu']
            location_stats_report['session_count'] = class_activities_report.groupby('lokasi').size().values
            location_stats_report['avg_emisi_per_session'] = location_stats_report['total_emisi'] / location_stats_report['session_count']
            
            # Sort by session count and take top 5 for report
            top_locations = location_stats_report.sort_values('session_count', ascending=False).head(5)
            
            html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Gedung Kelas</th>
                            <th>Jumlah Sesi</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Emisi per Sesi (kg CO₂)</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for idx, (_, row) in enumerate(top_locations.iterrows(), 1):
                html_content += f"""
                            <tr>
                                <td><strong>#{idx}</strong></td>
                                <td style="text-align: left; font-weight: 500;">{row['lokasi']}</td>
                                <td>{row['session_count']}</td>
                                <td>{row['total_emisi']:.2f}</td>
                                <td>{row['avg_emisi_per_session']:.2f}</td>
                            </tr>
                """
            
            html_content += "</tbody></table>"
            
            # Calculate insights for location usage
            most_used_location = top_locations.iloc[0]
            total_sessions = top_locations['session_count'].sum()
            most_used_percentage = (most_used_location['session_count'] / total_sessions * 100)
            
            location_conclusion = f"Gedung {most_used_location['lokasi']} merupakan gedung terpopuler dengan {most_used_location['session_count']} sesi ({most_used_percentage:.1f}% dari total aktivitas) dan emisi rata-rata {most_used_location['avg_emisi_per_session']:.2f} kg CO₂ per sesi."
        else:
            html_content += "<p>Data aktivitas kelas tidak tersedia.</p>"
            location_conclusion = "Data aktivitas kelas tidak tersedia."
    else:
        html_content += "<p>Data lokasi kelas tidak tersedia.</p>"
        location_conclusion = "Data lokasi kelas tidak tersedia."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {location_conclusion}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Institut Teknologi Bandung</strong></p>
            <p>Carbon Emission Dashboard - Electronic Devices Report</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def show():
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

    # Load data
    df_electronic = load_electronic_data()
    df_activities = load_daily_activities()
    df_responden = load_responden_data()
    
    if df_electronic.empty:
        st.error("Data elektronik tidak tersedia")
        return

    df_electronic['emisi_elektronik_mingguan'] = pd.to_numeric(df_electronic['emisi_elektronik_mingguan'], errors='coerce')
    df_electronic = df_electronic.dropna(subset=['emisi_elektronik_mingguan'])
    
    df_electronic['durasi_hp'] = pd.to_numeric(df_electronic['durasi_hp'], errors='coerce').fillna(0)
    df_electronic['durasi_laptop'] = pd.to_numeric(df_electronic['durasi_laptop'], errors='coerce').fillna(0)
    df_electronic['durasi_tab'] = pd.to_numeric(df_electronic['durasi_tab'], errors='coerce').fillna(0)
    
    activities_parsed = parse_time_activities(df_activities)

    # Filters
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([2.2, 2.2, 2.2, 1.2, 1.2])

    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:", 
            options=day_options, 
            placeholder="Pilih Opsi", 
            key='electronic_day_filter'
        )
    
    with filter_col2:
        device_options = ['Smartphone', 'Laptop', 'Tablet']
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

    filtered_df = apply_electronic_filters(df_electronic, selected_days, selected_devices, selected_fakultas, df_responden)

    # Export buttons
    with export_col1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            "Export CSV", 
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
                "Export PDF", 
                data=pdf_content, 
                file_name=f"electronic_{len(filtered_df)}.html", 
                mime="text/html", 
                use_container_width=True, 
                key="electronic_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return
    
    filtered_activities = activities_parsed[activities_parsed['id_responden'].isin(filtered_df['id_responden'])] if not activities_parsed.empty else pd.DataFrame()
    
    device_emissions = calculate_device_emissions(filtered_df, filtered_activities)

    # Row 1: Main Charts
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # 1. Tren Harian - Line chart 
        daily_cols = [col for col in filtered_df.columns if 'emisi_elektronik_' in col and col != 'emisi_elektronik_mingguan']
        
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
                    height=240, margin=dict(t=25, b=5, l=5, r=5),
                    xaxis_title="", yaxis_title="Emisi (kg CO₂)",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, 
                              font=dict(size=11, color="#000000")),
                    xaxis=dict(showgrid=False, tickfont=dict(size=7)),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=7))
                )
                
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 2. Emisi per Fakultas - Horizontal Bar (SAME AS TRANSPORTATION)
        if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
            fakultas_mapping = get_fakultas_mapping()
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            
            if 'id_responden' in df_responden.columns and 'id_responden' in filtered_df.columns:
                df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_elektronik_mingguan'].agg(['mean', 'count']).reset_index()
                fakultas_stats.columns = ['fakultas', 'avg_emisi', 'count']
                fakultas_stats = fakultas_stats[fakultas_stats['count'] >= 2].sort_values('avg_emisi')
                
                max_emisi = fakultas_stats['avg_emisi'].max()
                min_emisi = fakultas_stats['avg_emisi'].min()
                
                fig_fakultas = go.Figure()
                for i, (_, row) in enumerate(fakultas_stats.iterrows()):
                    if max_emisi > min_emisi:
                        ratio = (row['avg_emisi'] - min_emisi) / (max_emisi - min_emisi)
                        sequential_warm = ['#fee08b', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                        color_idx = int(ratio * (len(sequential_warm) - 1))
                        color = sequential_warm[color_idx]
                    else:
                        color = MAIN_PALETTE[i % len(MAIN_PALETTE)]
                    
                    fig_fakultas.add_trace(go.Bar(
                        x=[row['avg_emisi']], y=[row['fakultas']], orientation='h',
                        marker=dict(color=color), showlegend=False,
                        text=[f"{row['avg_emisi']:.1f}"], textposition='inside',
                        textfont=dict(color='white', size=7, weight='bold'),
                        hovertemplate=f'<b>{row["fakultas"]}</b><br>Rata-rata: {row["avg_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["count"]}<extra></extra>'
                    ))
                
                fig_fakultas.update_layout(
                    height=240, margin=dict(t=25, b=5, l=5, r=5), showlegend=False,
                    xaxis_title="Rata-rata Emisi (kg CO₂)", yaxis_title="",
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text="<b>Emisi per Fakultas</b>", x=0.36, y=0.95, 
                              font=dict(size=11, color="#000000")),
                    xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=7)),
                    yaxis=dict(tickfont=dict(size=7))
                )
                st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data fakultas tidak tersedia")
        else:
            st.info("Data fakultas tidak tersedia")

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
                    textfont=dict(size=7, family="Poppins"),
                    hovertemplate='<b>%{label}</b><br>%{value:.2f} kg CO₂ (%{percent})<extra></extra>'
                )])
                
                total_emisi = sum(emissions)
                center_text = f"<b style='font-size:14px'>{total_emisi:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                fig_devices.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                
                fig_devices.update_layout(
                    height=240, margin=dict(t=25, b=5, l=5, r=5), showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text="<b>Proporsi Emisi per Perangkat</b>", x=0.27, y=0.95, 
                              font=dict(size=11, color="#000000"))
                )
                
                st.plotly_chart(fig_devices, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Second 3 visualizations
    col1, col2, col3 = st.columns([1, 0.8, 1])

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
                        height=240, margin=dict(t=60, b=20, l=20, r=40),
                        title=dict(text="<b>Heatmap Hari dan Jam</b>", x=0.2, y=0.95, 
                                font=dict(size=11, color="#000000")),
                        xaxis=dict(tickfont=dict(size=7), tickangle=-45, title=dict(text="Jam", font=dict(size=10))),
                        yaxis=dict(tickfont=dict(size=7)),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 5. Emisi per Responden - Enhanced Scatter Plot with Palette Colors
        user_emissions = filtered_df[['id_responden', 'emisi_elektronik_mingguan']].copy()
        
        if len(user_emissions) > 0:
            Q1 = user_emissions['emisi_elektronik_mingguan'].quantile(0.25)
            Q3 = user_emissions['emisi_elektronik_mingguan'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            median_val = user_emissions['emisi_elektronik_mingguan'].median()
            
            user_emissions['category'] = 'Normal'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] > upper_bound, 'category'] = 'Heavy User'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] < lower_bound, 'category'] = 'Light User'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] > median_val * 1.5, 'category'] = 'High User'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] < median_val * 0.5, 'category'] = 'Eco User'
            
            user_emissions['user_index'] = range(len(user_emissions))
            
            fig_users = go.Figure()
            
            color_map = {
                'Eco User': '#66c2a5',     
                'Light User': '#abdda4',    
                'Normal': '#3288bd',        
                'High User': '#fdae61',     
                'Heavy User': '#d53e4f'     
            }
            
            size_map = {
                'Eco User': 8, 
                'Light User': 7, 
                'Normal': 6, 
                'High User': 9, 
                'Heavy User': 12
            }
            
            for category in user_emissions['category'].unique():
                category_data = user_emissions[user_emissions['category'] == category]
                
                fig_users.add_trace(go.Scatter(
                    x=category_data['user_index'],
                    y=category_data['emisi_elektronik_mingguan'],
                    mode='markers',
                    name=category,
                    marker=dict(
                        color=color_map[category],
                        size=size_map[category],
                        line=dict(color='white', width=1.5),
                        opacity=0.85,
                        symbol='circle'
                    ),
                    hovertemplate=f'<b>User %{{text}}</b><br>Emisi: %{{y:.2f}} kg CO₂<br>Kategori: {category}<br><i>Pola penggunaan individual</i><extra></extra>',
                    text=[f"{str(row['id_responden'])[-3:]}" for _, row in category_data.iterrows()]
                ))
            
            fig_users.add_hline(
                y=median_val,
                line_dash="dash",
                line_color="#5e4fa2",  
                line_width=2,
                annotation_text=f"Median: {median_val:.1f} kg CO₂",
                annotation_position="top right",
                annotation=dict(bgcolor="white", bordercolor="#5e4fa2", borderwidth=1)
            )
            
            fig_users.update_layout(
                height=240, margin=dict(t=20, b=5, l=5, r=5),
                title=dict(text="<b>Pola Emisi per Responden</b>", x=0.35, y=0.95, 
                          font=dict(size=11, color="#000000")),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickfont=dict(size=7), 
                          title=dict(text="Index Responden", font=dict(size=9))),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=7), 
                          title=dict(text="Emisi (kg CO₂)", font=dict(size=9))),
                legend=dict(orientation="v", yanchor="top", y=0.98, xanchor="left", x=0.02, 
                           font=dict(size=7), bgcolor="rgba(255,255,255,0.9)", 
                           bordercolor="rgba(0,0,0,0.1)", borderwidth=1)
            )
            
            st.plotly_chart(fig_users, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data emisi per responden tidak tersedia")

    with col3:
        # 6. Gedung Kelas Terpopuler - Diagram Batang (Vertical Bar Chart)
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
                
                location_stats = location_stats.sort_values('session_count', ascending=False).head(6)
                
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
                        textposition='outside',
                        textfont=dict(size=9, color='#2d3748', weight='bold'),
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
                    height=240,
                    margin=dict(t=50, b=10, l=5, r=5),
                    title=dict(text="<b>Gedung Kelas Terpopuler</b>", x=0.35, y=0.95,
                              font=dict(size=11, color="#000000")),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        showgrid=False, 
                        tickfont=dict(size=7), 
                        tickangle=-45,
                        title=dict(text="Gedung Kelas", font=dict(size=9))
                    ),
                    yaxis=dict(
                        showgrid=True, 
                        gridcolor='rgba(0,0,0,0.1)', 
                        tickfont=dict(size=7),
                        title=dict(text="Jumlah Sesi", font=dict(size=9))
                    ),
                    showlegend=False
                )
                
                st.plotly_chart(fig_location, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data aktivitas kelas tidak tersedia")
        else:
            st.info("Data lokasi kelas tidak tersedia")

if __name__ == "__main__":
    show()