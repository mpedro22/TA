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
PERIOD_COLORS = { 'Pagi': '#66c2a5', 'Siang': '#fdae61', 'Sore': '#f46d43', 'Malam': '#5e4fa2' }
MODEBAR_CONFIG = { 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': [ 'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d' ], 'toImageButtonOptions': { 'format': 'png', 'filename': 'carbon_emission_chart', 'height': 600, 'width': 800, 'scale': 2 } }
DAY_ORDER = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

OFFICIAL_CANTEENS = [
    'Kantin SBM', 'Pratama Corner', 'Kantin GKU Barat', 'Kantin Tunnel', 
    'Kantin Borju', 'Kantin Barrac', 'Cafetaria Sejoli CC Barat', 
    'Kantin CC Timur', 'Cafetaria Tunas Padi (Ex ITB Press)', 
    'Kantin Labtek III', 'Koperasi'
]

CANTEEN_DISPLAY_NAMES = {
    'Kantin SBM': 'Kantin SBM',
    'Pratama Corner': 'Pratama Corner',
    'Kantin GKU Barat': 'Kantin GKU Barat', 
    'Kantin Tunnel': 'Kantin Tunnel',
    'Kantin Borju': 'Kantin Borju',
    'Kantin Barrac': 'Kantin Barrac',
    'Cafetaria Sejoli CC Barat': 'Cafetaria Sejoli', 
    'Kantin CC Timur': 'Kantin CC Timur',
    'Cafetaria Tunas Padi (Ex ITB Press)': 'Cafetaria Tunas', 
    'Kantin Labtek III': 'Kantin Labtek III',
    'Koperasi': 'Koperasi',
}

@st.cache_data(ttl=3600)
def build_food_where_clause(selected_days, selected_periods, selected_fakultas):
    clauses = []
    join_needed = bool(selected_fakultas)
    
    if selected_days:
        days_str = ", ".join([f"'{day}'" for day in selected_days])
        clauses.append(f"m.hari IN ({days_str})")
        
    if selected_periods:
        periods_str = ", ".join([f"'{period}'" for period in selected_periods])
        clauses.append(f"m.meal_period IN ({periods_str})")

    if selected_fakultas:
        fakultas_str = ", ".join([f"'{f}'" for f in selected_fakultas])
        clauses.append(f"r.fakultas IN ({fakultas_str})")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where_sql, join_needed

@st.cache_data(ttl=3600)
def get_daily_trend_data(where_clause, join_needed):
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON m.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT m.hari, SUM(m.emisi_sampah_makanan_per_waktu) as total_emisi, COUNT(m.id_mahasiswa) as activity_count
    FROM v_aktivitas_makanan m {join_sql} {where_clause}
    GROUP BY m.hari
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_faculty_data(where_clause):
    query = f"""
    SELECT r.fakultas, SUM(m.emisi_sampah_makanan_per_waktu) as total_emisi, COUNT(m.id_mahasiswa) as activity_count
    FROM v_aktivitas_makanan m
    JOIN v_informasi_fakultas_mahasiswa r ON m.id_mahasiswa = r.id_mahasiswa
    {where_clause}
    GROUP BY r.fakultas
    ORDER BY total_emisi ASC
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_period_data(where_clause, join_needed):
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON m.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT m.meal_period, COUNT(m.id_mahasiswa) as activity_count, SUM(m.emisi_sampah_makanan_per_waktu) as total_emisi
    FROM v_aktivitas_makanan m {join_sql} {where_clause}
    GROUP BY m.meal_period
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_heatmap_data(where_clause, join_needed):
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON m.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    
    canteens_str = "','".join(OFFICIAL_CANTEENS)
    location_filter = f"m.lokasi IN ('{canteens_str}')"
    
    final_where_clause = f"{where_clause} AND {location_filter}" if where_clause else f"WHERE {location_filter}"

    query = f"""
    SELECT m.lokasi, m.time_slot, SUM(m.emisi_sampah_makanan_per_waktu) as total_emisi
    FROM v_aktivitas_makanan m {join_sql} {final_where_clause}
    GROUP BY m.lokasi, m.time_slot
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_canteen_data(where_clause, join_needed):
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON m.id_mahasiswa = r.id_mahasiswa" if join_needed else ""

    canteens_str = "','".join(OFFICIAL_CANTEENS)
    location_filter = f"m.lokasi IN ('{canteens_str}')"

    final_where_clause = f"{where_clause} AND {location_filter}" if where_clause else f"WHERE {location_filter}"

    query = f"""
    SELECT m.lokasi, SUM(m.emisi_sampah_makanan_per_waktu) as total_emisi, AVG(m.emisi_sampah_makanan_per_waktu) as avg_emisi, COUNT(m.id_mahasiswa) as activity_count
    FROM v_aktivitas_makanan m {join_sql} {final_where_clause}
    GROUP BY m.lokasi
    ORDER BY total_emisi DESC
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_filtered_raw_food_waste_data(selected_fakultas, selected_days):
    """
    Mengambil data mentah dari tabel 'sampah_makanan' yang difilter oleh fakultas dan hari datang.
    Digunakan untuk tombol 'Raw Data'.
    """
    clauses = []
    join_sql = "LEFT JOIN v_informasi_fakultas_mahasiswa r ON s.id_mahasiswa = r.id_mahasiswa"

    if selected_fakultas:
        fakultas_str = ", ".join([f"'{f}'" for f in selected_fakultas])
        clauses.append(f"r.fakultas IN ({fakultas_str})")
    if selected_days:
        day_patterns = [f"'%{day}%'" for day in selected_days]
        clauses.append(f"s.hari_datang ILIKE ANY (ARRAY[{', '.join(day_patterns)}])")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

    query = f"""
    SELECT
        s.id_mahasiswa,
        COALESCE(r.fakultas, 'N/A') as fakultas,
        s.hari_datang,
        s.tempat_makan,
        s.emisi_sampah_makanan_senin,
        s.emisi_sampah_makanan_selasa,
        s.emisi_sampah_makanan_rabu,
        s.emisi_sampah_makanan_kamis,
        s.emisi_sampah_makanan_jumat,
        s.emisi_sampah_makanan_sabtu,
        s.emisi_sampah_makanan_minggu
    FROM
        sampah_makanan s
    {join_sql}
    {where_sql}
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
@loading_decorator()
def generate_pdf_report(where_clause, join_needed):
    from datetime import datetime
    import time 
    
    time.sleep(0.6)

    daily_stats = get_daily_trend_data(where_clause, join_needed)
    fakultas_stats = get_faculty_data(where_clause) 
    period_stats = get_period_data(where_clause, join_needed)
    heatmap_data = get_heatmap_data(where_clause, join_needed)
    canteen_stats = get_canteen_data(where_clause, join_needed)
    
    total_emisi = daily_stats['total_emisi'].sum() if 'total_emisi' in daily_stats.columns and not daily_stats.empty else 0
    total_activities = daily_stats['activity_count'].sum() if 'activity_count' in daily_stats.columns and not daily_stats.empty else 0
    avg_emisi_per_activity = total_emisi / total_activities if total_activities > 0 else 0

    if total_emisi == 0 and total_activities == 0 and daily_stats.empty and fakultas_stats.empty and period_stats.empty and heatmap_data.empty and canteen_stats.empty:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda.</p></body></html>"
    
    # Inisialisasi default content
    daily_trend_table_html, trend_conclusion, trend_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Pola emisi harian tidak dapat diidentifikasi.", "Data tidak cukup untuk analisis tren.")
    fakultas_table_html, fakultas_conclusion, fakultas_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Profil emisi per fakultas tidak dapat dibuat.", "Data tidak cukup untuk analisis fakultas.")
    period_table_html, period_conclusion, period_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Distribusi periode makan tidak dapat dianalisis.", "Data tidak cukup untuk analisis periode.")
    heatmap_header_html, heatmap_body_html, heatmap_conclusion, heatmap_recommendation = ("<tr><th>-</th></tr>", "<tr><td>Data tidak tersedia.</td></tr>", "Pola emisi antar lokasi dan waktu belum dapat dipetakan.", "Data tidak cukup untuk mengidentifikasi hotspot.")
    canteen_table_html, canteen_conclusion, canteen_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Lokasi dengan kontribusi emisi terbesar tidak dapat ditentukan.", "Data tidak cukup untuk analisis lokasi.")
    
    # --- 1. Tren Emisi Harian ---
    # Judul: Tren Emisi Harian
    if not daily_stats.empty and daily_stats['total_emisi'].sum() > 0:
        daily_stats['day_order'] = pd.Categorical(daily_stats['hari'], categories=DAY_ORDER, ordered=True)
        daily_stats_sorted = daily_stats.sort_values('day_order')
        daily_trend_table_html = "".join([f"<tr><td>{row['hari']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td><td style='text-align:center;'>{row['activity_count']}</td></tr>" for _, row in daily_stats_sorted.iterrows()])
        
        if len(daily_stats_sorted) > 1:
            peak_day_row = daily_stats_sorted.loc[daily_stats_sorted['total_emisi'].idxmax()]
            low_day_row = daily_stats_sorted.loc[daily_stats_sorted['total_emisi'].idxmin()]
            
            trend_conclusion = f"Puncak emisi sampah makanan terjadi pada hari <strong>{peak_day_row['hari']}</strong> ({peak_day_row['total_emisi']:.1f} kg CO<sub>2</sub>) dan terendah pada <strong>{low_day_row['hari']}</strong> ({low_day_row['total_emisi']:.1f} kg CO<sub>2</sub>). Pola ini menunjukkan kebiasaan konsumsi mingguan mahasiswa."
            trend_recommendation = f"Fokuskan kampanye 'Zero Food Waste' intensif pada hari <strong>{peak_day_row['hari']}</strong>. Bisa melalui media sosial atau poster di kantin."
        elif len(daily_stats_sorted) == 1:
            day_name = daily_stats_sorted.iloc[0]['hari']
            day_emisi = daily_stats_sorted.iloc[0]['total_emisi']
            trend_conclusion = f"Data tren emisi harian hanya tersedia untuk hari <strong>{day_name}</strong>, dengan total emisi {day_emisi:.1f} kg CO<sub>2</sub>. Analisis pola konsumsi mingguan terbatas."
            trend_recommendation = "Perluas rentang hari pada filter untuk tren komprehensif. Analisis hari ini fokus pada periode makan dan lokasi."

    # --- 2. Emisi per Fakultas ---
    # Judul: Emisi per Fakultas
    if not fakultas_stats.empty and fakultas_stats['total_emisi'].sum() > 0:
        fakultas_stats_sorted = fakultas_stats.sort_values('total_emisi', ascending=False)
        # Tampilkan SEMUA fakultas yang memiliki emisi > 0
        fakultas_table_html = "".join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.2f}</td><td style='text-align:center;'>{row['activity_count']}</td></tr>" for _, row in fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iterrows()])
        
        if len(fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0]) > 1:
            highest_fakultas_row = fakultas_stats_sorted.iloc[0]
            lowest_fakultas_candidates = fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0]
            lowest_fakultas_row = lowest_fakultas_candidates.iloc[-1] if not lowest_fakultas_candidates.empty else highest_fakultas_row
            
            conclusion_detail = ""
            if lowest_fakultas_row['total_emisi'] > 0:
                emission_ratio = highest_fakultas_row['total_emisi'] / lowest_fakultas_row['total_emisi']
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> kontributor terbesar ({highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>), sekitar {emission_ratio:.1f}x lebih tinggi dari fakultas terendah <strong>{lowest_fakultas_row['fakultas']} ({lowest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>)</strong>. Ini mengindikasikan kantin populer atau kebiasaan konsumsi spesifik."
            else:
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> kontributor terbesar ({highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>), sementara fakultas lain memiliki emisi mendekati nol."

            fakultas_conclusion = f"Terdapat perbedaan kontribusi emisi sampah makanan antar fakultas. {conclusion_detail}"
            fakultas_recommendation = f"Jadikan Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> prioritas reduksi sampah. Berkolaborasi dengan kantin untuk evaluasi porsi/menu atau fasilitasi pemilahan organik. Pelajari praktik terbaik dari Fakultas <strong>{lowest_fakultas_row['fakultas']}</strong>."
        else: # Hanya ada satu fakultas dengan emisi > 0
            if not fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].empty:
                fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iloc[0]['fakultas']}</strong>, dengan total emisi {fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iloc[0]['total_emisi']:.1f} kg CO<sub>2</sub>. Perbandingan terbatas karena filter."
                fakultas_recommendation = "Perluas filter fakultas untuk perbandingan komprehensif atau pastikan data fakultas lain tersedia."
            else:
                fakultas_conclusion = "Tidak ada fakultas dengan emisi sampah makanan tercatat setelah filter."
                fakultas_recommendation = "Sesuaikan filter untuk mencakup fakultas dengan data emisi sampah makanan."

    # --- 3. Proporsi Emisi per Waktu ---
    # Judul: Proporsi Emisi per Waktu
    if not period_stats.empty and period_stats['total_emisi'].sum() > 0:
        period_stats_sorted = period_stats.sort_values('total_emisi', ascending=False)
        period_table_html = "".join([f"<tr><td>{row['meal_period']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td><td style='text-align:center;'>{row['activity_count']}</td></tr>" for _, row in period_stats_sorted.iterrows()])
        
        if len(period_stats_sorted) > 0:
            peak_period_row = period_stats_sorted.iloc[0]
            period_conclusion = f"Periode <strong>{peak_period_row['meal_period']}</strong> adalah waktu kritis dengan emisi sampah makanan tertinggi ({peak_period_row['total_emisi']:.1f} kg CO<sub>2</sub> dari {peak_period_row['activity_count']} aktivitas). Ini menunjukkan konsumsi makanan dan produksi sampah paling intensif pada waktu tersebut."
            period_recommendation = f"Berkolaborasi dengan vendor makanan untuk porsi kecil/sedang saat periode <strong>{peak_period_row['meal_period']}</strong>. Promosikan kampanye 'Habiskan Makananmu' lebih intensif pada waktu ini."
        else:
            period_conclusion = "Tidak ada data distribusi emisi per periode waktu untuk analisis."
            period_recommendation = "Pastikan data aktivitas makanan dikumpulkan dan filter tidak terlalu membatasi."
        
    # --- 4. Pola Emisi (Lokasi & Waktu) ---
    # Judul: Pola Emisi (Lokasi & Waktu)
    if not heatmap_data.empty and heatmap_data['total_emisi'].sum() > 0:
        pivot_df = heatmap_data.pivot_table(index='lokasi', columns='time_slot', values='total_emisi', fill_value=0)
        if not pivot_df.empty:
            try:
                sorted_columns = sorted(pivot_df.columns, key=lambda x: int(x.split(':')[0].split('-')[0]))
                pivot_df = pivot_df[sorted_columns]
            except (ValueError, IndexError): pass
            
            original_locations_heatmap = pivot_df.index.tolist()
            display_locations_heatmap = [CANTEEN_DISPLAY_NAMES.get(loc, loc) for loc in original_locations_heatmap]
            display_locations_heatmap = [name if len(name) <= 15 else name[:13] + '..' for name in display_locations_heatmap]

            heatmap_header_html = "<tr><th>Lokasi</th>" + "".join([f"<th>{time_slot}</th>" for time_slot in pivot_df.columns]) + "</tr>"
            body_rows_list = [
                f"<tr><td><strong>{display_locations_heatmap[i]}</strong></td>" + 
                "".join([f"<td style='text-align:center;'>{val:.2f}</td>" for val in row]) + 
                "</tr>" 
                for i, (loc_orig, row) in enumerate(pivot_df.iterrows())
            ]
            heatmap_body_html = "".join(body_rows_list)
            
            flat_heatmap = pivot_df.stack()
            if not flat_heatmap.empty:
                hotspot_value = flat_heatmap.max()
                hotspot_idx = flat_heatmap.idxmax()
                hotspot_location_orig, hotspot_time = hotspot_idx[0], hotspot_idx[1] 
                hotspot_location_display = CANTEEN_DISPLAY_NAMES.get(hotspot_location_orig, hotspot_location_orig)

                heatmap_conclusion = f"'Hotspot' emisi sampah makanan teridentifikasi di <strong>{hotspot_location_display}</strong> pada jam <strong>{hotspot_time}</strong>, dengan emisi {hotspot_value:.1f} kg CO<sub>2</sub>. Ini merupakan kombinasi lokasi dan waktu produksi sampah tertinggi."
                heatmap_recommendation = f"Jadikan lokasi dan waktu puncak ini acuan strategis. Pertimbangkan staf kebersihan tambahan atau optimalkan frekuensi pengumpulan sampah di <strong>{hotspot_location_display}</strong> pada jam <strong>{hotspot_time}</strong>. Edukasi langsung pemilahan sampah juga bisa diterapkan."
            else:
                heatmap_conclusion = "Pola emisi antar lokasi dan waktu belum terpetakan. Data mungkin terlalu sedikit atau filter terlalu spesifik."
                heatmap_recommendation = "Perluas filter lokasi, hari, atau periode waktu untuk analisis pola yang lebih komprehensif."
    else:
        heatmap_conclusion = "Pola emisi antar lokasi dan waktu belum dapat dipetakan. Data tidak cukup untuk mengidentifikasi hotspot."
        heatmap_recommendation = "Perluas filter lokasi, hari, atau periode waktu untuk analisis pola yang lebih komprehensif."

    # --- 5. Hotspot Emisi per Lokasi/Kantin ---
    # Judul: Hotspot Emisi per Lokasi/Kantin
    if not canteen_stats.empty and canteen_stats['total_emisi'].sum() > 0:
        hottest_canteen_row = canteen_stats.sort_values('total_emisi', ascending=False).iloc[0] 
        
        canteen_table_html = "".join([
            f"<tr><td>{CANTEEN_DISPLAY_NAMES.get(row['lokasi'], row['lokasi'])}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td><td style='text-align:center;'>{row['activity_count']}</td></tr>" 
            for _, row in canteen_stats.iterrows()
        ])
        
        hottest_canteen_orig = hottest_canteen_row['lokasi'] 
        hottest_canteen_display = CANTEEN_DISPLAY_NAMES.get(hottest_canteen_orig, hottest_canteen_orig)
        
        avg_emisi_canteen_val = hottest_canteen_row['avg_emisi'] if 'avg_emisi' in hottest_canteen_row else 0.0

        canteen_conclusion = f"Lokasi/kantin <strong>{hottest_canteen_display}</strong> adalah kontributor terbesar emisi sampah makanan, dengan rata-rata limbah per aktivitas <strong>{avg_emisi_canteen_val:.2f} kg CO<sub>2</sub></strong>. Tingginya emisi di sini menunjukkan masalah sistemik atau volume konsumsi tinggi."
        canteen_recommendation = f"Jadikan <strong>{hottest_canteen_display}</strong> percontohan reduksi sampah. Langkah: (1) Diskusi vendor evaluasi porsi/menu. (2) Fasilitasi pemilahan sampah organik jelas. (3) Kampanye edukasi pentingnya mengurangi sisa makanan."


    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Sampah Makanan</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
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
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th, td {{ padding: 7px; text-align: left; border: 1px solid #e5e7eb; }}
        th {{ background-color: #f3f4f6; font-weight: 600; text-align: center; }}
        td:first-child {{ font-weight: 500; }}
    </style></head>
    <body><div class="page">
        <div class="header"><h1>Laporan Emisi Sampah Makanan</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO<sub>2</sub></strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi_per_activity:.2f} kg CO<sub>2</sub></strong>Rata-rata/Aktivitas</div>
        </div>
        <h2>1. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        <h2>2. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        <h2>3. Proporsi Emisi per Waktu</h2>
        <table><thead><tr><th>Periode</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{period_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {period_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {period_recommendation}</div>
        <h2>4. Heatmap Emisi Lokasi per Jam</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>
        <h2>5. Emisi per Lokasi</h2>
        <table><thead><tr><th>Lokasi/Kantin</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Aktivitas</th></tr></thead><tbody>{canteen_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {canteen_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {canteen_recommendation}</div>
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
            <div class="header-bg-pattern"></div><div class="header-float-1"></div><div class="header-float-2"></div><div class="header-float-3"></div><div class="header-float-4"></div><div class="header-float-5"></div>              
            <div class="header-content"><h1 class="header-title">Emisi Sampah Makanan</h1></div>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(0.25)  

    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        selected_days = st.multiselect("Hari:", options=DAY_ORDER, placeholder="Pilih Opsi", key='food_day_filter')
    
    with filter_col2:
        period_options = ['Pagi', 'Siang', 'Sore', 'Malam']
        selected_periods = st.multiselect("Waktu:", options=period_options, placeholder="Pilih Opsi", key='food_period_filter')
    
    with filter_col3:
        fakultas_df = run_sql("SELECT DISTINCT fakultas FROM v_informasi_fakultas_mahasiswa WHERE fakultas IS NOT NULL AND fakultas <> '' ORDER BY fakultas")
        available_fakultas = fakultas_df['fakultas'].tolist() if not fakultas_df.empty else []
        selected_fakultas = st.multiselect("Fakultas:", options=available_fakultas, placeholder="Pilih Opsi", key='food_fakultas_filter')

    where_clause, join_needed = build_food_where_clause(selected_days, selected_periods, selected_fakultas)
    
    with export_col1:
        # Ambil data mentah yang difilter untuk diunduh
        raw_data_df = get_filtered_raw_food_waste_data(selected_fakultas, selected_days)
        st.download_button(
            "Raw Data", 
            data=raw_data_df.to_csv(index=False), 
            file_name=f"food_waste_raw_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            mime="text/csv", 
            use_container_width=True,
            disabled=(raw_data_df.empty) # Tombol aktif jika ada data
        )
    
    with export_col2:
        try:
            pdf_data = generate_pdf_report(where_clause, join_needed)
            
            if pdf_data: 
                st.download_button(
                    label="Laporan",
                    data=pdf_data, 
                    file_name=f"food_waste_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf", 
                    mime="application/pdf", 
                    use_container_width=True,
                    key="food_export_pdf"
                )
            else: 
                st.error("Gagal menyiapkan laporan PDF.")
        except Exception as e:
            st.error(f"Gagal membuat laporan: {e}")

    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1: 
            daily_trend_df = get_daily_trend_data(where_clause, join_needed)
            if not daily_trend_df.empty:
                daily_trend_df['day_order'] = pd.Categorical(daily_trend_df['hari'], categories=DAY_ORDER, ordered=True)
                daily_trend_df = daily_trend_df.sort_values('day_order')
                fig_trend = go.Figure(go.Scatter(x=daily_trend_df['hari'], y=daily_trend_df['total_emisi'], fill='tonexty', mode='lines+markers', line=dict(color='#3288bd', width=2, shape='spline'), marker=dict(size=6, color='#3288bd'), fillcolor="rgba(102, 194, 165, 0.3)", hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>', showlegend=False))
                fig_trend.update_layout(height=270, margin=dict(t=30, b=0, l=0, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, font=dict(size=12)), xaxis_title="Hari", yaxis_title="Emisi (kg CO₂)", font=dict(size=8))
                st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data tren harian untuk filter ini.")

        with col2: 
            faculty_where = where_clause.replace("WHERE", "AND") if "WHERE" in where_clause else ""
            faculty_df = get_faculty_data(faculty_where)
            if not faculty_df.empty:
                faculty_df_display = faculty_df.sort_values('total_emisi', ascending=True).tail(13)
                fig_fakultas = go.Figure()
                max_emisi, min_emisi = faculty_df_display['total_emisi'].max(), faculty_df_display['total_emisi'].min()
                for _, row in faculty_df_display.iterrows():
                    color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    color = color_palette[int(ratio * (len(color_palette) - 1))]
                    fig_fakultas.add_trace(go.Bar(x=[row['total_emisi']], y=[row['fakultas']], orientation='h', marker=dict(color=color), showlegend=False, text=[f"{row['total_emisi']:.1f}"], textposition='inside', textfont=dict(color='white', size=10, weight='bold'), hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Aktivitas: {row["activity_count"]}<extra></extra>'))
                fig_fakultas.update_layout(height=270, margin=dict(t=40, b=0, l=0, r=20), title=dict(text="<b>Emisi per Fakultas</b>", x=0.39, y=0.95, font=dict(size=12)), xaxis_title="Emisi (kg CO₂)", yaxis_title="Fakultas", font=dict(size=8))
                st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data fakultas untuk filter ini.")

        with col3: 
            period_data_df = get_period_data(where_clause, join_needed)
            if not period_data_df.empty:
                period_data_df = period_data_df.set_index('meal_period')
                colors = [PERIOD_COLORS.get(period, '#cccccc') for period in period_data_df.index]
                
                fig_period = go.Figure(data=[go.Pie(
                    labels=period_data_df.index, 
                    values=period_data_df['activity_count'], 
                    hole=0.45, 
                    marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)), 
                    textposition='outside', 
                    textinfo='label+percent', 
                    hovertemplate='<b>%{label}</b><br>%{value} aktivitas (%{percent})<br>Total Emisi: %{customdata:.2f} kg CO₂<extra></extra>',
                    customdata=period_data_df['total_emisi'] 
                )])

                total_emisi_chart = period_data_df['total_emisi'].sum()
                center_text = f"<b style='font-size:14px'>{total_emisi_chart:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                
                fig_period.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                fig_period.update_layout(height=270, margin=dict(t=30, b=35, l=5, r=5), showlegend=False, title=dict(text="<b>Proporsi Emisi per Waktu</b>", x=0.33, y=0.95, font=dict(size=12)))
                st.plotly_chart(fig_period, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data periode untuk filter ini.")

    with loading():
        col1, col2 = st.columns([1, 1])

        with col1: 
            heatmap_df = get_heatmap_data(where_clause, join_needed)
            if not heatmap_df.empty:
                pivot_df = heatmap_df.pivot_table(index='lokasi', columns='time_slot', values='total_emisi', fill_value=0)
                if not pivot_df.empty:
                    try:
                        sorted_columns = sorted(pivot_df.columns, key=lambda x: int(x.split(':')[0].split('-')[0]))
                        pivot_df = pivot_df[sorted_columns]
                    except (ValueError, IndexError): pass
                    
                    original_locations = pivot_df.index.tolist()
                    display_locations_truncated = [CANTEEN_DISPLAY_NAMES.get(loc, loc) for loc in original_locations]
                    # Fallback truncation for any unmapped or still too long names
                    display_locations_truncated = [name if len(name) <= 15 else name[:13] + '..' for name in display_locations_truncated]

                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=pivot_df.values,
                        x=pivot_df.columns,
                        y=original_locations, # Use original locations as tickvals for correct hover mapping
                        colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']],
                        hoverongaps=False,
                        hovertemplate='<b>%{y}</b><br>Jam: %{x}<br>Emisi: %{z:.2f} kg CO₂<extra></extra>',
                        xgap=1, ygap=1,
                        colorbar=dict(title=dict(text="Emisi", font=dict(size=9)), thickness=15, len=0.7)
                    ))
                    
                    fig_heatmap.update_layout(
                        height=270, 
                        margin=dict(t=30, b=20, l=20, r=20), 
                        title=dict(text="<b>Heatmap Emisi Lokasi per Jam</b>", x=0.35, y=0.95, font=dict(size=12)),
                        xaxis=dict(tickangle=25),
                        yaxis=dict(
                            tickvals=original_locations,
                            ticktext=display_locations_truncated,
                            automargin=True, 
                        ),
                        xaxis_title="Waktu", yaxis_title="Lokasi", font=dict(size=8)
                    )
                    
                    st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
                else:
                    st.info("Tidak ada data heatmap untuk pivot.")
            else:
                st.info("Tidak ada data heatmap untuk kantin yang dipilih.")

        with col2: 
            canteen_df = get_canteen_data(where_clause, join_needed)
            if not canteen_df.empty:
                canteen_df = canteen_df.sort_values('total_emisi', ascending=False)
                fig_canteen = go.Figure()
                
                max_emisi, min_emisi = canteen_df['total_emisi'].max(), canteen_df['total_emisi'].min()
                colors = []
                for _, row in canteen_df.iterrows():
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    if ratio < 0.2: colors.append('#66c2a5')
                    elif ratio < 0.4: colors.append('#abdda4')
                    elif ratio < 0.6: colors.append('#fdae61')
                    elif ratio < 0.8: colors.append('#f46d43')
                    else: colors.append('#d53e4f')
                
                display_names = canteen_df['lokasi'].apply(lambda x: CANTEEN_DISPLAY_NAMES.get(x, x)) 
                display_names = display_names.apply(lambda x: x if len(x) <= 12 else x[:12] + '..') 
                
                custom_data = canteen_df[['avg_emisi', 'activity_count', 'lokasi']].values
                
                fig_canteen.add_trace(go.Bar(
                    x=display_names,
                    y=canteen_df['total_emisi'],
                    marker=dict(color=colors, line=dict(color='white', width=1.5), opacity=0.85),
                    showlegend=False, 
                    text=[f"{val:.1f}" for val in canteen_df['total_emisi']], 
                    textposition='inside', 
                    textfont=dict(size=10, color='#2d3748', weight='bold'),
                    hovertemplate='<b>%{customdata[2]}</b><br>Total Emisi: %{y:.2f} kg CO₂<br>Rata-rata: %{customdata[0]:.2f} kg CO₂<br>Aktivitas: %{customdata[1]}<extra></extra>',
                    customdata=custom_data 
                ))
                
                avg_emisi_canteen = canteen_df['total_emisi'].mean()
                fig_canteen.add_hline(y=avg_emisi_canteen, line_dash="dash", line_color="#5e4fa2", line_width=2, annotation_text=f"Rata-rata: {avg_emisi_canteen:.1f}")
                
                fig_canteen.update_layout(
                    height=270, 
                    margin=dict(t=30, b=0, l=0, r=0), 
                    title=dict(text="<b>Emisi per Kantin</b>", x=0.45, y=0.95, font=dict(size=12)), 
                    yaxis_title="Total Emisi (kg CO2)",
                    xaxis=dict(tickangle=-15),
                    xaxis_title="Lokasi",
                )
                st.plotly_chart(fig_canteen, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data kantin untuk filter ini.")

if __name__ == "__main__":
    show()