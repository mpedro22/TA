import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time

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

@st.cache_data(ttl=3600)
@loading_decorator()
def load_data():
    """Load transportation data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    try:
        time.sleep(0.3)  # Simulate loading time for smooth UX
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading transportation data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
@loading_decorator()
def load_responden_data():
    """Load responden data for fakultas information"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    try:
        time.sleep(0.2)  # Simulate loading time for smooth UX
        return pd.read_csv(url)
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
        'Informatika': 'STEI', 'Teknik Telekomunikasi': 'STEI', 'Teknik Tenaga Listrik': 'STEI'
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
    
    time.sleep(0.1)  # Small delay for smooth filtering experience
    return filtered_df

@loading_decorator()
def generate_pdf_report(filtered_df, total_emisi, avg_emisi, eco_percentage, df_responden=None):
    """Generate professional HTML report optimized for PDF printing with loading"""
    from datetime import datetime
    import pandas as pd
    
    # Simulate processing time for complex report generation
    time.sleep(0.5)
    
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
    
    # Recalculate KPIs correctly
    total_emisi_fixed = valid_df['emisi_mingguan'].sum()
    avg_emisi_fixed = valid_df['emisi_mingguan'].mean()
    
    # 1. Transport mode summary
    transport_stats = valid_df.groupby('transportasi')['emisi_mingguan'].agg(['count', 'mean', 'sum']).round(2)
    transport_stats.columns = ['jumlah_pengguna', 'rata_rata_emisi', 'total_emisi']
    transport_stats = transport_stats.reset_index().sort_values('jumlah_pengguna', ascending=False)
    transport_stats['persentase'] = (transport_stats['jumlah_pengguna'] / len(valid_df) * 100).round(1)
    
    # 2. Faculty data
    fakultas_data = pd.DataFrame()
    fakultas_conclusion = "Data fakultas tidak tersedia."
    if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
        fakultas_mapping = get_fakultas_mapping()
        df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        df_with_fakultas = valid_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
        
        if not df_with_fakultas.empty:
            fakultas_stats = df_with_fakultas.groupby('fakultas')['emisi_mingguan'].agg(['mean', 'count', 'sum']).round(2)
            fakultas_stats.columns = ['rata_rata_emisi', 'jumlah_mahasiswa', 'total_emisi']
            fakultas_data = fakultas_stats[fakultas_stats['jumlah_mahasiswa'] >= 2].sort_values('rata_rata_emisi', ascending=False)
            
            if not fakultas_data.empty:
                highest = fakultas_data.index[0]
                highest_emisi = fakultas_data.iloc[0]['rata_rata_emisi']
                fakultas_conclusion = f"Fakultas {highest} memiliki rata-rata emisi tertinggi sebesar {highest_emisi:.2f} kg CO₂ per minggu."
    
    # 3. Daily data
    hari_cols = [c for c in filtered_df.columns if 'emisi_transportasi_' in c and c != 'emisi_transportasi_mingguan']
    daily_data = pd.DataFrame()
    daily_conclusion = "Data emisi harian tidak tersedia."
    
    if hari_cols:
        daily_totals = []
        for col in hari_cols:
            day = col.replace('emisi_transportasi_', '').capitalize()
            total_emisi = filtered_df[col].sum()
            daily_totals.append({'hari': day, 'total_emisi': total_emisi})
        
        daily_data = pd.DataFrame(daily_totals)
        daily_data = daily_data.sort_values('total_emisi', ascending=False)
        
        highest_day = daily_data.iloc[0]
        lowest_day = daily_data.iloc[-1]
        daily_conclusion = f"Hari {highest_day['hari']} mencatat emisi tertinggi ({highest_day['total_emisi']:.1f} kg CO₂), hari {lowest_day['hari']} terendah ({lowest_day['total_emisi']:.1f} kg CO₂)."
    
    # 4. Heatmap pattern data (updated for hari vs moda)
    heatmap_pattern_data = pd.DataFrame()
    heatmap_pattern_conclusion = "Data heatmap penggunaan moda transportasi per hari tidak tersedia."
    if hari_cols and len(transport_stats) > 0:
        heatmap_rows = []
        for col in hari_cols:
            day = col.replace('emisi_transportasi_', '').capitalize()
            row_data = {'hari': day}
            
            for _, transport_row in transport_stats.head(5).iterrows():
                mode = transport_row['transportasi']
                mode_data = filtered_df[filtered_df['transportasi'] == mode]
                users_count = (mode_data[col] > 0).sum()
                row_data[mode] = users_count
            
            total_day_usage = sum([v for k, v in row_data.items() if k != 'hari'])
            if total_day_usage > 0:
                heatmap_rows.append(row_data)
        
        heatmap_pattern_data = pd.DataFrame(heatmap_rows)
        if not heatmap_pattern_data.empty:
            # Find peak day and mode combinations
            day_totals = []
            mode_cols = [col for col in heatmap_pattern_data.columns if col != 'hari']
            
            for _, row in heatmap_pattern_data.iterrows():
                day_total = sum([row[mode] for mode in mode_cols])
                day_totals.append({'hari': row['hari'], 'total_usage': day_total})
            
            if day_totals:
                peak_day_data = max(day_totals, key=lambda x: x['total_usage'])
                peak_day = peak_day_data['hari']
                
                # Find which mode dominates which day
                mode_peak_info = []
                for mode in mode_cols:
                    mode_peak_day = heatmap_pattern_data.loc[heatmap_pattern_data[mode].idxmax()]
                    mode_peak_info.append(f"{mode}: puncak pada {mode_peak_day['hari']} ({mode_peak_day[mode]} pengguna)")
                
                if mode_peak_info:
                    heatmap_pattern_conclusion = f"Pola penggunaan menunjukkan {peak_day} sebagai hari dengan aktivitas tertinggi. " + ". ".join(mode_peak_info[:3]) + "."
                else:
                    heatmap_pattern_conclusion = f"Pola penggunaan menunjukkan {peak_day} sebagai hari dengan aktivitas transportasi tertinggi."
            else:
                heatmap_pattern_conclusion = "Tidak ada data penggunaan yang tersedia untuk analisis heatmap."
        else:
            heatmap_pattern_conclusion = "Tidak ada data penggunaan yang tersedia untuk analisis heatmap moda transportasi per hari."

    # 5. Kecamatan
    kecamatan_data = pd.DataFrame()
    kecamatan_conclusion = "Data kecamatan tidak tersedia."
    if 'kecamatan' in filtered_df.columns:
        kecamatan_stats = filtered_df.groupby('kecamatan')['emisi_mingguan'].agg(['sum', 'count', 'mean']).round(1)
        kecamatan_stats.columns = ['total_emisi', 'jumlah_mahasiswa', 'rata_rata_emisi']
        kecamatan_data = kecamatan_stats[kecamatan_stats['jumlah_mahasiswa'] >= 0].sort_values('total_emisi', ascending=False)
        
        if kecamatan_data.empty:
            kecamatan_data = kecamatan_stats[kecamatan_stats['jumlah_mahasiswa'] >= 1].sort_values('total_emisi', ascending=False)
        
        if not kecamatan_data.empty:
            highest_kecamatan = kecamatan_data.index[0]
            highest_total = kecamatan_data.iloc[0]['total_emisi']
            lowest_kecamatan = kecamatan_data.index[-1]
            lowest_total = kecamatan_data.iloc[-1]['total_emisi']
            kecamatan_conclusion = f"Kecamatan {highest_kecamatan} menghasilkan total emisi tertinggi ({highest_total:.1f} kg CO₂), sedangkan {lowest_kecamatan} menghasilkan emisi terendah ({lowest_total:.1f} kg CO₂)."
    
    most_used = transport_stats.iloc[0]
    transport_conclusion = f"Moda transportasi {most_used['transportasi']} mendominasi dengan {most_used['jumlah_pengguna']} pengguna ({most_used['persentase']:.1f}%)."
    
    # Generate HTML with clean green theme
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Emisi Transportasi ITB</title>
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
            <h1>LAPORAN EMISI TRANSPORTASI</h1>
            <div class="subtitle">Institut Teknologi Bandung</div>
            <div class="timestamp">Dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M WIB')}</div>
        </div>
        
        <div class="executive-summary avoid-break">
            <h2 style="margin-top: 0; color: #16a34a; font-size: 14px; font-weight: 600;">Ringkasan</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{total_emisi_fixed:.1f}</span>
                    <div class="metric-label">Total Emisi (kg CO₂)</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{avg_emisi_fixed:.2f}</span>
                    <div class="metric-label">Rata-rata per Mahasiswa</div>
                </div>
            </div>
        </div>

        <!-- 1. Tren Emisi Harian -->
        <div class="section avoid-break">
            <h2 class="section-title">1. Tren Emisi Harian</h2>
            <div class="section-content">
    """
    
    if not daily_data.empty:
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
        for _, row in daily_data.iterrows():
            html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{row['hari']}</td>
                            <td>{row['total_emisi']:.1f}</td>
                        </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data emisi harian tidak tersedia.</p>"
    
    html_content += f"""
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
                            <th>Fakultas</th>
                            <th>Mahasiswa</th>
                            <th>Rata-rata Emisi</th>
                            <th>Total Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for fakultas, row in fakultas_data.iterrows():
            html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{fakultas}</td>
                            <td>{row['jumlah_mahasiswa']}</td>
                            <td>{row['rata_rata_emisi']:.2f}</td>
                            <td>{row['total_emisi']:.1f}</td>
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

        <!-- 3. Komposisi Moda Transportasi -->
        <div class="section avoid-break">
            <h2 class="section-title">3. Komposisi Moda Transportasi</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Moda Transportasi</th>
                            <th>Pengguna</th>
                            <th>Persentase</th>
                            <th>Rata-rata Emisi</th>
                            <th>Total Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for _, row in transport_stats.iterrows():
        html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{row['transportasi']}</td>
                            <td>{row['jumlah_pengguna']}</td>
                            <td>{row['persentase']:.1f}%</td>
                            <td>{row['rata_rata_emisi']:.2f}</td>
                            <td>{row['total_emisi']:.1f}</td>
                        </tr>
        """
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {transport_conclusion}
                </div>
            </div>
        </div>

        <!-- 4. Pola Penggunaan Transportasi per Hari -->
        <div class="section avoid-break">
            <h2 class="section-title">4. Pola Penggunaan Transportasi per Hari</h2>
            <div class="section-content">
    """
    
    if not heatmap_pattern_data.empty:
        mode_columns = [col for col in heatmap_pattern_data.columns if col != 'hari']
        
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Hari</th>
        """
        for mode in mode_columns:
            html_content += f"<th>{mode}<br>(Pengguna)</th>"
        html_content += "</tr></thead><tbody>"
        
        for _, row in heatmap_pattern_data.iterrows():
            html_content += f"<tr><td style='text-align: left; font-weight: 500;'>{row['hari']}</td>"
            for mode in mode_columns:
                html_content += f"<td>{int(row[mode])}</td>"
            html_content += "</tr>"
        
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data heatmap penggunaan moda transportasi per hari tidak tersedia.</p>"
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {heatmap_pattern_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 5. Emisi per Kecamatan -->
        <div class="section avoid-break">
            <h2 class="section-title">5. Emisi per Kecamatan</h2>
            <div class="section-content">
    """
    
    if not kecamatan_data.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Kecamatan</th>
                            <th>Mahasiswa</th>
                            <th>Rata-rata Emisi</th>
                            <th>Total Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for idx, (kecamatan, row) in enumerate(kecamatan_data.head(10).iterrows(), 1):  
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{kecamatan}</td>
                            <td>{row['jumlah_mahasiswa']}</td>
                            <td>{row['rata_rata_emisi']:.1f}</td>
                            <td>{row['total_emisi']:.1f}</td>
                        </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>Data kecamatan tidak tersedia.</p>"
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {kecamatan_conclusion}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Institut Teknologi Bandung</strong></p>
            <p>Carbon Emission Dashboard - Transportation Report</p>
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
            <div class="header-content">
                <h1 class="header-title">Emisi Transportasi</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.2)  # Small delay for header animation

    # Load data with loading decorators
    df = load_data()
    df_responden = load_responden_data()
    
    if df.empty:
        st.error("Data transportasi tidak tersedia")
        return

    # Data processing with loading
    with loading():
        df['emisi_mingguan'] = pd.to_numeric(df['emisi_mingguan'], errors='coerce')
        df = df.dropna(subset=['transportasi'])
        df['emission_category'] = df['transportasi'].apply(categorize_emission_level)
        time.sleep(0.1)
    
    # Filters
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
            pdf_content = generate_pdf_report(filtered_df, total_emisi, avg_emisi, eco_percentage, df_responden)
            st.download_button(
                "Laporan",
                data=pdf_content,
                file_name=f"transport_{len(filtered_df)}.html",
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
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
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
                        
                        st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})
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
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

        time.sleep(0.2)  # Small delay for charts rendering

    # Row 2: Secondary Charts with loading - UPDATED LAYOUT
    with loading():
        col1, col2 = st.columns([1, 1])

        with col1:
            # Chart 4: Heatmap Hari vs Moda Transportasi (count users, not emission) - FIXED AXES
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
                
                # FIXED: pivot dengan hari sebagai index, transportasi sebagai columns
                pivot_df = heatmap_df.pivot(index='hari', columns='transportasi', values='pengguna').fillna(0)
                pivot_df = pivot_df.reindex(index=day_order, fill_value=0)
                
                # Ambil top 6 transportasi berdasarkan total penggunaan
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
                st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data pola harian tidak tersedia")

        with col2:
            # MOVED: Chart 6: Emisi per Kecamatan - Vertical Bar Chart
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
                        
                        # Shorten kecamatan names for display
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
                    
                    # Add average line for reference
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
                    st.plotly_chart(fig_kecamatan, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Data kecamatan tidak mencukupi untuk analisis")
            else:
                st.info("Data kecamatan tidak tersedia")

        time.sleep(0.2)  # Small delay for final charts

if __name__ == "__main__":
    show()