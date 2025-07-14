import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
from src.utils.db_connector import run_sql
from io import BytesIO
from xhtml2pdf import pisa

# KONFIGURASI DAN PALET WARNA


MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']
TRANSPORT_COLORS = { 'Sepeda': '#66c2a5', 'Jalan kaki': '#abdda4', 'Bike': '#66c2a5', 'Walk': '#abdda4', 'Bus': '#3288bd', 'Kereta': '#5e4fa2', 'Angkot': '#66c2a5', 'Angkutan Umum': '#3288bd', 'Ojek Online': '#5e4fa2', 'TransJakarta': '#3288bd', 'Motor': '#fdae61', 'Sepeda Motor': '#f46d43', 'Motorcycle': '#fdae61', 'Ojek': '#f46d43', 'Mobil': '#d53e4f', 'Mobil Pribadi': '#9e0142', 'Car': '#d53e4f', 'Taksi': '#9e0142', 'Taxi': '#9e0142' }
MODEBAR_CONFIG = { 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': [ 'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d' ], 'toImageButtonOptions': { 'format': 'png', 'filename': 'carbon_emission_chart', 'height': 600, 'width': 800, 'scale': 2 } }


# FUNGSI-FUNGSI QUERY SQL


@st.cache_data(ttl=3600)
def build_transport_where_clause(selected_modes, selected_fakultas, selected_days):
    """Membangun klausa WHERE SQL secara dinamis dan aman, termasuk filter hari."""
    clauses = []
    join_needed = bool(selected_fakultas)
    
    if selected_modes:
        modes_str = ", ".join([f"'{mode}'" for mode in selected_modes])
        clauses.append(f"t.transportasi IN ({modes_str})")
    if selected_fakultas:
        fakultas_str = ", ".join([f"'{f}'" for f in selected_fakultas])
        clauses.append(f"r.fakultas IN ({fakultas_str})")
    if selected_days:
        day_patterns = [f"'%{day}%'" for day in selected_days]
        clauses.append(f"t.hari_datang ILIKE ANY (ARRAY[{', '.join(day_patterns)}])")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where_sql, join_needed

@st.cache_data(ttl=3600)
def get_filtered_raw_data(where_clause, join_needed):
    """Query untuk mengambil data mentah sesuai filter untuk di-download."""
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT 
        t.*,
        COALESCE(r.fakultas, 'N/A') as fakultas,
        COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0) * t.emisi_transportasi as emisi_mingguan
    FROM transportasi t
    LEFT JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa
    {where_clause}
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_daily_trend_data(where_clause, join_needed):
    """Query data untuk chart Tren Emisi Harian."""
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT 
        TRIM(unnest(string_to_array(t.hari_datang, ','))) AS hari,
        SUM(t.emisi_transportasi) AS emisi
    FROM transportasi t
    {join_sql}
    {where_clause}
    GROUP BY hari
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_faculty_data(where_clause):
    """Query data untuk chart Emisi per Fakultas."""
    query = f"""
    SELECT
        r.fakultas,
        SUM(COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0) * t.emisi_transportasi) AS total_emisi,
        COUNT(DISTINCT t.id_mahasiswa) as count
    FROM transportasi t
    JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa
    {where_clause}
    GROUP BY r.fakultas
    ORDER BY total_emisi ASC
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_transport_composition_data(where_clause, join_needed):
    """Query data untuk chart Komposisi Moda."""
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT
        t.transportasi,
        COUNT(DISTINCT t.id_mahasiswa) as total_users,
        SUM(COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0) * t.emisi_transportasi) as total_emisi
    FROM transportasi t
    {join_sql}
    {where_clause}
    GROUP BY t.transportasi
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_heatmap_data(where_clause, join_needed):
    """Query data untuk Heatmap."""
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT 
        TRIM(unnest(string_to_array(t.hari_datang, ','))) AS hari,
        t.transportasi,
        COUNT(t.id_mahasiswa) as pengguna
    FROM transportasi t
    {join_sql}
    {where_clause}
    GROUP BY hari, t.transportasi
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_kecamatan_data(where_clause, join_needed):
    """Query data untuk chart Emisi per Kecamatan."""
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT
        t.kecamatan,
        AVG(COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0) * t.emisi_transportasi) as rata_rata_emisi,
        COUNT(DISTINCT t.id_mahasiswa) as jumlah_mahasiswa,
        SUM(COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0) * t.emisi_transportasi) as total_emisi
    FROM transportasi t
    {join_sql}
    {where_clause}
    {'AND' if where_clause else 'WHERE'} t.kecamatan IS NOT NULL AND t.kecamatan <> ''
    GROUP BY t.kecamatan
    ORDER BY jumlah_mahasiswa DESC
    LIMIT 8
    """
    return run_sql(query)
    

@st.cache_data(ttl=3600)
@loading_decorator()
def generate_pdf_report(where_clause, join_needed):
    from datetime import datetime
    time.sleep(0.6)

    df_daily = get_daily_trend_data(where_clause, join_needed)
    df_faculty = get_faculty_data(where_clause)
    df_composition = get_transport_composition_data(where_clause, join_needed)
    df_heatmap = get_heatmap_data(where_clause, join_needed)
    df_kecamatan = get_kecamatan_data(where_clause, join_needed)
    
    # Inisialisasi metrik utama dan default HTML untuk tabel/kesimpulan
    total_emisi = df_composition['total_emisi'].sum() if 'total_emisi' in df_composition.columns and not df_composition.empty else 0
    total_users = df_composition['total_users'].sum() if 'total_users' in df_composition.columns and not df_composition.empty else 0
    avg_emisi = total_emisi / total_users if total_users > 0 else 0
    
    # Fallback HTML jika tidak ada data sama sekali
    if df_composition.empty or df_composition['total_emisi'].sum() == 0:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"

    # --- Default Text & HTML for Sections ---
    daily_trend_table_html, trend_conclusion, trend_recommendation = ("<tr><td colspan='2'>Data tidak tersedia.</td></tr>", "Pola mobilitas mingguan belum dapat dipetakan.", "Data tidak cukup untuk analisis tren.")
    fakultas_table_html, fakultas_conclusion, fakultas_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Profil emisi per fakultas tidak dapat dibuat.", "Data tidak cukup untuk analisis fakultas.")
    mode_table_html, mode_conclusion, mode_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Preferensi moda transportasi tidak dapat dianalisis.", "Data tidak cukup untuk analisis moda.")
    heatmap_header_html, heatmap_body_html, heatmap_conclusion, heatmap_recommendation = ("<tr><th>-</th></tr>", "<tr><td>Data tidak tersedia.</td></tr>", "Pola perilaku harian belum teridentifikasi.", "Data tidak cukup untuk analisis heatmap.")
    kecamatan_table_html, kecamatan_conclusion, rec_kecamatan = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Hotspot geografis belum dapat diidentifikasi.", "Data tidak cukup untuk analisis kecamatan.")

    # --- Pembuatan Insight Dinamis ---
    
    # 1. Ritme Mobilitas Mingguan
    if not df_daily.empty and df_daily['emisi'].sum() > 0:
        daily_df_sorted = df_daily.sort_values(by='emisi', ascending=False)
        daily_trend_table_html = "".join([f"<tr><td>{row['hari']}</td><td style='text-align:right;'>{row['emisi']:.1f}</td></tr>" for _, row in daily_df_sorted.iterrows()])
        peak_day = daily_df_sorted.iloc[0]['hari']
        trend_conclusion = f"Puncak mobilitas terjadi pada hari <strong>{peak_day}</strong>, menunjukkan bahwa mayoritas perjalanan terkait aktivitas akademik dan operasional kampus."
        trend_recommendation = f"Fokuskan kebijakan transportasi pada hari kerja. Kaji kemungkinan penerapan 'flexible working/studying day' untuk mengurangi emisi puncak."

    # 2. Profil Demografi Spasial (Fakultas)
    if not df_faculty.empty and df_faculty['total_emisi'].sum() > 0 and 'count' in df_faculty.columns and df_faculty['count'].sum() > 0:
        df_faculty['avg_emisi'] = df_faculty['total_emisi'] / df_faculty['count']
        df_faculty_sorted = df_faculty.sort_values('avg_emisi', ascending=False)
        fakultas_table_html = "".join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['avg_emisi']:.2f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for _, row in df_faculty_sorted.head(10).iterrows()])
        
        if len(df_faculty_sorted) > 1:
            highest_fakultas = df_faculty_sorted.iloc[0]['fakultas']
            fakultas_conclusion = f"Mahasiswa dari fakultas <strong>{highest_fakultas}</strong> memiliki jejak karbon transportasi tertinggi, mengindikasikan kemungkinan komunitasnya tinggal lebih jauh atau lebih bergantung pada kendaraan pribadi."
            fakultas_recommendation = f"Terapkan intervensi berbasis lokasi. Prioritaskan perbaikan fasilitas parkir sepeda dan shelter 'drop-off' di sekitar gedung fakultas <strong>{highest_fakultas}</strong>."
        else: # Only one faculty or very few
            fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{df_faculty_sorted.iloc[0]['fakultas']}</strong>. Perbandingan dengan fakultas lain tidak dapat dilakukan."
            fakultas_recommendation = "Perluas filter fakultas untuk mendapatkan perbandingan yang lebih komprehensif."


    # 3. Preferensi Moda Transportasi
    if not df_composition.empty and df_composition['total_users'].sum() > 0:
        df_comp_sorted = df_composition.sort_values('total_users', ascending=False)
        df_comp_sorted['avg_emisi_per_user'] = df_comp_sorted['total_emisi'] / df_comp_sorted['total_users']
        mode_table_html = "".join([f"<tr><td>{row['transportasi']}</td><td style='text-align:center;'>{int(row['total_users'])}</td><td style='text-align:right;'>{row['avg_emisi_per_user']:.2f}</td></tr>" for _, row in df_comp_sorted.iterrows()])
        
        if len(df_comp_sorted) > 0: # Ensure there's at least one mode
            dominant_mode = df_comp_sorted.iloc[0]['transportasi']
            mode_conclusion = f"<strong>{dominant_mode}</strong> adalah moda pilihan utama, mencerminkan infrastruktur dan kondisi eksisting."
            mode_recommendation = "Tingkatkan 'user experience' untuk moda ramah lingkungan (tambah unit bike sharing) atau terapkan kebijakan 'mode shifting' (misal: zona rendah emisi) untuk mengurangi ketergantungan pada kendaraan pribadi."
        else:
            mode_conclusion = "Tidak ada data moda transportasi untuk analisis."
            mode_recommendation = "Pastikan data transportasi dikumpulkan dengan benar."


    # 4. Analisis Pola Perilaku Harian
    if not df_heatmap.empty and df_heatmap['pengguna'].sum() > 0: # Check if there are actual 'pengguna' counts
        pivot_df = df_heatmap.pivot_table(index='hari', columns='transportasi', values='pengguna', aggfunc='sum').fillna(0)
        day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        pivot_df = pivot_df.reindex(index=day_order, fill_value=0)
        
        top_modes = pivot_df.sum(axis=0).nlargest(6).index # Get top 6 modes by total usage for the heatmap table
        pivot_df_filtered = pivot_df[top_modes] # Filter the pivot table to only include these top modes

        if not pivot_df_filtered.empty and pivot_df_filtered.sum().sum() > 0: # Check if there's any data left after filtering modes
            header_cells_html = "<th>Hari</th>" + "".join([f"<th>{mode}</th>" for mode in pivot_df_filtered.columns])
            heatmap_header_html = f"<tr>{header_cells_html}</tr>"
            body_rows_list = [f"<tr><td><strong>{day}</strong></td>" + "".join([f"<td style='text-align:center;'>{int(count)}</td>" for count in row]) + "</tr>" for day, row in pivot_df_filtered.iterrows()]
            heatmap_body_html = "".join(body_rows_list)
            
            # Find peak usage
            peak_usage_day = pivot_df_filtered.sum(axis=1).idxmax() # Day with max total usage
            peak_usage_mode = pivot_df_filtered.loc[peak_usage_day].idxmax() # Mode with max usage on that day
            
            heatmap_conclusion = f"Teridentifikasi sebuah kebiasaan kuat (strong habit): penggunaan <strong>{peak_usage_mode}</strong> secara masif pada hari <strong>{peak_usage_day}</strong>."
            heatmap_recommendation = f"Fokus pada intervensi perilaku. Usulkan 'Tantangan {peak_usage_day} Hijau': ajak komunitas untuk tidak menggunakan {peak_usage_mode} dan berbagi pengalaman di media sosial."
        else: # No meaningful data for heatmap after filtering/reindexing
            heatmap_conclusion = "Pola perilaku harian belum teridentifikasi. Data tidak cukup atau moda transportasi/hari tidak relevan."
            heatmap_recommendation = "Perluas filter moda transportasi atau hari untuk analisis pola perilaku."


    # 5. Hotspot Geografis Asal Perjalanan
    if not df_kecamatan.empty and df_kecamatan['total_emisi'].sum() > 0:
        kecamatan_stats_sorted = df_kecamatan.sort_values('total_emisi', ascending=False)
        kecamatan_table_html = "".join([f"<tr><td>{row['kecamatan']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td><td style='text-align:center;'>{int(row['jumlah_mahasiswa'])}</td></tr>" for _, row in kecamatan_stats_sorted.iterrows()])
        
        if len(kecamatan_stats_sorted) > 0: # Check if there's at least one kecamatan
            hottest_spot = kecamatan_stats_sorted.iloc[0]['kecamatan']
            kecamatan_conclusion = f"Kecamatan <strong>{hottest_spot}</strong> merupakan 'feeder' utama komuter ke kampus dan sumber emisi terbesar. Ini adalah titik intervensi paling strategis di luar kampus."
            rec_kecamatan = f"Gunakan data ini sebagai dasar proposal ke Dishub untuk optimalisasi rute angkutan umum dari <strong>{hottest_spot}</strong>, atau jadikan titik jemput utama untuk layanan shuttle kampus."
        else:
            kecamatan_conclusion = "Tidak ada data kecamatan untuk analisis."
            rec_kecamatan = "Pastikan data kecamatan dikumpulkan dengan benar."


    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Transportasi</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Poppins', sans-serif; color: #333; line-height: 1.6; font-size: 11px; }}
        .page {{ padding: 25px; max-width: 800px; margin: auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #059669; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ color: #059669; margin: 0; }} h2 {{ color: #065f46; border-bottom: 1px solid #d1fae5; padding-bottom: 8px; margin-top: 30px; margin-bottom: 15px;}}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
        .card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .card.primary {{ border-left: 4px solid #10b981; }} .card.primary strong {{ color: #059669; }}
        .card.secondary {{ border-left: 4px solid #3b82f6; }} .card.secondary strong {{ color: #3b82f6; }}
        .card strong {{ font-size: 1.5em; display: block; }}
        .conclusion, .recommendation {{ padding: 12px 15px; margin-top: 10px; border-radius: 6px; }}
        .conclusion {{ background: #f0fdf4; border-left: 4px solid #10b981; }}
        .recommendation {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        ul {{ padding-left: 20px; margin-top: 8px; margin-bottom: 0; }} li {{ margin-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th, td {{ padding: 8px; text-align: left; border: 1px solid #e5e7eb; }}
        th {{ background-color: #f3f4f6; font-weight: 600; text-align: center; }}
        td:first-child {{ font-weight: 500; }}
    </style></head>
    <body><div class="page">
        <div class="header"><h1>Laporan Emisi Transportasi</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO<sub>2</sub></strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO<sub>2</sub></strong>Rata-rata/Mahasiswa</div>
        </div>
        <h2>1. Ritme Mobilitas Mingguan</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        <h2>2. Profil Demografi Spasial (Fakultas)</h2>
        <table><thead><tr><th>Fakultas</th><th>Rata-rata Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Responden</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        <h2>3. Preferensi Moda Transportasi</h2>
        <table><thead><tr><th>Moda Transportasi</th><th>Jumlah Pengguna</th><th>Rata-rata Emisi/Pengguna (kg CO<sub>2</sub>)</th></tr></thead><tbody>{mode_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {mode_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {mode_recommendation}</div>
        <h2>4. Analisis Pola Perilaku Harian</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>
        <h2>5. Hotspot Geografis Asal Perjalanan</h2>
        <table><thead><tr><th>Kecamatan</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Responden</th></tr></thead><tbody>{kecamatan_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {kecamatan_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {rec_kecamatan}</div>
    </div></body></html>
    """
    
    # --- BAGIAN KONVERSI KE PDF ---
    pdf_buffer = BytesIO()

    pisa_status = pisa.CreatePDF(
        src=html_content,    # String HTML Anda
        dest=pdf_buffer)     # Tujuan output adalah buffer bytes

    if pisa_status.err:
        st.error(f"Error during PDF conversion: {pisa_status.err}. Check HTML format or xhtml2pdf installation.")
        return None # Mengembalikan None jika ada error

    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    # Mengembalikan bytes PDF
    return pdf_bytes


# FUNGSI UTAMA (SHOW)


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
            <h1 class="header-title">Emisi Transportasi</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(0.25)
    
    # --- BAGIAN FILTER ---
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])
    with filter_col1:
        day_options = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        selected_days = st.multiselect("Hari:", options=day_options, placeholder="Pilih Opsi", key='transport_day_filter')
    
    with filter_col2:
        transport_modes_df = run_sql("SELECT DISTINCT transportasi FROM transportasi WHERE transportasi IS NOT NULL ORDER BY transportasi")
        available_modes = transport_modes_df['transportasi'].tolist() if not transport_modes_df.empty else []
        selected_modes = st.multiselect("Moda Transportasi:", options=available_modes, placeholder="Pilih Opsi", key='transport_mode_filter')
    
    with filter_col3:
        fakultas_df = run_sql("SELECT DISTINCT fakultas FROM v_informasi_fakultas_mahasiswa WHERE fakultas IS NOT NULL AND fakultas <> '' ORDER BY fakultas")
        available_fakultas = fakultas_df['fakultas'].tolist() if not fakultas_df.empty else []
        selected_fakultas = st.multiselect("Fakultas:", options=available_fakultas, placeholder="Pilih Opsi", key='transport_fakultas_filter')

    # Bangun klausa WHERE dari filter
    where_clause, join_needed = build_transport_where_clause(selected_modes, selected_fakultas, selected_days)
    
    # --- TOMBOL EXPORT (DIPERBAIKI) ---
    with export_col1:
        raw_data_df = get_filtered_raw_data(where_clause, join_needed)
        st.download_button(
            "Raw Data", 
            data=raw_data_df.to_csv(index=False), 
            file_name=f"transport_data_{len(raw_data_df)}.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=(raw_data_df.empty)
        )

    with export_col2:
        try:
            pdf_data = generate_pdf_report(where_clause, join_needed)
            
            if pdf_data:
                st.download_button(
                    label="Laporan",
                    data=pdf_data,
                    file_name=f"transport_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf", 
                    use_container_width=True,
                    key="transport_export_pdf"
                )
            else: 
                st.error("Gagal menyiapkan laporan PDF.")
        except Exception as e:
            st.error(f"Gagal membuat laporan: {e}")

    # --- BAGIAN VISUALISASI ---
    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            daily_df = get_daily_trend_data(where_clause, join_needed)
            if not daily_df.empty and daily_df['emisi'].sum() > 0:
                # Filter hari sekarang tidak dibutuhkan di sini, tapi kita lakukan untuk visualisasi saja
                if selected_days: 
                    daily_df_display = daily_df[daily_df['hari'].str.strip().isin(selected_days)]
                else:
                    daily_df_display = daily_df
                
                if not daily_df_display.empty:
                    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                    daily_df_display['order'] = pd.Categorical(daily_df_display['hari'].str.strip(), categories=day_order, ordered=True)
                    daily_df_display = daily_df_display.sort_values('order')
                    
                    fig_trend = go.Figure(go.Scatter(
                        x=daily_df_display['hari'], 
                        y=daily_df_display['emisi'], 
                        fill='tonexty', mode='lines+markers', 
                        line=dict(color='#3288bd', width=2, shape='spline'), 
                        marker=dict(size=6, color='#3288bd'), 
                        fillcolor="rgba(102, 194, 165, 0.3)", 
                        hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>', 
                        showlegend=False))
                    fig_trend.update_layout(
                        height=270, 
                        margin=dict(t=30, b=0, l=0, r=10), 
                        title=dict(text="<b>Tren Emisi Harian</b>", 
                                   x=0.38, 
                                   y=0.95, 
                                   font=dict(size=12)))
                    st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data tren untuk filter ini.")

        with col2:
            fakultas_stats = get_faculty_data(where_clause)
            if not fakultas_stats.empty and fakultas_stats['total_emisi'].sum() > 0:
                fig_fakultas = go.Figure()
                fakultas_stats_display = fakultas_stats.sort_values('total_emisi', ascending=True).tail(13)
                max_emisi, min_emisi = fakultas_stats_display['total_emisi'].max(), fakultas_stats_display['total_emisi'].min()
                for i, (_, row) in enumerate(fakultas_stats_display.iterrows()):
                    color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    color = color_palette[int(ratio * (len(color_palette) - 1))]
                    fig_fakultas.add_trace(go.Bar(
                        x=[row['total_emisi']], 
                        y=[row['fakultas']], 
                        orientation='h', 
                        marker=dict(color=color), 
                        showlegend=False, 
                        text=[f"{row['total_emisi']:.1f}"], 
                        textposition='inside', 
                        textfont=dict(color='white'), 
                        hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["count"]}<extra></extra>'))
                fig_fakultas.update_layout(
                    height=270, 
                    margin=dict(t=30, b=0, l=0, r=20), 
                    title=dict(text="<b>Emisi per Fakultas</b>", 
                               x=0.4, 
                               y=0.95, 
                               font=dict(size=12)))
                st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data fakultas untuk filter ini.")

        with col3:
            transport_data = get_transport_composition_data(where_clause, join_needed)
            if not transport_data.empty:
                colors = [TRANSPORT_COLORS.get(mode, MAIN_PALETTE[i % len(MAIN_PALETTE)]) for i, mode in enumerate(transport_data['transportasi'])]
                fig_donut = go.Figure(data=[go.Pie(
                    labels=transport_data['transportasi'], 
                    values=transport_data['total_users'], 
                    hole=0.45, marker=dict(colors=colors), 
                    textposition='outside', 
                    textinfo='label+percent', 
                    hovertemplate='<b>%{label}</b><br>%{value} pengguna (%{percent})<extra></extra>')])
                total_emisi_chart = transport_data['total_emisi'].sum()
                center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                fig_donut.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                fig_donut.update_layout(
                    height=270, 
                    margin=dict(t=30, b=5, l=5, r=5), 
                    showlegend=False, 
                    title=dict(text="<b>Proporsi Moda Transportasi</b>", 
                               x=0.3, 
                               y=0.95, 
                               font=dict(size=12)))
                st.plotly_chart(fig_donut, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data komposisi untuk filter ini.")
    
    with loading():
        col1, col2 = st.columns([1, 1])
        with col1:
            heatmap_df = get_heatmap_data(where_clause, join_needed)
            if not heatmap_df.empty:
                pivot_df = heatmap_df.pivot_table(index='hari', columns='transportasi', values='pengguna', aggfunc='sum').fillna(0)
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                pivot_df = pivot_df.reindex(index=day_order, fill_value=0)
                top_modes = pivot_df.sum(axis=0).nlargest(6).index
                pivot_df_filtered = pivot_df[top_modes]
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=pivot_df_filtered.values,
                    x=pivot_df_filtered.columns,
                    y=pivot_df_filtered.index,   
                    colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                    hoverongaps=False,
                    hovertemplate='<b>%{x}</b><br>%{y}: %{z} pengguna<extra></extra>',
                    xgap=1,  
                    ygap=1,  
                        colorbar=dict(
                        title=dict(text="Pengguna", font=dict(size=9)),
                        tickfont=dict(size=10),
                        thickness=15,
                        len=0.7
                    )
                ))
                fig_heatmap.update_layout(
                    height=270, 
                    margin=dict(t=30, b=0, l=0, r=0), 
                    title=dict(text="<b>Heatmap Penggunaan Moda per Hari</b>", 
                               x=0.3, 
                               y=0.95, 
                               font=dict(size=12)))
                st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data heatmap untuk filter ini.")
        
        with col2:
            kecamatan_df = get_kecamatan_data(where_clause, join_needed)
            if not kecamatan_df.empty:
                kecamatan_df = kecamatan_df.sort_values('rata_rata_emisi', ascending=False)
                fig_kecamatan = go.Figure()
                max_emisi, min_emisi = kecamatan_df['rata_rata_emisi'].max(), kecamatan_df['rata_rata_emisi'].min()
                for i, (_, row) in enumerate(kecamatan_df.iterrows()):
                    sequential_warm = ['#fee08b', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    ratio = (row['rata_rata_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    color = sequential_warm[int(ratio * (len(sequential_warm) - 1))]
                    display_name = row['kecamatan'] if len(row['kecamatan']) <= 10 else row['kecamatan'][:8] + '..'
                    fig_kecamatan.add_trace(go.Bar(
                        x=[display_name], 
                        y=[row['rata_rata_emisi']], 
                        marker=dict(color=color), 
                        showlegend=False, text=[f"{row['rata_rata_emisi']:.1f}"], 
                        textposition='inside', 
                        textfont=dict(color='#2d3748', weight='bold'), 
                        hovertemplate=f'<b>{row["kecamatan"]}</b><br>Rata-rata: {row["rata_rata_emisi"]:.1f} kg CO₂<br>Mahasiswa: {row["jumlah_mahasiswa"]}<extra></extra>', 
                        name=row['kecamatan']))
                avg_emisi_kec = kecamatan_df['rata_rata_emisi'].mean()
                fig_kecamatan.add_hline(
                    y=avg_emisi_kec, 
                    line_dash="dash", 
                    line_color="#5e4fa2", 
                    line_width=2, 
                    annotation_text=f"Rata-rata: {avg_emisi_kec:.1f}")
                fig_kecamatan.update_layout(
                    height=270, 
                    margin=dict(t=30, b=0, l=0, r=10), 
                    title=dict(text="<b>Emisi per Kecamatan</b>", 
                               x=0.4, y=0.95, font=dict(size=12)))
                st.plotly_chart(fig_kecamatan, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data kecamatan untuk filter ini.")

if __name__ == "__main__":
    show()