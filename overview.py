import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

@st.cache_data(ttl=60)
def load_data():
    """Load data from multiple Google Sheets tabs"""
    base_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid="
    
    try:
        return {
            "responden": pd.read_csv(base_url + "1606042726"),
            "transport": pd.read_csv(base_url + "155140281"),
            "electronic": pd.read_csv(base_url + "622151341"),
            "food": pd.read_csv(base_url + "994176057"),
            "daily": pd.read_csv(base_url + "1749257811")
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_metric_card(title, value, unit, icon, color_class="primary"):
    """Create a metric card with custom styling"""
    return f"""
    <div class="kpi-card {color_class}"">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{title} ({unit})</div>
    </div>
    """

def show():
    # Page Header
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Overview</h1>
        <p class="page-subtitle">lorem ipsum</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    data = load_data()
    if not data:
        st.error("Failed to load data. Please check your connection and try again.")
        return

    # Extract data
    df_responden = data["responden"]
    df_transport = data["transport"]
    df_electronic = data["electronic"]
    df_food = data["food"]
    df_daily = data["daily"]

    # Data processing
    df_transport["emisi_mingguan"] = pd.to_numeric(df_transport["emisi_mingguan"], errors='coerce')
    df_electronic["emisi_elektronik_mingguan"] = pd.to_numeric(df_electronic["emisi_elektronik_mingguan"], errors='coerce')
    df_food["emisi_makanminum_mingguan"] = pd.to_numeric(df_food["emisi_makanminum_mingguan"], errors='coerce')

    # Calculate totals
    total_emisi_transport = df_transport["emisi_mingguan"].sum()
    total_emisi_electronic = df_electronic["emisi_elektronik_mingguan"].sum()
    total_emisi_food = df_food["emisi_makanminum_mingguan"].sum()
    total_emisi = total_emisi_transport + total_emisi_electronic + total_emisi_food
    avg_emisi_per_mahasiswa = total_emisi / len(df_responden) if len(df_responden) > 0 else 0

    # KPI Section
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(create_metric_card("Total Emisi", f"{total_emisi:.1f}", "g CO₂", "🌍", "primary"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card("Rata-rata per Mahasiswa", f"{avg_emisi_per_mahasiswa:.1f}", "g CO₂", "👤", "secondary"), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card("Total Responden", f"{len(df_responden)}", "orang", "👥", "tertiary"), unsafe_allow_html=True)
    
    with col4:
        transport_pct = (total_emisi_transport / total_emisi * 100) if total_emisi > 0 else 0
        st.markdown(create_metric_card("Dominasi Transport", f"{transport_pct:.1f}", "%", "🚗", "quaternary"), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Main Charts Section
    st.markdown('<div class="charts-section">', unsafe_allow_html=True)
    
    # Row 1: Emission Distribution & Weekly Trend
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Distribusi Emisi per Kategori</div>', unsafe_allow_html=True)
        
        # Create pie chart for emission distribution
        distribusi_data = pd.DataFrame({
            "Kategori": ["Transportasi", "Elektronik", "Makanan & Minuman"],
            "Emisi": [total_emisi_transport, total_emisi_electronic, total_emisi_food],
            "Persentase": [
                total_emisi_transport/total_emisi*100 if total_emisi > 0 else 0,
                total_emisi_electronic/total_emisi*100 if total_emisi > 0 else 0,
                total_emisi_food/total_emisi*100 if total_emisi > 0 else 0
            ]
        })
        
        fig_pie = px.pie(
            distribusi_data, 
            names="Kategori", 
            values="Emisi",
            color_discrete_sequence=['#059669', '#10b981', '#34d399'],
            hole=0.4
        )
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=11,
            hovertemplate='<b>%{label}</b><br>Emisi: %{value:.1f} g CO₂<br>Persentase: %{percent}<extra></extra>'
        )
        fig_pie.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            font=dict(size=12)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Tren Aktivitas Mingguan</div>', unsafe_allow_html=True)
        
        # Create weekly activity trend
        if not df_daily.empty and 'hari' in df_daily.columns:
            harian = df_daily.groupby("hari")["kegiatan"].count().reset_index()
            harian.columns = ["Hari", "Jumlah_Aktivitas"]
            
            # Ensure proper day order
            day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            harian['Hari'] = pd.Categorical(harian['Hari'], categories=day_order, ordered=True)
            harian = harian.sort_values('Hari')
            
            fig_line = px.line(
                harian, 
                x="Hari", 
                y="Jumlah_Aktivitas", 
                markers=True,
                color_discrete_sequence=['#059669']
            )
            fig_line.update_traces(
                line=dict(width=4),
                marker=dict(size=8, color='#10b981', line=dict(width=2, color='#059669'))
            )
            fig_line.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="Hari",
                yaxis_title="Jumlah Aktivitas",
                hovermode='x unified'
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Data aktivitas harian tidak tersedia")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Row 2: Transportation Analysis & Top Locations
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Analisis Moda Transportasi</div>', unsafe_allow_html=True)
        
        if not df_transport.empty and 'transportasi' in df_transport.columns:
            transport_counts = df_transport['transportasi'].value_counts().head(6)
            
            fig_bar = px.bar(
                x=transport_counts.values,
                y=transport_counts.index,
                orientation='h',
                color=transport_counts.values,
                color_continuous_scale=['#d1fae5', '#059669']
            )
            fig_bar.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="Jumlah Pengguna",
                yaxis_title="Moda Transportasi",
                coloraxis_showscale=False
            )
            fig_bar.update_traces(
                hovertemplate='<b>%{y}</b><br>Pengguna: %{x} orang<extra></extra>'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Data transportasi tidak tersedia")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Lokasi Kampus Teraktif</div>', unsafe_allow_html=True)
        
        if not df_daily.empty and 'lokasi' in df_daily.columns:
            lokasi_counts = df_daily["lokasi"].value_counts().head(8)
            
            fig_locations = px.bar(
                x=lokasi_counts.index,
                y=lokasi_counts.values,
                color=lokasi_counts.values,
                color_continuous_scale=['#ecfdf5', '#059669']
            )
            fig_locations.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="Lokasi",
                yaxis_title="Frekuensi Aktivitas",
                coloraxis_showscale=False
            )
            fig_locations.update_xaxes(tickangle=45)
            fig_locations.update_traces(
                hovertemplate='<b>%{x}</b><br>Aktivitas: %{y} kali<extra></extra>'
            )
            st.plotly_chart(fig_locations, use_container_width=True)
        else:
            st.info("Data lokasi tidak tersedia")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Row 3: Heatmap and Program Study Analysis
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Heatmap Aktivitas Lokasi × Hari</div>', unsafe_allow_html=True)
        
        if not df_daily.empty and 'hari' in df_daily.columns and 'lokasi' in df_daily.columns:
            # Create heatmap data
            heatmap_data = df_daily.groupby(["hari", "lokasi"]).size().reset_index(name="Jumlah")
            
            if not heatmap_data.empty:
                # Get top locations for better visualization
                top_locations = df_daily["lokasi"].value_counts().head(10).index
                heatmap_filtered = heatmap_data[heatmap_data["lokasi"].isin(top_locations)]
                
                heatmap_pivot = heatmap_filtered.pivot(index="lokasi", columns="hari", values="Jumlah").fillna(0)
                
                # Reorder columns to proper day order
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                heatmap_pivot = heatmap_pivot.reindex(columns=[day for day in day_order if day in heatmap_pivot.columns])
                
                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="Hari", y="Lokasi", color="Jumlah Aktivitas"),
                    color_continuous_scale='Greens',
                    aspect="auto"
                )
                fig_heatmap.update_layout(
                    height=350,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("Data tidak cukup untuk membuat heatmap")
        else:
            st.info("Data heatmap tidak tersedia")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Sebaran Program Studi</div>', unsafe_allow_html=True)
        
        if not df_responden.empty and 'prodi' in df_responden.columns:
            prodi_counts = df_responden['prodi'].value_counts().head(8)
            
            fig_prodi = px.pie(
                names=prodi_counts.index,
                values=prodi_counts.values,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            fig_prodi.update_traces(
                textposition='inside',
                textinfo='percent',
                textfont_size=10,
                hovertemplate='<b>%{label}</b><br>Mahasiswa: %{value} orang<br>Persentase: %{percent}<extra></extra>'
            )
            fig_prodi.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
            )
            st.plotly_chart(fig_prodi, use_container_width=True)
        else:
            st.info("Data program studi tidak tersedia")
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Summary Section
    st.markdown("""
    <div class="chart-card" style="margin-top: 2rem;">
        <div class="chart-title">Key Insights</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem;">
            <div style="padding: 1rem; background: rgba(5, 150, 105, 0.05); border-radius: 12px; border-left: 4px solid #059669;">
                <h4 style="color: #059669; margin-bottom: 0.5rem;">Transportasi</h4>
                <p style="color: #374151; margin: 0;">Kontribusi terbesar terhadap emisi karbon kampus dengan dominasi kendaraan bermotor pribadi.</p>
            </div>
            <div style="padding: 1rem; background: rgba(59, 130, 246, 0.05); border-radius: 12px; border-left: 4px solid #3b82f6;">
                <h4 style="color: #3b82f6; margin-bottom: 0.5rem;">Elektronik</h4>
                <p style="color: #374151; margin: 0;">Penggunaan perangkat elektronik berkontribusi signifikan pada konsumsi energi kampus.</p>
            </div>
            <div style="padding: 1rem; background: rgba(245, 158, 11, 0.05); border-radius: 12px; border-left: 4px solid #f59e0b;">
                <h4 style="color: #f59e0b; margin-bottom: 0.5rem;">Konsumsi</h4>
                <p style="color: #374151; margin: 0;">Pola konsumsi makanan dan minuman menunjukkan potensi pengurangan emisi melalui pilihan berkelanjutan.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show()