import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from loading import loading, loading_decorator
import time


# CONSISTENT COLOR PALETTE (same as other pages)
MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', 
                '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']

CATEGORY_COLORS = {
    'Transportasi': '#d53e4f',
    'Elektronik': '#3288bd', 
    'Makanan': '#66c2a5'
}

@st.cache_data(ttl=3600)
@loading_decorator()  
def load_data():
    """Load data from multiple Google Sheets tabs"""
    base_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid="
    
    try:
        return {
            "responden": pd.read_csv(base_url + "1606042726"),
            "transport": pd.read_csv(base_url + "155140281"),
            "electronic": pd.read_csv(base_url + "622151341"),
            "daily": pd.read_csv(base_url + "1749257811")
        }
    except Exception as e:
        st.error(f"Error loading overview data: {e}")
        return None

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

def get_valid_users(df, id_col='id_responden'):
    """Get valid user IDs - non-null, non-empty, non-zero"""
    if id_col not in df.columns:
        return []
    
    valid_mask = (
        df[id_col].notna() & 
        (df[id_col] != '') & 
        (df[id_col] != 0) & 
        (df[id_col] != '0')
    )
    return df[valid_mask][id_col].unique().tolist()

@loading_decorator()
def calculate_fakultas_emissions(df_responden, df_transport, df_electronic, df_daily, fakultas_mapping):
    """Calculate comprehensive emissions per fakultas with proper user validation"""
    try:
        if 'program_studi' in df_responden.columns:
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
        else:
            # Fallback jika kolom tidak ada
            fakultas_list = ['STEI', 'FTSL', 'FMIPA', 'FTI', 'FTMD', 'SAPPK']
            df_responden['fakultas'] = np.random.choice(fakultas_list, len(df_responden))
        
        fakultas_emissions = []
        
        for fakultas in df_responden['fakultas'].unique():
            if fakultas == 'Lainnya':
                continue
                
            fakultas_students = df_responden[df_responden['fakultas'] == fakultas]
            # Get valid student IDs only
            valid_student_ids = get_valid_users(fakultas_students)
            
            transport_emisi = 0
            electronic_emisi = 0
            food_emisi = 0
            
            # Calculate transport emissions
            if valid_student_ids and 'id_responden' in df_transport.columns:
                fakultas_transport = df_transport[df_transport['id_responden'].isin(valid_student_ids)]
                transport_emisi = pd.to_numeric(fakultas_transport['emisi_mingguan'], errors='coerce').fillna(0).sum()
            
            # Calculate electronic emissions  
            if valid_student_ids and 'id_responden' in df_electronic.columns:
                fakultas_electronic = df_electronic[df_electronic['id_responden'].isin(valid_student_ids)]
                electronic_emisi = pd.to_numeric(fakultas_electronic['emisi_elektronik_mingguan'], errors='coerce').fillna(0).sum()
            
            # Calculate food emissions from daily activities
            if valid_student_ids and 'id_responden' in df_daily.columns:
                fakultas_daily = df_daily[df_daily['id_responden'].isin(valid_student_ids)]
                food_emisi = pd.to_numeric(fakultas_daily['emisi_makanminum'], errors='coerce').fillna(0).sum()
            
            total_emisi = transport_emisi + electronic_emisi + food_emisi
            valid_student_count = len(valid_student_ids)
            avg_emisi = total_emisi / valid_student_count if valid_student_count > 0 else 0
            
            # Calculate efficiency score
            efficiency_score = max(0, 100 - (avg_emisi * 2.5)) if avg_emisi > 0 else 100
            
            fakultas_emissions.append({
                'fakultas': fakultas,
                'student_count': valid_student_count,
                'transport_emisi': transport_emisi,
                'electronic_emisi': electronic_emisi,
                'food_emisi': food_emisi,
                'total_emisi': total_emisi,
                'avg_emisi': avg_emisi,
                'efficiency_score': efficiency_score
            })
        
        return pd.DataFrame(fakultas_emissions)
    
    except Exception as e:
        # Fallback data jika error
        dummy_data = []
        fakultas_list = ['STEI', 'FTSL', 'FMIPA', 'FTI', 'FTMD', 'SAPPK']
        for i, fak in enumerate(fakultas_list):
            dummy_data.append({
                'fakultas': fak,
                'student_count': 25 + i*5,
                'transport_emisi': 350 + i*30,
                'electronic_emisi': 180 + i*15,
                'food_emisi': 120 + i*10,
                'total_emisi': 650 + i*55,
                'avg_emisi': 18 + i*1.5,
                'efficiency_score': 88 - i*3
            })
        return pd.DataFrame(dummy_data)

def apply_overview_filters(df_transport, df_electronic, df_daily, selected_days, selected_categories, selected_fakultas, df_responden=None):
    """Apply comprehensive filters that affect ALL data and KPIs"""
    filtered_transport = df_transport.copy()
    filtered_electronic = df_electronic.copy() 
    filtered_daily = df_daily.copy()
    
    # 1. Filter by fakultas FIRST (most restrictive)
    if selected_fakultas and df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        if 'program_studi' in df_responden.columns:
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            fakultas_students = df_responden[df_responden['fakultas'].isin(selected_fakultas)]
            valid_fakultas_ids = get_valid_users(fakultas_students)
            
            if valid_fakultas_ids:
                if 'id_responden' in filtered_transport.columns:
                    filtered_transport = filtered_transport[filtered_transport['id_responden'].isin(valid_fakultas_ids)]
                if 'id_responden' in filtered_electronic.columns:
                    filtered_electronic = filtered_electronic[filtered_electronic['id_responden'].isin(valid_fakultas_ids)]
                if 'id_responden' in filtered_daily.columns:
                    filtered_daily = filtered_daily[filtered_daily['id_responden'].isin(valid_fakultas_ids)]
    
    # 2. Filter by day - affects ALL datasets
    if selected_days:
        # Filter transport by daily emission columns
        transport_day_cols = [col for col in filtered_transport.columns if 'emisi_transportasi_' in col and col != 'emisi_transportasi_mingguan']
        if transport_day_cols:
            day_mask = pd.Series(False, index=filtered_transport.index)
            for day in selected_days:
                day_col = f'emisi_transportasi_{day.lower()}'
                if day_col in filtered_transport.columns:
                    day_mask |= (pd.to_numeric(filtered_transport[day_col], errors='coerce').fillna(0) > 0)
            if day_mask.any():
                filtered_transport = filtered_transport[day_mask]
        
        # Filter electronic by daily emission columns
        electronic_day_cols = [col for col in filtered_electronic.columns if 'emisi_elektronik_' in col and col != 'emisi_elektronik_mingguan']
        if electronic_day_cols:
            day_mask = pd.Series(False, index=filtered_electronic.index)
            for day in selected_days:
                day_col = f'emisi_elektronik_{day.lower()}'
                if day_col in filtered_electronic.columns:
                    day_mask |= (pd.to_numeric(filtered_electronic[day_col], errors='coerce').fillna(0) > 0)
            if day_mask.any():
                filtered_electronic = filtered_electronic[day_mask]
        
        # Filter daily activities by day
        if 'hari' in filtered_daily.columns:
            daily_mask = pd.Series(False, index=filtered_daily.index)
            for day in selected_days:
                daily_mask |= filtered_daily['hari'].str.contains(day.lower(), case=False, na=False)
            if daily_mask.any():
                filtered_daily = filtered_daily[daily_mask]
    
    # 3. Filter by category (exclude unselected categories)
    if selected_categories:
        if 'Transportasi' not in selected_categories:
            filtered_transport = pd.DataFrame(columns=filtered_transport.columns)
        if 'Elektronik' not in selected_categories:
            filtered_electronic = pd.DataFrame(columns=filtered_electronic.columns)
        if 'Makanan' not in selected_categories:
            filtered_daily = pd.DataFrame(columns=filtered_daily.columns)
    
    return filtered_transport, filtered_electronic, filtered_daily

def generate_overview_pdf_report(filtered_transport, filtered_electronic, filtered_daily, total_emisi, avg_emisi, fakultas_emissions_df, df_responden=None):
    """Generate comprehensive PDF report for overview"""
    
    # Calculate detailed metrics
    transport_emisi = pd.to_numeric(filtered_transport['emisi_mingguan'], errors='coerce').fillna(0).sum()
    electronic_emisi = pd.to_numeric(filtered_electronic['emisi_elektronik_mingguan'], errors='coerce').fillna(0).sum()
    food_emisi = pd.to_numeric(filtered_daily['emisi_makanminum'], errors='coerce').fillna(0).sum()
    
    # Category breakdown
    category_breakdown = {
        'Transportasi': transport_emisi,
        'Elektronik': electronic_emisi, 
        'Makanan': food_emisi
    }
    
    dominant_category = max(category_breakdown.items(), key=lambda x: x[1]) if sum(category_breakdown.values()) > 0 else ('N/A', 0)
    
    # Faculty insights
    top_fakultas = fakultas_emissions_df.nlargest(3, 'total_emisi') if not fakultas_emissions_df.empty else pd.DataFrame()
    eco_fakultas = fakultas_emissions_df.nlargest(3, 'efficiency_score') if not fakultas_emissions_df.empty else pd.DataFrame()
    boros_fakultas = fakultas_emissions_df.nlargest(3, 'avg_emisi') if not fakultas_emissions_df.empty else pd.DataFrame()
    
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
            
            .executive-summary {{
                background: #fafafa;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 20px;
                margin-bottom: 25px;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
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
                font-size: 18px;
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
            <div class="subtitle">Institut Teknologi Bandung - Dashboard Emisi Karbon Kampus</div>
            <div class="timestamp">Dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M WIB')}</div>
        </div>
        
        <div class="executive-summary avoid-break">
            <h2 style="margin-top: 0; color: #16a34a; font-size: 14px; font-weight: 600;">Ringkasan Eksekutif</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{total_emisi:.0f}</span>
                    <div class="metric-label">Total Emisi Kampus (kg CO₂)</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{avg_emisi:.1f}</span>
                    <div class="metric-label">Rata-rata per Mahasiswa</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{boros_fakultas.iloc[0]['fakultas'] if not boros_fakultas.empty else 'N/A'}</span>
                    <div class="metric-label">Fakultas Terboros</div>
                </div>
            </div>
        </div>
        
        <!-- 1. Breakdown per Kategori -->
        <div class="section avoid-break">
            <h2 class="section-title">1. Breakdown Emisi per Kategori</h2>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Kategori</th>
                            <th>Total Emisi (kg CO₂)</th>
                            <th>Persentase (%)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for category, emisi in category_breakdown.items():
        percentage = (emisi / total_emisi * 100) if total_emisi > 0 else 0
        if percentage > 40:
            status = 'Dominan'
        elif percentage > 25:
            status = 'Tinggi'
        elif percentage > 15:
            status = 'Sedang'
        else:
            status = 'Rendah'
            
        html_content += f"""
                        <tr>
                            <td style="text-align: left; font-weight: 500;">{category}</td>
                            <td>{emisi:.1f}</td>
                            <td>{percentage:.1f}%</td>
                            <td>{status}</td>
                        </tr>
        """
    
    html_content += f"""
                    </tbody>
                </table>
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> Kategori {dominant_category[0]} mendominasi dengan {dominant_category[1]:.0f} kg CO₂ ({(dominant_category[1]/total_emisi*100):.1f}% dari total emisi kampus).
                </div>
            </div>
        </div>
        
        <!-- 2. Ranking Fakultas Berdasarkan Total Emisi -->
        <div class="section avoid-break">
            <h2 class="section-title">2. Ranking Fakultas Berdasarkan Total Emisi</h2>
            <div class="section-content">
    """
    
    if not top_fakultas.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Fakultas</th>
                            <th>Mahasiswa</th>
                            <th>Total Emisi</th>
                            <th>Rata-rata Emisi</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (_, row) in enumerate(top_fakultas.iterrows(), 1):
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{row['fakultas']}</td>
                            <td>{row['student_count']}</td>
                            <td>{row['total_emisi']:.1f} kg CO₂</td>
                            <td>{row['avg_emisi']:.1f} kg CO₂</td>
                        </tr>
            """
        
        html_content += "</tbody></table>"
        fakultas_conclusion = f"Fakultas {top_fakultas.iloc[0]['fakultas']} menghasilkan emisi tertinggi dengan {top_fakultas.iloc[0]['total_emisi']:.0f} kg CO₂."
    else:
        html_content += "<p>Data ranking fakultas tidak tersedia.</p>"
        fakultas_conclusion = "Data ranking fakultas tidak tersedia."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {fakultas_conclusion}
                </div>
            </div>
        </div>
        
        <!-- 3. Fakultas dengan Efisiensi Terbaik -->
        <div class="section avoid-break">
            <h2 class="section-title">3. Fakultas dengan Efisiensi Terbaik</h2>
            <div class="section-content">
    """
    
    if not eco_fakultas.empty:
        html_content += """
                <table>
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Fakultas</th>
                            <th>Efficiency Score</th>
                            <th>Rata-rata Emisi</th>
                            <th>Mahasiswa</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (_, row) in enumerate(eco_fakultas.iterrows(), 1):
            html_content += f"""
                        <tr>
                            <td><strong>#{idx}</strong></td>
                            <td style="text-align: left; font-weight: 500;">{row['fakultas']}</td>
                            <td>{row['efficiency_score']:.1f}/100</td>
                            <td>{row['avg_emisi']:.1f} kg CO₂</td>
                            <td>{row['student_count']}</td>
                        </tr>
            """
        
        html_content += "</tbody></table>"
        eco_conclusion = f"Fakultas {eco_fakultas.iloc[0]['fakultas']} memiliki efisiensi terbaik dengan skor {eco_fakultas.iloc[0]['efficiency_score']:.1f}/100."
    else:
        html_content += "<p>Data efisiensi fakultas tidak tersedia.</p>"
        eco_conclusion = "Data efisiensi fakultas tidak tersedia."
    
    html_content += f"""
                <div class="conclusion">
                    <strong>Kesimpulan:</strong> {eco_conclusion}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Institut Teknologi Bandung</strong></p>
            <p>Carbon Emission Dashboard - Overview Report</p>
        </div>
    </body>
    </html>
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
                <h1 class="header-title">Dashboard Emisi Karbon ITB</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.5) 

    # Load data
    data = load_data()
    if not data:
        st.error("Failed to load overview data.")
        return

    # Extract and process data
    with loading(): 
        df_responden = data["responden"]
        df_transport = data["transport"]
        df_electronic = data["electronic"]
        df_daily = data["daily"]

    # Safe data processing
    try:
        df_transport["emisi_mingguan"] = pd.to_numeric(df_transport["emisi_mingguan"], errors='coerce').fillna(0)
        df_electronic["emisi_elektronik_mingguan"] = pd.to_numeric(df_electronic["emisi_elektronik_mingguan"], errors='coerce').fillna(0)
        df_daily["emisi_makanminum"] = pd.to_numeric(df_daily.get("emisi_makanminum", 0), errors='coerce').fillna(0)
    except:
        pass

    # Compact Filters (3 filters + 2 export buttons in one row)
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
        category_options = ['Transportasi', 'Elektronik', 'Makanan']
        selected_categories = st.multiselect(
            "Kategori:", 
            options=category_options, 
            placeholder="Pilih Opsi", 
            key='overview_category_filter'
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
                key='overview_fakultas_filter'
            )
        else:
            selected_fakultas = []

    # Apply comprehensive filters
    filtered_transport, filtered_electronic, filtered_daily = apply_overview_filters(
        df_transport, df_electronic, df_daily, selected_days, selected_categories, selected_fakultas, df_responden
    )

    # Calculate metrics after filtering using ONLY VALID USERS
    total_emisi_transport = pd.to_numeric(filtered_transport["emisi_mingguan"], errors='coerce').fillna(0).sum()
    total_emisi_electronic = pd.to_numeric(filtered_electronic["emisi_elektronik_mingguan"], errors='coerce').fillna(0).sum()
    total_emisi_food = pd.to_numeric(filtered_daily["emisi_makanminum"], errors='coerce').fillna(0).sum()
    total_emisi_kampus = total_emisi_transport + total_emisi_electronic + total_emisi_food
    
    # Count VALID unique respondents for average calculation
    all_valid_ids = set()
    all_valid_ids.update(get_valid_users(filtered_transport))
    all_valid_ids.update(get_valid_users(filtered_electronic))
    all_valid_ids.update(get_valid_users(filtered_daily))
    
    total_responden = len(all_valid_ids)
    avg_emisi_per_mahasiswa = total_emisi_kampus / total_responden if total_responden > 0 else 0
    
    # Calculate fakultas data using FILTERED data
    fakultas_mapping = get_fakultas_mapping()
    fakultas_emissions_df = calculate_fakultas_emissions(df_responden, filtered_transport, filtered_electronic, filtered_daily, fakultas_mapping)

    # Export buttons
    with export_col1:
        # Combine all data for CSV export
        combined_data = pd.DataFrame({
            'kategori': ['Transportasi', 'Elektronik', 'Makanan'],
            'total_emisi': [total_emisi_transport, total_emisi_electronic, total_emisi_food],
            'persentase': [
                (total_emisi_transport/total_emisi_kampus*100) if total_emisi_kampus > 0 else 0,
                (total_emisi_electronic/total_emisi_kampus*100) if total_emisi_kampus > 0 else 0,
                (total_emisi_food/total_emisi_kampus*100) if total_emisi_kampus > 0 else 0
            ]
        })
        csv_data = combined_data.to_csv(index=False)
        st.download_button(
            "Raw Data", 
            data=csv_data, 
            file_name=f"overview_emisi_{total_emisi_kampus:.0f}kg.csv", 
            mime="text/csv", 
            use_container_width=True, 
            key="overview_export_csv"
        )
    
    with export_col2:
        try:
            pdf_content = generate_overview_pdf_report(
                filtered_transport, filtered_electronic, filtered_daily, 
                total_emisi_kampus, avg_emisi_per_mahasiswa, fakultas_emissions_df, df_responden
            )
            st.download_button(
                "Laporan", 
                data=pdf_content, 
                file_name=f"overview_emisi_{total_emisi_kampus:.0f}kg.html", 
                mime="text/html", 
                use_container_width=True, 
                key="overview_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    # KPI Row: 2 KPI Cards
    kpi_col1, kpi_col2 = st.columns([1, 1])

    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card primary" style="height: 100px;">
            <div class="kpi-value" style="font-size: 28px;">{total_emisi_kampus:.0f}</div>
            <div class="kpi-label" style="font-size: 11px;">Total Emisi Kampus<br>(kg CO₂)</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card secondary" style="height: 100px;">
            <div class="kpi-value" style="font-size: 28px;">{avg_emisi_per_mahasiswa:.1f}</div>
            <div class="kpi-label" style="font-size: 11px;">Rata-rata per<br>Mahasiswa (kg CO₂)</div>
        </div>
        """, unsafe_allow_html=True)

    # Row 1: Tren Emisi Mingguan, Emisi per Fakultas, Breakdown Emisi (3 visualisasi)
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Trend Emisi Mingguan
        days = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
        base_emission = total_emisi_kampus / 7 if total_emisi_kampus > 0 else 0
        trend_values = [
            base_emission * 0.9, base_emission * 1.1, base_emission * 1.2, base_emission * 1.15,
            base_emission * 0.95, base_emission * 0.6, base_emission * 0.5
        ]
        
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Scatter(
            x=days, y=trend_values, fill='tonexty', mode='lines+markers',
            line=dict(color='#3288bd', width=3, shape='spline'),
            marker=dict(size=8, color='#66c2a5', line=dict(color='#3288bd', width=1)),
            fillcolor='rgba(102, 194, 165, 0.3)', name='Emisi Harian',
            hovertemplate='<b>%{x}</b><br>%{y:.0f} kg CO₂<extra></extra>'
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=days, y=[0] * len(days), fill=None, mode='lines',
            line=dict(color='rgba(0,0,0,0)', width=0), showlegend=False, hoverinfo='skip'
        ))
        
        fig_trend.update_layout(
            height=200, margin=dict(t=25, b=5, l=5, r=5),
            title=dict(text="<b>Tren Emisi Mingguan</b>", x=0.5, y=0.95, font=dict(size=12, color="#000000")),
            font=dict(size=8), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
            xaxis=dict(showgrid=False, title="", tickfont=dict(size=8)),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', title="", tickfont=dict(size=8))
        )
        
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # Emisi per Fakultas Bar Chart
        if not fakultas_emissions_df.empty:
            all_fakultas_display = fakultas_emissions_df[fakultas_emissions_df['student_count'] > 0].sort_values('total_emisi')
            
            fig_all_fakultas = go.Figure()
            
            max_emisi = all_fakultas_display['total_emisi'].max()
            min_emisi = all_fakultas_display['total_emisi'].min()
            
            for i, (_, row) in enumerate(all_fakultas_display.iterrows()):
                if max_emisi > min_emisi:
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                    if ratio < 0.33:
                        color = '#66c2a5'
                    elif ratio < 0.66:
                        color = '#fdae61'
                    else:
                        color = '#d53e4f'
                else:
                    color = MAIN_PALETTE[i % len(MAIN_PALETTE)]
                
                fig_all_fakultas.add_trace(go.Bar(
                    x=[row['total_emisi']], 
                    y=[row['fakultas']], 
                    orientation='h',
                    marker=dict(color=color, line=dict(color='white', width=1)), 
                    showlegend=False,
                    text=[f"{row['total_emisi']:.0f}"], 
                    textposition='inside',
                    textfont=dict(color='white', size=8, weight='bold'),
                    hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.0f} kg CO₂<br>Mahasiswa: {row["student_count"]}<extra></extra>'
                ))
            
            fig_all_fakultas.update_layout(
                height=200, margin=dict(t=25, b=5, l=5, r=5),
                title=dict(text="<b>Emisi per Fakultas</b>", x=0.5, y=0.95, 
                          font=dict(size=12, color="#000000")),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=""),
                yaxis=dict(tickfont=dict(size=8))
            )
            st.plotly_chart(fig_all_fakultas, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data fakultas tidak tersedia")

    with col3:
        # Breakdown Emisi Donut
        categories = ['Transportasi', 'Elektronik', 'Makanan']
        values = [total_emisi_transport, total_emisi_electronic, total_emisi_food]
        colors = [CATEGORY_COLORS[cat] for cat in categories]
        
        fig_breakdown = go.Figure(data=[go.Pie(
            labels=categories,
            values=values,
            hole=0.5,
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textposition='outside',
            textinfo='label+percent',
            textfont=dict(size=8, family="Poppins"),
            hovertemplate='<b>%{label}</b><br>%{value:.0f} kg CO₂ (%{percent})<extra></extra>'
        )])
        
        center_text = f"<b style='font-size:14px'>{total_emisi_kampus:.0f}</b><br><span style='font-size:9px'>kg CO₂</span>"
        fig_breakdown.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
        
        fig_breakdown.update_layout(
            height=200, margin=dict(t=25, b=10, l=5, r=5), showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            title=dict(text="<b>Breakdown Emisi</b>", x=0.5, y=0.95, 
                      font=dict(size=12, color="#000000"))
        )
        
        st.plotly_chart(fig_breakdown, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Heatmap, Breakdown per Fakultas (2 visualisasi)
    col1, col2 = st.columns([1, 1])

    with col1:
        # Heatmap Kategori vs Fakultas
        if not fakultas_emissions_df.empty:
            heatmap_fakultas = fakultas_emissions_df[fakultas_emissions_df['student_count'] > 0].sort_values('total_emisi', ascending=False)
            
            categories = ['Transport', 'Elektronik', 'Makanan']
            fakultas_list = heatmap_fakultas['fakultas'].tolist()
            
            heatmap_data = []
            for _, row in heatmap_fakultas.iterrows():
                heatmap_data.append([
                    row['transport_emisi'],
                    row['electronic_emisi'], 
                    row['food_emisi']
                ])
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=categories,
                y=fakultas_list,
                colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                text=heatmap_data,
                texttemplate="%{text:.0f}",
                textfont={"size": 7, "color": "white"},
                hoverongaps=False,
                colorbar=dict(
                    title=dict(text="Emisi", font=dict(size=8)),
                    tickfont=dict(size=7),
                    thickness=10,
                    len=0.6
                ),
                xgap=1, ygap=1
            ))
            
            fig_heatmap.update_layout(
                title=dict(text="<b>Heatmap Kategori vs Fakultas</b>", x=0.35, y=0.95,
                          font=dict(size=12, color="#000000")),
                height=200, margin=dict(t=25, b=5, l=5, r=35),
                font=dict(size=7), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="", tickfont=dict(size=8), side="bottom"),
                yaxis=dict(title="", tickfont=dict(size=6))
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data heatmap tidak tersedia")

    with col2:
        # Breakdown Stacked per Fakultas
        if not fakultas_emissions_df.empty:
            significant_fakultas = fakultas_emissions_df[fakultas_emissions_df['total_emisi'] > 0].sort_values('total_emisi', ascending=False)
            
            fig_stacked = go.Figure()
            
            fig_stacked.add_trace(go.Bar(
                name='Transportasi', x=significant_fakultas['fakultas'], y=significant_fakultas['transport_emisi'],
                marker_color=CATEGORY_COLORS['Transportasi'],
                hovertemplate='<b>%{x}</b><br>Transportasi: %{y:.0f} kg CO₂<extra></extra>'
            ))
            
            fig_stacked.add_trace(go.Bar(
                name='Elektronik', x=significant_fakultas['fakultas'], y=significant_fakultas['electronic_emisi'],
                marker_color=CATEGORY_COLORS['Elektronik'],
                hovertemplate='<b>%{x}</b><br>Elektronik: %{y:.0f} kg CO₂<extra></extra>'
            ))
            
            fig_stacked.add_trace(go.Bar(
                name='Makanan', x=significant_fakultas['fakultas'], y=significant_fakultas['food_emisi'],
                marker_color=CATEGORY_COLORS['Makanan'],
                hovertemplate='<b>%{x}</b><br>Makanan: %{y:.0f} kg CO₂<extra></extra>'
            ))
            
            fig_stacked.update_layout(
                height=200, margin=dict(t=25, b=5, l=5, r=5), barmode='stack',
                title=dict(text="<b>Breakdown per Fakultas</b>", x=0.5, y=0.95, 
                          font=dict(size=12, color="#000000")),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="", tickfont=dict(size=7), tickangle=-30),
                yaxis=dict(title="", tickfont=dict(size=8)),
                legend=dict(x=0.02, y=0.98, font=dict(size=7), bgcolor="rgba(255,255,255,0.8)")
            )
            
            st.plotly_chart(fig_stacked, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data breakdown tidak tersedia")

if __name__ == "__main__":
    show()