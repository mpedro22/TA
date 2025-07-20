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
DEVICE_COLORS = { 'HP': '#d53e4f', 'Laptop': '#3288bd', 'Tablet': '#66c2a5', 'AC': '#f46d43', 'Lampu': '#fdae61' }
MODEBAR_CONFIG = { 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': [ 'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d', 'resetCameraLastSave3d' ], 'toImageButtonOptions': { 'format': 'png', 'filename': 'carbon_emission_chart', 'height': 600, 'width': 800, 'scale': 2 } }
DAY_ORDER = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
PERSONAL_DEVICES = ['HP', 'Laptop', 'Tablet']
FACILITY_DEVICES = ['AC', 'Lampu']

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
    if 'HP' in selected_devices: personal_terms.append("COALESCE(t.durasi_hp, 0)*4")
    if 'Laptop' in selected_devices: personal_terms.append("COALESCE(t.durasi_laptop, 0)*50")
    if 'Tablet' in selected_devices: personal_terms.append("COALESCE(t.durasi_tab, 0)*10")
    personal_sum_clause = f"(({ ' + '.join(personal_terms) if personal_terms else '0' }) * 0.829 / 1000)"
    facility_terms = []
    if 'AC' in selected_devices: facility_terms.append("COALESCE(a.emisi_ac, 0)")
    if 'Lampu' in selected_devices: facility_terms.append("COALESCE(a.emisi_lampu, 0)")
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
        SELECT 'Laptop' as device, SUM((COALESCE(t.durasi_laptop, 0) * 50 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik} UNION ALL
        SELECT 'HP' as device, SUM((COALESCE(t.durasi_hp, 0) * 4 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik} UNION ALL
        SELECT 'Tablet' as device, SUM((COALESCE(t.durasi_tab, 0) * 10 * 0.829 / 1000) * COALESCE(array_length(string_to_array(t.hari_datang, ','), 1), 0)) as emisi FROM elektronik t {join_elektronik_sql} {where_elektronik}
    ), facility_devices AS (
        SELECT 'AC' as device, SUM(COALESCE(a.emisi_ac, 0)) as emisi FROM aktivitas_harian a {join_aktivitas_sql} {where_aktivitas} UNION ALL
        SELECT 'Lampu' as device, SUM(COALESCE(a.emisi_lampu, 0)) as emisi FROM aktivitas_harian a {join_aktivitas_sql} {where_aktivitas}
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
def get_filtered_elektronik_data(selected_fakultas, selected_days):
    """
    Mengambil data mentah dari tabel 'elektronik' yang difilter oleh fakultas dan hari datang.
    Digunakan untuk tombol 'Data'.
    """
    clauses = []
    join_sql = "LEFT JOIN v_informasi_fakultas_mahasiswa r ON e.id_mahasiswa = r.id_mahasiswa"

    if selected_fakultas:
        fakultas_str = ", ".join([f"'{f}'" for f in selected_fakultas])
        clauses.append(f"r.fakultas IN ({fakultas_str})")
    if selected_days:
        day_patterns = [f"'%{day}%'" for day in selected_days]
        clauses.append(f"e.hari_datang ILIKE ANY (ARRAY[{', '.join(day_patterns)}])")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

    query = f"""
    SELECT
        e.id_mahasiswa,
        COALESCE(r.fakultas, 'N/A') as fakultas,
        e.hari_datang,
        COALESCE(e.durasi_hp, 0) as durasi_hp,
        COALESCE(e.durasi_laptop, 0) as durasi_laptop,
        COALESCE(e.durasi_tab, 0) as durasi_tab,
        COALESCE(e.emisi_elektronik_pribadi, 0) as emisi_elektronik_pribadi,
        COALESCE(e.emisi_elektronik, 0) as emisi_elektronik
    FROM
        elektronik e
    {join_sql}
    {where_sql}
    """
    return run_sql(query)

@st.cache_data(ttl=3600)
@loading_decorator()
def generate_pdf_report(where_elektronik, where_aktivitas, join_needed, selected_days, selected_devices):
    from datetime import datetime
    import time # Pastikan ini sudah diimpor di bagian atas file
    
    time.sleep(0.6)
    
    df_daily = get_daily_trend_data(where_elektronik, where_aktivitas, join_needed, selected_devices)
    df_faculty = get_faculty_data(where_elektronik, where_aktivitas, selected_devices)
    df_devices = get_device_emissions_data(where_elektronik, where_aktivitas, join_needed)
    df_heatmap = get_heatmap_data(where_aktivitas, join_needed, selected_devices)
    df_classrooms = get_classroom_data(where_aktivitas, join_needed, selected_devices)
    
    # Filter df_devices based on selected_devices for accurate total_emisi
    df_devices_filtered = df_devices[df_devices['device'].isin(selected_devices)] if selected_devices else df_devices
    df_devices = df_devices_filtered[df_devices_filtered['emisi'].notna() & (df_devices_filtered['emisi'] > 0)]

    total_emisi = df_devices['emisi'].sum() if not df_devices.empty else 0
    
    total_mahasiswa_unik = 0
    try:
        unique_mhs_query = f"""
        WITH FilteredStudents AS (
            SELECT t.id_mahasiswa FROM elektronik t
            LEFT JOIN v_informasi_fakultas_mahasiswa r ON t.id_mahasiswa = r.id_mahasiswa
            {where_elektronik} AND (COALESCE(t.durasi_hp, 0) > 0 OR COALESCE(t.durasi_laptop, 0) > 0 OR COALESCE(t.durasi_tab, 0) > 0)
            UNION
            SELECT a.id_mahasiswa FROM aktivitas_harian a
            LEFT JOIN v_informasi_fakultas_mahasiswa r ON a.id_mahasiswa = r.id_mahasiswa
            {where_aktivitas} AND (COALESCE(a.emisi_ac, 0) > 0 OR COALESCE(a.emisi_lampu, 0) > 0)
        )
        SELECT COUNT(DISTINCT id_mahasiswa) as count FROM FilteredStudents
        """
        result = run_sql(unique_mhs_query)
        if not result.empty and 'count' in result.columns:
            total_mahasiswa_unik = result.iloc[0,0]
    except Exception as e:
        total_mahasiswa_unik = 0

    avg_emisi = total_emisi / total_mahasiswa_unik if total_mahasiswa_unik > 0 else 0

    # Validasi awal jika tidak ada data sama sekali setelah filter, return pesan default
    if total_emisi == 0 and total_mahasiswa_unik == 0 and df_daily.empty and df_faculty.empty and df_devices.empty and df_heatmap.empty and df_classrooms.empty:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan sesuaikan filter Anda dan coba lagi.</p></body></html>"

    # Inisialisasi default content
    daily_trend_table_html, trend_conclusion, trend_recommendation = ("<tr><td colspan='2'>Data tidak tersedia.</td></tr>", "Pola emisi harian tidak dapat diidentifikasi.", "Data tidak cukup untuk analisis tren.")
    fakultas_table_html, fakultas_conclusion, fakultas_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Distribusi emisi per fakultas tidak dapat dibuat.", "Data tidak cukup untuk analisis fakultas.")
    device_table_html, device_conclusion, device_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Proporsi emisi perangkat tidak dapat dianalisis.", "Data tidak cukup untuk analisis perangkat.")
    heatmap_header_html, heatmap_body_html, heatmap_conclusion, heatmap_recommendation = ("<tr><th>-</th></tr>", "<tr><td>Data tidak tersedia.</td></tr>", "Pola penggunaan fasilitas tidak teridentifikasi.", "Data tidak cukup untuk analisis heatmap.")
    location_table_html, location_conclusion, location_recommendation = ("<tr><td colspan='3'>Data tidak tersedia.</td></tr>", "Lokasi dengan konsumsi energi tertinggi tidak dapat ditentukan.", "Data tidak cukup untuk analisis lokasi.")
    
    # --- 1. Tren Emisi Harian ---
    # Judul: Tren Emisi Harian
    if not df_daily.empty and df_daily['total_emisi'].sum() > 0:
        df_daily_filtered_by_selection = df_daily[df_daily['hari'].isin(selected_days)] if selected_days else df_daily
        df_daily_filtered_by_selection['order'] = pd.Categorical(df_daily_filtered_by_selection['hari'], categories=DAY_ORDER, ordered=True)
        daily_df_sorted = df_daily_filtered_by_selection.sort_values('order')
        daily_trend_table_html = "".join([f"<tr><td>{row['hari']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for _, row in daily_df_sorted.iterrows()])
        
        if len(daily_df_sorted) > 1:
            peak_day_row = daily_df_sorted.loc[daily_df_sorted['total_emisi'].idxmax()]
            low_day_row = daily_df_sorted.loc[daily_df_sorted['total_emisi'].idxmin()]
            
            trend_conclusion = f"Puncak emisi terjadi pada hari <strong>{peak_day_row['hari']}</strong> ({peak_day_row['total_emisi']:.1f} kg CO<sub>2</sub>) dan terendah pada <strong>{low_day_row['hari']}</strong> ({low_day_row['total_emisi']:.1f} kg CO<sub>2</sub>). Ini menunjukkan variasi signifikan dalam penggunaan energi harian mahasiswa."
            trend_recommendation = f"Fokuskan program efisiensi dan kesadaran pada hari <strong>{peak_day_row['hari']}</strong>. Analisis aktivitas spesifik dapat memberikan petunjuk lebih lanjut untuk intervensi bertarget."
        elif len(daily_df_sorted) == 1:
            day_name = daily_df_sorted.iloc[0]['hari']
            day_emisi = daily_df_sorted.iloc[0]['total_emisi']
            trend_conclusion = f"Data tren emisi harian hanya tersedia untuk hari <strong>{day_name}</strong>, dengan total emisi {day_emisi:.1f} kg CO<sub>2</sub>. Analisis pola harian terbatas."
            trend_recommendation = "Perluas rentang hari pada filter untuk melihat tren komprehensif. Analisis hari ini dapat difokuskan pada komposisi perangkat dan lokasi."

    # --- 2. Emisi per Fakultas ---
    # Judul: Emisi per Fakultas
    if not df_faculty.empty and df_faculty['total_emisi'].sum() > 0:
        fakultas_stats_sorted = df_faculty.sort_values('total_emisi', ascending=False)
        # Tampilkan SEMUA fakultas yang memiliki emisi > 0
        fakultas_table_html = "".join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.2f}</td><td style='text-align:center;'>{int(row.get('total_count', 0))}</td></tr>" for _, row in fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iterrows()])
        
        if len(fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0]) > 1:
            highest_fakultas_row = fakultas_stats_sorted.iloc[0]
            lowest_fakultas_candidates = fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0]
            lowest_fakultas_row = lowest_fakultas_candidates.iloc[-1] if not lowest_fakultas_candidates.empty else highest_fakultas_row
            
            conclusion_detail = ""
            if lowest_fakultas_row['total_emisi'] > 0:
                emission_ratio = highest_fakultas_row['total_emisi'] / lowest_fakultas_row['total_emisi']
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> kontributor emisi elektronik tertinggi ({highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>), sekitar {emission_ratio:.1f}x lebih tinggi dari fakultas terendah <strong>{lowest_fakultas_row['fakultas']} ({lowest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>)</strong>."
            else:
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> kontributor emisi tertinggi ({highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>), sementara fakultas lain memiliki emisi mendekati nol."

            fakultas_conclusion = f"Terdapat perbedaan kontribusi emisi elektronik antar fakultas. {conclusion_detail} Ini mengindikasikan variasi penggunaan perangkat/fasilitas elektronik di tiap fakultas."
            fakultas_recommendation = f"Fokuskan intervensi pada Fakultas <strong>{highest_fakultas_row['fakultas']}</strong>. Analisis komposisi perangkat atau audit energi sederhana di gedung utama fakultas dapat memberikan dampak signifikan. Pelajari praktik terbaik dari Fakultas <strong>{lowest_fakultas_row['fakultas']}</strong>."
        else: # Hanya ada satu fakultas dengan emisi > 0
            if not fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].empty:
                fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iloc[0]['fakultas']}</strong>, dengan total emisi elektronik {fakultas_stats_sorted[fakultas_stats_sorted['total_emisi'] > 0].iloc[0]['total_emisi']:.1f} kg CO<sub>2</sub>. Perbandingan terbatas karena filter."
                fakultas_recommendation = "Perluas filter fakultas untuk perbandingan komprehensif atau pastikan data fakultas lain tersedia."
            else:
                fakultas_conclusion = "Tidak ada fakultas dengan emisi elektronik tercatat setelah filter."
                fakultas_recommendation = "Sesuaikan filter untuk mencakup fakultas dengan data emisi elektronik."

    # --- 3. Proporsi Emisi per Perangkat ---
    # Judul: Proporsi Emisi per Perangkat
    if not df_devices.empty and df_devices['emisi'].sum() > 0:
        df_devices_sorted = df_devices.sort_values('emisi', ascending=False)
        total_device_emission = df_devices_sorted['emisi'].sum()
        device_table_html = "".join([f"<tr><td>{row['device']}</td><td style='text-align:right;'>{row['emisi']:.2f}</td><td style='text-align:right;'>{(row['emisi']/total_device_emission*100 if total_device_emission > 0 else 0):.1f}%</td></tr>" for _, row in df_devices_sorted.iterrows()])
        
        dominant_device = df_devices_sorted.iloc[0]
        dominant_percentage = (dominant_device['emisi'] / total_device_emission) * 100
        
        device_conclusion = f"<strong>{dominant_device['device']}</strong> adalah kontributor utama emisi elektronik ({dominant_percentage:.0f}% dari total emisi perangkat). Ini menunjukkan fokus utama efisiensi energi."
        
        if dominant_device['device'] in FACILITY_DEVICES:
            device_recommendation = f"Fokus utama efisiensi pada fasilitas gedung. Pertimbangkan kebijakan operasional (timer/suhu AC) atau upgrade ke perangkat <strong>{dominant_device['device']}</strong> yang lebih hemat energi."
        else:
            device_recommendation = f"Fokus pada perilaku pengguna. Promosikan mode hemat daya untuk <strong>{dominant_device['device']}</strong>, dan kampanye untuk mencabut pengisi daya saat tidak digunakan."

    # --- 4. Pola Penggunaan Fasilitas Kampus ---
    # Judul: Pola Penggunaan Fasilitas Kampus
    if not df_heatmap.empty and df_heatmap['total_emisi'].sum() > 0:
        pivot_df = df_heatmap.pivot_table(index='hari', columns='time_range', values='total_emisi', fill_value=0)
        try:
            sorted_columns = sorted(pivot_df.columns, key=lambda x: int(x.split(':')[0].split('-')[0]))
            pivot_df = pivot_df[sorted_columns]
        except (ValueError, IndexError): pass
        pivot_df = pivot_df.reindex(index=DAY_ORDER, fill_value=0).dropna(how='all')
        if selected_days: pivot_df = pivot_df.loc[selected_days]
        
        if not pivot_df.empty and pivot_df.sum().sum() > 0:
            peak_usage_idx = pivot_df.stack().idxmax()
            peak_day, peak_time = peak_usage_idx[0], peak_usage_idx[1]
            heatmap_header_html = "<tr><th>Hari</th>" + "".join([f"<th>{time_slot}</th>" for time_slot in pivot_df.columns]) + "</tr>"
            body_rows_list = [f"<tr><td><strong>{day}</strong></td>" + "".join([f"<td style='text-align:center;'>{val:.2f}</td>" for val in row]) + "</tr>" for day, row in pivot_df.iterrows()]
            heatmap_body_html = "".join(body_rows_list)
            
            heatmap_conclusion = f"Puncak penggunaan fasilitas teridentifikasi pada hari <strong>{peak_day}</strong> di jam <strong>{peak_time}</strong>. Ini menunjukkan waktu paling intensif energi untuk AC dan/atau Lampu."
            heatmap_recommendation = "Jadikan waktu puncak ini acuan. Pertimbangkan sistem otomatisasi (timer AC/lampu) aktif sebelum dan non-aktif setelah jam sibuk untuk efisiensi maksimal."
        else:
            heatmap_conclusion = "Pola penggunaan fasilitas belum teridentifikasi. Data mungkin terlalu sedikit atau filter terlalu spesifik."
            heatmap_recommendation = "Perluas filter hari atau perangkat untuk analisis pola penggunaan fasilitas yang lebih komprehensif."
    else:
        heatmap_conclusion = "Pola penggunaan fasilitas belum teridentifikasi. Data tidak cukup untuk analisis heatmap."
        heatmap_recommendation = "Perluas filter hari atau perangkat untuk analisis pola penggunaan fasilitas yang lebih komprehensif."

    # --- 5. Lokasi Kelas Paling Intensif Energi ---
    # Judul: Lokasi Kelas Paling Intensif Energi
    if not df_classrooms.empty and df_classrooms['total_emisi'].sum() > 0:
        location_stats_sorted = df_classrooms.sort_values('total_emisi', ascending=False)
        # Tampilkan SEMUA lokasi yang memiliki emisi > 0
        location_table_html = "".join([f"<tr><td>{row['lokasi']}</td><td style='text-align:center;'>{int(row['session_count'])}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for _, row in location_stats_sorted[location_stats_sorted['total_emisi'] > 0].iterrows()])
        
        if len(location_stats_sorted[location_stats_sorted['total_emisi'] > 0]) > 0:
            highest_emission_loc_row = location_stats_sorted.iloc[0]
            location_conclusion = f"Gedung/Ruang <strong>{highest_emission_loc_row['lokasi']}</strong> adalah lokasi dengan konsumsi energi tertinggi untuk kegiatan kelas ({highest_emission_loc_row['total_emisi']:.1f} kg CO<sub>2</sub> dari {highest_emission_loc_row['session_count']} sesi)."
            location_recommendation = f"Lokasi ini kandidat utama proyek efisiensi energi. Audit sederhana pada perangkat AC dan pencahayaan di <strong>{highest_emission_loc_row['lokasi']}</strong> dapat memberikan insight cepat untuk potensi penghematan."
        else:
            location_conclusion = "Tidak ada lokasi kelas dengan konsumsi energi tercatat setelah filter."
            location_recommendation = "Coba sesuaikan filter untuk mencakup lokasi kelas dengan data aktivitas."

    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Emisi Elektronik</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
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
        .recommendation {{ background: #fffbeb; border-left: 4px solid #f59e0b; }} /* Changed back to 4px from 44px */
        ul {{ padding-left: 20px; margin-top: 8px; margin-bottom: 0; }} li {{ margin-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }} th, td {{ padding: 8px; text-align: left; border: 1px solid #e5e7eb; }}
        th {{ background-color: #f3f4f6; font-weight: 600; text-align: center; }}
        td:first-child {{ font-weight: 500; }}
    </style></head>
    <body><div class="page">
        <div class="header"><h1>Laporan Emisi Elektronik</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO<sub>2</sub></strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO<sub>2</sub></strong>Rata-rata/Mahasiswa</div>
        </div>
        <h2>1. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{daily_trend_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        <h2>2. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Jumlah Mahasiswa</th></tr></thead><tbody>{fakultas_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>
        <h2>3. Proporsi Emisi per Perangkat</h2>
        <table><thead><tr><th>Perangkat</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Persentase</th></tr></thead><tbody>{device_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {device_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {device_recommendation}</div>
        <h2>4. Pola Penggunaan Fasilitas Kampus</h2>
        <table><thead>{heatmap_header_html}</thead><tbody>{heatmap_body_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {heatmap_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {heatmap_recommendation}</div>
        <h2>5. Lokasi Kelas Paling Intensif Energi</h2>
        <table><thead><tr><th>Gedung</th><th>Jumlah Sesi</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>{location_table_html}</tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {location_conclusion}</div><div class="recommendation"><strong>Rekomendasi:</strong> {location_recommendation}</div>
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
        selected_devices_input = st.multiselect("Perangkat:", options=device_options, placeholder="Pilih Opsi", key='electronic_device_filter')
        if not selected_devices_input: 
            selected_devices = PERSONAL_DEVICES + FACILITY_DEVICES 
        else:
            selected_devices = selected_devices_input
    with filter_col3:
        fakultas_df = run_sql("SELECT DISTINCT fakultas FROM v_informasi_fakultas_mahasiswa WHERE fakultas IS NOT NULL AND fakultas <> '' ORDER BY fakultas")
        available_fakultas = fakultas_df['fakultas'].tolist() if not fakultas_df.empty else []
        selected_fakultas = st.multiselect("Fakultas:", options=available_fakultas, placeholder="Pilih Opsi", key='electronic_fakultas_filter')

    where_elektronik, where_aktivitas, join_needed = build_universal_where_clause(selected_fakultas, selected_days)

    with export_col1:
        # Ambil data mentah yang difilter untuk diunduh
        data_df = get_filtered_elektronik_data(selected_fakultas, selected_days)
        st.download_button(
            "Data", 
            data=data_df.to_csv(index=False), # Pastikan ini adalah data yang valid
            file_name=f"electronic_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=(data_df.empty) # Tombol aktif jika ada data
        )
    with export_col2:
        try:
            pdf_data = generate_pdf_report(where_elektronik, where_aktivitas, join_needed, selected_days, selected_devices)
            
            if pdf_data: 
                st.download_button(
                    label="Laporan",
                    data=pdf_data,
                    file_name=f"electronic_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
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
                    fig_trend.update_layout(height=270, margin=dict(t=25, b=0, l=0, r=20), title=dict(text="<b>Tren Emisi Harian</b>", x=0.38, y=0.95, font=dict(size=12)), xaxis_title="Hari", yaxis_title="Emisi (kg CO₂)", font=dict(size=10))
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
                fig_fakultas.update_layout(height=270, margin=dict(t=40, b=0, l=0, r=20), title=dict(text="<b>Emisi per Fakultas</b>", x=0.4, y=0.95, font=dict(size=12)), xaxis_title="Emisi (kg CO₂)", yaxis_title="Fakultas", font=dict(size=8))
                st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data fakultas untuk filter ini.")
            
        with col3:
            device_emissions_df = get_device_emissions_data(where_elektronik, where_aktivitas, join_needed)
            if not device_emissions_df.empty:
                display_devices = device_emissions_df.copy()
                # Tidak perlu filter di sini karena _get_dynamic_emission_clauses sudah menggunakan selected_devices
                # dan selected_devices sudah di-default di atas.
                
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
                    fig_heatmap.update_layout(height=270, margin=dict(t=30, b=0, l=0, r=0), title=dict(text="<b>Heatmap Emisi Harian per Jam</b>", x=0.3, y=0.95, font=dict(size=12)), xaxis_title="Hari", yaxis_title="Waktu", font=dict(size=8))
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
                fig_location.update_layout(height=270, margin=dict(t=25, b=0, l=0, r=0), title=dict(text="<b>Emisi per Lokasi</b>", x=0.5   , y=0.95, font=dict(size=12)), xaxis_title="Lokasi", yaxis_title="Emisi (kg CO₂)", font=dict(size=8))
                st.plotly_chart(fig_location, config=MODEBAR_CONFIG, use_container_width=True)
            else: st.info("Tidak ada data aktivitas kelas untuk filter ini.")

if __name__ == "__main__":
    show()