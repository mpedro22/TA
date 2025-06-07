import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    """Generate comprehensive PDF report content for electronic emissions"""
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
    
    # Generate dynamic insights
    insights = []
    
    # Device usage insights - find most used device dynamically
    device_usage = {
        'Smartphone': smartphone_users,
        'Laptop': laptop_users, 
        'Tablet': tablet_users
    }
    
    if any(device_usage.values()):
        most_used_device = max(device_usage.items(), key=lambda x: x[1])
        most_used_percentage = (most_used_device[1] / total_responden * 100) if total_responden > 0 else 0
        
        if most_used_percentage > 80:
            insights.append(f"{most_used_device[0]} digunakan oleh hampir semua mahasiswa ({most_used_device[1]} dari {total_responden} responden atau {most_used_percentage:.1f}%), menunjukkan ketergantungan tinggi pada perangkat ini")
        elif most_used_percentage > 60:
            insights.append(f"{most_used_device[0]} adalah perangkat dominan dengan {most_used_device[1]} pengguna ({most_used_percentage:.1f}% dari total responden)")
        else:
            insights.append(f"Penggunaan perangkat relatif terdistribusi merata, dengan {most_used_device[0]} sebagai yang tertinggi ({most_used_percentage:.1f}%)")
    
    # Daily pattern insights with better explanation
    if daily_analysis and len(daily_analysis) >= 5:
        if avg_weekday > avg_weekend * 1.2:  # 20% higher threshold
            difference = ((avg_weekday - avg_weekend) / avg_weekend * 100)
            insights.append(f"Aktivitas kampus pada hari kerja menghasilkan emisi {difference:.1f}% lebih tinggi dari weekend, mengindikasikan pola akademik yang konsisten")
        elif avg_weekend > avg_weekday * 1.2:
            difference = ((avg_weekend - avg_weekday) / avg_weekday * 100)
            insights.append(f"Emisi weekend {difference:.1f}% lebih tinggi dari hari kerja, kemungkinan karena aktivitas non-akademik atau fasilitas yang tetap beroperasi")
        else:
            insights.append(f"Pola emisi relatif stabil sepanjang minggu (weekday: {avg_weekday:.1f} vs weekend: {avg_weekend:.1f} kg CO₂), menunjukkan konsistensi penggunaan fasilitas")
    
    # Device dominance insights with context
    if dominant_percentage > 60:
        insights.append(f"{dominant_device[0]} sangat mendominasi dengan {dominant_percentage:.1f}% total emisi - ini adalah area prioritas utama untuk efisiensi energi")
    elif dominant_percentage > 40:
        insights.append(f"{dominant_device[0]} memberikan kontribusi terbesar ({dominant_percentage:.1f}%) namun tidak mendominasi sepenuhnya - diperlukan pendekatan holistik")
    elif dominant_percentage < 25:
        insights.append(f"Emisi terdistribusi merata antar perangkat (tertinggi {dominant_device[0]}: {dominant_percentage:.1f}%) - efisiensi perlu ditingkatkan di semua lini")
    
    # Infrastructure vs Personal insight with actionable context
    if infrastructure_percentage > personal_percentage * 1.5:
        insights.append(f"Infrastruktur kampus (AC, lampu) berkontribusi {infrastructure_percentage:.1f}% vs perangkat personal {personal_percentage:.1f}% - fokus pada optimasi building management system akan memberikan dampak terbesar")
    elif personal_percentage > infrastructure_percentage * 1.5:
        insights.append(f"Perangkat personal mendominasi ({personal_percentage:.1f}% vs infrastruktur {infrastructure_percentage:.1f}%) - program edukasi digital sustainability kepada mahasiswa menjadi kunci")
    else:
        insights.append(f"Kontribusi infrastruktur dan perangkat personal relatif seimbang - diperlukan strategi terintegrasi untuk kedua aspek")
    
    # Usage duration insights with health/productivity context
    if avg_smartphone_duration > 10:
        insights.append(f"Intensitas smartphone sangat tinggi ({avg_smartphone_duration:.1f} jam/hari) - berpotensi mempengaruhi produktivitas akademik dan meningkatkan jejak karbon digital")
    elif avg_laptop_duration > 12:
        insights.append(f"Penggunaan laptop intensif ({avg_laptop_duration:.1f} jam/hari) mengindikasikan beban akademik tinggi - perlu optimasi power management")
    elif avg_smartphone_duration < 3 and avg_laptop_duration < 4:
        insights.append(f"Penggunaan perangkat relatif rendah (smartphone: {avg_smartphone_duration:.1f}h, laptop: {avg_laptop_duration:.1f}h) - pola yang baik untuk sustainability")
    
    # Outlier insights with actionable explanation
    if not top_fakultas.empty:
        highest_fakultas_emission = top_fakultas.iloc[0]['avg_emission']
        if highest_fakultas_emission > avg_emisi_per_person * 2:
            fakultas_name = top_fakultas.iloc[0]['fakultas']
            multiplier = highest_fakultas_emission / avg_emisi_per_person
            insights.append(f"Fakultas {fakultas_name} memiliki rata-rata emisi {multiplier:.1f}x lebih tinggi dari rata-rata umum - kemungkinan karena kebutuhan peralatan khusus atau jam operasional yang berbeda, perlu investigasi lebih lanjut")
    
    # Faculty pattern insights
    if not top_fakultas.empty and len(top_fakultas) >= 2:
        highest_faculty = top_fakultas.iloc[0]
        second_faculty = top_fakultas.iloc[1]
        gap_percentage = ((highest_faculty['avg_emission'] - second_faculty['avg_emission']) / second_faculty['avg_emission'] * 100)
        
        if gap_percentage > 50:
            insights.append(f"Terdapat kesenjangan emisi signifikan antar fakultas - {highest_faculty['fakultas']} {gap_percentage:.1f}% lebih tinggi dari {second_faculty['fakultas']}, menunjukkan perbedaan pola penggunaan yang perlu diselaraskan")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                line-height: 1.6;
                color: #2d3748;
                background-color: #f7fafc;
                margin: 0;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow: hidden;
            }}
            
            .header {{
                background: #2d5a3d;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            
            .header h2 {{
                font-size: 14px;
                font-weight: 400;
                opacity: 0.9;
                margin-bottom: 15px;
            }}
            
            .header .timestamp {{
                font-size: 12px;
                opacity: 0.8;
                background: rgba(255,255,255,0.1);
                padding: 6px 12px;
                border-radius: 4px;
                display: inline-block;
            }}
            
            .content {{
                padding: 30px;
            }}
            
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-bottom: 30px;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .kpi-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #e2e8f0;
            }}
            
            .kpi-value {{
                font-size: 28px;
                font-weight: 700;
                color: #2d5a3d;
                margin-bottom: 5px;
                display: block;
            }}
            
            .kpi-label {{
                font-size: 12px;
                color: #718096;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 500;
            }}
            
            .section {{
                margin-bottom: 30px;
                background: #f8f9fa;
                padding: 25px;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
            }}
            
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #10b981;
            }}
            
            .insights-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            
            .insight-box {{
                background: white;
                padding: 15px;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
            }}
            
            .insight-title {{
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            
            .insight-value {{
                font-size: 22px;
                font-weight: 700;
                color: #10b981;
                margin-bottom: 5px;
            }}
            
            .insight-description {{
                color: #718096;
                font-size: 12px;
            }}
            
            .table-container {{
                background: white;
                border-radius: 4px;
                overflow: hidden;
                border: 1px solid #e2e8f0;
                margin-bottom: 15px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            th {{
                background: #f0fdf4;
                color: #2d3748;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            td {{
                padding: 10px 15px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 13px;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            .key-insights {{
                background: white;
                padding: 20px;
                border-radius: 6px;
                border-left: 4px solid #10b981;
                margin: 20px 0;
            }}
            
            .key-insights h3 {{
                color: #2d3748;
                margin-bottom: 15px;
                font-size: 16px;
                font-weight: 600;
            }}
            
            .insights-list {{
                list-style: none;
                padding: 0;
            }}
            
            .insights-list li {{
                padding: 8px 0;
                color: #4a5568;
                border-bottom: 1px solid #f1f5f9;
                font-size: 14px;
                line-height: 1.5;
            }}
            
            .insights-list li:last-child {{
                border-bottom: none;
            }}
            
            .insights-list li::before {{
                content: '•';
                color: #10b981;
                font-weight: bold;
                margin-right: 8px;
            }}
            
            .footer {{
                background: #2d5a3d;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            
            .footer p {{
                margin-bottom: 3px;
                opacity: 0.9;
                font-size: 12px;
            }}
            
            .status-badge {{
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
            }}
            
            .status-high {{ background: #fecaca; color: #dc2626; }}
            .status-medium {{ background: #fef3c7; color: #d97706; }}
            .status-low {{ background: #d1fae5; color: #059669; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Laporan Emisi Elektronik ITB</h1>
                <h2>Analisis Penggunaan Perangkat Elektronik & Infrastruktur Kampus</h2>
                <div class="timestamp">Generated on {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}</div>
            </div>
            
            <div class="content">
                <!-- Executive Summary -->
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{total_responden:,}</div>
                        <div class="kpi-label">Total Responden</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{avg_emisi_per_person:.2f}</div>
                        <div class="kpi-label">Rata-rata Emisi per Orang</div>
                    </div>
                </div>
                
                <!-- Device Usage Statistics -->
                <div class="section">
                    <h3 class="section-title">Statistik Penggunaan Perangkat</h3>
                    <div class="insights-grid">
                        <div class="insight-box">
                            <div class="insight-title">Pengguna Smartphone</div>
                            <div class="insight-value">{smartphone_users}</div>
                            <div class="insight-description">dari {total_responden} responden ({smartphone_users/total_responden*100 if total_responden > 0 else 0:.1f}%)</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Pengguna Laptop</div>
                            <div class="insight-value">{laptop_users}</div>
                            <div class="insight-description">dari {total_responden} responden ({laptop_users/total_responden*100 if total_responden > 0 else 0:.1f}%)</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Pengguna Tablet</div>
                            <div class="insight-value">{tablet_users}</div>
                            <div class="insight-description">dari {total_responden} responden ({tablet_users/total_responden*100 if total_responden > 0 else 0:.1f}%)</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Rata-rata Durasi Smartphone</div>
                            <div class="insight-value">{avg_smartphone_duration:.1f}</div>
                            <div class="insight-description">jam per hari</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Rata-rata Durasi Laptop</div>
                            <div class="insight-value">{avg_laptop_duration:.1f}</div>
                            <div class="insight-description">jam per hari</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Rata-rata Durasi Tablet</div>
                            <div class="insight-value">{avg_tablet_duration:.1f}</div>
                            <div class="insight-description">jam per hari</div>
                        </div>
                    </div>
                </div>
                
                <!-- Device Emissions Breakdown -->
                <div class="section">
                    <h3 class="section-title">Breakdown Emisi per Perangkat</h3>
                    <div class="table-container">
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
            status = '<span class="status-badge status-high">Tinggi</span>'
        elif percentage > 15:
            status = '<span class="status-badge status-medium">Sedang</span>'
        else:
            status = '<span class="status-badge status-low">Rendah</span>'
        
        html_content += f"""
                                <tr>
                                    <td><strong>{device}</strong></td>
                                    <td>{emisi:.2f}</td>
                                    <td>{percentage:.1f}%</td>
                                    <td>{status}</td>
                                </tr>
        """
    
    html_content += f"""
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Daily Emissions Analysis -->
                <div class="section">
                    <h3 class="section-title">Analisis Emisi Harian</h3>
                    <div class="insights-grid">
                        <div class="insight-box">
                            <div class="insight-title">Hari dengan Emisi Tertinggi</div>
                            <div class="insight-value">{highest_day['day']}</div>
                            <div class="insight-description">{highest_day['emission']:.2f} kg CO₂</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Hari dengan Emisi Terendah</div>
                            <div class="insight-value">{lowest_day['day']}</div>
                            <div class="insight-description">{lowest_day['emission']:.2f} kg CO₂</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Rata-rata Hari Kerja</div>
                            <div class="insight-value">{avg_weekday:.1f}</div>
                            <div class="insight-description">kg CO₂ (Senin-Jumat)</div>
                        </div>
                        <div class="insight-box">
                            <div class="insight-title">Rata-rata Weekend</div>
                            <div class="insight-value">{avg_weekend:.1f}</div>
                            <div class="insight-description">kg CO₂ (Sabtu-Minggu)</div>
                        </div>
                    </div>
                    
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Hari</th>
                                    <th>Emisi (kg CO₂)</th>
                                    <th>Persentase dari Total</th>
                                </tr>
                            </thead>
                            <tbody>
    """
    
    # Add daily emissions data
    total_daily_emissions = sum([d['emission'] for d in daily_analysis])
    for day_data in daily_analysis:
        percentage = (day_data['emission'] / total_daily_emissions * 100) if total_daily_emissions > 0 else 0
        html_content += f"""
                                <tr>
                                    <td><strong>{day_data['day']}</strong></td>
                                    <td>{day_data['emission']:.2f}</td>
                                    <td>{percentage:.1f}%</td>
                                </tr>
        """
    
    html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>
    """
    
    # Add top fakultas if available
    if not top_fakultas.empty:
        html_content += f"""
                <div class="section">
                    <h3 class="section-title">Fakultas dengan Rata-rata Emisi Tertinggi</h3>
                    <div class="table-container">
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
                                    <td>{row['fakultas']}</td>
                                    <td>{row['avg_emission']:.2f}</td>
                                    <td>{row['student_count']} mahasiswa</td>
                                </tr>
            """
        
        html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>
        """
    
    # Add dynamic insights
    if insights:
        html_content += f"""
                <div class="key-insights">
                    <h3>Key Insights</h3>
                    <ul class="insights-list">
        """
        for insight in insights:
            html_content += f"<li>{insight}</li>"
        
        html_content += """
                    </ul>
                </div>
        """
    
    html_content += f"""
            </div>
            
            <div class="footer">
                <p><strong>Institut Teknologi Bandung</strong></p>
                <p>Carbon Emission Dashboard - Electronic Devices Analysis</p>
                <p>Data analysis mendukung pencapaian target sustainability ITB</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def show():
    # Header dengan styling dari style.css
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

    # Data processing
    df_electronic['emisi_elektronik_mingguan'] = pd.to_numeric(df_electronic['emisi_elektronik_mingguan'], errors='coerce')
    df_electronic = df_electronic.dropna(subset=['emisi_elektronik_mingguan'])
    
    # Process personal device data
    df_electronic['durasi_hp'] = pd.to_numeric(df_electronic['durasi_hp'], errors='coerce').fillna(0)
    df_electronic['durasi_laptop'] = pd.to_numeric(df_electronic['durasi_laptop'], errors='coerce').fillna(0)
    df_electronic['durasi_tab'] = pd.to_numeric(df_electronic['durasi_tab'], errors='coerce').fillna(0)
    
    # Parse activities data
    activities_parsed = parse_time_activities(df_activities)

    # FILTERS - menggunakan styling dari style.css
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

    # Apply filters to get filtered data for export and charts
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
            pdf_content = generate_electronic_pdf_report(filtered_df, filtered_activities, device_emissions)
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

    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah atau kosongkan filter.")
        return
    
    # Filter activities based on filtered users
    filtered_activities = activities_parsed[activities_parsed['id_responden'].isin(filtered_df['id_responden'])] if not activities_parsed.empty else pd.DataFrame()
    
    # Calculate device emissions
    device_emissions = calculate_device_emissions(filtered_df, filtered_activities)

    # Row 1: First 3 visualizations
    col1, col2, col3 = st.columns([0.9, 1.4, 0.7])

    with col1:
        # 1. Tren Harian - Line chart
        daily_cols = [col for col in filtered_df.columns if 'emisi_elektronik_' in col and col != 'emisi_elektronik_mingguan']
        
        if daily_cols:
            daily_data = []
            for col in daily_cols:
                day = col.replace('emisi_elektronik_', '').capitalize()
                # Apply day filter if selected
                if not selected_days or day in selected_days:
                    total_emisi = filtered_df[col].sum()
                    daily_data.append({'Hari': day, 'Emisi': total_emisi})
            
            if daily_data:
                daily_df = pd.DataFrame(daily_data)
                
                # Order days properly
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                daily_df['Order'] = daily_df['Hari'].map({day: i for i, day in enumerate(day_order)})
                daily_df = daily_df.sort_values('Order')
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=daily_df['Hari'],
                    y=daily_df['Emisi'],
                    fill='tonexty',
                    mode='lines+markers',
                    line=dict(color='#8e44ad', width=2, shape='spline'),
                    marker=dict(size=5, color='#8e44ad', line=dict(color='white', width=1)),
                    fillcolor='rgba(142, 68, 173, 0.2)',
                    hovertemplate='<b>%{x}</b><br>Emisi: %{y:.1f} kg CO₂<extra></extra>',
                    showlegend=False
                ))
                
                fig_trend.update_layout(
                    height=240, 
                    margin=dict(t=20, b=0, l=0, r=0),
                    title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95,
                              font=dict(family="Poppins", size=10, color="#059669")),
                    font=dict(family="Poppins", size=6),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10))),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (kg CO₂)", font=dict(size=10)))
                )
                
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 2. Perbandingan per Fakultas - BOX PLOT untuk distribusi
        if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
            if 'id_responden' in df_responden.columns and 'id_responden' in filtered_df.columns:
                df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                
                # Apply fakultas filter
                if selected_fakultas:
                    df_plot = df_with_fakultas[df_with_fakultas['fakultas'].isin(selected_fakultas)]
                else:
                    # Filter fakultas with enough data
                    fakultas_counts = df_with_fakultas['fakultas'].value_counts()
                    valid_fakultas = fakultas_counts[fakultas_counts >= 2].index.tolist()
                    df_plot = df_with_fakultas[df_with_fakultas['fakultas'].isin(valid_fakultas)]
                    
                    # Take top 6 fakultas for clarity
                    top_fakultas = df_plot.groupby('fakultas')['emisi_elektronik_mingguan'].mean().nlargest(6).index
                    df_plot = df_plot[df_plot['fakultas'].isin(top_fakultas)]
                
                if not df_plot.empty:
                    fig_fakultas = go.Figure()
                    
                    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
                    
                    for i, fakultas in enumerate(df_plot['fakultas'].unique()):
                        data = df_plot[df_plot['fakultas'] == fakultas]['emisi_elektronik_mingguan']
                        
                        fig_fakultas.add_trace(go.Box(
                            y=data,
                            name=fakultas,
                            marker=dict(color=colors[i % len(colors)]),
                            boxmean=True,
                            hovertemplate=f'<b>{fakultas}</b><br>Emisi: %{{y:.2f}} kg CO₂<br><i>Distribusi emisi mahasiswa</i><extra></extra>'
                        ))
                    
                    fig_fakultas.update_layout(
                        height=240,
                        margin=dict(t=20, b=0, l=0, r=0),
                        title=dict(text="<b>Distribusi Emisi per Fakultas</b>", x=0.35, y=0.95,
                                  font=dict(family="Poppins", size=10, color="#059669")),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=False,
                        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (kg CO₂)", font=dict(size=10))),
                        xaxis=dict(tickfont=dict(size=8), tickangle=-45, title=dict(text="Fakultas", font=dict(size=10)))
                    )
                    
                    st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})

    with col3:
        # 3. Perbandingan per Perangkat - DONUT CHART
        if device_emissions:
            # Filter device emissions based on device filter
            filtered_device_emissions = device_emissions.copy()
            if selected_devices:
                # Keep infrastructure (AC, Lampu) and filter personal devices
                filtered_device_emissions = {k: v for k, v in device_emissions.items() 
                                           if k in selected_devices or k in ['AC', 'Lampu']}
            
            devices = list(filtered_device_emissions.keys())
            emissions = list(filtered_device_emissions.values())
            
            if devices and emissions:
                # Vibrant colors for each device
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][:len(devices)]
                
                fig_devices = go.Figure(data=[go.Pie(
                    labels=devices,
                    values=emissions,
                    hole=.6,
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=3)),
                    textposition='outside',
                    textinfo='label+percent',
                    textfont=dict(size=8, family="Poppins"),
                    sort=False
                )])
                
                # Center text with total
                total_emisi = sum(emissions)
                center_text = f"<b style='font-size:14px'>{total_emisi:.1f}</b><br><span style='font-size:10px'>kg CO₂</span><br><span style='font-size:8px; opacity:0.8'>Total</span>"
                fig_devices.add_annotation(
                    text=center_text, x=0.5, y=0.5, font_size=12, showarrow=False,
                    font=dict(family="Poppins", color="#1f2937")
                )
                
                fig_devices.update_traces(
                    hovertemplate='<b>%{label}</b><br>Emisi: %{value:.2f} kg CO₂<br>Proporsi: %{percent}<br><i>Kontribusi total emisi</i><extra></extra>'
                )
                
                fig_devices.update_layout(
                    height=240,
                    margin=dict(t=60, b=30, l=0, r=0),
                    title=dict(text="<b>Proporsi Emisi per Perangkat</b>", x=0.21, y=0.95,
                              font=dict(family="Poppins", size=10, color="#059669")),
                    font=dict(family="Poppins", size=6),
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                
                st.plotly_chart(fig_devices, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Second 3 visualizations
    col1, col2, col3 = st.columns([1, 0.8, 1])

    with col1:
        # 4. Heatmap Hari dan Jam
        if not filtered_activities.empty:
            # Filter activities by selected days
            activities_for_heatmap = filtered_activities.copy()
            if selected_days:
                activities_for_heatmap = activities_for_heatmap[activities_for_heatmap['day'].isin(selected_days)]
            
            if not activities_for_heatmap.empty:
                # Create heatmap data using time ranges
                heatmap_df = activities_for_heatmap.groupby(['day', 'time_range']).agg({
                    'emisi_ac': 'sum',
                    'emisi_lampu': 'sum'
                }).reset_index()
                heatmap_df['total_emisi'] = heatmap_df['emisi_ac'] + heatmap_df['emisi_lampu']
                
                heatmap_data = heatmap_df.pivot(index='day', columns='time_range', values='total_emisi')
                heatmap_data = heatmap_data.fillna(0)
                
                # Reorder days
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                heatmap_data = heatmap_data.reindex([day for day in day_order if day in heatmap_data.index])
                
                # Sort columns by start time for proper ordering
                if not heatmap_data.empty and len(heatmap_data.columns) > 0:
                    time_columns = heatmap_data.columns.tolist()
                    # Sort by extracting start hour from range (e.g., "10:00-12:00" -> 10)
                    time_columns.sort(key=lambda x: int(x.split(':')[0]) if ':' in str(x) else 0)
                    heatmap_data = heatmap_data[time_columns]
                    
                    fig_heatmap = px.imshow(
                        heatmap_data,
                        color_continuous_scale='plasma',
                        aspect='auto',
                        labels=dict(x="Jam Range", y="Hari", color="Emisi (kg CO₂)")
                    )
                    
                    fig_heatmap.update_traces(
                        hovertemplate='<b>%{y}</b><br>Jam: %{x}<br>Emisi: %{z:.2f} kg CO₂<br>'
                    )
                    
                    fig_heatmap.update_layout(
                        height=240,
                        margin=dict(t=25, b=0, l=0, r=30),
                        coloraxis_showscale=False,
                        font=dict(family="Poppins", size=6),
                        paper_bgcolor='rgba(0,0,0,0)',
                        title=dict(
                            text="<b>Heatmap Hari dan Jam</b>",
                            x=0.5, y=0.95, xanchor='center', yanchor='top',
                            font=dict(family="Poppins", size=10, color="#059669")
                        ),
                        xaxis=dict(tickfont=dict(size=8), tickangle=-45, title=dict(text="Jam", font=dict(size=10))),
                        yaxis=dict(tickfont=dict(size=8), title=dict(text="Hari", font=dict(size=10)))
                    )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # 5. Emisi per Responden - SCATTER PLOT
        user_emissions = filtered_df[['id_responden', 'emisi_elektronik_mingguan']].copy()
        
        if len(user_emissions) > 0:
            # Calculate quartiles for outlier detection
            Q1 = user_emissions['emisi_elektronik_mingguan'].quantile(0.25)
            Q3 = user_emissions['emisi_elektronik_mingguan'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Categorize users
            user_emissions['category'] = 'Normal'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] > upper_bound, 'category'] = 'High User'
            user_emissions.loc[user_emissions['emisi_elektronik_mingguan'] < lower_bound, 'category'] = 'Low User'
            
            # Create index for x-axis
            user_emissions['user_index'] = range(len(user_emissions))
            
            fig_users = go.Figure()
            
            # Color mapping for categories
            color_map = {'Normal': '#3498db', 'High User': '#e74c3c', 'Low User': '#2ecc71'}
            size_map = {'Normal': 6, 'High User': 10, 'Low User': 8}
            
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
                        line=dict(color='white', width=1),
                        opacity=0.8
                    ),
                    hovertemplate=f'<b>User %{{text}}</b><br>Emisi: %{{y:.2f}} kg CO₂<br>Kategori: {category}<br><i>Analisis outlier</i><extra></extra>',
                    text=[f"{str(row['id_responden'])[-3:]}" for _, row in category_data.iterrows()]
                ))
            
            # Add median line
            median_emisi = user_emissions['emisi_elektronik_mingguan'].median()
            fig_users.add_hline(
                y=median_emisi,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Median: {median_emisi:.1f}",
                annotation_position="bottom right"
            )
            
            fig_users.update_layout(
                height=240,
                margin=dict(t=20, b=0, l=0, r=0),
                title=dict(
                    text="<b>Distribusi Emisi per Responden</b>",
                    x=0.5, y=0.95, xanchor='center', yanchor='top',
                    font=dict(family="Poppins", size=10, color="#059669")
                ),
                font=dict(family="Poppins", size=8),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Index Responden", font=dict(size=10))),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', tickfont=dict(size=8), title=dict(text="Emisi (kg CO₂)", font=dict(size=10))),
                legend=dict(orientation="h", yanchor="bottom", y=0.7, xanchor="center", x=0.7, font=dict(size=8))
            )
            
            st.plotly_chart(fig_users, use_container_width=True, config={'displayModeBar': False})

    with col3:
        # 6. Ruang Kelas Tersering - POLAR BAR CHART
        if not filtered_activities.empty and 'lokasi' in filtered_activities.columns:
            # Filter by selected days
            activities_for_location = filtered_activities.copy()
            if selected_days:
                activities_for_location = activities_for_location[activities_for_location['day'].isin(selected_days)]
            
            # Filter for class activities only
            class_activities = activities_for_location[activities_for_location['kegiatan'].str.contains('kelas', case=False, na=False)]
            
            if not class_activities.empty:
                location_stats = class_activities.groupby('lokasi').agg({
                    'emisi_ac': 'sum',
                    'emisi_lampu': 'sum',
                    'duration': 'sum'
                }).reset_index()
                location_stats['total_emisi'] = location_stats['emisi_ac'] + location_stats['emisi_lampu']
                location_stats['session_count'] = class_activities.groupby('lokasi').size().values
                
                # Sort by session count and take top 8
                location_stats = location_stats.sort_values('session_count', ascending=False).head(8)
                
                fig_location = go.Figure()
                
                # Create polar bar chart
                fig_location.add_trace(go.Barpolar(
                    r=location_stats['session_count'],
                    theta=location_stats['lokasi'],
                    marker=dict(
                        color=location_stats['total_emisi'],
                        colorscale='plasma',
                        line=dict(color='white', width=1),
                        colorbar=dict(thickness=8, len=0.5, x=1.1)
                    ),
                    hovertemplate='<b>%{theta}</b><br>Sesi: %{r}<br>Emisi: %{marker.color:.2f} kg CO₂<br><i>Ruang paling aktif</i><extra></extra>',
                    showlegend=False
                ))
                
                fig_location.update_layout(
                    height=240,
                    margin=dict(t=50, b=30, l=0, r=0),
                    title=dict(text="<b>Ruang Kelas Tersering</b>", x=0.375, y=0.95,
                              font=dict(family="Poppins", size=10, color="#059669")),
                    font=dict(family="Poppins", size=5),
                    paper_bgcolor='rgba(0,0,0,0)',
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, location_stats['session_count'].max() * 1.1],
                            tickfont=dict(size=8)
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=8),
                            rotation=90,
                            direction="clockwise"
                        )
                    )
                )
                
                st.plotly_chart(fig_location, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()