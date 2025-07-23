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

MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']
TRANSPORT_COLORS = { 'Sepeda': '#66c2a5', 'Jalan kaki': '#abdda4', 'Bike': '#66c2a5', 'Walk': '#abdda4', 'Bus': '#3288bd', 'Kereta': '#5e4fa2', 'Angkot': '#66c2a5', 'Angkutan Umum': '#3288bd', 'Ojek Online': '#5e4fa2', 'TransJakarta': '#3288bd', 'Motor': '#fdae61', 'Sepeda Motor': '#f46d43', 'Motorcycle': '#fdae61', 'Ojek': '#f46d43', 'Mobil': '#d53e4f', 'Mobil Pribadi': '#9e0142', 'Car': '#d53e4f', 'Taksi': '#9e0142', 'Taxi': '#9e0142' }
MODEBAR_CONFIG = { 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': [ 'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d' ], 'toImageButtonOptions': { 'format': 'png', 'filename': 'carbon_emission_chart', 'height': 600, 'width': 800, 'scale': 2 } }
DAY_ORDER = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

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
def get_filtered_data(where_clause, join_needed):
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
    import time 
    
    time.sleep(0.6) 
    df_daily = get_daily_trend_data(where_clause, join_needed)
    df_faculty = get_faculty_data(where_clause) 
    df_composition = get_transport_composition_data(where_clause, join_needed) 
    df_heatmap = get_heatmap_data(where_clause, join_needed) 
    df_kecamatan = get_kecamatan_data(where_clause, join_needed) 
    
    # KPI Calculation for PDF
    total_emisi = df_composition['total_emisi'].sum() if 'total_emisi' in df_composition.columns and not df_composition.empty else 0
    
    unique_students_in_filtered_data = 0
    if not df_composition.empty and 'total_users' in df_composition.columns: # Menggunakan total_users
        try:
            unique_students_query_result = run_sql(f"""
                SELECT COUNT(DISTINCT t.id_mahasiswa) as count FROM transportasi t
                LEFT JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa
                {where_clause}
            """)
            if not unique_students_query_result.empty and 'count' in unique_students_query_result.columns:
                unique_students_in_filtered_data = unique_students_query_result.iloc[0,0]
        except Exception as e:
            unique_students_in_filtered_data = df_composition['total_users'].sum() 
            if unique_students_in_filtered_data == 0 and not df_daily.empty: 
                 unique_students_in_filtered_data = df_daily['emisi'].count() 
    
    avg_emisi = total_emisi / unique_students_in_filtered_data if unique_students_in_filtered_data > 0 else 0
    
    if total_emisi == 0 and unique_students_in_filtered_data == 0 and df_daily.empty and df_faculty.empty and df_heatmap.empty and df_kecamatan.empty:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"

    daily_trend_table_html, trend_conclusion, trend_recommendation = ("<tr><td colspan='2'>Data tidak tersedia.</td></tr>", "Pola mobilitas mingguan tidak dapat diidentifikasi.", "Data tidak cukup untuk analisis tren.")
    fakultas_table_html, fakultas_conclusion, fakultas_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Distribusi emisi per fakultas tidak dapat dibuat.", "Data tidak cukup untuk analisis fakultas.")
    mode_table_html, mode_conclusion, mode_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Preferensi moda transportasi tidak dapat dianalisis.", "Data tidak cukup untuk analisis moda.")
    heatmap_header_html, heatmap_body_html, heatmap_conclusion, heatmap_recommendation = ("<tr><th>-</th></tr>", "<tr><td>Data tidak tersedia.</td></tr>", "Pola penggunaan moda transportasi harian belum teridentifikasi.", "Data tidak cukup untuk analisis heatmap.")
    kecamatan_table_html, kecamatan_conclusion, rec_kecamatan = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Hotspot geografis asal perjalanan belum dapat diidentifikasi.", "Data tidak cukup untuk analisis kecamatan.")
    
    # --- 1. Tren Emisi Harian ---
    # Judul: Tren Emisi Harian (sesuai visualisasi dashboard)
    if not df_daily.empty and df_daily['emisi'].sum() > 0:
        daily_df_sorted = df_daily.sort_values(by='emisi', ascending=False)
        daily_trend_table_html = "".join([f"<tr><td>{row['hari']}</td><td style='text-align:right;'>{row['emisi']:.1f}</td></tr>" for _, row in daily_df_sorted.iterrows()])
        
        if len(daily_df_sorted) > 1:
            peak_day = daily_df_sorted.iloc[0]['hari']
            low_day = daily_df_sorted.iloc[-1]['hari']
            peak_emisi_val = daily_df_sorted.iloc[0]['emisi']
            low_emisi_val = daily_df_sorted.iloc[-1]['emisi']

            if low_emisi_val > 0 and (peak_emisi_val / low_emisi_val) > 1.5: # Ambang batas 1.5x untuk variasi signifikan
                trend_conclusion = f"Terdapat variasi signifikan dalam mobilitas harian mahasiswa, dengan puncak emisi terjadi pada hari <strong>{peak_day}</strong> ({peak_emisi_val:.1f} kg CO<sub>2</sub>) dan titik terendah pada hari <strong>{low_day}</strong> ({low_emisi_val:.1f} kg CO<sub>2</sub>). Pola ini menunjukkan intensitas aktivitas akademik dan operasional kampus yang lebih tinggi pada hari kerja."
                trend_recommendation = f"Fokuskan kebijakan transportasi berkelanjutan dan kampanye kesadaran pada hari <strong>{peak_day}</strong> untuk mendapatkan dampak maksimal. Pertimbangkan untuk menganalisis aktivitas spesifik yang menyumbang emisi tinggi pada hari tersebut, seperti jam sibuk kedatangan/kepulangan mahasiswa, untuk intervensi yang lebih bertarget (misal: penambahan shuttle bus atau promosi carpooling pada jam-jam tersebut)."
            else:
                trend_conclusion = "Pola mobilitas cenderung konsisten sepanjang hari-hari yang dipilih, tanpa adanya lonjakan yang ekstrem. Emisi transportasi mahasiswa tersebar relatif merata."
                trend_recommendation = "Rekomendasi berupa kampanye mobilitas berkelanjutan secara umum, tidak spesifik pada hari tertentu. Fokus dapat dialihkan ke jenis moda atau lokasi asal perjalanan yang dominan."
        elif len(daily_df_sorted) == 1:
            day_name = daily_df_sorted.iloc[0]['hari']
            day_emisi = daily_df_sorted.iloc[0]['emisi']
            trend_conclusion = f"Data tren emisi harian hanya tersedia untuk hari <strong>{day_name}</strong>, dengan total emisi tercatat sebesar {day_emisi:.1f} kg CO<sub>2</sub>. Ini membatasi analisis pola mobilitas mingguan secara komprehensif."
            trend_recommendation = "Untuk melihat pola tren yang lebih komprehensif, perluas rentang hari pada filter. Analisis untuk hari ini dapat difokuskan pada komposisi moda transportasi dan lokasi asal perjalanan."

    # --- 2. Emisi per Fakultas ---
    # Judul: Emisi per Fakultas (sesuai visualisasi dashboard)
    if not df_faculty.empty and df_faculty['total_emisi'].sum() > 0 and 'count' in df_faculty.columns and df_faculty['count'].sum() > 0:
        df_faculty['avg_emisi'] = df_faculty['total_emisi'] / df_faculty['count']
        df_faculty_sorted = df_faculty.sort_values('avg_emisi', ascending=False) # Sort by average emission per mahasiswa
        
        # Tampilkan SEMUA fakultas yang memiliki emisi > 0
        fakultas_table_html = "".join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['avg_emisi']:.2f}</td><td style='text-align:center;'>{int(row['count'])}</td></tr>" for _, row in df_faculty_sorted[df_faculty_sorted['total_emisi'] > 0].iterrows()])
        
        if len(df_faculty_sorted[df_faculty_sorted['total_emisi'] > 0]) > 1: # Cek apakah ada lebih dari satu fakultas dengan emisi > 0
            highest_fakultas_row = df_faculty_sorted.iloc[0]
            # Temukan fakultas dengan emisi rata-rata terendah (yang bukan nol)
            lowest_fakultas_candidates = df_faculty_sorted[df_faculty_sorted['avg_emisi'] > 0]
            lowest_fakultas_row = lowest_fakultas_candidates.iloc[-1] if not lowest_fakultas_candidates.empty else highest_fakultas_row
            
            conclusion_detail = ""
            if lowest_fakultas_row['avg_emisi'] > 0:
                emission_ratio = highest_fakultas_row['avg_emisi'] / lowest_fakultas_row['avg_emisi']
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> menunjukkan jejak karbon transportasi per mahasiswa tertinggi dengan rata-rata <strong>{highest_fakultas_row['avg_emisi']:.2f} kg CO<sub>2</sub></strong> per mahasiswa, sekitar {emission_ratio:.1f} kali lebih tinggi dari fakultas dengan emisi rata-rata terendah, <strong>{lowest_fakultas_row['fakultas']} ({lowest_fakultas_row['avg_emisi']:.2f} kg CO<sub>2</sub>)</strong>."
            else: 
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> memiliki jejak karbon transportasi per mahasiswa tertinggi sebesar <strong>{highest_fakultas_row['avg_emisi']:.2f} kg CO<sub>2</sub></strong>, sementara beberapa fakultas lain memiliki rata-rata emisi mendekati nol."

            fakultas_conclusion = f"Terdapat perbedaan yang jelas dalam jejak karbon transportasi per mahasiswa antar fakultas. {conclusion_detail} Pola ini mungkin mengindikasikan bahwa mahasiswa dari fakultas dengan emisi tinggi cenderung tinggal lebih jauh dari kampus atau lebih bergantung pada kendaraan pribadi, atau memiliki akses terbatas ke moda ramah lingkungan."
            fakultas_recommendation = f"Terapkan intervensi berbasis lokasi dan demografi. Prioritaskan program edukasi dan insentif yang ditargetkan pada Fakultas <strong>{highest_fakultas_row['fakultas']}</strong>, seperti perbaikan fasilitas parkir sepeda, penambahan layanan shuttle, atau promosi carpooling dari area padat mahasiswa di fakultas tersebut. Pertimbangkan juga studi kasus dari Fakultas <strong>{lowest_fakultas_row['fakultas']}</strong> untuk memahami praktik terbaik mereka."
        else: # Hanya ada satu fakultas dengan emisi > 0
            if not df_faculty_sorted[df_faculty_sorted['total_emisi'] > 0].empty:
                fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{df_faculty_sorted[df_faculty_sorted['total_emisi'] > 0].iloc[0]['fakultas']}</strong>, dengan rata-rata emisi per mahasiswa sebesar {df_faculty_sorted[df_faculty_sorted['total_emisi'] > 0].iloc[0]['avg_emisi']:.2f} kg CO<sub>2</sub>. Perbandingan dengan fakultas lain tidak dapat dilakukan karena keterbatasan data filter."
                fakultas_recommendation = "Perluas filter fakultas untuk mendapatkan perbandingan yang lebih komprehensif atau pastikan data dari fakultas lain tersedia."
            else: # Tidak ada fakultas dengan emisi > 0
                fakultas_conclusion = "Tidak ada fakultas dengan emisi transportasi tercatat setelah filter diterapkan."
                fakultas_recommendation = "Coba sesuaikan filter Anda untuk mencakup fakultas dengan data emisi transportasi."

    # --- 3. Proporsi Moda Transportasi ---
    # Judul: Proporsi Moda Transportasi (sesuai visualisasi dashboard)
    if not df_composition.empty and df_composition['total_users'].sum() > 0: # Menggunakan total_users
        df_comp_sorted = df_composition.sort_values('total_users', ascending=False) # Menggunakan total_users
        df_comp_sorted['avg_emisi_per_mahasiswa'] = df_comp_sorted['total_emisi'] / df_comp_sorted['total_users'] # Menggunakan total_users
        mode_table_html = "".join([f"<tr><td>{row['transportasi']}</td><td style='text-align:center;'>{int(row['total_users'])}</td><td style='text-align:right;'>{row['avg_emisi_per_mahasiswa']:.2f}</td></tr>" for _, row in df_comp_sorted.iterrows()]) # Menggunakan total_users
        
        if len(df_comp_sorted) > 0: 
            dominant_mode_row = df_comp_sorted.iloc[0]
            mode_conclusion = f"<strong>{dominant_mode_row['transportasi']}</strong> adalah moda transportasi pilihan utama di antara mahasiswa yang terfilter, dengan {int(dominant_mode_row['total_users'])} mahasiswa menggunakannya. Ini menunjukkan bahwa infrastruktur dan kondisi eksisting mendukung penggunaan moda ini, namun juga merupakan penyumbang emisi terbesar jika moda tersebut tinggi karbon."
            mode_recommendation = f"Tingkatkan 'user experience' dan aksesibilitas untuk moda transportasi ramah lingkungan (misal: penambahan unit bike sharing, perbaikan jalur pejalan kaki/sepeda). Jika <strong>{dominant_mode_row['transportasi']}</strong> adalah moda tinggi karbon (misal: mobil pribadi, motor), terapkan kebijakan 'mode shifting' (misal: zona rendah emisi, insentif untuk transportasi publik) untuk mengurangi ketergantungan pada moda tersebut."
        else:
            mode_conclusion = "Tidak ada data moda transportasi untuk analisis. Ini mungkin karena filter yang terlalu spesifik."
            mode_recommendation = "Pastikan data transportasi dikumpulkan dengan benar dan filter yang diterapkan tidak terlalu membatasi."


    # --- 4. Heatmap Penggunaan Moda per Hari ---
    # Judul: Heatmap Penggunaan Moda per Hari (sesuai visualisasi dashboard)
    if not df_heatmap.empty and df_heatmap['pengguna'].sum() > 0: # Menggunakan 'pengguna'
        pivot_df = df_heatmap.pivot_table(index='hari', columns='transportasi', values='pengguna', aggfunc='sum').fillna(0) # Menggunakan 'pengguna'
        pivot_df = pivot_df.reindex(index=DAY_ORDER, fill_value=0) # Memastikan urutan hari benar
        
        top_modes_in_data = pivot_df.sum(axis=0).nlargest(6).index.tolist() # Pilih top 6 mode yang paling banyak digunakan untuk heatmap
        pivot_df_filtered = pivot_df[top_modes_in_data] 

        if not pivot_df_filtered.empty and pivot_df_filtered.sum().sum() > 0: 
            header_cells_html = "<th>Hari</th>" + "".join([f"<th>{mode}</th>" for mode in pivot_df_filtered.columns])
            heatmap_header_html = f"<tr>{header_cells_html}</tr>"
            body_rows_list = [f"<tr><td><strong>{day}</strong></td>" + "".join([f"<td style='text-align:center;'>{int(count)}</td>" for count in row]) + "</tr>" for day, row in pivot_df_filtered.iterrows()]
            heatmap_body_html = "".join(body_rows_list)
            
            # Find peak usage
            flat_pivot = pivot_df_filtered.stack()
            if not flat_pivot.empty:
                peak_usage_idx = flat_pivot.idxmax()
                peak_day, peak_mode = peak_usage_idx[0], peak_usage_idx[1]
                peak_value = flat_pivot.max()
                
                heatmap_conclusion = f"Teridentifikasi sebuah pola penggunaan yang kuat: moda transportasi <strong>{peak_mode}</strong> paling sering digunakan pada hari <strong>{peak_day}</strong>, dengan jumlah <strong>{int(peak_value)}</strong> mahasiswa. Ini menunjukkan kebiasaan mobilitas harian yang terprediksi di antara mahasiswa yang terfilter."
                heatmap_recommendation = f"Fokus pada intervensi perilaku yang ditargetkan pada hari dan moda puncak. Usulkan 'Tantangan {peak_day} Hijau': ajak komunitas untuk mencoba moda transportasi rendah karbon sebagai alternatif dari {peak_mode} pada hari tersebut, dan dukung dengan kampanye di media sosial kampus."
            else: 
                 heatmap_conclusion = "Pola penggunaan moda transportasi harian belum teridentifikasi. Data mungkin terlalu sedikit atau filter terlalu spesifik."
                 heatmap_recommendation = "Perluas filter moda transportasi atau hari untuk analisis pola perilaku yang lebih komprehensif."
        else: 
            heatmap_conclusion = "Pola penggunaan moda transportasi harian belum teridentifikasi. Data tidak cukup atau filter terlalu spesifik."
            heatmap_recommendation = "Perluas filter moda transportasi atau hari untuk analisis pola perilaku yang lebih komprehensif."


    # --- 5. Emisi per Kecamatan ---
    # Judul: Emisi per Kecamatan (sesuai visualisasi dashboard)
    if not df_kecamatan.empty and df_kecamatan['total_emisi'].sum() > 0:
        kecamatan_stats_sorted = df_kecamatan.sort_values('total_emisi', ascending=False)
        kecamatan_table_html = "".join([f"<tr><td>{row['kecamatan']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td><td style='text-align:center;'>{int(row['jumlah_mahasiswa'])}</td></tr>" for _, row in kecamatan_stats_sorted.iterrows()])
        
        if len(kecamatan_stats_sorted) > 0:
            hottest_spot_row = kecamatan_stats_sorted.iloc[0]
            kecamatan_conclusion = f"Kecamatan <strong>{hottest_spot_row['kecamatan']}</strong> teridentifikasi sebagai 'hotspot' emisi transportasi, dengan total emisi <strong>{hottest_spot_row['total_emisi']:.1f} kg CO<sub>2</sub></strong> dari {int(hottest_spot_row['jumlah_mahasiswa'])} mahasiswa. Ini menunjukkan bahwa area ini adalah 'feeder' utama komuter ke kampus dan titik intervensi strategis di luar kampus."
            rec_kecamatan = f"Gunakan data ini sebagai dasar proposal kolaborasi dengan Dinas Perhubungan setempat untuk optimalisasi rute angkutan umum dari <strong>{hottest_spot_row['kecamatan']}</strong> menuju kampus. Alternatifnya, kampus dapat mempertimbangkan penyediaan layanan shuttle khusus dari area ini atau mendukung pembentukan komunitas carpooling bagi mahasiswa yang tinggal di sana."
        else:
            kecamatan_conclusion = "Tidak ada data kecamatan untuk analisis. Ini mungkin karena filter yang terlalu spesifik atau data alamat mahasiswa belum lengkap."
            rec_kecamatan = "Pastikan data kecamatan dikumpulkan dengan benar, atau perluas filter untuk mencakup lebih banyak area asal mahasiswa."


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
        <h2>1. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        <h2>2. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Rata-rata Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Mahasiswa</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        <h2>3. Proporsi Moda Transportasi</h2>
        <table><thead><tr><th>Moda Transportasi</th><th>Jumlah Mahasiswa</th><th>Rata-rata Emisi/Mahasiswa (kg CO<sub>2</sub>)</th></tr></thead><tbody>{mode_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {mode_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {mode_recommendation}</div>
        <h2>4. Heatmap Penggunaan Moda per Hari</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>
        <h2>5. Emisi per Kecamatan</h2>
        <table><thead><tr><th>Kecamatan</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Mahasiswa</th></tr></thead><tbody>{kecamatan_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {kecamatan_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {rec_kecamatan}</div>
    </div></body></html>
    """
    
    pdf_buffer = BytesIO()

    pisa_status = pisa.CreatePDF(
        src=html_content,   
        dest=pdf_buffer)     

    if pisa_status.err:
        st.error(f"Error during PDF conversion: {pisa_status.err}. Check HTML format or xhtml2pdf installation.")
        return None 

    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf_bytes

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

    where_clause, join_needed = build_transport_where_clause(selected_modes, selected_fakultas, selected_days)
    
    with export_col1:
        data_df = get_filtered_data(where_clause, join_needed)
        st.download_button(
            "Data", 
            data=data_df.to_csv(index=False), 
            file_name=f"transport_data{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=(data_df.empty)
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

    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            daily_df = get_daily_trend_data(where_clause, join_needed)
            if not daily_df.empty and daily_df['emisi'].sum() > 0:
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
                        margin=dict(t=30, b=0, l=0, r=30), 
                        title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, font=dict(size=12)),
                        yaxis_title="Emisi (kg CO₂)", xaxis_title="Hari"
                        )
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
                    margin=dict(t=40, b=0, l=0, r=20), 
                    title=dict(text="<b>Emisi per Fakultas</b>", 
                               x=0.4, 
                               y=0.95, 
                               font=dict(size=12)),
                    yaxis_title="Fakultas", xaxis_title="Emisi (kg CO₂)"
                    )
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
                    margin=dict(t=50, b=5, l=5, r=5), 
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
                               font=dict(size=12)),
                    xaxis_title="Moda Transportasi", 
                    yaxis_title="Hari")
                st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data heatmap untuk filter ini.")
        
        with col2:
            kecamatan_df = get_kecamatan_data(where_clause, join_needed)
            if not kecamatan_df.empty:
                # REVISI DISINI: Mengurutkan dan menampilkan berdasarkan TOTAL EMISI
                kecamatan_df = kecamatan_df.sort_values('total_emisi', ascending=False)
                fig_kecamatan = go.Figure()
                
                # Menentukan skala warna berdasarkan TOTAL EMISI, bukan rata-rata
                max_emisi_total = kecamatan_df['total_emisi'].max()
                min_emisi_total = kecamatan_df['total_emisi'].min()
                
                for i, (_, row) in enumerate(kecamatan_df.iterrows()):
                    sequential_warm = ['#fee08b', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    color = sequential_warm[0] # Default jika min==max
                    if max_emisi_total != min_emisi_total:
                        ratio = (row['total_emisi'] - min_emisi_total) / (max_emisi_total - min_emisi_total) 
                        color_idx = min(int(ratio * (len(sequential_warm) - 1)), len(sequential_warm) - 1)
                        color = sequential_warm[color_idx]
                    
                    display_name = row['kecamatan'] if len(row['kecamatan']) <= 10 else row['kecamatan'][:8] + '..'
                    fig_kecamatan.add_trace(go.Bar(
                        x=[display_name], 
                        y=[row['total_emisi']], # MENGUBAH Y-AXIS KE TOTAL EMISI
                        marker=dict(color=color), 
                        showlegend=False, 
                        text=[f"{row['total_emisi']:.1f}"], # TEXT DISPLAY TOTAL EMISI
                        textposition='inside', 
                        textfont=dict(color='#2d3748', weight='bold'), 
                        hovertemplate=f'<b>{row["kecamatan"]}</b><br>Total Emisi: %{{y:.1f}} kg CO₂<br>Rata-rata Emisi/Mahasiswa: {row["rata_rata_emisi"]:.2f} kg CO₂<br>Jumlah Mahasiswa: {row["jumlah_mahasiswa"]}<extra></extra>', 
                        name=row['kecamatan']))
                
                # Rata-rata garis horizontal juga berdasarkan TOTAL EMISI
                avg_emisi_kec_total = kecamatan_df['total_emisi'].mean()
                fig_kecamatan.add_hline(
                    y=avg_emisi_kec_total, 
                    line_dash="dash", 
                    line_color="#5e4fa2", 
                    line_width=2, 
                    annotation_text=f"Rata-rata: {avg_emisi_kec_total:.1f}")
                
                fig_kecamatan.update_layout(
                    height=270, 
                    margin=dict(t=30, b=0, l=0, r=10), 
                    title=dict(text="<b>Emisi per Kecamatan</b>", 
                               x=0.4, y=0.95, font=dict(size=12)),
                               xaxis_title="Kecamatan",
                               yaxis_title="Total Emisi (kg CO₂)") # Y-AXIS TITLE KE TOTAL EMISI
                st.plotly_chart(fig_kecamatan, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data kecamatan untuk filter ini.")

if __name__ == "__main__":
    show()