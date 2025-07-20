import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src.components.loading import loading, loading_decorator
import time
import warnings
warnings.filterwarnings('ignore')
from src.utils.db_connector import run_sql
from io import BytesIO
from xhtml2pdf import pisa

CATEGORY_COLORS = {'Transportasi': '#d53e4f', 'Elektronik': '#3288bd', 'Sampah': '#66c2a5'}
PROFILE_COLOR_MAP = {
    "Kontributor Utama": "#9e0142", "Komuter & Digital": "#d53e4f", "Komuter & Boros Pangan": "#f46d43",
    "Digital & Boros Pangan": "#fdae61", "Komuter Berat": "#fee08b", "Pengguna Elektronik Berat": "#e6f598",
    "Boros Pangan": "#abdda4", "Sangat Sadar Lingkungan": "#66c2a5", "Profil Campuran": "#3288bd"
}
MODEBAR_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'pan2d', 'pan3d', 'select2d', 'lasso2d', 'zoom2d', 'zoom3d', 'zoomIn2d', 'zoomOut2d',
        'autoScale2d', 'resetScale2d', 'resetScale3d', 'hoverClosestCartesian', 'hoverCompareCartesian',
        'toggleSpikelines', 'hoverClosest3d', 'orbitRotation', 'tableRotation',
        'resetCameraDefault3d', 'resetCameraLastSave3d'
    ],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'carbon_emission_chart',
        'height': 600,
        'width': 800,
        'scale': 2
    }
}
DAY_ORDER = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

@st.cache_data(ttl=3600)
def get_all_student_periodic_emissions() -> pd.DataFrame:
    """
    Mengambil total emisi per kategori per mahasiswa dari v_emisi_per_mahasiswa.
    Data ini bersifat AGREGASI MINGGUAN/KESELURUHAN per mahasiswa.
    Digunakan sebagai sumber data utama jika TIDAK ada filter 'Hari' yang aktif.
    """
    query = """
    SELECT
        ve.id_mahasiswa,
        COALESCE(TRIM(vim.fakultas), 'Unknown') AS fakultas,
        COALESCE(ve.transportasi, 0) AS transportasi,
        COALESCE(ve.elektronik, 0) AS elektronik,
        COALESCE(ve.sampah_makanan, 0) AS sampah_makanan
    FROM
        v_emisi_per_mahasiswa ve
    LEFT JOIN
        v_informasi_fakultas_mahasiswa vim ON ve.id_mahasiswa = vim.id_mahasiswa
    """
    df = run_sql(query)
    df['fakultas'] = df['fakultas'].str.strip()
    return df

@st.cache_data(ttl=3600)
def get_daily_activity_emissions_for_trend(selected_fakultas: list, selected_days: list, selected_categories: list) -> pd.DataFrame:
    """
    Mengambil emisi harian berdasarkan aktivitas dari tabel-tabel detail.
    Ini adalah sumber data granular utama untuk chart Tren Emisi Harian (selalu).
    Ini juga menjadi sumber data utama untuk semua visualisasi jika ada filter 'Hari' yang aktif.
    Filter langsung diterapkan di level SQL.
    """
    
    where_clauses = []
    
    if selected_days:
        days_str = ", ".join([f"'{day}'" for day in selected_days])
        where_clauses.append(f"de.hari IN ({days_str})")
    
    if selected_categories:
        categories_str = ", ".join([f"'{cat}'" for cat in selected_categories])
        where_clauses.append(f"de.kategori IN ({categories_str})")

    if selected_fakultas:
        clean_selected_fakultas = [f.strip() for f in selected_fakultas]
        fakultas_str = ", ".join([f"'{f}'" for f in clean_selected_fakultas])
        where_clauses.append(f"COALESCE(TRIM(vim.fakultas), 'Unknown') IN ({fakultas_str})") 
    
    final_where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
    WITH DailyEmissions AS (
        -- 1. Emisi Transportasi per hari
        SELECT
            t.id_mahasiswa,
            TRIM(UNNEST(STRING_TO_ARRAY(t.hari_datang, ','))) AS hari,
            'Transportasi' AS kategori,
            COALESCE(t.emisi_transportasi, 0.0) AS emisi
        FROM transportasi t
        WHERE t.hari_datang IS NOT NULL AND TRIM(t.hari_datang) <> '' AND COALESCE(t.emisi_transportasi, 0.0) > 0.0 -- Tambahkan ini
        
        UNION ALL
        
        -- 2. Emisi Elektronik (Pribadi) per hari
        SELECT
            e.id_mahasiswa,
            TRIM(UNNEST(STRING_TO_ARRAY(e.hari_datang, ','))) AS hari,
            'Elektronik' AS kategori,
            (COALESCE(e.emisi_elektronik, 0.0) / NULLIF(COALESCE(array_length(string_to_array(e.hari_datang, ','), 1), 0), 0)) AS emisi
        FROM elektronik e
        WHERE e.hari_datang IS NOT NULL AND TRIM(e.hari_datang) <> '' 
          AND COALESCE(array_length(string_to_array(e.hari_datang, ','), 1), 0) > 0
          AND COALESCE(e.emisi_elektronik, 0.0) > 0.0 -- Tambahkan ini
        
        UNION ALL

        -- 3. Emisi Elektronik (Fasilitas: AC & Lampu) per hari
        SELECT
            ah.id_mahasiswa,
            TRIM(ah.hari) AS hari,
            'Elektronik' AS kategori,
            (COALESCE(ah.emisi_ac, 0.0) + COALESCE(ah.emisi_lampu, 0.0)) AS emisi
        FROM aktivitas_harian ah
        WHERE ah.hari IS NOT NULL AND TRIM(ah.hari) <> ''
          AND (COALESCE(ah.emisi_ac, 0.0) > 0.0 OR COALESCE(ah.emisi_lampu, 0.0) > 0.0)

        UNION ALL
        
        -- 4. Emisi Sampah per hari
        SELECT
            m.id_mahasiswa,
            TRIM(m.hari) AS hari,
            'Sampah' AS kategori,
            COALESCE(m.emisi_sampah_makanan_per_waktu, 0.0) AS emisi
        FROM v_aktivitas_makanan m
        WHERE m.emisi_sampah_makanan_per_waktu IS NOT NULL AND m.emisi_sampah_makanan_per_waktu > 0.0
          AND m.hari IS NOT NULL AND TRIM(m.hari) <> ''
    )
    SELECT
        de.id_mahasiswa,
        COALESCE(TRIM(vim.fakultas), 'Unknown') AS fakultas,
        de.hari,
        de.kategori,
        SUM(de.emisi) AS emisi
    FROM DailyEmissions de
    LEFT JOIN v_informasi_fakultas_mahasiswa vim ON de.id_mahasiswa = vim.id_mahasiswa
    {final_where_sql}
    GROUP BY de.id_mahasiswa, vim.fakultas, de.hari, de.kategori
    """
    df = run_sql(query)
    df['fakultas'] = df['fakultas'].str.strip()
    return df

def create_behavior_profile(row, thresholds):
    """Mengklasifikasikan responden ke dalam profil perilaku berdasarkan ambang batas emisi."""
    t_val = row['transportasi'] if 'transportasi' in row and not pd.isna(row['transportasi']) else 0.0
    e_val = row['elektronik'] if 'elektronik' in row and not pd.isna(row['elektronik']) else 0.0
    f_val = row['sampah_makanan'] if 'sampah_makanan' in row and not pd.isna(row['sampah_makanan']) else 0.0

    t_level = "Tinggi" if t_val > thresholds.get('transportasi', 0) else "Rendah"
    e_level = "Tinggi" if e_val > thresholds.get('elektronik', 0) else "Rendah"
    f_level = "Tinggi" if f_val > thresholds.get('sampah_makanan', 0) else "Rendah"
    
    if t_level == "Tinggi" and e_level == "Tinggi" and f_level == "Tinggi": return "Kontributor Utama"
    if t_level == "Rendah" and e_level == "Rendah" and f_level == "Rendah": return "Sangat Sadar Lingkungan"
    if t_level == "Tinggi" and e_level == "Tinggi": return "Komuter & Digital"
    if t_level == "Tinggi" and f_level == "Tinggi": return "Komuter & Boros Pangan"
    if e_level == "Tinggi" and f_level == "Tinggi": return "Digital & Boros Pangan"
    if t_level == "Tinggi": return "Komuter Berat"
    if e_level == "Tinggi": return "Pengguna Elektronik Berat"
    if f_level == "Tinggi": return "Boros Pangan"
    return "Profil Campuran"

@st.cache_data(ttl=3600)
@loading_decorator()
def generate_overview_pdf_report(filtered_agg_df_for_report, daily_pivot_for_report, fakultas_stats_for_report, num_responden_unique_pdf: int):
    """
    Menghasilkan laporan overview komprehensif dalam format PDF.
    """
    from datetime import datetime
    time.sleep(0.6) 

    if filtered_agg_df_for_report.empty:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda dan coba lagi.</p></body></html>"

    total_emisi = filtered_agg_df_for_report['total_emisi'].sum()
    avg_emisi = total_emisi / num_responden_unique_pdf if num_responden_unique_pdf > 0 else 0

    composition_data = {
        'Transportasi': filtered_agg_df_for_report['transportasi'].sum() if 'transportasi' in filtered_agg_df_for_report.columns else 0.0, 
        'Elektronik': filtered_agg_df_for_report['elektronik'].sum() if 'elektronik' in filtered_agg_df_for_report.columns else 0.0, 
        'Sampah': filtered_agg_df_for_report['sampah_makanan'].sum() if 'sampah_makanan' in filtered_agg_df_for_report.columns else 0.0
    }
    
    # Filter out categories with zero emission for a more relevant conclusion
    composition_data_filtered_for_conclusion = {k: v for k, v in composition_data.items() if v > 0}
    
    dominant_cat = "Tidak Tersedia"
    dominant_pct = 0
    secondary_cat = "Tidak Tersedia"
    secondary_pct = 0

    if total_emisi > 0 and composition_data_filtered_for_conclusion:
        sorted_comp = sorted(composition_data_filtered_for_conclusion.items(), key=lambda item: item[1], reverse=True)
        dominant_cat = sorted_comp[0][0]
        dominant_pct = (sorted_comp[0][1] / total_emisi * 100)
        
        if len(sorted_comp) > 1:
            secondary_cat = sorted_comp[1][0]
            secondary_pct = (sorted_comp[1][1] / total_emisi * 100)

        composition_conclusion = f"Sumber emisi utama adalah <strong>{dominant_cat}</strong>, menyumbang <strong>{dominant_pct:.1f}%</strong> dari total emisi ({total_emisi:.1f} kg CO<sub>2</sub>) sesuai filter yang aktif. {f'Kategori kedua terbesar adalah {secondary_cat} sebesar {secondary_pct:.1f}%.' if secondary_cat != 'Tidak Tersedia' else ''} Proporsi ini mengindikasikan area utama yang perlu menjadi fokus strategis untuk inisiatif pengurangan emisi."
        
    else:
        composition_conclusion = "Data komposisi emisi tidak tersedia atau semua kategori memiliki emisi nol setelah filter diterapkan. Tidak dapat menentukan sumber emisi dominan."

    rec_map_cat = {
        'Transportasi': "Dorong penggunaan transportasi publik, sepeda, atau jalan kaki dengan menyediakan fasilitas yang memadai (misal: rute aman, parkir sepeda). Pertimbangkan insentif bagi pengguna moda berkelanjutan dan evaluasi kebijakan parkir kendaraan pribadi di kampus.",
        'Elektronik': "Tingkatkan efisiensi energi di fasilitas kampus (misal: penggantian lampu LED, optimasi sistem pendingin ruangan). Edukasi mahasiswa dan staf untuk praktik hemat energi seperti mematikan perangkat yang tidak digunakan dan memanfaatkan mode hemat daya.",
        'Sampah': "Implementasikan kampanye pengurangan limbah makanan yang konkret seperti 'Jangan Sisakan Makanan'. Dukung program pengolahan sampah organik (komposting) dan jalin kerja sama dengan kantin untuk manajemen porsi yang lebih baik serta penanganan sisa makanan."
    }
    composition_recommendation = rec_map_cat.get(dominant_cat, "Rekomendasi spesifik berdasarkan komposisi emisi belum dapat diberikan karena data tidak memadai atau semua kategori memiliki emisi nol.")

    peak_day = "Tidak Tersedia"
    peak_emisi = 0
    daily_pivot_for_report_reindexed = daily_pivot_for_report.reindex(DAY_ORDER).fillna(0.0)
    
    if not daily_pivot_for_report_reindexed.empty and daily_pivot_for_report_reindexed.sum().sum() > 0:
        daily_totals = daily_pivot_for_report_reindexed.sum(axis=1) 
        if not daily_totals.empty and daily_totals.max() > 0:
            peak_day = daily_totals.idxmax()
            peak_emisi = daily_totals.max()
            trend_conclusion = f"Emisi harian tertinggi cenderung terjadi pada hari <strong>{peak_day}</strong>, dengan total <strong>{peak_emisi:.1f} kg CO<sub>2</sub></strong>. Pola ini mungkin terkait dengan intensitas aktivitas akademik dan operasional kampus pada hari tersebut."
            trend_recommendation = f"Fokuskan program kesadaran dan efisiensi energi pada hari <strong>{peak_day}</strong>. Lakukan analisis lebih lanjut terhadap jenis aktivitas spesifik yang menyumbang emisi tinggi pada hari tersebut untuk intervensi yang lebih bertarget (misal: optimasi jadwal penggunaan fasilitas)."
        else:
            trend_conclusion = "Tidak ada pola emisi harian yang menonjol atau emisi terdistribusi secara merata di antara hari-hari yang dipilih."
            trend_recommendation = "Lanjutkan pemantauan tren harian. Jika terjadi lonjakan emisi, identifikasi pemicunya. Dorong partisipasi yang lebih luas dalam pengisian data aktivitas untuk gambaran tren yang lebih jelas."
    else:
        trend_conclusion = "Data tren emisi harian tidak tersedia untuk analisis setelah filter diterapkan."
        trend_recommendation = "Pastikan data aktivitas harian dikumpulkan secara konsisten dan mencukupi untuk memungkinkan analisis tren yang bermanfaat."

    fakultas_report_html = "<tr><td colspan='2'>Data tidak tersedia.</td></tr>" 
    fakultas_conclusion = "Data emisi per fakultas tidak cukup untuk analisis komparatif (diperlukan minimal 2 fakultas dengan data emisi yang valid)."
    fakultas_recommendation = "Dorong partisipasi lebih banyak mahasiswa dari berbagai fakultas untuk mendapatkan perbandingan yang lebih komprehensif dan representatif."
    
    if not fakultas_stats_for_report.empty and fakultas_stats_for_report['total_emisi'].sum() > 0:
        fakultas_report = fakultas_stats_for_report.sort_values('total_emisi', ascending=False)
        # Menampilkan SEMUA fakultas, bukan hanya top 10
        fakultas_report_html = ''.join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for idx, row in fakultas_report.iterrows()])
        
        if len(fakultas_report) > 1:
            highest_fakultas_row = fakultas_report.iloc[0]
            lowest_fakultas_row = fakultas_report.iloc[-1]
            
            conclusion_detail = ""
            if lowest_fakultas_row['total_emisi'] > 0:
                emission_ratio = highest_fakultas_row['total_emisi'] / lowest_fakultas_row['total_emisi']
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> menunjukkan emisi tertinggi dengan <strong>{highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub></strong>, sekitar {emission_ratio:.1f} kali lebih tinggi dari fakultas dengan emisi terendah, <strong>{lowest_fakultas_row['fakultas']} ({lowest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>)</strong>."
            else:
                conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> memiliki emisi tertinggi sebesar <strong>{highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub></strong>, sementara beberapa fakultas lain memiliki emisi mendekati nol atau nol."

            fakultas_conclusion = f"Terdapat variasi signifikan emisi antar fakultas. {conclusion_detail} Pola ini mungkin mengindikasikan perbedaan dalam kebiasaan penggunaan sumber daya atau aktivitas spesifik yang menghasilkan emisi di tiap fakultas."
            fakultas_recommendation = f"Fasilitasi program 'benchmarking' antar fakultas (misal: studi kasus dari Fakultas <strong>{lowest_fakultas_row['fakultas']}</strong> ke <strong>{highest_fakultas_row['fakultas']}</strong>). Lakukan audit energi dan limbah yang lebih spesifik untuk fakultas dengan emisi tinggi guna mengidentifikasi sumber emisi terbesar dan potensi pengurangan yang optimal."
        else: 
            fakultas_conclusion = f"Data hanya mencakup Fakultas <strong>{fakultas_report.iloc[0]['fakultas']}</strong> setelah filter diterapkan. Perbandingan lintas fakultas tidak dapat dilakukan."
            fakultas_recommendation = "Perluas filter fakultas untuk mendapatkan perbandingan yang lebih komprehensif atau pastikan data dari fakultas lain tersedia."

    segmentation_table_html = "<tr><td colspan='5'>Data tidak cukup untuk segmentasi.</td></tr>"
    segmentation_conclusion = "Tidak dapat membuat profil perilaku mahasiswa karena data responden terbatas (diperlukan minimal 6 responden unik setelah filter diterapkan untuk analisis ini)."
    segmentation_recommendation = "Tingkatkan jumlah responden yang mengisi data untuk mendapatkan gambaran profil perilaku yang lebih akurat dan dapat digunakan untuk kebijakan yang lebih bertarget dan efektif."

    if num_responden_unique_pdf > 5: 
        if not filtered_agg_df_for_report.empty:
            # Handle potential NaNs from median if all values are zero or missing after filtering
            median_transportasi = filtered_agg_df_for_report['transportasi'].median() if 'transportasi' in filtered_agg_df_for_report.columns else 0.0
            median_elektronik = filtered_agg_df_for_report['elektronik'].median() if 'elektronik' in filtered_agg_df_for_report.columns else 0.0
            median_sampah = filtered_agg_df_for_report['sampah_makanan'].median() if 'sampah_makanan' in filtered_agg_df_for_report.columns else 0.0

            # Pastikan nilai median yang mungkin NaN diubah menjadi 0
            median_transportasi = 0.0 if pd.isna(median_transportasi) else median_transportasi
            median_elektronik = 0.0 if pd.isna(median_elektronik) else median_elektronik
            median_sampah = 0.0 if pd.isna(median_sampah) else median_sampah

            thresholds = {
                'transportasi': median_transportasi,
                'elektronik': median_elektronik,
                'sampah_makanan': median_sampah
            }
            
            df_with_profile = filtered_agg_df_for_report.copy()
            df_with_profile['profil_perilaku'] = df_with_profile.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
            
            profile_stats = df_with_profile.groupby('profil_perilaku').agg(
                jumlah_mahasiswa=('id_mahasiswa', 'count'),
                avg_transportasi=('transportasi', 'mean'),
                avg_elektronik=('elektronik', 'mean'),
                avg_sampah=('sampah_makanan', 'mean')
            ).sort_values('jumlah_mahasiswa', ascending=False).reset_index()

            if not profile_stats.empty:
                segmentation_table_html = "".join([
                    f"<tr><td><strong>{row['profil_perilaku']}</strong></td>"
                    f"<td style='text-align:center;'>{row['jumlah_mahasiswa']}</td>"
                    f"<td style='text-align:right;'>{row['avg_transportasi']:.2f}</td>"
                    f"<td style='text-align:right;'>{row['avg_elektronik']:.2f}</td>"
                    f"<td style='text-align:right;'>{row['avg_sampah']:.2f}</td></tr>"
                    for _, row in profile_stats.iterrows()])
                
                dominant_profile = profile_stats.iloc[0]['profil_perilaku']
                dominant_count = profile_stats.iloc[0]['jumlah_mahasiswa']
                avg_transport_dom = profile_stats.iloc[0]['avg_transportasi']
                avg_elektronik_dom = profile_stats.iloc[0]['avg_elektronik']
                avg_sampah_dom = profile_stats.iloc[0]['avg_sampah']
                
                segmentation_conclusion = f"Analisis perilaku mengidentifikasi '<strong>{dominant_profile}</strong>' sebagai kelompok terbesar dengan <strong>{dominant_count}</strong> mahasiswa. Kelompok ini memiliki rata-rata emisi transportasi {avg_transport_dom:.2f} kg CO<sub>2</sub>, elektronik {avg_elektronik_dom:.2f} kg CO<sub>2</sub>, dan sampah {avg_sampah_dom:.2f} kg CO<sub>2</sub>. Memahami profil ini membantu menentukan strategi pengurangan emisi yang tepat sasaran."
                
                rec_map_behavior = {
                    "Kontributor Utama": "Prioritaskan kelompok ini dengan program edukasi dan insentif yang menyeluruh, seperti 'Green Campus Challenge' dengan hadiah atau panduan personal tentang efisiensi energi dan promosi gaya hidup minim emisi.",
                    "Komuter & Digital": "Fokus pada transportasi berkelanjutan (misal: promo tiket bus/kereta, diskon sewa sepeda) dan kampanye penghematan energi perangkat elektronik (misal: 'Cabut Chargermu!').",
                    "Komuter & Boros Pangan": "Kombinasikan program transportasi berkelanjutan dengan inisiatif pengurangan limbah makanan, seperti workshop masak minim sisa atau kerja sama dengan kantin untuk opsi porsi kecil/program makanan sisa.",
                    "Digital & Boros Pangan": "Targetkan dengan kampanye 'Hemat Energi Layar' untuk perangkat dan 'Habiskan Porsi Makananmu' di area makan. Pertimbangkan aplikasi pelacak emisi yang menyoroti dampak dari kebiasaan digital dan pangan.",
                    "Komuter Berat": "Perluas pilihan transportasi alternatif, seperti penyediaan lebih banyak shuttle bus kampus, hari 'Tanpa Kendaraan Pribadi' dengan hadiah, atau dukungan komunitas carpooling mahasiswa.",
                    "Pengguna Elektronik Berat": "Edukasi mendalam tentang konsumsi daya perangkat. Promosikan penggunaan mode hemat daya, berikan daftar perangkat elektronik efisien, atau tawarkan audit energi kecil untuk ruang kerja/belajar.",
                    "Boros Pangan": "Fokus pada edukasi tentang dampak limbah makanan, seperti kampanye 'Piring Bersih', program donasi makanan berlebih ke komunitas, atau kerja sama dengan katering kampus untuk mengurangi sisa produksi.",
                    "Sangat Sadar Lingkungan": "Libatkan mereka sebagai 'Duta Lingkungan' atau mentor bagi mahasiswa lain. Berikan platform untuk berbagi praktik terbaik dan ide-ide inovatif untuk keberlanjutan kampus.",
                    "Profil Campuran": "Sediakan materi edukasi umum yang mudah diakses (infografis, video singkat) tentang sumber emisi utama dan tips sederhana untuk mengurangi jejak karbon dalam kehidupan kampus sehari-hari."
                }
                rekomendasi_utama = rec_map_behavior.get(dominant_profile, rec_map_behavior["Profil Campuran"])
                segmentation_recommendation = f"Kebijakan kampus perlu disesuaikan untuk profil '<strong>{dominant_profile}</strong>'. {rekomendasi_utama}"
        else:
            segmentation_conclusion = "Tidak ada data emisi yang cukup untuk analisis segmentasi perilaku setelah filter diterapkan."
            segmentation_recommendation = "Coba sesuaikan filter Anda untuk mencakup lebih banyak responden."

    composition_table_html = ''.join([f"<tr><td>{cat}</td><td style='text-align:right;'>{val:.1f}</td><td style='text-align:right;'>{(val/total_emisi*100 if total_emisi>0 else 0):.1f}%</td></tr>" for cat, val in composition_data.items()])
    
    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Overview</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
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
        <div class="header"><h1>Laporan Overview Emisi Karbon</h1><p>Institut Teknologi Bandung | Dibuat pada: {datetime.now().strftime('%d %B %Y')}</p></div>
        <div class="grid">
            <div class="card primary"><strong>{total_emisi:.1f} kg CO<sub>2</sub></strong>Total Emisi</div>
            <div class="card secondary"><strong>{avg_emisi:.2f} kg CO<sub>2</sub></strong>Rata-rata per Mahasiswa</div>
        </div>
        <h2>1. Emisi per Fakultas</h2>
        <table><thead><tr><th>Fakultas</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>
        {fakultas_report_html}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>

        <h2>2. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>
        {''.join([f"<tr><td>{day}</td><td style='text-align:right;'>{daily_pivot_for_report_reindexed.loc[day].sum():.1f}</td></tr>" for day in daily_pivot_for_report_reindexed.index if daily_pivot_for_report_reindexed.loc[day].sum() > 0]) if not daily_pivot_for_report_reindexed.empty and daily_pivot_for_report_reindexed.sum().sum() > 0 else "<tr><td colspan='2'>Data tidak tersedia.</td></tr>"}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {trend_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {trend_recommendation}</div>
        
        <h2>3. Komposisi Emisi</h2>
        <table><thead><tr><th>Kategori</th><th>Total Emisi (kg CO<sub>2</sub>)</th><th>Persentase</th></tr></thead><tbody>
        {composition_table_html}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {composition_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {composition_recommendation}</div>

        <h2>4. Segmentasi Perilaku</h2>
        <table><thead>
            <tr><th>Profil Klaster</th><th>Jumlah Mahasiswa</th><th>Rata-rata Emisi Transportasi</th><th>Rata-rata Emisi Elektronik</th><th>Rata-rata Emisi Makanan</th></tr>
        </thead><tbody>
            {segmentation_table_html}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {segmentation_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {segmentation_recommendation}</div>
    </div></body></html>
    """

    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(src=html_content, dest=pdf_buffer)     
    if pisa_status.err:
        st.error("Gagal membuat PDF. Periksa format HTML atau instalasi pustaka.")
        return None 
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_bytes

def show():
    """Fungsi untuk menampilkan halaman Dashboard Utama."""
    st.markdown("""
        <style>.kpi-card{padding:1rem;border-radius:8px;text-align:center;background-color:#f8f9fa}.kpi-value{font-size:2em;font-weight:600}.kpi-label{font-size:0.9em;color:#555}.primary{border-left:4px solid #10b981}.primary .kpi-value{color:#059669}.secondary{border-left:4px solid #3b82f6}.secondary .kpi-value{color:#3b82f6}</style>
        <div class="wow-header"><div class="header-bg-pattern"></div><div class="header-float-1"></div><div class="header-float-2"></div><div class="header-float-3"></div><div class="header-float-4"></div><div class="header-float-5"></div><div class="header-content"><h1 class="header-title">Dashboard Utama</h1></div></div>
        """, unsafe_allow_html=True)
    time.sleep(0.25)

    with loading():
        base_all_student_data_for_fakultas_list = get_all_student_periodic_emissions()
        available_fakultas = sorted(base_all_student_data_for_fakultas_list['fakultas'].unique())
        if 'Unknown' in available_fakultas:
            available_fakultas.remove('Unknown') 
            available_fakultas.sort()
            available_fakultas.insert(0, 'Unknown') 
    
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])
    with filter_col1:
        selected_days = st.multiselect("Hari:", DAY_ORDER, placeholder="Pilih Opsi", key='overview_day_filter')
    with filter_col2:
        selected_categories = st.multiselect("Jenis:", ['Transportasi', 'Elektronik', 'Sampah'], placeholder="Pilih Opsi", key='overview_category_filter')
    with filter_col3:
        selected_fakultas = st.multiselect("Fakultas:", available_fakultas, placeholder="Pilih Opsi", key='overview_fakultas_filter')
    
    cleaned_selected_fakultas = [f.strip() for f in selected_fakultas] if selected_fakultas else []

    with loading():
        if not selected_days: 
            main_source_for_kpis_segments = get_all_student_periodic_emissions()

            if cleaned_selected_fakultas:
                main_source_for_kpis_segments = main_source_for_kpis_segments[main_source_for_kpis_segments['fakultas'].isin(cleaned_selected_fakultas)]
            
            if selected_categories:
                temp_df_for_category_filter = main_source_for_kpis_segments.copy()
                if 'Transportasi' not in selected_categories:
                    temp_df_for_category_filter['transportasi'] = 0.0
                if 'Elektronik' not in selected_categories:
                    temp_df_for_category_filter['elektronik'] = 0.0
                if 'Sampah' not in selected_categories:
                    temp_df_for_category_filter['sampah_makanan'] = 0.0
                main_source_for_kpis_segments = temp_df_for_category_filter 
            
            main_source_for_kpis_segments['total_emisi'] = main_source_for_kpis_segments[['transportasi', 'elektronik', 'sampah_makanan']].sum(axis=1)

            daily_trend_data = get_daily_activity_emissions_for_trend(cleaned_selected_fakultas, [], selected_categories)
            daily_pivot = daily_trend_data.groupby(
                ['hari', 'kategori']
            )['emisi'].sum().unstack(fill_value=0.0).reindex(DAY_ORDER).fillna(0.0)

        else: 
            daily_filtered_data_for_all = get_daily_activity_emissions_for_trend(cleaned_selected_fakultas, selected_days, selected_categories)
            
            main_source_for_kpis_segments = daily_filtered_data_for_all.groupby(['id_mahasiswa', 'fakultas', 'kategori'])['emisi'].sum().unstack(fill_value=0.0).reset_index()
            
            for cat in ['Transportasi', 'Elektronik', 'Sampah']:
                if cat not in main_source_for_kpis_segments.columns:
                    main_source_for_kpis_segments[cat] = 0.0

            main_source_for_kpis_segments = main_source_for_kpis_segments.rename(columns={
                'Transportasi': 'transportasi',
                'Elektronik': 'elektronik',
                'Sampah': 'sampah_makanan'
            })
            
            main_source_for_kpis_segments['total_emisi'] = main_source_for_kpis_segments[['transportasi', 'elektronik', 'sampah_makanan']].sum(axis=1)

            daily_pivot = daily_filtered_data_for_all.groupby(
                ['hari', 'kategori']
            )['emisi'].sum().unstack(fill_value=0.0).reindex(DAY_ORDER).fillna(0.0) 

        for cat in ['Transportasi', 'Elektronik', 'Sampah']:
            if cat not in daily_pivot.columns:
                daily_pivot[cat] = 0.0 

        filtered_overall_data_for_metrics = main_source_for_kpis_segments

        if filtered_overall_data_for_metrics.empty:
            st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan sesuaikan filter Anda.")
            st.session_state.overview_empty_data = True
            
            filtered_overall_data_for_metrics = pd.DataFrame(columns=['id_mahasiswa', 'fakultas', 'transportasi', 'elektronik', 'sampah_makanan', 'total_emisi']) 
            fakultas_stats = pd.DataFrame(columns=['fakultas', 'total_emisi', 'count'])
            num_responden_unique_kpi = 0 
        else:
            st.session_state.overview_empty_data = False 

            fakultas_stats = filtered_overall_data_for_metrics.groupby('fakultas').agg(
                total_emisi=('total_emisi', 'sum'),
                count=('id_mahasiswa', 'nunique')
            ).reset_index()

            num_responden_unique_kpi = filtered_overall_data_for_metrics['id_mahasiswa'].nunique()

    with export_col1:
        st.download_button(
            "Data", 
            filtered_overall_data_for_metrics.to_csv(index=False), 
            file_name=f"overview_data{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="overview_export_csv",
            disabled=st.session_state.overview_empty_data
        )
    with export_col2:
        try:
            pdf_data = generate_overview_pdf_report(filtered_overall_data_for_metrics, daily_pivot, fakultas_stats, num_responden_unique_kpi)
            if pdf_data: 
                st.download_button(
                    label="Laporan",
                    data=pdf_data,
                    file_name=f"overview_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="overview_export_pdf_final",
                    disabled=st.session_state.overview_empty_data
                )
            else: 
                pass
        except Exception as e:
            st.error(f"Gagal membuat laporan: {e}")
            st.session_state.overview_empty_data = True 

    col1, col2, col3 = st.columns([1, 1, 1.5], gap="small")

    with col1:
        total_emisi_kpi = filtered_overall_data_for_metrics['total_emisi'].sum()
        avg_emisi_kpi = total_emisi_kpi / num_responden_unique_kpi if num_responden_unique_kpi > 0 else 0

        st.markdown(f'<div class="kpi-card primary" style="margin-bottom: 1rem;"><div class="kpi-value">{total_emisi_kpi:.1f}</div><div class="kpi-label">Total Emisi (kg CO₂)</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card secondary" style="margin-bottom: 1.5rem;"><div class="kpi-value">{avg_emisi_kpi:.2f}</div><div class="kpi-label">Rata-rata per Mahasiswa</div></div>', unsafe_allow_html=True)
        
        if not fakultas_stats.empty and fakultas_stats['total_emisi'].sum() > 0:
            fakultas_stats_display = fakultas_stats[fakultas_stats['total_emisi'] > 0].sort_values('total_emisi', ascending=True).tail(13)
            
            if not fakultas_stats_display.empty:
                fig_fakultas = go.Figure()
                
                max_emisi = fakultas_stats_display['total_emisi'].max()
                min_emisi = fakultas_stats_display['total_emisi'].min()
                
                for _, row in fakultas_stats_display.iterrows():
                    color = CATEGORY_COLORS['Sampah'] 
                    if max_emisi != min_emisi: 
                        ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                        color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                        color_idx = min(int(ratio * (len(color_palette) - 1)), len(color_palette) - 1) 
                        color = color_palette[color_idx]
                    
                    fig_fakultas.add_trace(go.Bar(
                        x=[row['total_emisi']],
                        y=[row['fakultas']],
                        orientation='h',
                        marker=dict(color=color),
                        showlegend=False,
                        text=[f"{row['total_emisi']:.1f}"],
                        textposition='inside',
                        textfont=dict(color='white', size=10, weight='bold'),
                        hovertemplate=f'<b>{row["fakultas"]}</b><br>Total Emisi: %{{x:.1f}} kg CO₂<br>Jumlah Mahasiswa: {row["count"]}<extra></extra>'
                    ))

                fig_fakultas.update_layout(
                    height=382,
                    title_text="<b>Emisi per Fakultas</b>",
                    title_x=0.32,
                    margin=dict(t=40, b=0, l=0, r=20),
                    xaxis_title="Total Emisi (kg CO₂)",
                    yaxis_title="Fakultas",
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data emisi per fakultas untuk filter yang dipilih.")
        else:
            st.info("Tidak ada data emisi per fakultas untuk filter yang dipilih.")

    with col2:
        if not daily_pivot.empty and daily_pivot.sum().sum() > 0:
            fig_trend = go.Figure()
            all_categories = ['Transportasi', 'Elektronik', 'Sampah']
            for cat in all_categories:
                # Cek apakah kolom kategori ada dan memiliki sum > 0
                if cat in daily_pivot.columns and daily_pivot[cat].sum() > 0:
                    fig_trend.add_trace(go.Scatter(
                        x=daily_pivot.index,
                        y=daily_pivot[cat],
                        name=cat,
                        mode='lines+markers',
                        line=dict(color=CATEGORY_COLORS.get(cat, '#cccccc')),
                        hovertemplate='<b>%{x}</b><br>' + cat + ': %{y:.1f} kg CO₂<extra></extra>'
                    ))
            
            # Hanya plot jika ada setidaknya satu trace yang ditambahkan
            if fig_trend.data:
                fig_trend.update_layout(height=265, title_text="<b>Tren Emisi Harian</b>", title_x=0.32, title_y=0.95,
                    margin=dict(t=30, b=0, l=0, r=0), legend_title_text='', yaxis_title="Emisi (kg CO₂)", xaxis_title="Hari",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font_size=9))
                st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
            else:
                st.info("Tidak ada data tren harian untuk filter yang dipilih.")
        else:
            st.info("Tidak ada data tren harian untuk filter yang dipilih.")

        categories_data = {
            'Transportasi': filtered_overall_data_for_metrics['transportasi'].sum() if 'transportasi' in filtered_overall_data_for_metrics.columns else 0.0,
            'Elektronik': filtered_overall_data_for_metrics['elektronik'].sum() if 'elektronik' in filtered_overall_data_for_metrics.columns else 0.0,
            'Sampah': filtered_overall_data_for_metrics['sampah_makanan'].sum() if 'sampah_makanan' in filtered_overall_data_for_metrics.columns else 0.0
        }
        
        final_pie_labels = []
        final_pie_values = []
        
        for label, value in categories_data.items():
            if value > 0:
                final_pie_labels.append(label)
                final_pie_values.append(value)
        
        if final_pie_values and sum(final_pie_values) > 0:
            fig_composition = go.Figure(go.Pie(
                labels=final_pie_labels,
                values=final_pie_values,
                hole=0.45,
                marker=dict(
                    colors=[CATEGORY_COLORS.get(cat) for cat in final_pie_labels],
                    line=dict(color='#FFFFFF', width=2)
                ),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=10, family="Poppins"),
                hovertemplate='<b>%{label}</b><br>Emisi: %{value:.1f} kg CO₂ (%{percent})<extra></extra>'
            ))

            total_emisi_pie = sum(final_pie_values)
            center_text = f"<b style='font-size:14px'>{total_emisi_pie:.1f}</b><br><span style='font-size:8px'>kg CO₂</span>"
            fig_composition.add_annotation(text=center_text, x=0.5, y=0.5, font_size=10, showarrow=False)
            
            fig_composition.update_layout(
                height=280,
                title_text="<b>Komposisi Emisi</b>",
                title_x=0.32,
                title_y=0.95,
                margin=dict(t=65, b=30, l=0, r=0),
                showlegend=False
            )
            st.plotly_chart(fig_composition, config=MODEBAR_CONFIG, use_container_width=True)
        else:
            st.info("Tidak ada data emisi yang ditemukan untuk kategori yang dipilih.")
    
    with col3:
        if num_responden_unique_kpi > 5 and not filtered_overall_data_for_metrics.empty: 
            median_transportasi = filtered_overall_data_for_metrics['transportasi'].median() if 'transportasi' in filtered_overall_data_for_metrics.columns else 0.0
            median_elektronik = filtered_overall_data_for_metrics['elektronik'].median() if 'elektronik' in filtered_overall_data_for_metrics.columns else 0.0
            median_sampah = filtered_overall_data_for_metrics['sampah_makanan'].median() if 'sampah_makanan' in filtered_overall_data_for_metrics.columns else 0.0

            median_transportasi = 0.0 if pd.isna(median_transportasi) else median_transportasi
            median_elektronik = 0.0 if pd.isna(median_elektronik) else median_elektronik
            median_sampah = 0.0 if pd.isna(median_sampah) else median_sampah

            thresholds = {
                'transportasi': median_transportasi,
                'elektronik': median_elektronik,
                'sampah_makanan': median_sampah
            }
            
            agg_df_for_segmentation = filtered_overall_data_for_metrics.copy()
            agg_df_for_segmentation['profil_perilaku'] = agg_df_for_segmentation.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
            
            profile_counts = agg_df_for_segmentation['profil_perilaku'].value_counts().reset_index()
            profile_counts.columns = ['profil', 'jumlah']

            if not profile_counts.empty:
                fig_treemap = px.treemap(
                    profile_counts,
                    path=[px.Constant("Semua Profil"), 'profil'],
                    values='jumlah',
                    color='profil',
                    color_discrete_map=PROFILE_COLOR_MAP,
                    custom_data=['jumlah']
                )
                
                fig_treemap.update_traces(
                    texttemplate="<b>%{label}</b><br>%{value} Mahasiswa",
                    hovertemplate="<b>%{label}</b><br>Jumlah: %{customdata[0]} mahasiswa<extra></extra>",
                    textfont=dict(size=14),
                    insidetextfont=dict(size=16, color='black'),
                    marker=dict(line=dict(width=2, color='white'))
                )
                
                fig_treemap.update_layout(
                    height=570,
                    title_text="<b>Segmentasi Profil</b>",
                    title_x=0.33,
                    margin = dict(t=30, l=5, r=5, b=10)
                )
                
                st.plotly_chart(fig_treemap, use_container_width=True, config=MODEBAR_CONFIG)
            else:
                st.info("Tidak ada profil perilaku yang ditemukan untuk filter yang dipilih.")
        else:
            st.info("Data tidak cukup untuk membuat segmentasi perilaku (minimal 6 responden unik diperlukan setelah filter diterapkan).")
            
        time.sleep(0.15)

if __name__ == "__main__":
    if 'overview_empty_data' not in st.session_state:
        st.session_state.overview_empty_data = False
    show()