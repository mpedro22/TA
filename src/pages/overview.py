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

# Palet warna dan konfigurasi umum
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

# overview.py

# overview.py

@st.cache_data(ttl=3600)
def get_all_student_emissions_data():
    """
    Mengambil total emisi per kategori per mahasiswa dari v_emisi_per_mahasiswa.
    Ini adalah sumber data utama untuk KPI, Emisi per Fakultas, Komposisi Emisi, dan Segmentasi Perilaku.
    """
    # HAPUS TITIK KOMA (;) DI AKHIR QUERY
    query = """
    SELECT
        ve.id_mahasiswa,
        COALESCE(vim.fakultas, 'Unknown') AS fakultas,
        ve.transportasi,
        ve.elektronik,
        ve.sampah_makanan
    FROM
        v_emisi_per_mahasiswa ve
    LEFT JOIN
        v_informasi_fakultas_mahasiswa vim ON ve.id_mahasiswa = vim.id_mahasiswa
    LIMIT 100000
    """
    return run_sql(query)

# overview.py

@st.cache_data(ttl=3600)
def get_daily_activity_emissions():
    """
    Mengambil emisi harian berdasarkan aktivitas dari tabel-tabel detail.
    (VERSI PERBAIKAN 2 - Menambahkan TRIM pada semua kolom hari)
    """
    daily_query = """
    WITH DailyEmissions AS (
        -- 1. Emisi Transportasi per hari
        SELECT
            t.id_mahasiswa,
            TRIM(UNNEST(STRING_TO_ARRAY(t.hari_datang, ','))) AS hari,
            'Transportasi' AS kategori,
            t.emisi_transportasi AS emisi
        FROM transportasi t
        WHERE t.emisi_transportasi > 0 AND t.hari_datang IS NOT NULL AND t.hari_datang <> ''
        
        UNION ALL
        
        -- 2. Emisi Elektronik (Pribadi) per hari
        SELECT
            e.id_mahasiswa,
            TRIM(UNNEST(STRING_TO_ARRAY(e.hari_datang, ','))) AS hari,
            'Elektronik' AS kategori,
            (e.emisi_elektronik / NULLIF(array_length(string_to_array(e.hari_datang, ','), 1), 0)) AS emisi
        FROM elektronik e
        WHERE e.emisi_elektronik > 0 AND e.hari_datang IS NOT NULL AND e.hari_datang <> ''
        
        UNION ALL

        -- 3. Emisi Elektronik (Fasilitas: AC & Lampu) per hari
        SELECT
            ah.id_mahasiswa,
            TRIM(ah.hari) AS hari, -- DITAMBAHKAN TRIM
            'Elektronik' AS kategori,
            (ah.emisi_ac + ah.emisi_lampu) AS emisi
        FROM aktivitas_harian ah
        WHERE (ah.emisi_ac > 0 OR ah.emisi_lampu > 0)
          AND ah.hari IS NOT NULL AND ah.hari <> ''

        UNION ALL
        
        -- 4. Emisi Sampah per hari (dari view yang benar)
        SELECT
            m.id_mahasiswa,
            TRIM(m.hari) AS hari, -- DITAMBAHKAN TRIM
            'Sampah' AS kategori,
            m.emisi_sampah_makanan_per_waktu AS emisi
        FROM v_aktivitas_makanan m
        WHERE m.emisi_sampah_makanan_per_waktu > 0
          AND m.hari IS NOT NULL AND m.hari <> ''
    )
    SELECT
        de.id_mahasiswa,
        COALESCE(r.fakultas, 'Unknown') AS fakultas,
        de.hari,
        de.kategori,
        SUM(de.emisi) AS emisi
    FROM DailyEmissions de
    LEFT JOIN v_informasi_fakultas_mahasiswa r ON de.id_mahasiswa = r.id_mahasiswa
    WHERE de.hari IN ('Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu') -- Filter pengaman
    GROUP BY de.id_mahasiswa, r.fakultas, de.hari, de.kategori
    LIMIT 100000
    """
    return run_sql(daily_query)


def create_behavior_profile(row, thresholds):
    """Mengklasifikasikan responden ke dalam profil perilaku berdasarkan ambang batas emisi."""
    t_level = "Tinggi" if row['transportasi'] > thresholds['transportasi'] else "Rendah"
    e_level = "Tinggi" if row['elektronik'] > thresholds['elektronik'] else "Rendah"
    f_level = "Tinggi" if row['sampah_makanan'] > thresholds['sampah_makanan'] else "Rendah" # Perubahan kolom
    
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
def generate_overview_pdf_report(agg_df_for_report, daily_pivot_for_report, fakultas_stats_for_report):
    """
    Menghasilkan laporan overview komprehensif dalam format PDF.
    """
    from datetime import datetime
    time.sleep(0.6) # Simulasi waktu proses untuk loading animation

    if agg_df_for_report.empty:
        return b"<html><body><h1>Tidak ada data untuk dilaporkan</h1><p>Silakan ubah filter Anda dan coba lagi.</p></body></html>"

    # Perhitungan KPI utama
    total_emisi = agg_df_for_report['total_emisi'].sum()
    avg_emisi = agg_df_for_report['total_emisi'].mean()
    num_responden = agg_df_for_report['id_mahasiswa'].nunique()
    
    # Data komposisi emisi (total dari filtered_agg_df)
    composition_data = {
        'Transportasi': agg_df_for_report['transportasi'].sum(), 
        'Elektronik': agg_df_for_report['elektronik'].sum(), 
        'Sampah': agg_df_for_report['sampah_makanan'].sum() # Perubahan kolom
    }
    
    # Filter kategori yang memiliki emisi > 0 untuk analisis dominant
    composition_data_filtered = {k: v for k, v in composition_data.items() if v > 0}
    
    dominant_cat = "Tidak Tersedia"
    dominant_pct = 0
    secondary_cat = "Tidak Tersedia"
    secondary_pct = 0

    if total_emisi > 0 and composition_data_filtered:
        sorted_comp = sorted(composition_data_filtered.items(), key=lambda item: item[1], reverse=True)
        dominant_cat = sorted_comp[0][0]
        dominant_pct = (sorted_comp[0][1] / total_emisi * 100)
        
        if len(sorted_comp) > 1:
            secondary_cat = sorted_comp[1][0]
            secondary_pct = (sorted_comp[1][1] / total_emisi * 100)

        composition_conclusion = f"Sumber emisi utama adalah <strong>{dominant_cat}</strong>, menyumbang <strong>{dominant_pct:.1f}%</strong> dari total emisi ({total_emisi:.1f} kg CO<sub>2</sub>). {f'Kategori kedua terbesar adalah {secondary_cat} sebesar {secondary_pct:.1f}%.' if secondary_cat != 'Tidak Tersedia' else ''} Ini menunjukkan area mana yang paling perlu diperhatikan untuk pengurangan emisi."
        
    else:
        composition_conclusion = "Data komposisi emisi tidak tersedia atau semua kategori memiliki emisi nol."

    rec_map_cat = {
        'Transportasi': "Dorong penggunaan transportasi publik, sepeda, atau jalan kaki dengan menyediakan fasilitas yang memadai. Pertimbangkan insentif untuk carpooling dan evaluasi kebijakan parkir untuk mengurangi penggunaan kendaraan pribadi di kampus.",
        'Elektronik': "Tingkatkan efisiensi energi di fasilitas kampus (misal: ganti lampu LED, optimalkan AC dengan sensor). Edukasi mahasiswa dan staf untuk mematikan perangkat elektronik yang tidak digunakan dan memanfaatkan mode hemat daya.",
        'Sampah': "Lakukan kampanye pengurangan limbah makanan yang konkret, seperti 'Jangan Sisakan Makanan'. Dukung program komposting dan kerja sama dengan kantin untuk manajemen porsi yang lebih baik serta penanganan sisa makanan yang bisa dimanfaatkan kembali."
    }
    composition_recommendation = rec_map_cat.get(dominant_cat, "Rekomendasi spesifik berdasarkan komposisi emisi belum dapat diberikan.")

    # Analisis Tren Emisi Harian
    peak_day = "Tidak Tersedia"
    peak_emisi = 0
    if not daily_pivot_for_report.empty:
        # Sum semua kategori untuk mendapatkan total emisi harian
        daily_totals = daily_pivot_for_report[['Transportasi', 'Elektronik', 'Sampah']].sum(axis=1)
        if not daily_totals.empty and daily_totals.max() > 0:
            peak_day = daily_totals.idxmax()
            peak_emisi = daily_totals.max()
            trend_conclusion = f"Emisi harian tertinggi terjadi pada hari <strong>{peak_day}</strong>, dengan total <strong>{peak_emisi:.1f} kg CO<sub>2</sub></strong>. Puncak ini mungkin terkait dengan aktivitas kampus yang padat pada hari tersebut."
            trend_recommendation = f"Selidiki aktivitas apa saja yang paling banyak terjadi pada hari <strong>{peak_day}</strong> yang menyebabkan emisi tinggi. Pertimbangkan program penghematan energi atau pengingat digital pada hari-hari tersebut untuk mengurangi konsumsi yang tidak perlu."
        else:
            trend_conclusion = "Tidak ada pola emisi harian yang menonjol atau emisi sangat rendah. Emisi cenderung tersebar merata antar hari."
            trend_recommendation = "Lanjutkan memantau tren harian. Jika emisi mulai meningkat, identifikasi pemicunya. Dorong partisipasi lebih banyak dalam pengisian data aktivitas untuk gambaran tren yang lebih jelas."
    else:
        trend_conclusion = "Data tren harian tidak tersedia untuk analisis."
        trend_recommendation = "Pastikan data aktivitas harian dikumpulkan secara konsisten untuk memungkinkan analisis tren yang bermanfaat."

    # Analisis Emisi per Fakultas
    fakultas_report = pd.DataFrame() # Inisialisasi DataFrame kosong
    fakultas_conclusion = "Data fakultas tidak cukup untuk dianalisis (minimal 2 fakultas dengan data emisi diperlukan)."
    fakultas_recommendation = "Dorong partisipasi lebih banyak mahasiswa dari berbagai fakultas untuk mendapatkan perbandingan yang lebih komprehensif."
    
    if not fakultas_stats_for_report.empty and len(fakultas_stats_for_report) > 1:
        fakultas_report = fakultas_stats_for_report.sort_values('total_emisi', ascending=False)
        highest_fakultas_row = fakultas_report.iloc[0]
        lowest_fakultas_row = fakultas_report.iloc[-1]
        
        conclusion_detail = ""
        if lowest_fakultas_row['total_emisi'] > 0:
            emission_ratio = highest_fakultas_row['total_emisi'] / lowest_fakultas_row['total_emisi']
            conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> memiliki emisi <strong>{highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub></strong>, sekitar {emission_ratio:.1f} kali lebih tinggi dari fakultas <strong>{lowest_fakultas_row['fakultas']} ({lowest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub>)</strong>."
        else:
            conclusion_detail = f"Fakultas <strong>{highest_fakultas_row['fakultas']}</strong> memiliki emisi tertinggi sebesar <strong>{highest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub></strong>, sementara <strong>{lowest_fakultas_row['fakultas']}</strong> memiliki emisi terendah sebesar <strong>{lowest_fakultas_row['total_emisi']:.1f} kg CO<sub>2</sub></strong>."

        fakultas_conclusion = f"Terdapat perbedaan emisi yang jelas antar fakultas. {conclusion_detail} Ini menunjukkan variasi dalam kebiasaan penggunaan energi atau jumlah aktivitas yang menghasilkan emisi di tiap fakultas."
        fakultas_recommendation = f"Fasilitasi program pertukaran informasi atau 'benchmarking' antara fakultas beremisi rendah (misal <strong>{lowest_fakultas_row['fakultas']}</strong>) dan beremisi tinggi (misal <strong>{highest_fakultas_row['fakultas']}</strong>). Lakukan audit energi dan limbah yang lebih spesifik untuk fakultas dengan emisi tinggi guna menemukan sumber emisi terbesar dan cara menguranginya."

    # Analisis Segmentasi Perilaku
    segmentation_table_html = "<tr><td colspan='5'>Data tidak cukup untuk segmentasi.</td></tr>"
    segmentation_conclusion = "Tidak dapat membuat profil perilaku mahasiswa karena data terbatas (diperlukan minimal 6 responden unik untuk analisis ini)."
    segmentation_recommendation = "Tingkatkan jumlah responden yang mengisi data untuk mendapatkan gambaran profil perilaku yang lebih akurat dan dapat digunakan untuk kebijakan yang lebih bertarget."

    if len(agg_df_for_report['id_mahasiswa'].unique()) > 5:
        thresholds = {
            'transportasi': agg_df_for_report['transportasi'].median(),
            'elektronik': agg_df_for_report['elektronik'].median(),
            'sampah_makanan': agg_df_for_report['sampah_makanan'].median() # Perubahan kolom
        }
        df_with_profile = agg_df_for_report.copy()
        df_with_profile['profil_perilaku'] = df_with_profile.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
        
        profile_stats = df_with_profile.groupby('profil_perilaku').agg(
            jumlah_mahasiswa=('id_mahasiswa', 'count'),
            avg_transportasi=('transportasi', 'mean'),
            avg_elektronik=('elektronik', 'mean'),
            avg_sampah=('sampah_makanan', 'mean') # Perubahan kolom
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
                "Kontributor Utama": "Prioritaskan kelompok ini dengan program edukasi dan insentif yang menyeluruh. Contoh: 'Green Campus Challenge' dengan hadiah, panduan personal tentang efisiensi energi, dan promosi gaya hidup minim emisi.",
                "Komuter & Digital": "Fokus pada transportasi berkelanjutan (misal: promo tiket bus/kereta, diskon sewa sepeda) dan kampanye penghematan energi perangkat elektronik (misal: 'Cabut Chargermu!').",
                "Komuter & Boros Pangan": "Kombinasikan program transportasi berkelanjutan dengan inisiatif pengurangan limbah makanan. Contoh: workshop masak minim sisa, kerja sama dengan kantin untuk opsi porsi kecil atau program makanan sisa.",
                "Digital & Boros Pangan": "Targetkan dengan kampanye 'Hemat Energi Layar' untuk perangkat dan 'Habiskan Porsi Makananmu' di area makan. Pertimbangkan aplikasi pelacak emisi yang menyoroti dampak dari kebiasaan digital dan pangan.",
                "Komuter Berat": "Perluas pilihan transportasi alternatif. Contoh: sediakan lebih banyak shuttle bus kampus, hari 'Tanpa Kendaraan Pribadi' dengan hadiah, atau dukung komunitas carpooling mahasiswa.",
                "Pengguna Elektronik Berat": "Edukasi mendalam tentang konsumsi daya perangkat. Promosikan penggunaan mode hemat daya, berikan daftar perangkat elektronik efisien, atau tawarkan audit energi kecil untuk ruang kerja/belajar.",
                "Boros Pangan": "Fokus pada edukasi tentang dampak limbah makanan. Contoh: kampanye 'Piring Bersih', program donasi makanan berlebih ke komunitas, atau kerja sama dengan katering kampus untuk mengurangi sisa produksi.",
                "Sangat Sadar Lingkungan": "Libatkan mereka sebagai 'Duta Lingkungan' atau mentor bagi mahasiswa lain. Berikan platform untuk berbagi praktik terbaik dan ide-ide inovatif untuk keberlanjutan kampus.",
                "Profil Campuran": "Sediakan materi edukasi umum yang mudah diakses (infografis, video singkat) tentang sumber emisi utama dan tips sederhana untuk mengurangi jejak karbon dalam kehidupan kampus sehari-hari."
            }
            rekomendasi_utama = rec_map_behavior.get(dominant_profile, rec_map_behavior["Profil Campuran"])
            segmentation_recommendation = f"Kebijakan kampus perlu disesuaikan untuk profil '<strong>{dominant_profile}</strong>'. {rekomendasi_utama}"

    # HTML untuk tabel komposisi
    composition_table_html = ''.join([f"<tr><td>{cat}</td><td style='text-align:right;'>{val:.1f}</td><td style='text-align:right;'>{(val/total_emisi*100 if total_emisi>0 else 0):.1f}%</td></tr>" for cat, val in composition_data.items()])
    
    # Konten HTML untuk PDF
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
        .recommendation {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
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
        {''.join([f"<tr><td>{row['fakultas']}</td><td style='text-align:right;'>{row['total_emisi']:.1f}</td></tr>" for idx, row in fakultas_report.head(10).iterrows()]) if not fakultas_report.empty else "<tr><td colspan='2'>Data tidak tersedia.</td></tr>"}
        </tbody></table>
        <div class="conclusion"><strong>Insight:</strong> {fakultas_conclusion}</div>
        <div class="recommendation"><strong>Rekomendasi:</strong> {fakultas_recommendation}</div>

        <h2>2. Tren Emisi Harian</h2>
        <table><thead><tr><th>Hari</th><th>Total Emisi (kg CO<sub>2</sub>)</th></tr></thead><tbody>
        {''.join([f"<tr><td>{day}</td><td style='text-align:right;'>{daily_pivot_for_report.loc[day].sum():.1f}</td></tr>" for day in daily_pivot_for_report.index]) if not daily_pivot_for_report.empty else "<tr><td colspan='2'>Data tidak tersedia.</td></tr>"}
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

    # Buat PDF
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
    time.sleep(0.25) # Untuk efek loading visual

    with loading():
        # Memuat data emisi total per mahasiswa dari view (untuk KPI, fakultas, komposisi, segmentasi)
        full_student_emissions_data = get_all_student_emissions_data()
        if full_student_emissions_data.empty:
            st.warning("Tidak ada data emisi mahasiswa yang tersedia dari database. Pastikan koneksi dan data ada.")
            return

        # Memuat data emisi harian berdasarkan aktivitas (untuk chart Tren Emisi Harian)
        base_daily_activity_data = get_daily_activity_emissions()
        # base_daily_activity_data bisa saja kosong jika tidak ada aktivitas yang dicatat
        
        # Ambil daftar fakultas yang tersedia dari data emisi mahasiswa
        available_fakultas = sorted(full_student_emissions_data['fakultas'].unique())
    
    # Kolom untuk filter dan tombol ekspor
    filter_col1, filter_col2, filter_col3, export_col1, export_col2 = st.columns([1.8, 1.8, 1.8, 1, 1])
    with filter_col1:
        selected_days = st.multiselect("Hari:", DAY_ORDER, placeholder="Pilih Opsi", key='overview_day_filter')
    with filter_col2:
        selected_categories = st.multiselect("Jenis:", ['Transportasi', 'Elektronik', 'Sampah'], placeholder="Pilih Opsi", key='overview_category_filter')
    with filter_col3:
        selected_fakultas = st.multiselect("Fakultas:", available_fakultas, placeholder="Pilih Opsi", key='overview_fakultas_filter')

    with loading():
        # --- Dataframe untuk KPI, Emisi per Fakultas, Komposisi, Segmentasi (filtered by fakultas) ---
        # Data ini menggunakan full_student_emissions_data sebagai basis
        filtered_agg_df = full_student_emissions_data.copy()
        if selected_fakultas:
            filtered_agg_df = filtered_agg_df[filtered_agg_df['fakultas'].isin(selected_fakultas)]
        
        # Hitung ulang total emisi per mahasiswa setelah filtering fakultas
        filtered_agg_df['total_emisi'] = filtered_agg_df[['transportasi', 'elektronik', 'sampah_makanan']].sum(axis=1)

        # --- Dataframe untuk Tren Emisi Harian (filtered by hari, kategori, fakultas) ---
        # Data ini menggunakan base_daily_activity_data sebagai basis
        filtered_daily_data = base_daily_activity_data.copy()
        if selected_fakultas:
            filtered_daily_data = filtered_daily_data[filtered_daily_data['fakultas'].isin(selected_fakultas)]
        if selected_days:
            filtered_daily_data = filtered_daily_data[filtered_daily_data['hari'].isin(selected_days)]
        if selected_categories:
            # Gunakan selected_categories langsung karena nama di CTE sudah disesuaikan
            filtered_daily_data = filtered_daily_data[filtered_daily_data['kategori'].isin(selected_categories)] 
        
        # Peringatan jika filtered_agg_df kosong (tidak ada data untuk total emisi)
        if filtered_agg_df.empty:
            st.warning("Tidak ada data yang sesuai dengan filter yang dipilih untuk perhitungan total emisi. Beberapa chart mungkin kosong."); return
        
        # Peringatan jika filtered_daily_data kosong (tidak ada data untuk tren harian)
        if filtered_daily_data.empty and not base_daily_activity_data.empty: # Cek jika memang ada data awal tapi filter membuatnya kosong
            st.warning("Data aktivitas harian tidak tersedia untuk filter yang dipilih, chart tren harian mungkin kosong.")
            
        # Perhitungan statistik untuk chart Emisi per Fakultas
        fakultas_stats = filtered_agg_df.groupby('fakultas').agg(
            total_emisi=('total_emisi', 'sum'),
            count=('id_mahasiswa', 'nunique')
        ).reset_index()

        # Pivoting data harian untuk chart Tren Emisi Harian
        daily_pivot = filtered_daily_data.pivot_table(
            index='hari',
            columns='kategori',
            values='emisi',
            aggfunc='sum'
        ).reindex(DAY_ORDER).fillna(0)

        # Pastikan kolom kategori ada di daily_pivot, jika tidak tambahkan dengan 0
        for cat in ['Transportasi', 'Elektronik', 'Sampah']:
            if cat not in daily_pivot.columns:
                daily_pivot[cat] = 0

    # --- Tombol Ekspor ---
    with export_col1:
        st.download_button(
            "Raw Data",
            filtered_agg_df.to_csv(index=False), # Ekspor data yang sudah difilter
            f"overview_filtered_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True,
            key="overview_export_csv",
            disabled=filtered_agg_df.empty
        )
    with export_col2:
        try:
            # generate_overview_pdf_report menggunakan data yang sudah difilter
            pdf_data = generate_overview_pdf_report(filtered_agg_df, daily_pivot, fakultas_stats)
            if pdf_data: 
                st.download_button(
                    label="Laporan PDF",
                    data=pdf_data,
                    file_name=f"overview_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="overview_export_pdf_final",
                    disabled=filtered_agg_df.empty
                )
            else:
                st.error("Gagal menyiapkan laporan PDF.")
        except Exception as e:
            st.error(f"Gagal membuat laporan: {e}")

    # --- Tampilan Dashboard: Kolom 1 (KPIs & Emisi per Fakultas) ---
    col1, col2, col3 = st.columns([1, 1, 1.5], gap="small")

    with col1:
        total_emisi_kpi = filtered_agg_df['total_emisi'].sum()
        avg_emisi_kpi = filtered_agg_df['total_emisi'].mean() if not filtered_agg_df.empty else 0
        st.markdown(f'<div class="kpi-card primary" style="margin-bottom: 1rem;"><div class="kpi-value">{total_emisi_kpi:.1f}</div><div class="kpi-label">Total Emisi (kg CO₂)</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card secondary" style="margin-bottom: 1.5rem;"><div class="kpi-value">{avg_emisi_kpi:.2f}</div><div class="kpi-label">Rata-rata per Mahasiswa</div></div>', unsafe_allow_html=True)
        
        # Chart Emisi per Fakultas
        # Tampilkan hanya jika ada data fakultas yang relevan setelah filter
        if not fakultas_stats.empty and fakultas_stats['total_emisi'].sum() > 0:
            fakultas_stats_display = fakultas_stats.sort_values('total_emisi', ascending=True).head(13) # Ambil 13 fakultas teratas/terbawah
            fig_fakultas = go.Figure()
            max_emisi = fakultas_stats_display['total_emisi'].max()
            min_emisi = fakultas_stats_display['total_emisi'].min()
            
            for _, row in fakultas_stats_display.iterrows():
                if max_emisi > min_emisi:
                    # Skala warna berdasarkan posisi emisi relatif terhadap min/max
                    ratio = (row['total_emisi'] - min_emisi) / (max_emisi - min_emisi)
                    color_palette = ['#66c2a5', '#abdda4', '#fdae61', '#f46d43', '#d53e4f', '#9e0142']
                    color_idx = int(ratio * (len(color_palette) - 1))
                    color = color_palette[color_idx]
                else: # Jika semua emisi sama, gunakan warna default
                    color = CATEGORY_COLORS['Sampah']

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
                yaxis_title=None,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_fakultas, config=MODEBAR_CONFIG, use_container_width=True)
        else:
            st.info("Tidak ada data emisi per fakultas untuk filter yang dipilih.")

    # --- Tampilan Dashboard: Kolom 2 (Tren Harian & Komposisi Emisi) ---
    with col2:
        # Chart Tren Emisi Harian
        # Hanya tampilkan jika filtered_daily_data tidak kosong dan ada emisi
        if not filtered_daily_data.empty and daily_pivot.sum().sum() > 0:
            fig_trend = go.Figure()
            
            # Tentukan kategori mana yang akan ditampilkan, sesuai filter atau semua
            cats_to_show = selected_categories or list(CATEGORY_COLORS.keys())
            
            for cat in cats_to_show:
                if cat in daily_pivot.columns: # Pastikan kategori ada di daily_pivot
                    fig_trend.add_trace(go.Scatter(
                        x=daily_pivot.index, 
                        y=daily_pivot[cat], 
                        name=cat, 
                        mode='lines+markers', 
                        line=dict(color=CATEGORY_COLORS.get(cat, '#cccccc')), # Gunakan warna dari mapping
                        hovertemplate='<b>%{x}</b><br>' + cat + ': %{y:.1f} kg CO₂<extra></extra>'
                    ))
            
            fig_trend.update_layout(height=265, title_text="<b>Tren Emisi Harian</b>", title_x=0.32,
                margin=dict(t=40, b=0, l=0, r=0), legend_title_text='', yaxis_title="Emisi (kg CO₂)", xaxis_title=None,
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font_size=9))
            st.plotly_chart(fig_trend, config=MODEBAR_CONFIG, use_container_width=True)
        else: 
            st.info("Tidak ada data tren harian untuk filter yang dipilih.")

        # Chart Komposisi Emisi (menggunakan filtered_agg_df)
        categories_data = {
            'Transportasi': filtered_agg_df['transportasi'].sum(),
            'Elektronik': filtered_agg_df['elektronik'].sum(),
            'Sampah': filtered_agg_df['sampah_makanan'].sum() # Pastikan kolom sampah_makanan digunakan
        }
        
        # Filter kategori dengan nilai emisi > 0 atau jika hanya 1 kategori dipilih (untuk menghindari pie chart kosong)
        final_pie_labels = []
        final_pie_values = []
        
        # Jika hanya satu kategori dipilih dan nilainya 0, tambahkan kategori itu
        if len(selected_categories) == 1 and categories_data[selected_categories[0]] == 0:
            final_pie_labels.append(selected_categories[0])
            final_pie_values.append(0)
        else: # Untuk semua kategori atau multiple category selection
            for label, value in categories_data.items():
                if value > 0 and (not selected_categories or label in selected_categories):
                    final_pie_labels.append(label)
                    final_pie_values.append(value)
        
        if final_pie_values and sum(final_pie_values) > 0: # Pastikan ada data untuk pie chart
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
    
    # --- Tampilan Dashboard: Kolom 3 (Segmentasi Perilaku) ---
    with col3:
        # Segmentasi Perilaku hanya jika jumlah responden unik > 5
        if len(filtered_agg_df['id_mahasiswa'].unique()) > 5:
            thresholds = {
                'transportasi': filtered_agg_df['transportasi'].median(),
                'elektronik': filtered_agg_df['elektronik'].median(),
                'sampah_makanan': filtered_agg_df['sampah_makanan'].median() # Pastikan kolom sampah_makanan digunakan
            }
            
            agg_df_for_segmentation = filtered_agg_df.copy()
            agg_df_for_segmentation['profil_perilaku'] = agg_df_for_segmentation.apply(lambda row: create_behavior_profile(row, thresholds), axis=1)
            
            profile_counts = agg_df_for_segmentation['profil_perilaku'].value_counts().reset_index()
            profile_counts.columns = ['profil', 'jumlah']

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
            st.info("Data tidak cukup untuk membuat segmentasi perilaku (minimal 6 responden unik diperlukan).")
            
        time.sleep(0.15) # Untuk efek loading visual di akhir

if __name__ == "__main__":
    show()