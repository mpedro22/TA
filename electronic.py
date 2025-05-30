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

def parse_time_slots(df_activities):
    """Parse time slots from hari column (e.g., selasa_0810)"""
    time_data = []
    if df_activities.empty or 'hari' not in df_activities.columns:
        return pd.DataFrame()
    
    for _, row in df_activities.iterrows():
        hari_value = str(row['hari'])
        if '_' in hari_value:
            parts = hari_value.split('_')
            if len(parts) == 2:
                day = parts[0].capitalize()
                time_str = parts[1]
                if len(time_str) == 4:  # Format like 0810
                    start_hour = int(time_str[:2])
                    end_hour = int(time_str[2:])
                    
                    # Categorize time periods
                    if 6 <= start_hour < 12:
                        period = 'Pagi'
                    elif 12 <= start_hour < 16:
                        period = 'Siang'
                    elif 16 <= start_hour < 19:
                        period = 'Sore'
                    else:
                        period = 'Malam'
                    
                    time_data.append({
                        'day': day,
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                        'period': period,
                        'duration': end_hour - start_hour,
                        'time_slot': f"{start_hour:02d}:00-{end_hour:02d}:00",
                        'day_order': {'Senin': 1, 'Selasa': 2, 'Rabu': 3, 'Kamis': 4, 'Jumat': 5, 'Sabtu': 6, 'Minggu': 7}.get(day, 0),
                        'kegiatan': row.get('kegiatan', ''),
                        'lokasi': row.get('lokasi', '')
                    })
    
    return pd.DataFrame(time_data)

def filter_class_activities(df_activities):
    """Filter activities to only include class-related activities"""
    if df_activities.empty:
        return pd.DataFrame()
    
    # Check if 'kegiatan' column exists and filter for 'kelas'
    if 'kegiatan' in df_activities.columns:
        # Filter for activities that contain 'kelas' (case-insensitive)
        class_activities = df_activities[df_activities['kegiatan'].str.contains('kelas', case=False, na=False)]
        return class_activities
    
    # If no kegiatan column, return original data
    return df_activities

def show():
    st.markdown("""
    <div class="wow-header">
        <div class="header-bg-pattern"></div>
        <div class="header-float-1"></div>
        <div class="header-float-2"></div>
        <div class="header-float-3"></div>
        <div class="header-content">
            <h1 class="header-title">Emisi Elektronik</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    df_electronic = load_electronic_data()
    df_activities = load_daily_activities()
    
    if df_electronic.empty:
        st.error("Data elektronik tidak tersedia")
        return

    # Data processing for electronic data
    df_electronic['emisi_elektronik_mingguan'] = pd.to_numeric(df_electronic['emisi_elektronik_mingguan'], errors='coerce')
    df_electronic = df_electronic.dropna(subset=['emisi_elektronik_mingguan'])
    
    # Calculate device charging emissions and usage
    df_electronic['durasi_hp'] = pd.to_numeric(df_electronic['durasi_hp'], errors='coerce').fillna(0)
    df_electronic['durasi_laptop'] = pd.to_numeric(df_electronic['durasi_laptop'], errors='coerce').fillna(0)
    df_electronic['durasi_tab'] = pd.to_numeric(df_electronic['durasi_tab'], errors='coerce').fillna(0)
    
    # Calculate individual device emissions
    df_electronic['emisi_hp'] = df_electronic['durasi_hp'] * 0.02 * 0.5  # 20W device
    df_electronic['emisi_laptop'] = df_electronic['durasi_laptop'] * 0.08 * 0.5  # 80W device  
    df_electronic['emisi_tab'] = df_electronic['durasi_tab'] * 0.03 * 0.5  # 30W device
    df_electronic['emisi_charging'] = df_electronic['emisi_hp'] + df_electronic['emisi_laptop'] + df_electronic['emisi_tab']
    
    # Device usage statistics
    df_electronic['uses_hp'] = df_electronic['durasi_hp'] > 0
    df_electronic['uses_laptop'] = df_electronic['durasi_laptop'] > 0
    df_electronic['uses_tab'] = df_electronic['durasi_tab'] > 0
    
    # Check if lampu columns exist
    if 'emisi_lampu' in df_electronic.columns:
        df_electronic['emisi_lampu'] = pd.to_numeric(df_electronic['emisi_lampu'], errors='coerce').fillna(0)
    else:
        df_electronic['emisi_lampu'] = df_electronic['emisi_elektronik_mingguan'] * 0.15
    
    # Calculate AC emissions
    df_electronic['emisi_ac'] = df_electronic['emisi_elektronik_mingguan'] - df_electronic['emisi_charging'] - df_electronic['emisi_lampu']
    df_electronic['emisi_ac'] = df_electronic['emisi_ac'].clip(lower=0)

    # Filter activities for class only
    df_class_activities = filter_class_activities(df_activities)
    
    # Parse time data from class activities only
    time_data = parse_time_slots(df_class_activities)
    
    # Process location data for class activities only
    location_data = pd.DataFrame()
    if not df_class_activities.empty and 'lokasi' in df_class_activities.columns:
        location_data = df_class_activities.groupby('lokasi').size().reset_index(name='class_count')

    # Calculate metrics
    total_emisi = df_electronic['emisi_elektronik_mingguan'].sum()
    avg_emisi = df_electronic['emisi_elektronik_mingguan'].mean()
    total_charging = df_electronic['emisi_charging'].sum()
    total_ac = df_electronic['emisi_ac'].sum()
    total_lampu = df_electronic['emisi_lampu'].sum()

    # Device statistics
    total_hp = df_electronic['emisi_hp'].sum()
    total_laptop = df_electronic['emisi_laptop'].sum()
    total_tab = df_electronic['emisi_tab'].sum()
    
    users_hp = df_electronic['uses_hp'].sum()
    users_laptop = df_electronic['uses_laptop'].sum()
    users_tab = df_electronic['uses_tab'].sum()

    # Calculate insights
    peak_hour_data = time_data.groupby('start_hour').size() if not time_data.empty else pd.Series()
    peak_hour = peak_hour_data.idxmax() if not peak_hour_data.empty else 0
    most_active_period = time_data.groupby('period').size().idxmax() if not time_data.empty else "N/A"

    # CONSISTENT SPACING: Remove manual spacing, let CSS handle it
    
    # MAIN LAYOUT: Charts di kiri, KPIs di kanan
    main_content, kpi_sidebar = st.columns([3, 1])
    
    # KPI SIDEBAR (Kanan) - 3 KPI vertikal bulat menggunakan class CSS
    with kpi_sidebar:
        # KPI 1: Total Emisi
        st.markdown(f"""
        <div class="kpi-circle">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            "></div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #059669; margin-bottom: 0.3rem;">{total_emisi:.0f}</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase;">TOTAL EMISI</div>
            <div style="font-size: 0.6rem; color: #64748b;">kg CO₂/minggu</div>
        </div>
        """, unsafe_allow_html=True)
        
        # KPI 2: Rata-rata
        st.markdown(f"""
        <div class="kpi-circle">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            "></div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #10b981; margin-bottom: 0.3rem;">{avg_emisi:.1f}</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase;">RATA-RATA</div>
            <div style="font-size: 0.6rem; color: #64748b;">kg CO₂/orang</div>
        </div>
        """, unsafe_allow_html=True)
        
        # KPI 3: Peak Hour
        st.markdown(f"""
        <div class="kpi-circle">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #34d399 0%, #6ee7b7 100%);
            "></div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #34d399; margin-bottom: 0.3rem;">{peak_hour:02d}:00</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase;">JAM PUNCAK</div>
            <div style="font-size: 0.6rem; color: #64748b;">{most_active_period}</div>
        </div>
        """, unsafe_allow_html=True)

    # MAIN CONTENT (Kiri) - Charts
    with main_content:
        # Row 1: Main visualizations
        viz_col1, viz_col2 = st.columns([1, 1])
        
        with viz_col1:
            # 3-Component breakdown
            fig_donut = go.Figure(data=[go.Pie(
                labels=['AC Ruang Kelas', 'Perangkat Charging', 'Lampu'], 
                values=[total_ac, total_charging, total_lampu],
                hole=.6,
                marker=dict(
                    colors=['#059669', '#10b981', '#6ee7b7'], 
                    line=dict(color='#FFFFFF', width=3)
                ),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=10, family="Poppins"),
                sort=False
            )])
            
            center_text = f"<b style='font-size:18px'>{total_emisi:.1f}</b><br><span style='font-size:14px'>kg CO₂</span><br><span style='font-size:12px; opacity:0.8'>Total Mingguan</span>"
            fig_donut.add_annotation(
                text=center_text,
                x=0.5, y=0.5, font_size=16, showarrow=False,
                font=dict(family="Poppins", color="#059669")
            )
            
            fig_donut.update_traces(
                hovertemplate='<b>%{label}</b><br>Emisi: %{value:.1f} kg CO₂<br>Persentase: %{percent}<br>Kontribusi terhadap total emisi elektronik<extra></extra>'
            )
            
            fig_donut.update_layout(
                height=280,
                margin=dict(t=40, b=20, l=20, r=20),
                showlegend=False,
                font=dict(family="Poppins", size=9),
                paper_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Breakdown Sumber Emisi",
                    x=0.5, y=0.95, xanchor='center', yanchor='top',
                    font=dict(family="Poppins", size=14, color="#059669")
                )
            )
            
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
        with viz_col2:
            # Device comparison analysis
            device_data = {
                'Device': ['Smartphone', 'Laptop', 'Tablet'],
                'Total_Emisi': [total_hp, total_laptop, total_tab],
                'Jumlah_Pengguna': [users_hp, users_laptop, users_tab],
                'Avg_Durasi': [
                    df_electronic[df_electronic['uses_hp']]['durasi_hp'].mean() if users_hp > 0 else 0,
                    df_electronic[df_electronic['uses_laptop']]['durasi_laptop'].mean() if users_laptop > 0 else 0,
                    df_electronic[df_electronic['uses_tab']]['durasi_tab'].mean() if users_tab > 0 else 0
                ]
            }
            
            device_df = pd.DataFrame(device_data)
            device_df['Emisi_per_User'] = device_df['Total_Emisi'] / device_df['Jumlah_Pengguna'].replace(0, 1)
            
            fig_device = go.Figure()
            
            # Add bars for each device
            colors = ['#059669', '#10b981', '#6ee7b7']
            for i, (_, row) in enumerate(device_df.iterrows()):
                fig_device.add_trace(go.Bar(
                    x=[row['Device']],
                    y=[row['Total_Emisi']],
                    name=row['Device'],
                    marker=dict(color=colors[i]),
                    text=[f"{row['Total_Emisi']:.2f} kg"],
                    textposition='outside',
                    hovertemplate=f'<b>{row["Device"]}</b><br>Total Emisi: {row["Total_Emisi"]:.2f} kg CO₂<br>Pengguna: {row["Jumlah_Pengguna"]} orang<br>Rata-rata Durasi: {row["Avg_Durasi"]:.1f} menit<br>Emisi per User: {row["Emisi_per_User"]:.3f} kg CO₂<extra></extra>',
                    showlegend=False
                ))
            
            fig_device.update_layout(
                height=280,
                margin=dict(t=40, b=20, l=20, r=20),
                xaxis_title="Jenis Perangkat",
                yaxis_title="Total Emisi (kg CO₂)",
                font=dict(family="Poppins", size=9),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Perbandingan Emisi Perangkat",
                    x=0.5, y=0.95, xanchor='center', yanchor='top',
                    font=dict(family="Poppins", size=14, color="#059669")
                ),
                xaxis=dict(tickfont=dict(size=9)),
                yaxis=dict(tickfont=dict(size=8), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
            )
            
            st.plotly_chart(fig_device, use_container_width=True, config={'displayModeBar': False})

        # CONSISTENT SPACING: Let CSS handle spacing between sections

        # Row 2: Advanced analytics
        advanced_col1, advanced_col2 = st.columns([1.8, 1.2])
        
        with advanced_col1:
            # Weekly class schedule heatmap
            if not time_data.empty:
                # Create pivot table from actual data
                heatmap_df = time_data.groupby(['day', 'start_hour']).size().reset_index(name='class_count')
                heatmap_data = heatmap_df.pivot(index='day', columns='start_hour', values='class_count')
                heatmap_data = heatmap_data.fillna(0)
                
                # Reorder days
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                heatmap_data = heatmap_data.reindex([day for day in day_order if day in heatmap_data.index])
                
                fig_heatmap = px.imshow(
                    heatmap_data,
                    color_continuous_scale='Greens',
                    aspect='auto',
                    labels=dict(x="Jam Mulai", y="Hari", color="Jumlah Kelas")
                )
                
                fig_heatmap.update_traces(
                    hovertemplate='<b>%{y}</b> jam %{x}:00<br>Jumlah Kelas: %{z}<br>Intensitas penggunaan ruang kelas<extra></extra>'
                )
                
                fig_heatmap.update_layout(
                    height=250,
                    margin=dict(t=40, b=20, l=20, r=20),
                    coloraxis_showscale=True,
                    coloraxis=dict(colorbar=dict(thickness=12, len=0.8)),
                    font=dict(family="Poppins", size=8),
                    paper_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text="Heatmap Jadwal Kelas Mingguan",
                        x=0.5, y=0.95, xanchor='center', yanchor='top',
                        font=dict(family="Poppins", size=14, color="#059669")
                    ),
                    xaxis=dict(tickfont=dict(size=8), title="Jam Mulai"),
                    yaxis=dict(tickfont=dict(size=8), title="")
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
        
        with advanced_col2:
            # Location analysis for class activities only
            if not location_data.empty:
                top_locations = location_data.nlargest(6, 'class_count')
                
                fig_location = go.Figure()
                
                # Create gradient bars
                colors = px.colors.sample_colorscale('Greens', [n/(len(top_locations)-1) for n in range(len(top_locations))])
                
                for i, (_, row) in enumerate(top_locations.iterrows()):
                    fig_location.add_trace(go.Bar(
                        x=[row['class_count']],
                        y=[row['lokasi']],
                        orientation='h',
                        marker=dict(color=colors[i], line=dict(color='#059669', width=1)),
                        text=[f"{row['class_count']}"],
                        textposition='inside',
                        textfont=dict(color='white', size=10),
                        hovertemplate=f'<b>{row["lokasi"]}</b><br>Jumlah Kelas: {row["class_count"]} sesi<br>Potensi lokasi optimasi AC dan lampu<extra></extra>',
                        showlegend=False
                    ))
                
                fig_location.update_layout(
                    height=260,
                    margin=dict(t=40, b=20, l=20, r=20),
                    xaxis_title="Jumlah Sesi Kelas",
                    yaxis_title="",
                    font=dict(family="Poppins", size=8),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text="Lokasi Kelas Tersibuk",
                        x=0.5, y=0.95, xanchor='center', yanchor='top',
                        font=dict(family="Poppins", size=14, color="#059669")
                    ),
                    xaxis=dict(tickfont=dict(size=8), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(tickfont=dict(size=7))
                )
                
                st.plotly_chart(fig_location, use_container_width=True, config={'displayModeBar': False})
            else:
                # Device efficiency comparison as fallback
                if device_df['Jumlah_Pengguna'].sum() > 0:
                    fig_efficiency = px.scatter(
                        device_df,
                        x='Jumlah_Pengguna',
                        y='Emisi_per_User',
                        size='Total_Emisi',
                        color='Device',
                        color_discrete_sequence=['#059669', '#10b981', '#6ee7b7'],
                        size_max=50
                    )
                    
                    fig_efficiency.update_traces(
                        hovertemplate='<b>%{marker.color}</b><br>Pengguna: %{x}<br>Emisi per User: %{y:.3f} kg CO₂<br>Total Emisi: %{marker.size:.2f} kg CO₂<extra></extra>'
                    )
                    
                    fig_efficiency.update_layout(
                        height=250,
                        margin=dict(t=40, b=20, l=20, r=20),
                        xaxis_title="Jumlah Pengguna",
                        yaxis_title="Emisi per User (kg CO₂)",
                        font=dict(family="Poppins", size=8),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        title=dict(
                            text="Efisiensi Emisi per Device",
                            x=0.5, y=0.95, xanchor='center', yanchor='top',
                            font=dict(family="Poppins", size=14, color="#059669")
                        ),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=8)),
                        xaxis=dict(tickfont=dict(size=8), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                        yaxis=dict(tickfont=dict(size=8), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
                    )
                    
                    st.plotly_chart(fig_efficiency, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()