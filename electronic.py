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

def create_circular_kpi(title, value, subtitle, progress=0.8, color="#059669"):
    """Create a circular KPI card"""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.95) 100%);
        border-radius: 20px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 0.3rem 0;
        height: 120px;
        display: flex;
        align-items: center;
        border: 2px solid rgba(5,150,105,0.1);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100px;
            height: 100px;
            background: linear-gradient(45deg, {color}20, {color}10);
            border-radius: 50%;
        "></div>
        <div style="
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: conic-gradient({color} {progress * 360}deg, #e5e7eb 0deg);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            margin-right: 1rem;
        ">
            <div style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1rem;
                font-weight: bold;
                color: {color};
            ">{value}</div>
        </div>
        <div style="flex: 1;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #374151; margin-bottom: 0.3rem;">{title}</div>
            <div style="font-size: 0.75rem; color: #6b7280; line-height: 1.3;">{subtitle}</div>
        </div>
    </div>
    """

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
                if len(time_str) == 4:  
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
    
    if 'kegiatan' in df_activities.columns:
        class_activities = df_activities[df_activities['kegiatan'].str.contains('kelas', case=False, na=False)]
        return class_activities
    
    return df_activities

def show():
    st.markdown("""
    <div class="wow-header">
        <div class="header-bg-pattern"></div>
        <div class="header-float-1"></div>
        <div class="header-float-2"></div>
        <div class="header-float-3"></div>
        <div class="header-content">
            <h1 class="header-title">Emisi Perangkat Elektronik</h1>
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

    st.markdown("<div style='margin: 0.4rem 0;'></div>", unsafe_allow_html=True)

    # Row 1: Circular KPIs
    kpi_row1, kpi_row2 = st.columns([2, 1])
    
    with kpi_row1:
        kpi_sub1, kpi_sub2 = st.columns([1, 1])
        with kpi_sub1:
            progress_emisi = min(total_emisi / 1000, 1.0)  # Scale for visual appeal
            st.markdown(create_circular_kpi(
                "Total Emisi Elektronik", 
                f"{total_emisi:.0f}", 
                "kg CO₂ per minggu\nsemua mahasiswa",
                progress_emisi,
                "#059669"
            ), unsafe_allow_html=True)
        
        with kpi_sub2:
            progress_avg = min(avg_emisi / 10, 1.0)  # Scale for visual appeal
            st.markdown(create_circular_kpi(
                "Rata-rata per Mahasiswa", 
                f"{avg_emisi:.1f}", 
                "kg CO₂ per orang\nper minggu",
                progress_avg,
                "#10b981"
            ), unsafe_allow_html=True)
    
    with kpi_row2:
        progress_peak = (peak_hour / 24) if peak_hour > 0 else 0
        st.markdown(create_circular_kpi(
            "Peak Hour Kelas", 
            f"{peak_hour:02d}:00" if peak_hour > 0 else "N/A", 
            f"Periode tersibuk:\n{most_active_period}",
            progress_peak,
            "#34d399"
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)

    # Row 2: Main visualizations
    viz_col1, viz_col2, viz_col3 = st.columns([1.3, 1.4, 1.3])
    
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
            textfont=dict(size=9, family="Poppins"),
            sort=False
        )])
        
        center_text = f"<b style='font-size:16px'>{total_emisi:.1f}</b><br><span style='font-size:12px'>kg CO₂</span><br><span style='font-size:10px; opacity:0.8'>Total Mingguan</span>"
        fig_donut.add_annotation(
            text=center_text,
            x=0.5, y=0.5, font_size=14, showarrow=False,
            font=dict(family="Poppins", color="#059669")
        )
        
        fig_donut.update_traces(
            hovertemplate='<b>%{label}</b><br>Emisi: %{value:.1f} kg CO₂<br>Persentase: %{percent}<br>Kontribusi terhadap total emisi elektronik<extra></extra>'
        )
        
        fig_donut.update_layout(
            height=220,
            margin=dict(t=30, b=5, l=5, r=5),
            showlegend=False,
            font=dict(family="Poppins", size=8),
            paper_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Breakdown Sumber Emisi",
                x=0.5, y=0.95, xanchor='center', yanchor='top',
                font=dict(family="Poppins", size=12, color="#059669")
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
            height=220,
            margin=dict(t=30, b=5, l=5, r=5),
            xaxis_title="Jenis Perangkat",
            yaxis_title="Total Emisi (kg CO₂)",
            font=dict(family="Poppins", size=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Perbandingan Emisi Perangkat",
                x=0.5, y=0.95, xanchor='center', yanchor='top',
                font=dict(family="Poppins", size=12, color="#059669")
            ),
            xaxis=dict(tickfont=dict(size=8)),
            yaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
        
        st.plotly_chart(fig_device, use_container_width=True, config={'displayModeBar': False})
    
    with viz_col3:
        # Location analysis for class activities only
        if not location_data.empty:
            top_locations = location_data.nlargest(8, 'class_count')
            
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
                    textfont=dict(color='white', size=9),
                    hovertemplate=f'<b>{row["lokasi"]}</b><br>Jumlah Kelas: {row["class_count"]} sesi<br>Potensi lokasi optimasi AC dan lampu<extra></extra>',
                    showlegend=False
                ))
            
            fig_location.update_layout(
                height=220,
                margin=dict(t=30, b=5, l=5, r=5),
                xaxis_title="Jumlah Sesi Kelas",
                yaxis_title="",
                font=dict(family="Poppins", size=7),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Lokasi Kelas Tersibuk",
                    x=0.5, y=0.95, xanchor='center', yanchor='top',
                    font=dict(family="Poppins", size=12, color="#059669")
                ),
                xaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                yaxis=dict(tickfont=dict(size=6))
            )
            
            st.plotly_chart(fig_location, use_container_width=True, config={'displayModeBar': False})
        else:
            # Time period analysis as fallback
            if not time_data.empty:
                period_analysis = time_data.groupby('period').size().reset_index(name='class_count')
                period_duration = time_data.groupby('period')['duration'].mean().reset_index()
                period_analysis = period_analysis.merge(period_duration, on='period')
                period_analysis = period_analysis.sort_values('class_count', ascending=True)
                
                fig_period = px.bar(
                    period_analysis,
                    x='class_count',
                    y='period',
                    orientation='h',
                    color='class_count',
                    color_continuous_scale='Greens',
                    text='class_count'
                )
                
                fig_period.update_traces(
                    texttemplate='%{text}',
                    textposition='inside',
                    textfont=dict(color='white', size=10),
                    hovertemplate='<b>%{y}</b><br>Total Kelas: %{x}<br>Rata-rata Durasi: %{customdata:.1f} jam<extra></extra>',
                    customdata=period_analysis['duration']
                )
                
                fig_period.update_layout(
                    height=220,
                    margin=dict(t=30, b=5, l=5, r=5),
                    xaxis_title="Intensitas Kelas",
                    yaxis_title="",
                    coloraxis_showscale=False,
                    font=dict(family="Poppins", size=8),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text="Kelas per Periode Waktu",
                        x=0.5, y=0.95, xanchor='center', yanchor='top',
                        font=dict(family="Poppins", size=12, color="#059669")
                    ),
                    xaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(tickfont=dict(size=8))
                )
                
                st.plotly_chart(fig_period, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)

    # Row 3: Advanced analytics
    advanced_col1, advanced_col2 = st.columns([1.5, 1])
    
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
                height=180,
                margin=dict(t=30, b=5, l=5, r=5),
                coloraxis_showscale=True,
                coloraxis=dict(colorbar=dict(thickness=10, len=0.7)),
                font=dict(family="Poppins", size=7),
                paper_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Heatmap Jadwal Kelas Mingguan",
                    x=0.5, y=0.95, xanchor='center', yanchor='top',
                    font=dict(family="Poppins", size=12, color="#059669")
                ),
                xaxis=dict(tickfont=dict(size=7), title="Jam Mulai"),
                yaxis=dict(tickfont=dict(size=7), title="")
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})
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
                    height=180,
                    margin=dict(t=30, b=5, l=5, r=5),
                    xaxis_title="Jumlah Pengguna",
                    yaxis_title="Emisi per User (kg CO₂)",
                    font=dict(family="Poppins", size=7),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text="Efisiensi Emisi per Device",
                        x=0.5, y=0.95, xanchor='center', yanchor='top',
                        font=dict(family="Poppins", size=12, color="#059669")
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=7)),
                    xaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
                )
                
                st.plotly_chart(fig_efficiency, use_container_width=True, config={'displayModeBar': False})
    
    with advanced_col2:
        # Device usage statistics
        device_stats = pd.DataFrame({
            'Device': ['Smartphone', 'Laptop', 'Tablet'],
            'Users': [users_hp, users_laptop, users_tab],
            'Avg_Duration': [
                df_electronic[df_electronic['uses_hp']]['durasi_hp'].mean() if users_hp > 0 else 0,
                df_electronic[df_electronic['uses_laptop']]['durasi_laptop'].mean() if users_laptop > 0 else 0,
                df_electronic[df_electronic['uses_tab']]['durasi_tab'].mean() if users_tab > 0 else 0
            ],
            'Total_Duration': [
                df_electronic['durasi_hp'].sum(),
                df_electronic['durasi_laptop'].sum(), 
                df_electronic['durasi_tab'].sum()
            ]
        })
        
        fig_usage = px.bar(
            device_stats,
            x='Device',
            y='Users',
            color='Avg_Duration',
            color_continuous_scale='Greens',
            text='Users'
        )
        
        fig_usage.update_traces(
            texttemplate='%{text} users',
            textposition='outside',
            textfont=dict(size=9),
            hovertemplate='<b>%{x}</b><br>Pengguna: %{y} orang<br>Rata-rata Durasi: %{marker.color:.1f} menit<br>Total Durasi: %{customdata:.0f} menit<extra></extra>',
            customdata=device_stats['Total_Duration']
        )
        
        fig_usage.update_layout(
            height=180,
            margin=dict(t=30, b=5, l=5, r=5),
            xaxis_title="",
            yaxis_title="Jumlah Pengguna",
            coloraxis_showscale=False,
            font=dict(family="Poppins", size=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Statistik Penggunaan Device",
                x=0.5, y=0.95, xanchor='center', yanchor='top',
                font=dict(family="Poppins", size=12, color="#059669")
            ),
            xaxis=dict(tickfont=dict(size=8)),
            yaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
        
        st.plotly_chart(fig_usage, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()