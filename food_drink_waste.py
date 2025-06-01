import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

@st.cache_data(ttl=3600)
def load_daily_activities_data():
    """Load daily activities data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading daily activities data: {e}")
        return pd.DataFrame()

def create_metric_card(title, value, unit, change=None, color_class="primary", custom_height=None):
    """Create a clean metric card using CSS class from style.css"""
    change_html = ""
    if change is not None:
        change_color = "#10b981" if change >= 0 else "#ef4444"
        change_symbol = "↗" if change >= 0 else "↘"
        change_html = f'<div style="font-size: 0.6rem; color: {change_color}; margin-top: 0.1rem;">{change_symbol} {change:+.1f}%</div>'
    
    height_style = f"height:200px;" if custom_height else ""

    return f"""
    <div class="kpi-circle {color_class}" style="{height_style}">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{title}</div>
        <div style="font-size: 0.6rem; color: #64748b; margin-top: 0.1rem;">{unit}</div>
        {change_html}
    </div>
    """

def parse_meal_activities(df):
    """Parse meal activities from daily activities data"""
    meal_activities = []
    
    if df.empty:
        return pd.DataFrame()
    
    # Filter for meal/drink activities only
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
                    
                    # Categorize meal periods - 4 periods (pagi, siang, sore, malam)
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
                    
                    lokasi = str(row.get('lokasi', ''))
                    location_category = lokasi if lokasi and lokasi != 'nan' else 'Unknown'
                    
                    meal_activities.append({
                        'id_responden': row.get('id_responden', ''),
                        'day': day_name,
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                        'duration': end_hour - start_hour,
                        'time_slot': f"{start_hour:02d}:00-{end_hour:02d}:00",
                        'meal_period': meal_period,
                        'lokasi': lokasi,
                        'location_category': location_category,
                        'emisi_makanminum': pd.to_numeric(row.get('emisi_makanminum', 0), errors='coerce'),
                        'day_order': {'Senin': 1, 'Selasa': 2, 'Rabu': 3, 'Kamis': 4, 'Jumat': 5, 'Sabtu': 6, 'Minggu': 7}.get(day_name, 0),
                        'is_weekend': day_name in ['Sabtu', 'Minggu']
                    })
    
    return pd.DataFrame(meal_activities)

def show():
    st.markdown("""
    <div class="wow-header">
        <div class="header-bg-pattern"></div>
        <div class="header-float-1"></div>
        <div class="header-float-2"></div>
        <div class="header-float-3"></div>
        <div class="header-content">
            <h1 class="header-title">Emisi Sampah Makanan dan Minuman</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load and process data
    df_activities = load_daily_activities_data()
    
    if df_activities.empty:
        st.error("Data aktivitas harian tidak tersedia")
        return

    # Parse meal activities
    meal_data = parse_meal_activities(df_activities)
    
    if meal_data.empty:
        st.error("Data aktivitas makanan & minuman tidak ditemukan")
        return
    
    # Calculate metrics
    total_emisi = meal_data['emisi_makanminum'].sum()
    unique_respondents = meal_data['id_responden'].nunique()
    emisi_per_person = meal_data.groupby('id_responden')['emisi_makanminum'].sum()
    avg_emisi_per_person = emisi_per_person.mean()

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns([0.9, 0.9, 1.6, 1.6])
    
    with row1_col1:
        st.markdown(f"""
        <div class="kpi-square">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            "></div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #059669; margin-bottom: 0.3rem;">{total_emisi:.1f}</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase;">TOTAL EMISI</div>
            <div style="font-size: 0.6rem; color: #64748b;">kg CO₂/minggu</div>
        </div>
        """, unsafe_allow_html=True)

    with row1_col2:
        st.markdown(f"""
        <div class="kpi-square">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            "></div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #059669; margin-bottom: 0.3rem;">{avg_emisi_per_person:.2f}</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase;">RATA-RATA</div>
            <div style="font-size: 0.6rem; color: #64748b;">kg CO₂/orang</div>
        </div>
        """, unsafe_allow_html=True)

    
    # Pie Chart - Distribusi Lokasi
    with row1_col3:
        if not meal_data.empty:
            location_data = meal_data['location_category'].value_counts() 
            
            colors = ['#059669', '#10b981', '#34d399', '#6ee7b7', '#86efac', '#bbf7d0', 
                     '#dcfce7', '#f0fdf4', '#065f46', '#047857', '#059669', '#0d9488']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=location_data.index,
                values=location_data.values,
                hole=0.5,
                marker=dict(colors=colors[:len(location_data)])
            )])
            
            fig_pie.update_layout(
                height=170,
                margin=dict(t=25, b=5, l=5, r=25),
                paper_bgcolor='rgba(0,0,0,0)',
                title=dict(text="Distribusi Lokasi", x=0.38, y=0.95, font=dict(family="Poppins", size=9, color="#059669")),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0, font=dict(size=7)),
                font=dict(family="Poppins", size=7)
            )
            
            fig_pie.update_traces(textposition='inside', textinfo='percent', textfont_size=7)
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    # Chart utama - Bubble Chart
    with row1_col4:
        if not meal_data.empty:
            bubble_data = meal_data.groupby(['day', 'time_slot'])['emisi_makanminum'].sum().reset_index()
            day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            bubble_data['day_order'] = bubble_data['day'].map({day: i for i, day in enumerate(day_order)})
            bubble_data = bubble_data.sort_values(['day_order'])
            
            fig_bubble = go.Figure()
            max_emisi = bubble_data['emisi_makanminum'].max()
            
            for _, row in bubble_data.iterrows():
                intensity = row['emisi_makanminum'] / max_emisi if max_emisi > 0 else 0
                color = f'rgba({int(6 + intensity * 100)}, {int(150 + intensity * 55)}, {int(105 - intensity * 20)}, 0.8)'
                
                fig_bubble.add_trace(go.Scatter(
                    x=[row['day']],
                    y=[row['time_slot']],
                    mode='markers',
                    marker=dict(
                        size=max(8, row['emisi_makanminum'] * 4),
                        color=color,
                        line=dict(color='white', width=1),
                        opacity=0.8
                    ),
                    hovertemplate=f'<b>{row["day"]}</b><br>Waktu: {row["time_slot"]}<br>Emisi: {row["emisi_makanminum"]:.2f} kg CO₂<extra></extra>',
                    showlegend=False
                ))
            
            fig_bubble.update_layout(
                height=170,  
                margin=dict(t=25, b=10, l=10, r=10),
                font=dict(family="Poppins", size=8),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="Pola Waktu per Hari", x=0.38, y=0.93, font=dict(family="Poppins", size=9, color="#059669")),
                xaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                yaxis=dict(tickfont=dict(size=7), showgrid=True, gridcolor='rgba(0,0,0,0.1)')
            )
            
            st.plotly_chart(fig_bubble, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Bar Chart + Line Chart
    row2_col1, row2_col2 = st.columns([1, 1])
    
    with row2_col1:
        # Bar Chart - Periode
        if not meal_data.empty:
            period_data = meal_data.groupby('meal_period')['emisi_makanminum'].sum().reset_index()
            period_order = ['Pagi', 'Siang', 'Sore', 'Malam']
            period_data = period_data.set_index('meal_period').reindex(period_order, fill_value=0).reset_index()
            
            fig_period = go.Figure(data=[
                go.Bar(
                    x=period_data['meal_period'],
                    y=period_data['emisi_makanminum'],
                    marker_color=['#059669', '#10b981', '#34d399', '#6ee7b7'],
                    text=period_data['emisi_makanminum'].round(1),
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Emisi: %{y:.2f} kg CO₂<extra></extra>'
                )
            ])
            
            fig_period.update_layout(
                height=170,
                margin=dict(t=25, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="Distribusi Periode", x=0.42, y=0.93, font=dict(family="Poppins", size=9, color="#059669")),
                xaxis=dict(tickfont=dict(size=7)),
                yaxis=dict(tickfont=dict(size=7)),
                showlegend=False,
                font=dict(family="Poppins", size=7)
            )
            
            st.plotly_chart(fig_period, use_container_width=True, config={'displayModeBar': False})

    with row2_col2:
        # Line Chart - Tren Harian
        if not meal_data.empty:
            daily_trend = meal_data.groupby('day')['emisi_makanminum'].sum().reset_index()
            day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            daily_trend['day_order'] = daily_trend['day'].map({day: i for i, day in enumerate(day_order)})
            daily_trend = daily_trend.sort_values('day_order')
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_trend['day'],
                y=daily_trend['emisi_makanminum'],
                mode='lines+markers',
                line=dict(color='#059669', width=3, shape='spline'),
                marker=dict(size=6, color='#10b981', line=dict(color='white', width=1)),
                fill='tonexty',
                fillcolor='rgba(5, 150, 105, 0.2)',
                hovertemplate='<b>%{x}</b><br>Emisi: %{y:.2f} kg CO₂<extra></extra>'
            ))
            
            fig_trend.update_layout(
                height=170,
                margin=dict(t=25, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(text="Tren Harian", x=0.45, y=0.93, font=dict(family="Poppins", size=9, color="#059669")),
                xaxis=dict(tickfont=dict(size=7)),
                yaxis=dict(tickfont=dict(size=7)),
                showlegend=False,
                font=dict(family="Poppins", size=7)
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    # Row 3: Heatmap
    if not meal_data.empty:
        heatmap_data = meal_data.groupby(['location_category', 'time_slot'])['emisi_makanminum'].sum().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='time_slot', columns='location_category', values='emisi_makanminum').fillna(0)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,  
            y=heatmap_pivot.index,    
            colorscale='Greens',
            hoverongaps=False,
            hovertemplate='<b>%{x}</b><br>Waktu: %{y}<br>Emisi: %{z:.2f} kg CO₂<extra></extra>'
        ))
        
        fig_heatmap.update_layout(
            height=200,  
            margin=dict(t=25, b=10, l=60, r=10),
            font=dict(family="Poppins", size=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(text="Heatmap: Lokasi vs Waktu Konsumsi", x=0.42, y=0.95, font=dict(family="Poppins", size=9, color="#059669")),
            xaxis=dict(title="Lokasi Konsumsi", tickfont=dict(size=7), tickangle=45),
            yaxis=dict(title="Waktu", tickfont=dict(size=7))
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()