# src/pages/electronic.py

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

# =============================================================================
# KONFIGURASI DAN PALET WARNA
# =============================================================================

MAIN_PALETTE = ['#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']
DEVICE_COLORS = { 'HP': '#d53e4f', 'Laptop': '#3288bd', 'Tablet': '#66c2a5', 'AC': '#f46d43', 'Lampu': '#fdae61' }
MODEBAR_CONFIG = { 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': [ 'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d' ], 'toImageButtonOptions': { 'format': 'png', 'filename': 'carbon_emission_chart', 'height': 600, 'width': 800, 'scale': 2 } }
DAY_ORDER = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
PERSONAL_DEVICES = ['HP', 'Laptop', 'Tablet']
FACILITY_DEVICES = ['AC', 'Lampu']

# =============================================================================
# FUNGSI-FUNGSI QUERY SQL (TIDAK ADA PERUBAHAN)
# =============================================================================

@st.cache_data(ttl=3600)
def build_universal_where_clause(selected_fakultas, selected_days):
    elektronik_conditions = []
    aktivitas_conditions = []
    join_needed = bool(selected_fakultas)
    if selected_days:
        day_elektronik_conds = [f"t.hari_datang ILIKE '%{day}%'" for day in selected_days]
        elektronik_conditions.append(f"({' OR '.join(day_elektronik_conds)})")
        days_placeholder = ', '.join([f"'{day}'" for day in selected_days])
        aktivitas_conditions.append(f"a.hari IN ({days_placeholder})")
    if selected_fakultas:
        fakultas_placeholder = ', '.join([f"'{f}'" for f in selected_fakultas])
        fakultas_condition = f"r.fakultas IN ({fakultas_placeholder})"
        elektronik_conditions.append(fakultas_condition)
        aktivitas_conditions.append(fakultas_condition)
    where_elektronik = "WHERE " + " AND ".join(elektronik_conditions) if elektronik_conditions else ""
    where_aktivitas = "WHERE " + " AND ".join(aktivitas_conditions) if aktivitas_conditions else ""
    return where_elektronik, where_aktivitas, join_needed

def _get_dynamic_emission_clauses(selected_devices):
    if not selected_devices:
        selected_devices = PERSONAL_DEVICES + FACILITY_DEVICES
    personal_terms = []
    if 'HP' in selected_devices: personal_terms.append("t.durasi_hp*4")
    if 'Laptop' in selected_devices: personal_terms.append("t.durasi_laptop*50")
    if 'Tablet' in selected_devices: personal_terms.append("t.durasi_tab*10")
    personal_sum_clause = f"(({ ' + '.join(personal_terms) if personal_terms else '0' }) * 0.829 / 1000)"
    facility_terms = []
    if 'AC' in selected_devices: facility_terms.append("a.emisi_ac")
    if 'Lampu' in selected_devices: facility_terms.append("a.emisi_lampu")
    facility_sum_clause = f"({ ' + '.join(facility_terms) if facility_terms else '0' })"
    include_personal = any(d in selected_devices for d in PERSONAL_DEVICES)
    include_facility = any(d in selected_devices for d in FACILITY_DEVICES)
    return personal_sum_clause, facility_sum_clause, include_personal, include_facility

@st.cache_data(ttl=3600)
def get_daily_trend_data(where_elektronik, where_aktivitas, join_needed, selected_devices):
    personal_sum, facility_sum, include_personal, include_facility = _get_dynamic_emission_clauses(selected_devices)
    if not include_personal and not include_facility: return pd.DataFrame(columns=['hari', 'total_emisi'])
    join_elektronik_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    join_aktivitas_sql = "JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    personal_cte = f"SELECT TRIM(unnest(string_to_array(t.hari_datang, ','))) AS hari, SUM({personal_sum}) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik} GROUP BY hari"
    facility_cte = f"SELECT a.hari, SUM({facility_sum}) as emisi FROM aktivitas_harian a {join_aktivitas_sql} {where_aktivitas} GROUP BY a.hari"
    if include_personal and include_facility:
        query = f"WITH personal_daily AS ({personal_cte}), facility_daily AS ({facility_cte}) SELECT COALESCE(p.hari, f.hari) as hari, COALESCE(p.emisi, 0) + COALESCE(f.emisi, 0) as total_emisi FROM personal_daily p FULL OUTER JOIN facility_daily f ON p.hari = f.hari"
    elif include_personal:
        query = f"WITH personal_daily AS ({personal_cte}) SELECT hari, emisi as total_emisi FROM personal_daily"
    else:
        query = f"WITH facility_daily AS ({facility_cte}) SELECT hari, emisi as total_emisi FROM facility_daily"
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_faculty_data(where_elektronik, where_aktivitas, selected_devices):
    personal_sum, facility_sum, include_personal, include_facility = _get_dynamic_emission_clauses(selected_devices)
    if not include_personal and not include_facility: return pd.DataFrame(columns=['fakultas', 'total_emisi', 'total_count'])
    personal_sum_weekly = f"{personal_sum} * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)"
    personal_cte = f"SELECT r.fakultas, SUM({personal_sum_weekly}) as emisi FROM elektronik t JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa {where_elektronik} GROUP BY r.fakultas"
    facility_cte = f"SELECT r.fakultas, SUM({facility_sum}) as emisi FROM aktivitas_harian a JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa {where_aktivitas} GROUP BY r.fakultas"
    responden_count_cte = "responden_count AS (SELECT fakultas, COUNT(DISTINCT id_mahasiswa) as total_count FROM v_informasi_fakultas_mahasiswa GROUP BY fakultas)"
    if include_personal and include_facility:
        query = f"WITH personal_agg AS ({personal_cte}), facility_agg AS ({facility_cte}), {responden_count_cte} SELECT COALESCE(p.fakultas, f.fakultas) as fakultas, (COALESCE(p.emisi, 0) + COALESCE(f.emisi, 0)) as total_emisi, rc.total_count FROM personal_agg p FULL OUTER JOIN facility_agg f ON p.fakultas = f.fakultas JOIN responden_count rc ON rc.fakultas = COALESCE(p.fakultas, f.fakultas) ORDER BY total_emisi ASC"
    elif include_personal:
        query = f"WITH personal_agg AS ({personal_cte}), {responden_count_cte} SELECT p.fakultas, p.emisi as total_emisi, rc.total_count FROM personal_agg p JOIN responden_count rc ON rc.fakultas = p.fakultas ORDER BY total_emisi ASC"
    else:
        query = f"WITH facility_agg AS ({facility_cte}), {responden_count_cte} SELECT f.fakultas, f.emisi as total_emisi, rc.total_count FROM facility_agg f JOIN responden_count rc ON rc.fakultas = f.fakultas ORDER BY total_emisi ASC"
    df = run_sql(query)
    if 'total_emisi' in df.columns and not df.empty and 'total_count' not in df.columns:
        fakultas_list_str = "','".join(df['fakultas'].unique())
        count_df = run_sql(f"SELECT fakultas, COUNT(DISTINCT id_mahasiswa) as total_count FROM v_informasi_fakultas_mahasiswa WHERE fakultas IN ('{fakultas_list_str}') GROUP BY fakultas")
        if not count_df.empty: df = pd.merge(df, count_df, on='fakultas', how='left')
    return df

@st.cache_data(ttl=3600)
def get_device_emissions_data(where_elektronik, where_aktivitas, join_needed):
    join_elektronik_sql = "JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    join_aktivitas_sql = "JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    WITH personal_devices AS (
        SELECT 'Laptop' as device, SUM((t.durasi_laptop * 50 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik} UNION ALL
        SELECT 'HP' as device, SUM((t.durasi_hp * 4 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik} UNION ALL
        SELECT 'Tablet' as device, SUM((t.durasi_tab * 10 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik}
    ), facility_devices AS (
        SELECT 'AC' as device, SUM(a.emisi_ac) as emisi FROM aktivitas_harian a {join_aktivitas_sql} {where_aktivitas} UNION ALL
        SELECT 'Lampu' as device, SUM(a.emisi_lampu) as emisi FROM aktivitas_harian a {join_aktivitas_sql} {where_aktivitas}
    )
    SELECT device, emisi FROM personal_devices UNION ALL SELECT device, emisi FROM facility_devices
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_heatmap_data(where_aktivitas, join_needed, selected_devices):
    _, facility_sum, _, include_facility = _get_dynamic_emission_clauses(selected_devices)
    if not include_facility: return pd.DataFrame(columns=['hari', 'time_range', 'total_emisi'])
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    query = f"""
    SELECT a.hari, CONCAT(SPLIT_PART(a.waktu, '-', 1), ':00-', SPLIT_PART(a.waktu, '-', 2), ':00') as time_range, SUM({facility_sum}) as total_emisi
    FROM aktivitas_harian a {join_sql} {where_aktivitas}
    GROUP BY a.hari, time_range
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
def get_classroom_data(where_aktivitas, join_needed, selected_devices):
    _, facility_sum, _, include_facility = _get_dynamic_emission_clauses(selected_devices)
    if not include_facility: return pd.DataFrame(columns=['lokasi', 'session_count', 'total_emisi'])
    join_sql = "JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa" if join_needed else ""
    class_condition = "a.kegiatan ILIKE '%kelas%'"
    final_where_classroom = f"{where_aktivitas} AND {class_condition}" if where_aktivitas else f"WHERE {class_condition}"
    query = f"""
    SELECT a.lokasi, COUNT(*) as session_count, SUM({facility_sum}) as total_emisi
    FROM aktivitas_harian a {join_sql}
    {final_where_classroom}
    GROUP BY a.lokasi ORDER BY session_count DESC LIMIT 10
    """
    df = run_sql(query)
    if not df.empty and 'total_emisi' in df.columns and 'session_count' in df.columns and df['session_count'].sum() > 0:
        df['avg_emisi_per_session'] = df['total_emisi'] / df['session_count']
    else: df['avg_emisi_per_session'] = 0
    return df

@st.cache_data(ttl=3600)
@loading_decorator()
def generate_pdf_report(where_elektronik, where_aktivitas, join_needed, selected_days, selected_devices):
    from datetime import datetime
    time.sleep(0.6)
    
    # Menjalankan semua query yang dibutuhkan untuk laporan
    df_daily = get_daily_trend_data(where_elektronik, where_aktivitas, join_needed, selected_devices)
    df_faculty = get_faculty_data(where_elektronik, where_aktivitas, selected_devices)
    df_devices_raw = get_device_emissions_data(where_elektronik, where_aktivitas, join_needed)
    df_heatmap = get_heatmap_data(where_aktivitas, join_needed, selected_devices)
    df_classrooms = get_classroom_data(where_aktivitas, join_needed, selected_devices)
    
    # Filter df_devices berdasarkan pilihan, karena query-nya mengambil semua
    df_devices_filtered = df_devices_raw[df_devices_raw['device'].isin(selected_devices)] if selected_devices else df_devices_raw
    df_devices = df_devices_filtered[df_devices_filtered['emisi'].notna() & (df_devices_filtered['emisi'] > 0)]

    # Inisialisasi metrik utama dan default HTML untuk tabel/kesimpulan
    total_emisi = df_devices['emisi'].sum() if not df_devices.empty else 0
    avg_emisi = 0
    try:
        total_responden_unique_df = run_sql("SELECT COUNT(DISTINCT id_mahasiswa) as count FROM v_informasi_fakultas_mahasiswa")
        if not total_responden_unique_df.empty and 'count' in total_responden_unique_df.columns:
            total_responden_unique = total_responden_unique_df['count'].iloc[0]
            if total_responden_unique > 0:
                avg_emisi = total_emisi / total_responden_unique
        else:
            total_responden_unique = 0
    except (IndexError, KeyError):
        total_responden_unique = 0

    # Fallback HTML jika tidak ada data sama sekali
    if df_devices.empty or df_devices['emisi'].sum() == 0:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan sesuaikan filter Anda dan coba lagi.</p></body></html>"

    # --- Default Text & HTML for Sections ---
    daily_trend_table_html, trend_conclusion, trend_recommendation = ("<tr><td colspan='2'>Data tidak tersedia.</td></tr>", "Pola emisi harian tidak dapat diidentifikasi.", "Data tidak cukup untuk analisis tren.")
    fakultas_table_html, fakultas_conclusion, fakultas_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Profil emisi per fakultas tidak dapat dibuat.", "Data tidak cukup untuk analisis fakultas.")
    device_table_html, device_conclusion, device_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Proporsi emisi perangkat tidak dapat dianalisis.", "Data tidak cukup untuk analisis perangkat.")
    heatmap_header_html, heatmap_body_html, heatmap_conclusion, heatmap_recommendation = ("<tr><th>-</th></tr>", "<tr><td>Data tidak tersedia.</td></tr>", "Pola penggunaan fasilitas tidak teridentifikasi.", "Data tidak cukup untuk analisis heatmap.")
    location_table_html, location_conclusion, location_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Lokasi dengan konsumsi energi tertinggi tidak dapat ditentukan.", "Data tidak cukup untuk analisis lokasi.")

    # --- Pembuatan Insight Dinamis ---
    
    # 1. Tren Harian
    if not df_daily.empty and df_daily['total_emisi'].sum() > 0:
        df_daily_filtered = df_daily[df_daily['hari'].isin(selected_days)] if selected_days else df_daily
        df_daily_filtered['order'] = pd.Categorical(df_daily_filtered['hari'], categories=DAY_ORDER, ordered=True)
        daily_df_sorted = df_daily_filtered.sort_values('order')
        daily_trend_table_html = "".join([f"<tr><td>{row['hari']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for _, row in daily_df_sorted.iterrows()])
        
        if len(daily_df_sorted) > 1:
            peak_day = daily_df_sorted.loc[daily_df_sorted['total_emisi'].idxmax()]
            low_day = daily_df_sorted.loc[daily_df_sorted['total_emisi'].idxmin()]
            if low_day['total_emisi'] > 0 and (peak_day['total_emisi'] / low_day['total_emisi']) > 1.5:
                trend_conclusion = f"Terdapat variasi signifikan dalam penggunaan energi harian, dengan puncak emisi terjadi pada hari <strong>{peak_day['hari']}</strong> ({peak_day['total_emisi']:.1f} kg CO<sub>2</sub>) dan titik terendah pada hari <strong>{low_day['hari']}</strong> ({low_day['total_emisi']:.1f} kg CO<sub>2</sub>)."
                trend_recommendation = f"Fokuskan program efisiensi dan kampanye kesadaran pada hari <strong>{peak_day['hari']}</strong> untuk mendapatkan dampak maksimal. Analisis aktivitas spesifik pada hari tersebut dapat memberikan petunjuk lebih lanjut."
            else:
                trend_conclusion = "Penggunaan energi cenderung konsisten sepanjang hari-hari yang dipilih, tanpa adanya lonjakan yang ekstrem."
                trend_recommendation = "Rekomendasi berupa kampanye hemat energi secara umum, tidak spesifik pada hari tertentu. Fokus dapat dialihkan ke jenis perangkat atau lokasi."
        elif len(daily_df_sorted) == 1:
            day_name = daily_df_sorted.iloc[0]['hari']
            day_emisi = daily_df_sorted.iloc[0]['total_emisi']
            trend_conclusion = f"Data hanya tersedia untuk hari <strong>{day_name}</strong>, dengan total emisi tercatat sebesar {day_emisi:.1f} kg CO<sub>2</sub>."
            trend_recommendation = "Untuk melihat tren, perluas rentang hari pada filter. Analisis untuk hari ini dapat difokuskan pada komposisi perangkat dan lokasi."

    # 2. Emisi per Fakultas
    if not df_faculty.empty and df_faculty['total_emisi'].sum() > 0:
        fakultas_stats_sorted = df_faculty.sort_values('total_emisi', ascending=False)
        fakultas_table_html = "".join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.2f}</td><td style='text-align:center;'>{int(row.get('total_count', 0))}</td></tr>" for _, row in fakultas_stats_sorted.head(10).iterrows()])
        
        if len(fakultas_stats_sorted) > 1:
            highest_fakultas = fakultas_stats_sorted.iloc[0]
            avg_emisi_fak = fakultas_stats_sorted['total_emisi'].mean()
            percent_above_avg = ((highest_fakultas['total_emisi'] / avg_emisi_fak) - 1) * 100 if avg_emisi_fak > 0 else 0
            fakultas_conclusion = f"Fakultas <strong>{highest_fakultas['fakultas']}</strong> menunjukkan kontribusi emisi tertinggi, yaitu sebesar {highest_fakultas['total_emisi']:.1f} kg CO<sub>2</sub>, atau sekitar <strong>{percent_above_avg:.0f}% di atas rata-rata</strong> emisi per fakultas."
            fakultas_recommendation = f"Data ini mengindikasikan bahwa intervensi yang ditargetkan pada Fakultas <strong>{highest_fakultas['fakultas']}</strong> kemungkinan akan memberikan dampak terbesar. Pertimbangkan untuk menganalisis komposisi perangkat yang digunakan atau melakukan audit energi sederhana di gedung-gedung utama fakultas tersebut."
        else:
            fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{fakultas_stats_sorted.iloc[0]['fakultas']}</strong>."
            fakultas_recommendation = "Perluas filter untuk membandingkan dengan fakultas lain."

    # 3. Proporsi Perangkat
    if not df_devices.empty and df_devices['emisi'].sum() > 0:
        df_devices_sorted = df_devices.sort_values('emisi', ascending=False)
        total_device_emission = df_devices_sorted['emisi'].sum()
        device_table_html = "".join([f"<tr><td>{row['device']}</td><td style='text-align:right;'>{row['emisi']:.2f}</td><td style='text-align:right;'>{(row['emisi']/total_device_emission*100 if total_device_emission > 0 else 0):.1f}%</td></tr>" for _, row in df_devices_sorted.iterrows()])
        
        dominant_device = df_devices_sorted.iloc[0]
        dominant_percentage = (dominant_device['emisi'] / total_device_emission) * 100
        
        if dominant_percentage > 50:
            device_conclusion = f"<strong>{dominant_device['device']}</strong> adalah kontributor utama yang dominan, menyumbang <strong>{dominant_percentage:.0f}%</strong> dari total emisi perangkat yang dipilih."
        elif len(df_devices_sorted) > 1:
            second_device = df_devices_sorted.iloc[1]
            device_conclusion = f"Emisi terbagi antara beberapa perangkat, dengan <strong>{dominant_device['device']}</strong> sebagai yang tertinggi, diikuti oleh <strong>{second_device['device']}</strong>."
        else:
            device_conclusion = f"Seluruh emisi berasal dari <strong>{dominant_device['device']}</strong> berdasarkan filter saat ini."

        if dominant_device['device'] in FACILITY_DEVICES:
            device_recommendation = f"Fokus utama untuk efisiensi adalah pada fasilitas gedung. Pertimbangkan kebijakan operasional (misal: pengaturan timer, suhu AC) atau evaluasi untuk upgrade ke perangkat <strong>{dominant_device['device']}</strong> yang lebih hemat energi."
        else:
            device_recommendation = f"Fokus pada perilaku pengguna adalah kunci. Promosikan penggunaan mode hemat daya untuk <strong>{dominant_device['device']}</strong>, dan kampanyekan untuk mencabut pengisi daya saat tidak digunakan."

    # 4. Heatmap Fasilitas
    if not df_heatmap.empty and df_heatmap['total_emisi'].sum() > 0:
        pivot_df = df_heatmap.pivot_table(index='hari', columns='time_range', values='total_emisi', fill_value=0)
        try:
            sorted_columns = sorted(pivot_df.columns, key=lambda x: int(x.split(':')[0].split('-')[0]))
            pivot_df = pivot_df[sorted_columns]
        except (ValueError, IndexError): pass
        pivot_df = pivot_df.reindex(index=DAY_ORDER, fill_value=0).dropna(how='all')
        if selected_days: pivot_df = pivot_df.loc[selected_days] # Filter by selected days
        
        if not pivot_df.empty and pivot_df.sum().sum() > 0:
            peak_usage_idx = pivot_df.stack().idxmax()
            peak_day, peak_time = peak_usage_idx[0], peak_usage_idx[1]
            heatmap_header_html = "<tr><th>Hari</th>" + "".join([f"<th>{time_slot}</th>" for time_slot in pivot_df.columns]) + "</tr>"
            body_rows_list = [f"<tr><td><strong>{day}</strong></td>" + "".join([f"<td style='text-align:center;'>{val:.2f}</td>" for val in row]) + "</tr>" for day, row in pivot_df.iterrows()]
            heatmap_body_html = "".join(body_rows_list)
            heatmap_conclusion = f"Puncak penggunaan fasilitas teridentifikasi pada hari <strong>{peak_day}</strong> di sekitar jam <strong>{peak_time}</strong>. Ini menunjukkan waktu paling intensif energi untuk AC dan/atau Lampu."
            heatmap_recommendation = "Jadikan waktu puncak ini sebagai acuan. Pertimbangkan untuk menerapkan sistem otomatisasi (timer AC/lampu) yang aktif sebelum dan non-aktif setelah jam sibuk ini untuk efisiensi maksimal."

    # 5. Lokasi Kelas
    if not df_classrooms.empty and df_classrooms['total_emisi'].sum() > 0:
        location_stats_sorted = df_classrooms.sort_values('total_emisi', ascending=False)
        location_table_html = "".join([f"<tr><td>{row['lokasi']}</td><td style='text-align:center;'>{int(row['session_count'])}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for _, row in location_stats_sorted.head(10).iterrows()])
        highest_emission_loc = location_stats_sorted.iloc[0]
        location_conclusion = f"Gedung/Ruang <strong>{highest_emission_loc['lokasi']}</strong> tercatat sebagai lokasi dengan konsumsi energi tertinggi untuk kegiatan kelas, dengan total emisi <strong>{highest_emission_loc['total_emisi']:.1f} kg CO<sub>2</sub></strong> dari {highest_emission_loc['session_count']} sesi."
        location_recommendation = f"Lokasi ini adalah kandidat utama untuk proyek percontohan efisiensi energi. Audit sederhana pada perangkat AC dan sistem pencahayaan di <strong>{highest_emission_loc['lokasi']}</strong> dapat memberikan insight cepat untuk potensi penghematan."

    # --- Penggabungan HTML Final ---
    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Elektronik</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet"><style>
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
    </style></head><body><div class="page"><div class="header"><h1>Laporan Emisi Elektronik</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div><div class="grid"><div class="card primary"><strong>{total_emisi:.1f} kg CO<sub>2</sub></strong>Total Emisi (sesuai filter)</div><div class="card secondary"><strong>{avg_emisi:.2f} kg CO<sub>2</sub></strong>Rata-rata/Total Mahasiswa</div></div><h2>1. Tren Emisi Harian</h2><table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table><div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div><h2>2. Emisi per Fakultas</h2><table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Responden</th></tr></thead><tbody>{fakultas_table_html}</tbody></table><div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div><h2>3. Proporsi Emisi per Perangkat</h2><table><thead><tr><th>Perangkat</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Persentase</th></tr></thead><tbody>{device_table_html}</tbody></table><div class="conclusion"><strong>Insight:</strong> {device_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {device_recommendation}</div><h2>4. Pola Penggunaan Fasilitas Kampus</h2><table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table><div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div><h2>5. Lokasi Kelas Paling Intensif Energi</h2><table><thead><tr><th>Gedung</th><th>Jumlah Sesi</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{location_table_html}</tbody></table><div class="conclusion"><strong>Insight:</strong> {location_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {location_recommendation}</div></div></body></html>
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


# =============================================================================
# FUNGSI UTAMA (SHOW) - Perubahan minor untuk memanggil report yang baru
# =============================================================================

def show():
    st.markdown("""
        <style> .wow-header { position: relative; overflow: hidden; } </style>
        <div class="wow-header">
            <div class="header-bg-pattern"></div><div class="header-float-1"></div><div class="header-float-2"></div><div class="header-float-3"></div><div class="header-float-4"></div><div class="header-float-5"></div>
            <div class="header-content"><h1 class="header-title">Emisi Elektronik</h1></div>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(0.25)
    
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])

    with filter_col1:
        selected_days = st.multiselect("Hari:", options=DAY_ORDER, placeholder="Pilih Opsi", key='electronic_day_filter')
    with filter_col2:
        device_options = list(DEVICE_COLORS.keys())
        selected_devices = st.multiselect("Perangkat:", options=device_options, placeholder="Pilih Opsi", key='electronic_device_filter')
    with filter_col3:
        fakultas_df = run_sql("SELECT DISTINCT fakultas FROM v_informasi_fakultas_mahasiswa WHERE fakultas IS NOT NULL AND fakultas <> '' ORDER BY fakultas")
        available_fakultas = fakultas_df['fakultas'].tolist() if not fakultas_df.empty else []
        selected_fakultas = st.multiselect("Fakultas:", options=available_fakultas, placeholder="Pilih Opsi", key='electronic_fakultas_filter')

    where_elektronik, where_aktivitas, join_needed = build_universal_where_clause(selected_fakultas, selected_days)

    with export_col1:
        st.download_button("Raw Data", "Fitur dinonaktifkan.", "raw_data.csv", disabled=True, use_container_width=True)
    with export_col2:
        try:
            pdf_data = generate_pdf_report(where_elektronik, where_aktivitas, join_needed, selected_days, selected_devices)
            
            if pdf_data: 
                st.download_button(
                    label="Laporan",
                    data=pdf_data,
                    file_name=f"electronic_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf", # Ubah ekstensi menjadi .pdf
                    mime="application/pdf", 
                    use_container_width=True,
                    key="electronic_export_pdf"
                )
            else: 
                st.error("Gagal menyiapkan laporan PDF.")
        except Exception as e:
            st.error(f"Gagal membuat laporan: {e}")

    with loading():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            daily_df = get_daily_trend_data(where_elektronik, where_aktivitas, join_needed, selected_devices)
            if not daily_df.empty:
                if selected_days: daily_df = daily_df[daily_df['hari'].str.strip().isin(selected_days)]
                if not daily_df.empty:
                    daily_df['order'] = pd.Categorical(daily_df['hari'], categories=DAY_ORDER, ordered=True)
                    daily_df = daily_df.sort_values('order')
                    fig_trend = go.Figure(go.Scatter(x=daily_df['hari'], y=daily_df['total_emisi'], fill='tonexty', mode='lines+markers', line=dict(color='#3288bd', width=2, shape='spline'), marker=dict(size=6, color='#3288bd'), fillcolor="rgba(102, 194, 165, 0.3)", hovertemplate='<b>%{x}</b><br>%{y:.1f} kg CO₂<extra></extra>', showlegend=False))
                    fig_trend.update_layout(height=270, margin=dict(t=25, b=0, l=0, r=20), title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, font=dict(size=11)))
                    st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
                else: st.info("Tidak ada data tren untuk filter ini.")
            else: st.info("Tidak ada data tren untuk filter ini.")
        
        with col2:
            fakultas_stats = get_faculty_data(where_elektronik, where_aktivitas, selected_devices)
            if not fakultas_stats.empty and 'total_emisi' in fakultas_stats.columns and fakultas_stats['total_emisi'].sum() > 0:
                fakultas_stats_display = fakultas_stats.sort_values('total_emisi', ascending=True).tail(13)
                fig_fakultas = go.Figure()
                max_emisi, min_emisi = fakultas_stats_display['total_emisi'].max(), fakultas_stats_display['total_emisi'].min()
                for _, row in fakultas_stats_display.iterrows():
                    color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    color = color_palette[int(ratio * (len(color_palette) - 1))]
                    fig_fakultas.add_trace(go.Bar(x=[row['total_emisi']], y=[row['fakultas']], orientation='h', marker=dict(color=color), showlegend=False, text=[f"{row['total_emisi']:.1f}"], textposition='inside', textfont=dict(color='white'), hovertemplate=f'<b>{row["fakultas"]}</b><br>Total: {row["total_emisi"]:.1f} kg CO₂<br>Responden: {int(row.get("total_count", 0))}<extra></extra>'))
                fig_fakultas.update_layout(height=270, margin=dict(t=25, b=0, l=0, r=20), title=dict(text="<b>Emisi per Fakultas</b>", x=0.4, y=0.95, font=dict(size=11)))
                st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data fakultas untuk filter ini.")
            
        with col3:
            device_emissions_df = get_device_emissions_data(where_elektronik, where_aktivitas, join_needed)
            if not device_emissions_df.empty:
                display_devices = device_emissions_df.copy()
                if selected_devices:
                    display_devices = display_devices[display_devices['device'].isin(selected_devices)]
                if not display_devices.empty and display_devices['emisi'].sum() > 0:
                    colors = [DEVICE_COLORS.get(d, '#cccccc') for d in display_devices['device']]
                    fig_devices = go.Figure(data=[go.Pie(labels=display_devices['device'], values=display_devices['emisi'], hole=0.45, marker=dict(colors=colors), textposition='outside', textinfo='label+percent', hovertemplate='<b>%{label}</b><br>%{value:.2f} kg CO₂ (%{percent})<extra></extra>')])
                    total_emisi_val = display_devices['emisi'].sum()
                    center_text = f"<b style='font-size:14px'>{total_emisi_val:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
                    fig_devices.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
                    fig_devices.update_layout(height=270, margin=dict(t=40, b=10, l=0, r=0), showlegend=False, title=dict(text="<b>Proporsi Emisi per Perangkat</b>", x=0.32, y=0.95, font=dict(size=12)))
                    st.plotly_chart(fig_devices, config=MODEBAR_CONFIG, use_container_width=True)
                else: st.info("Tidak ada data untuk perangkat dipilih.")
            else: st.info("Tidak ada data emisi perangkat.")

    with loading():
        col1, col2 = st.columns([1, 1])
        with col1:
            heatmap_df = get_heatmap_data(where_aktivitas, join_needed, selected_devices)
            if not heatmap_df.empty:
                pivot_df = heatmap_df.pivot_table(index='hari', columns='time_range', values='total_emisi', fill_value=0)
                try: 
                    sorted_columns = sorted(pivot_df.columns, key=lambda x: int(x.split(':')[0].split('-')[0]))
                    pivot_df = pivot_df[sorted_columns]
                except (ValueError, IndexError): pass
                pivot_df = pivot_df.reindex(index=DAY_ORDER, fill_value=0)
                if selected_days: pivot_df = pivot_df.loc[selected_days]
                if not pivot_df.empty and pivot_df.sum().sum() > 0:
                    fig_heatmap = go.Figure(data=go.Heatmap(z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index, colorscale=[[0, '#fee08b'], [0.25, '#fdae61'], [0.5, '#f46d43'], [0.75, '#d53e4f'], [1, '#9e0142']], hoverongaps=False, hovertemplate='<b>%{y}</b><br>Jam: %{x}<br>Emisi: %{z:.2f} kg CO₂<extra></extra>', xgap=1, ygap=1, colorbar=dict(title=dict(text="Emisi", font=dict(size=9)), tickfont=dict(size=10), thickness=15, len=0.7)))
                    fig_heatmap.update_layout(height=270, margin=dict(t=30, b=0, l=0, r=0), title=dict(text="<b>Heatmap Emisi Fasilitas</b>", x=0.3, y=0.95, font=dict(size=12)))
                    st.plotly_chart(fig_heatmap, config=MODEBAR_CONFIG, use_container_width=True)
                else: st.info("Tidak ada data heatmap untuk filter ini.")
            else: st.info("Tidak ada data heatmap untuk filter ini.")

        with col2:
            classroom_df = get_classroom_data(where_aktivitas, join_needed, selected_devices)
            if not classroom_df.empty:
                fig_location = go.Figure()
                classroom_df = classroom_df.sort_values('total_emisi', ascending=False)
                max_emisi, min_emisi = classroom_df['total_emisi'].max(), classroom_df['total_emisi'].min()
                for i, (_, row) in enumerate(classroom_df.iterrows()):
                    color_palette = ['#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#d53e4f']
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi) if max_emisi > min_emisi else 0
                    color = color_palette[int(ratio * (len(color_palette) - 1))]
                    display_name = row['lokasi'] if len(row['lokasi']) <= 12 else row['lokasi'][:10] + '..'
                    fig_location.add_trace(go.Bar(x=[display_name], y=[row['total_emisi']], marker=dict(color=color), showlegend=False, text=[f"{row['total_emisi']:.1f}"], textposition='auto', hovertemplate=f'<b>{row["lokasi"]}</b><br>Total Emisi: {row["total_emisi"]:.2f} kg CO₂<br>Jumlah Sesi: {row["session_count"]}<extra></extra>', name=row['lokasi']))
                avg_emisi_loc = classroom_df['total_emisi'].mean()
                fig_location.add_hline(y=avg_emisi_loc, line_dash="dash", line_color="#5e4fa2", line_width=2, annotation_text=f"Rata-rata: {avg_emisi_loc:.1f}")
                fig_location.update_layout(height=270, margin=dict(t=25, b=0, l=0, r=0), title=dict(text="<b>Gedung Kelas Paling Boros Energi</b>", x=0.3, y=0.95, font=dict(size=12)), yaxis_title="Total Emisi (kg CO2)")
                st.plotly_chart(fig_location, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data aktivitas kelas untuk filter ini.")

if __name__ == "__main__":
    show()