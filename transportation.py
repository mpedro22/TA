import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

@st.cache_data(ttl=300)
def load_data():
    """Load transportation data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading transportation data: {e}")
        return pd.DataFrame()

def create_metric_card(title, value, unit, change=None, color_class="primary"):
    """Create a clean metric card"""
    change_html = ""
    if change is not None:
        change_color = "#10b981" if change >= 0 else "#ef4444"
        change_symbol = "↗" if change >= 0 else "↘"
        change_html = f'<div style="font-size: 0.7rem; color: {change_color}; margin-top: 0.2rem;">{change_symbol} {change:+.1f}%</div>'
    
    return f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{title}</div>
        <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.2rem;">{unit}</div>
        {change_html}
    </div>
    """

def show():
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
    if df.empty:
        st.error("Data transportasi tidak tersedia")
        return

    # Data processing
    df['emisi_mingguan'] = pd.to_numeric(df['emisi_mingguan'], errors='coerce')
    df = df.dropna(subset=['transportasi'])

    # Calculate metrics
    total_emisi = df['emisi_mingguan'].sum()
    avg_emisi = df['emisi_mingguan'].mean()
    total_users = len(df)
    moda_populer = df['transportasi'].mode()[0] if not df['transportasi'].empty else "N/A"
    moda_pct = df['transportasi'].value_counts(normalize=True).iloc[0] * 100 if not df['transportasi'].empty else 0

    # KPI Section
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(create_metric_card("Total Emisi", f"{total_emisi:.1f}", "kg CO₂/minggu", None, "primary"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card("Rata-rata Emisi", f"{avg_emisi:.2f}", "kg CO₂/orang", None, "primary"), unsafe_allow_html=True)
        
    with col3:
        st.markdown(create_metric_card("Moda Dominan", f"{moda_populer}", f"{moda_pct:.1f}% pengguna", None, "primary"), unsafe_allow_html=True)

    # Row 1: Main Charts
    col1, col2 = st.columns([1.3, 1])

    with col1:
        # Chart 1: Donut Chart
        transport_counts = df['transportasi'].value_counts()
        
        fig_donut = px.pie(
            names=transport_counts.index,
            values=transport_counts.values,
            hole=0.5,
            color_discrete_sequence=['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5']
        )
        
        fig_donut.update_traces(
            textposition='outside',
            textinfo='label+percent',
            textfont_size=9,
            textfont_family="Poppins",
            hovertemplate='<b>%{label}</b><br>Pengguna: %{value} orang<br>Persentase: %{percent}<extra></extra>',
            pull=[0.05 if i == 0 else 0 for i in range(len(transport_counts))]
        )
        
        fig_donut.update_layout(
            height=240,
            margin=dict(t=40, b=5, l=5, r=40),
            showlegend=True,
            legend=dict(
                orientation="v", 
                yanchor="top", 
                y=0.8, 
                xanchor="left", 
                x=1.05,
                font=dict(family="Poppins", size=8)
            ),
            font=dict(family="Poppins", size=9),
            annotations=[dict(
                text=f'<b>{total_users}</b><br>Total<br>Pengguna', 
                x=0.5, y=0.5, 
                font=dict(size=11, family="Poppins"), 
                showarrow=False
            )],
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Komposisi Moda Transportasi",
                x=0.5,
                y=0.98,
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=13, color="#1e293b")
            )
        )
        
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    with col2:
        # Chart 2: Box Plot
        fig_box = px.box(
            df, 
            x='transportasi', 
            y='emisi_mingguan',
            color='transportasi',
            color_discrete_sequence=['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0']
        )
        
        fig_box.update_traces(
            hovertemplate='<b>%{x}</b><br>Emisi: %{y:.2f} kg CO₂<extra></extra>'
        )
        
        fig_box.update_layout(
            height=240,
            margin=dict(t=40, b=5, l=5, r=5),
            showlegend=False,
            xaxis_title="Moda Transportasi",
            yaxis_title="Emisi Mingguan (kg CO₂)",
            font=dict(family="Poppins", size=9),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Distribusi Emisi per Moda",
                x=0.5,
                y=0.98,
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=13, color="#1e293b")
            ),
            xaxis=dict(
                tickangle=45,
                tickfont=dict(family="Poppins", size=7)
            ),
            yaxis=dict(
                tickfont=dict(family="Poppins", size=8)
            )
        )
        
        st.plotly_chart(fig_box, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Secondary Charts
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Chart 3: Line Chart
        hari_cols = [c for c in df.columns if 'emisi_transportasi_' in c]
        
        if hari_cols:
            daily_emissions = df[hari_cols].sum().reset_index()
            daily_emissions.columns = ['Hari', 'Emisi']
            daily_emissions['Hari'] = daily_emissions['Hari'].str.replace('emisi_transportasi_', '').str.capitalize()
            
            day_map = {'Senin': 1, 'Selasa': 2, 'Rabu': 3, 'Kamis': 4, 'Jumat': 5, 'Sabtu': 6, 'Minggu': 7}
            daily_emissions['order'] = daily_emissions['Hari'].map(day_map)
            daily_emissions = daily_emissions.sort_values('order')
            
            fig_trend = px.line(
                daily_emissions, 
                x='Hari', 
                y='Emisi', 
                markers=True,
                color_discrete_sequence=['#059669']
            )
            
            fig_trend.update_traces(
                line=dict(width=3, shape='spline'),
                marker=dict(size=5, color='#10b981', line=dict(width=2, color='#059669')),
                hovertemplate='<b>%{x}</b><br>Total Emisi: %{y:.1f} kg CO₂<extra></extra>'
            )
            
            fig_trend.update_layout(
                height=180,
                margin=dict(t=35, b=5, l=5, r=5),
                xaxis_title="",
                yaxis_title="Emisi (kg CO₂)",
                hovermode='x unified',
                font=dict(family="Poppins", size=8),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Tren Emisi Harian",
                    x=0.5,
                    y=0.98,
                    xanchor='center',
                    yanchor='top',
                    font=dict(family="Poppins", size=12, color="#1e293b")
                ),
                xaxis=dict(
                    tickfont=dict(family="Poppins", size=7),
                    showgrid=False
                ),
                yaxis=dict(
                    tickfont=dict(family="Poppins", size=7),
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)'
                )
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data emisi harian tidak tersedia")

    with col2:
        # Chart 4: Parking Locations
        if 'lokasi_parkir' in df.columns:
            parking_data = df['lokasi_parkir'].value_counts().head(5)
            
            fig_parking = px.bar(
                x=parking_data.values,
                y=parking_data.index,
                orientation='h',
                color=parking_data.values,
                color_continuous_scale='Greens'
            )
            
            fig_parking.update_traces(
                hovertemplate='<b>%{y}</b><br>Pengguna: %{x} orang<extra></extra>',
                texttemplate='%{x}',
                textposition='inside',
                textfont=dict(family="Poppins", size=8, color="white")
            )
            
            fig_parking.update_layout(
                height=180,
                margin=dict(t=35, b=5, l=5, r=5),
                xaxis_title="Jumlah Pengguna",
                yaxis_title="",
                coloraxis_showscale=False,
                font=dict(family="Poppins", size=8),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title=dict(
                    text="Lokasi Parkir Populer",
                    x=0.5,
                    y=0.98,
                    xanchor='center',
                    yanchor='top',
                    font=dict(family="Poppins", size=12, color="#1e293b")
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
            
            st.plotly_chart(fig_parking, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data lokasi parkir tidak tersedia")

    with col3:
        # Chart 5: Scatter Plot
        stats = df.groupby('transportasi')['emisi_mingguan'].agg(['mean', 'count']).reset_index()
        stats.columns = ['transportasi', 'avg_emisi', 'frekuensi']
        
        fig_scatter = px.scatter(
            stats, 
            x='frekuensi', 
            y='avg_emisi',
            size='frekuensi',
            color='avg_emisi',
            color_continuous_scale='Greens',
            text='transportasi',
            size_max=35
        )
        
        fig_scatter.update_traces(
            textposition="top center",
            textfont=dict(size=7, family="Poppins"),
            hovertemplate='<b>%{text}</b><br>Pengguna: %{x} orang<br>Rata-rata Emisi: %{y:.2f} kg CO₂<extra></extra>'
        )
        
        fig_scatter.update_layout(
            height=180,
            margin=dict(t=35, b=5, l=5, r=5),
            xaxis_title="Jumlah Pengguna",
            yaxis_title="Rata-rata Emisi (kg CO₂)",
            coloraxis_showscale=False,
            font=dict(family="Poppins", size=8),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(
                text="Emisi vs Popularitas",
                x=0.5,
                y=0.98,
                xanchor='center',
                yanchor='top',
                font=dict(family="Poppins", size=12, color="#1e293b")
            ),
            xaxis=dict(
                tickfont=dict(family="Poppins", size=7),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                tickfont=dict(family="Poppins", size=7),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            )
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    show()