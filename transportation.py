import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import base64
from io import BytesIO
import plotly.io as pio

@st.cache_data(ttl=3600)
def load_data():
    """Load transportation data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading transportation data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_responden_data():
    """Load responden data for fakultas information"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    try:
        return pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

def get_transport_colors():
    """Define transportation mode colors based on emission levels"""
    return {
        'Sepeda': '#10b981', 'Jalan kaki': '#34d399', 'Bike': '#10b981', 'Walk': '#34d399',
        'Bus': '#3b82f6', 'Kereta': '#1d4ed8', 'Angkot': '#60a5fa', 'Angkutan Umum': '#2563eb',
        'Ojek Online': '#1e40af', 'TransJakarta': '#1d4ed8',
        'Motor': '#f59e0b', 'Sepeda Motor': '#f59e0b', 'Motorcycle': '#f59e0b', 'Ojek': '#d97706',
        'Mobil': '#ef4444', 'Mobil Pribadi': '#ef4444', 'Car': '#ef4444', 'Taksi': '#dc2626', 'Taxi': '#dc2626'
    }

def get_category_colors():
    """Define colors for emission categories"""
    return {
        'Eco-friendly': '#10b981',     
        'Low Emission': '#3b82f6',     
        'Medium Emission': '#f59e0b',  
        'High Emission': '#ef4444',    
        'Unknown': '#94a3b8'           
    }

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

def initialize_filters():
    """Initialize session state for filters"""
    if 'transport_emission_filter' not in st.session_state:
        st.session_state.transport_emission_filter = []
    if 'transport_mode_filter' not in st.session_state:
        st.session_state.transport_mode_filter = []
    if 'transport_fakultas_filter' not in st.session_state:
        st.session_state.transport_fakultas_filter = []
    if 'transport_reset_counter' not in st.session_state:
        st.session_state.transport_reset_counter = 0
    if 'just_reset' not in st.session_state:
        st.session_state.just_reset = False

def apply_filters(df, df_responden=None):
    """Apply filters to the dataframe"""
    filtered_df = df.copy()
    
    # Filter by day (using daily emission columns if available)
    if st.session_state.transport_emission_filter:
        day_cols = []
        for day in st.session_state.transport_emission_filter:
            day_col = f'emisi_transportasi_{day.lower()}'
            if day_col in filtered_df.columns:
                day_cols.append(day_col)
        
        if day_cols:
            mask = filtered_df[day_cols].sum(axis=1) > 0
            filtered_df = filtered_df[mask]
    
    # Filter by transport mode
    if st.session_state.transport_mode_filter:
        filtered_df = filtered_df[filtered_df['transportasi'].isin(st.session_state.transport_mode_filter)]
    
    # Filter by fakultas
    if st.session_state.transport_fakultas_filter and df_responden is not None and not df_responden.empty:
        fakultas_mapping = get_fakultas_mapping()
        if 'program_studi' in df_responden.columns:
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            fakultas_students = df_responden[df_responden['fakultas'].isin(st.session_state.transport_fakultas_filter)]
            if 'id_responden' in fakultas_students.columns and 'id_responden' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['id_responden'].isin(fakultas_students['id_responden'])]
    
    return filtered_df

def generate_pdf_report(filtered_df, total_emisi, avg_emisi, eco_percentage):
    """Generate PDF report content"""
    from datetime import datetime
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; border-bottom: 2px solid #059669; padding-bottom: 20px; margin-bottom: 30px; }}
            .kpi-section {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .kpi-box {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .kpi-value {{ font-size: 24px; font-weight: bold; color: #059669; }}
            .kpi-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .summary {{ margin: 30px 0; }}
            .footer {{ margin-top: 50px; text-align: center; font-size: 10px; color: #888; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Laporan Emisi Transportasi</h1>
            <h2>ITB Carbon Dashboard</h2>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="kpi-section">
            <div class="kpi-box">
                <div class="kpi-value">{total_emisi:.1f}</div>
                <div class="kpi-label">Total Emisi (kg CO₂/minggu)</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-value">{avg_emisi:.2f}</div>
                <div class="kpi-label">Rata-rata per Mahasiswa</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-value">{len(filtered_df)}</div>
                <div class="kpi-label">Total Responden</div>
            </div>
        </div>
        
        <div class="summary">
            <h3>Ringkasan Analisis</h3>
            <p><strong>Jumlah Data:</strong> {len(filtered_df)} responden</p>
            <p><strong>Moda Transportasi:</strong> {filtered_df['transportasi'].nunique()} jenis</p>
            <p><strong>Emisi Tertinggi:</strong> {filtered_df['emisi_mingguan'].max():.2f} kg CO₂/minggu</p>
            <p><strong>Emisi Terendah:</strong> {filtered_df['emisi_mingguan'].min():.2f} kg CO₂/minggu</p>
        </div>
        
        <div class="summary">
            <h3>Distribusi Moda Transportasi</h3>
            <table>
                <tr><th>Moda Transportasi</th><th>Jumlah Pengguna</th><th>Persentase</th><th>Rata-rata Emisi</th></tr>
    """
    
    transport_stats = filtered_df.groupby('transportasi').agg({
        'emisi_mingguan': ['count', 'mean']
    }).round(2)
    transport_stats.columns = ['count', 'avg_emisi']
    transport_stats['percentage'] = (transport_stats['count'] / len(filtered_df) * 100).round(1)
    transport_stats = transport_stats.sort_values('count', ascending=False)
    
    for mode, row in transport_stats.iterrows():
        html_content += f"""
                <tr>
                    <td>{mode}</td>
                    <td>{row['count']}</td>
                    <td>{row['percentage']}%</td>
                    <td>{row['avg_emisi']:.2f} kg CO₂</td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="footer">
            <p>Laporan ini dibuat oleh ITB Carbon Dashboard</p>
            <p>Data mencerminkan emisi transportasi mahasiswa ITB per minggu</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def show():

    # Initialize filters
    initialize_filters()
    
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

    # Load data
    df = load_data()
    df_responden = load_responden_data()
    
    if df.empty:
        st.error("Data transportasi tidak tersedia")
        return

    # Data processing
    df['emisi_mingguan'] = pd.to_numeric(df['emisi_mingguan'], errors='coerce')
    df = df.dropna(subset=['transportasi'])
    df['emission_category'] = df['transportasi'].apply(categorize_emission_level)
    
    filter_col1, filter_col2, filter_col3, reset_col, export_col1, export_col2 = st.columns([2, 2, 2, 1, 1, 1])

    reset_counter = st.session_state.transport_reset_counter

    if st.session_state.just_reset:
        default_days = []
        default_modes = []
        default_fakultas = []
        st.session_state.just_reset = False
    else:
        default_days = st.session_state.transport_emission_filter
        default_modes = st.session_state.transport_mode_filter
        default_fakultas = st.session_state.transport_fakultas_filter
    
    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect(
            "Hari:",
            options=day_options,
            default=default_days,
            key=f'day_multiselect_{reset_counter}'
        )
        st.session_state.transport_emission_filter = selected_days
    
    with filter_col2:
        available_modes = sorted(df['transportasi'].unique())
        selected_modes = st.multiselect(
            "Moda Transportasi:",
            options=available_modes,
            default=default_modes,
            key=f'mode_multiselect_{reset_counter}'
        )
        st.session_state.transport_mode_filter = selected_modes
    
    with filter_col3:
        if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
            fakultas_mapping = get_fakultas_mapping()
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            available_fakultas = sorted(df_responden['fakultas'].unique())
            selected_fakultas = st.multiselect(
                "Fakultas:",
                options=available_fakultas,
                default=default_fakultas,
                key=f'fakultas_multiselect_{reset_counter}'
            )
            st.session_state.transport_fakultas_filter = selected_fakultas
        else:
            st.markdown('<div style="height: 58px;"></div>', unsafe_allow_html=True)
    
    with reset_col:
        st.markdown('''
        <style>
        /* Multiple targeting untuk reset button */
        div[data-testid="column"]:nth-child(4) .stButton > button,
        div[data-testid="column"]:nth-child(4) button,
        .reset-button-custom .stButton > button,
        .reset-button-custom button {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
            color: white !important;
            border: 2px solid #ef4444 !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            font-family: 'Poppins', sans-serif !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25) !important;
            width: 100% !important;
            height: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        div[data-testid="column"]:nth-child(4) .stButton > button:hover,
        .reset-button-custom .stButton > button:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
            transform: translateY(-2px) scale(1.03) !important;
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.35) !important;
        }
        </style>
        <div class="reset-button-custom">
        ''', unsafe_allow_html=True)
        
        if st.button("Reset", use_container_width=True, key="reset_transport_filters"):
            st.session_state.transport_emission_filter = []
            st.session_state.transport_mode_filter = []
            st.session_state.transport_fakultas_filter = []
            st.session_state.just_reset = True
            st.session_state.transport_reset_counter += 1
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters 
    filtered_df = apply_filters(df, df_responden)
    
    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah filter atau reset.")
        return
    
    # Calculate metrics for export
    total_emisi = filtered_df['emisi_mingguan'].sum()
    avg_emisi = filtered_df['emisi_mingguan'].mean()
    total_users = len(filtered_df)
    eco_friendly_users = len(filtered_df[filtered_df['emission_category'] == 'Eco-friendly'])
    eco_percentage = (eco_friendly_users / total_users * 100) if total_users > 0 else 0

    with export_col1:
        st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Export CSV",
            data=csv_data,
            file_name=f"transport_{len(filtered_df)}.csv",
            mime="text/csv",
            use_container_width=True,
            key="transport_export_csv"
        )
    
    with export_col2:
        st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)
        try:
            pdf_content = generate_pdf_report(filtered_df, total_emisi, avg_emisi, eco_percentage)
            st.download_button(
                label="Export PDF",
                data=pdf_content,
                file_name=f"transport_{len(filtered_df)}.html",
                mime="text/html",
                use_container_width=True,
                key="transport_export_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    st.markdown('<div style="margin: 0.2rem 0;"></div>', unsafe_allow_html=True)

    # Row 1: Main Charts - Height dikurangi untuk kompaktifitas
    col1, col2 = st.columns([1.2, 1])

    with col1:
        # Chart 1: Compact Donut Chart
        transport_counts = filtered_df['transportasi'].value_counts()
        transport_colors = get_transport_colors()
        colors = [transport_colors.get(mode, '#94a3b8') for mode in transport_counts.index]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=transport_counts.index,
            values=transport_counts.values,
            hole=0.45,
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textposition='outside',
            textinfo='label+percent',
            textfont=dict(size=8, family="Poppins", color="#374151"),
            pull=[0.06 if i == 0 else 0 for i in range(len(transport_counts))],
            hovertemplate='<b>%{label}</b><br>Pengguna: %{value} orang<br>Persentase: %{percent}<extra></extra>'
        )])
        
        center_text = f"<b style='font-size:16px; color:#059669'>{total_users}</b><br><span style='font-size:10px; color:#64748b'>Mahasiswa</span><br><span style='font-size:9px; color:#94a3b8'>{len(transport_counts)} Moda</span>"
        fig_donut.add_annotation(
            text=center_text,
            x=0.5, y=0.5, font_size=11, showarrow=False,  
            font=dict(family="Poppins")
        )
        
        fig_donut.update_layout(
            height=240, 
            margin=dict(t=25, b=5, l=5, r=5),  
            showlegend=True,
            legend=dict(
                orientation="v", 
                yanchor="middle", 
                y=0.5, 
                xanchor="left", 
                x=1.05,
                font=dict(family="Poppins", size=7)  
            ),
            font=dict(family="Poppins"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="<b>Komposisi Moda Transportasi</b>",
                x=0.5,
                y=0.98, 
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=12, color="#059669")
            )
        )
        
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Chart 2: Compact Fakultas Comparison
        if df_responden is not None and not df_responden.empty and 'program_studi' in df_responden.columns:
            fakultas_mapping = get_fakultas_mapping()
            df_responden['fakultas'] = df_responden['program_studi'].map(fakultas_mapping).fillna('Lainnya')
            
            if 'id_responden' in df_responden.columns and 'id_responden' in filtered_df.columns:
                df_with_fakultas = filtered_df.merge(df_responden[['id_responden', 'fakultas']], on='id_responden', how='left')
                
                fakultas_stats = df_with_fakultas.groupby('fakultas').agg({
                    'emisi_mingguan': ['mean', 'count', 'sum']
                }).round(2)
                fakultas_stats.columns = ['avg_emisi', 'mahasiswa_count', 'total_emisi']
                fakultas_stats = fakultas_stats.reset_index()
                fakultas_stats = fakultas_stats[fakultas_stats['mahasiswa_count'] >= 2]
                fakultas_stats = fakultas_stats.sort_values('avg_emisi', ascending=True)
                
                max_emisi = fakultas_stats['avg_emisi'].max()
                min_emisi = fakultas_stats['avg_emisi'].min()
                
                colors = []
                for emisi in fakultas_stats['avg_emisi']:
                    ratio = (emisi - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    if ratio <= 0.33:
                        colors.append('#27ae60')
                    elif ratio <= 0.66:
                        colors.append('#f39c12')
                    else:
                        colors.append('#e74c3c')
                
                fig_fakultas = go.Figure()
                
                for i, (_, row) in enumerate(fakultas_stats.iterrows()):
                    fig_fakultas.add_trace(go.Bar(
                        x=[row['avg_emisi']],
                        y=[row['fakultas']],
                        orientation='h',
                        marker=dict(color=colors[i], line=dict(color='white', width=1)),
                        text=[f"{row['avg_emisi']:.1f}"],
                        textposition='inside',
                        textfont=dict(color='white', size=7, family="Poppins", weight='bold'),
                        hovertemplate=f'<b>{row["fakultas"]}</b><br>Rata-rata: {row["avg_emisi"]:.2f} kg CO₂<br>Mahasiswa: {row["mahasiswa_count"]}<extra></extra>',
                        showlegend=False
                    ))
                
                fig_fakultas.update_layout(
                    height=240,  
                    margin=dict(t=25, b=5, l=5, r=5),  
                    showlegend=False,
                    xaxis_title="Rata-rata Emisi (kg CO₂)",
                    yaxis_title="",
                    font=dict(family="Poppins", size=7),  
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text="<b>Perbandingan Emisi Antar Fakultas</b>",
                        x=0.5,
                        y=0.98,  
                        xanchor='center',
                        yanchor='top',
                        font=dict(family="Poppins", size=12, color="#059669")
                    ),
                    xaxis=dict(
                        tickfont=dict(family="Poppins", size=7),
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.1)'
                    ),
                    yaxis=dict(
                        tickfont=dict(family="Poppins", size=7)
                    )
                )
                
                st.plotly_chart(fig_fakultas, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Data fakultas tidak dapat dihubungkan dengan data transportasi")
        else:
            st.info("Data fakultas tidak tersedia")

    # Minimal spacing untuk mencegah tabrakan
    st.markdown('<div style="margin: 0.1rem 0;"></div>', unsafe_allow_html=True)

    # Row 2: Compact Secondary Charts
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Chart 3: Compact Scatter
        stats = filtered_df.groupby('transportasi')['emisi_mingguan'].agg(['mean', 'count']).reset_index()
        stats.columns = ['transportasi', 'avg_emisi', 'frekuensi']
        stats['color'] = stats['transportasi'].map(get_transport_colors()).fillna('#94a3b8')
        stats['emission_category'] = stats['transportasi'].apply(categorize_emission_level)
        
        fig_scatter = go.Figure()
        
        category_colors = get_category_colors()
        for category in stats['emission_category'].unique():
            category_data = stats[stats['emission_category'] == category]
            color = category_colors.get(category, '#94a3b8')
            
            fig_scatter.add_trace(go.Scatter(
                x=category_data['frekuensi'],
                y=category_data['avg_emisi'],
                mode='markers+text',
                marker=dict(
                    size=category_data['frekuensi'] * 1.5 + 6,  # Marker lebih kecil
                    color=color,
                    line=dict(color='white', width=1),
                    opacity=0.8
                ),
                text=category_data['transportasi'],
                textposition="top center",
                textfont=dict(size=6, family="Poppins", color=color, weight='bold'),  # Font lebih kecil
                name=category,
                hovertemplate='<b>%{text}</b><br>Pengguna: %{x}<br>Emisi: %{y:.2f} kg CO₂<extra></extra>'
            ))
        
        fig_scatter.update_layout(
            height=220, 
            margin=dict(t=20, b=5, l=5, r=5),  
            xaxis_title="Popularitas (Jumlah Pengguna)",
            yaxis_title="Emisi (kg CO₂)",
            font=dict(family="Poppins", size=7),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="<b>Emisi vs Popularitas</b>",
                x=0.5,
                y=0.98, 
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=11, color="#059669")
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2, 
                xanchor="center",
                x=0.5,
                font=dict(size=6)
            ),
            xaxis=dict(
                tickfont=dict(family="Poppins", size=6),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                tickfont=dict(family="Poppins", size=6),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            )
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # Chart 4: Compact Daily Trend
        hari_cols = [c for c in filtered_df.columns if 'emisi_transportasi_' in c]
        
        if hari_cols:
            daily_emissions = filtered_df[hari_cols].sum().reset_index()
            daily_emissions.columns = ['Hari', 'Emisi']
            daily_emissions['Hari'] = daily_emissions['Hari'].str.replace('emisi_transportasi_', '').str.capitalize()
            
            day_map = {'Senin': 1, 'Selasa': 2, 'Rabu': 3, 'Kamis': 4, 'Jumat': 5, 'Sabtu': 6, 'Minggu': 7}
            daily_emissions['order'] = daily_emissions['Hari'].map(day_map)
            daily_emissions = daily_emissions.sort_values('order')
            
            fig_trend = go.Figure()
            
            fig_trend.add_trace(go.Scatter(
                x=daily_emissions['Hari'],
                y=daily_emissions['Emisi'],
                fill='tonexty',
                mode='lines+markers',
                line=dict(color='#8e44ad', width=2, shape='spline'),  
                marker=dict(
                    size=5,  # Marker lebih kecil
                    color='#8e44ad',
                    line=dict(color='white', width=1)
                ),
                fillcolor='rgba(142, 68, 173, 0.2)',
                hovertemplate='<b>%{x}</b><br>Emisi: %{y:.1f} kg CO₂<extra></extra>',
                showlegend=False
            ))
            
            fig_trend.update_layout(
                height=220,  
                margin=dict(t=20, b=5, l=5, r=5),  
                xaxis_title="",
                yaxis_title="Emisi (kg CO₂)",
                font=dict(family="Poppins", size=7),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="<b>Tren Emisi Harian</b>",
                    x=0.5,
                    y=0.98,  
                    xanchor='center',
                    yanchor='top',
                    font=dict(family="Poppins", size=11, color="#059669")
                ),
                xaxis=dict(
                    tickfont=dict(family="Poppins", size=6),
                    showgrid=False
                ),
                yaxis=dict(
                    tickfont=dict(family="Poppins", size=6),
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)'
                )
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data emisi harian tidak tersedia")

    with col3:
        # Chart 5: Compact Efficiency ranking
        efficiency_data = filtered_df.groupby('transportasi').agg({
            'emisi_mingguan': ['mean', 'count']
        }).round(2)
        efficiency_data.columns = ['avg_emisi', 'count']
        efficiency_data = efficiency_data.reset_index()
        efficiency_data['efficiency_score'] = 100 / (efficiency_data['avg_emisi'] + 1)
        efficiency_data = efficiency_data.nlargest(6, 'efficiency_score')
        
        fig_efficiency = px.bar(
            efficiency_data,
            x='efficiency_score',
            y='transportasi',
            orientation='h',
            color='transportasi',
            color_discrete_map=get_transport_colors(),
            text='efficiency_score'
        )
        
        fig_efficiency.update_traces(
            texttemplate='%{text:.0f}',
            textposition='inside',
            textfont=dict(color="white", size=7, weight='bold'),  
            hovertemplate='<b>%{y}</b><br>Skor: %{x:.1f}<extra></extra>'
        )
        
        fig_efficiency.update_layout(
            height=220,  # Kembalikan ke ukuran yang lebih besar
            margin=dict(t=20, b=5, l=5, r=5),  
            xaxis_title="Skor Efisiensi",
            yaxis_title="",
            showlegend=False,
            font=dict(family="Poppins", size=7),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="<b>Efisiensi Moda Transport</b>",
                x=0.5,
                y=0.98, 
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=11, color="#059669")
            ),
            xaxis=dict(
                tickfont=dict(family="Poppins", size=6),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                tickfont=dict(family="Poppins", size=6)
            )
        )
        
        st.plotly_chart(fig_efficiency, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()