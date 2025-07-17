import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
import random
import re
import time 

# Muat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi dari variabel lingkungan
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Konfigurasi Google Sheets API
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json' # Pastikan file ini ada dan berisi kredensial akun layanan
SHEET_URL = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4" # Ganti dengan URL spreadsheet Anda
RAW_DATA_WORKSHEET_NAME = "Form Responses 1 RAW (Dummy)" # Nama worksheet yang berisi data mentah dari Google Form

def connect_to_gsheet(url, worksheet_name):
    """Menghubungkan ke Google Sheet dan worksheet tertentu."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(url).worksheet(worksheet_name)
        print(f"Berhasil terhubung ke Google Sheet: '{worksheet_name}'")
        return sheet
    except Exception as e:
        print(f"Gagal terhubung ke Google Sheet '{worksheet_name}': {e}")
        return None

def extract_data_to_df(sheet):
    """Mengekstrak seluruh data dari worksheet ke Pandas DataFrame."""
    if not sheet: return pd.DataFrame()
    print(f"📥 Mengekstrak data dari sheet '{sheet.title}'...")
    data = sheet.get_all_values()
    if not data or len(data) < 2: # Periksa jika sheet kosong atau hanya berisi header
        print("   -> Sheet kosong atau hanya berisi header.")
        return pd.DataFrame()
    headers = data.pop(0) # Baris pertama adalah header
    df = pd.DataFrame(data, columns=headers)
    print(f"   -> Ditemukan {len(df)} baris data mentah.")
    return df

def get_fakultas_mapping():
    """Mengembalikan mapping program studi ke fakultas."""
    return {'Meteorologi':'FITB','Oseanografi':'FITB','Teknik Geodesi dan Geomatika':'FITB','Teknik Geologi':'FITB','Aktuaria':'FMIPA','Astronomi':'FMIPA','Fisika':'FMIPA',
            'Kimia':'FMIPA','Matematika':'FMIPA','Desain Interior':'FSRD','Desain Komunikasi Visual':'FSRD','Desain Produk':'FSRD','Kriya':'FSRD','Seni Rupa':'FSRD',
            'Manajemen Rekayasa Industri':'FTI','Teknik Fisika':'FTI','Teknik Industri':'FTI','Teknik Kimia':'FTI','Teknik Geofisika':'FTTM','Teknik Metalurgi':'FTTM',
            'Teknik Perminyakan':'FTTM','Teknik Pertambangan':'FTTM','Teknik Dirgantara':'FTMD','Teknik Material':'FTMD','Teknik Mesin':'FTMD','Teknik Kelautan':'FTSL',
            'Teknik Lingkungan':'FTSL','Teknik Sipil':'FTSL','Arsitektur':'SAPPK','Perencanaan Wilayah dan Kota':'SAPPK','Kewirausahaan':'SBM','Manajemen':'SBM',
            'Farmasi Klinik dan Komunitas':'SF','Sains dan Teknologi Farmasi':'SF','Biologi':'SITH','Mikrobiologi':'SITH','Sistem dan Teknologi Informasi':'STEI',
            'Teknik Biomedis':'STEI','Teknik Elektro':'STEI','Informatika':'STEI','Teknik Telekomunikasi':'STEI','Teknik Tenaga Listrik':'STEI'}

def clear_supabase_tables(supabase: Client):
    """
    Membersihkan data dari tabel-tabel Supabase sebelum proses ETL baru.
    Urutan penghapusan penting untuk menghindari masalah foreign key.
    """
    print("\n🧹 Membersihkan tabel di Supabase sebelum memuat data baru...")
    
    # Urutan penting: hapus tabel anak (child) dulu sebelum tabel induk (parent)
    tables_to_clear = ["aktivitas_harian", "transportasi", "elektronik", "sampah_makanan", "mahasiswa"]
    
    for table_name in tables_to_clear:
        try:
            # Menghapus semua baris dari tabel. Menggunakan .neq('id_mahasiswa', 0)
            # karena id_mahasiswa adalah primary key/foreign key di semua tabel ini dan 
            # diasumsikan tidak akan pernah 0, efektif menghapus semua baris.
            # Supabase delete().gte().execute() lebih baik untuk performa daripada .neq
            # Tapi untuk full clear, cukup delete() tanpa filter pun bisa.
            # Menggunakan .gt(pk_column, 0) lebih aman jika pk_column bisa bernilai 0
            # Atau simply: supabase.table(table_name).delete().execute() jika tidak ada PK 0
            
            # Mendapatkan primary key dari tabel untuk delete (jika diperlukan)
            # Karena semua tabel di sini punya id_mahasiswa sebagai PK/FK utama, kita bisa pakai itu
            pk_col_for_clear = 'id_mahasiswa' 
            
            # Coba ambil semua ID untuk dihapus (jika tabel tidak terlalu besar)
            # Atau langsung delete semua jika tabel tidak terlalu besar.
            # Untuk tabel besar, DELETE FROM table_name saja
            # supabase.table(table_name).delete().gt(pk_col_for_clear, 0).execute() # Alternatif delete
            
            # Karena tabel ini mungkin sangat besar, lebih baik melakukan DELETE ALL.
            # Supabase client biasanya punya metode delete().gt('id', 0) atau serupa.
            # Untuk tabel besar, langsung saja tanpa filter jika PostgREST mengizinkan.
            # Contoh: supabase.table(table_name).delete().execute() # ini akan menghapus semua
            
            # Supabase Python client's delete() with a dummy filter (like .gt(0))
            # or with a filter that matches all rows is common for full clear.
            # The current .neq('id_mahasiswa', 0) works if id_mahasiswa is always positive.
            response = supabase.table(table_name).delete().neq('id_mahasiswa', 0).execute() 
            
            # response.data akan berisi list dari objek yang dihapus.
            if response.data is not None:
                print(f"   -> Berhasil membersihkan tabel '{table_name}'. Dihapus: {len(response.data)} baris.")
            else:
                print(f"   -> Berhasil membersihkan tabel '{table_name}'. (Tidak ada baris yang cocok atau tabel sudah kosong).")

        except Exception as e:
            print(f"   -> Gagal membersihkan tabel '{table_name}': {e}")
            pass # Melanjutkan meskipun ada error pembersihan tabel

    print("✅ Proses pembersihan tabel selesai.")


def load_to_supabase(supabase: Client, table_name: str, df: pd.DataFrame, pk_column: str, is_log=False):
    """
    Memuat DataFrame ke Supabase.
    Menggunakan upsert untuk tabel utama dan delete+insert (dengan batching) untuk tabel log (aktivitas_harian).
    """
    if df.empty:
        print(f"Tidak ada data untuk dimuat ke '{table_name}'.")
        return
    
    # Mengganti NaN dan string kosong dengan None agar Supabase bisa menanganinya sebagai NULL
    df_cleaned = df.replace({np.nan: None, '': None})
    records = df_cleaned.to_dict(orient="records")
    
    print(f"Memuat {len(records)} baris ke tabel '{table_name}'...")
    
    # Ukuran batch untuk INSERT/DELETE
    batch_size_delete = 500  # Untuk operasi DELETE, agar URL tidak terlalu panjang
    batch_size_insert = 1000 # Untuk operasi INSERT, agar body request tidak terlalu besar
    
    try:
        if is_log: # Log table (aktivitas_harian) memerlukan penghapusan log lama lalu insertion baru
            ids_to_delete_all = df_cleaned[pk_column].unique().tolist()
            if ids_to_delete_all:
                print(f"   - Menghapus log lama untuk {len(ids_to_delete_all)} responden (batching DELETE)...")
                
                for i in range(0, len(ids_to_delete_all), batch_size_delete):
                    batch_ids = ids_to_delete_all[i:i + batch_size_delete]
                    try:
                        supabase.table(table_name).delete().in_(pk_column, batch_ids).execute()
                        print(f"     -> Berhasil menghapus batch {i//batch_size_delete + 1} dari {len(ids_to_delete_all)//batch_size_delete + 1} ({len(batch_ids)} IDs).")
                        time.sleep(0.1) # Jeda kecil antar batch DELETE
                    except Exception as batch_e:
                        print(f"     -> Gagal menghapus batch {i//batch_size_delete + 1} (IDs: {batch_ids[0]}-{batch_ids[-1]}): {batch_e}")
                        pass # Melanjutkan meskipun ada error pada batch
                
            print("   - Memasukkan log baru (batching INSERT)...")
            for i in range(0, len(records), batch_size_insert):
                batch_records = records[i:i + batch_size_insert]
                try:
                    supabase.table(table_name).insert(batch_records).execute()
                    print(f"     -> Berhasil memasukkan batch {i//batch_size_insert + 1} dari {len(records)//batch_size_insert + 1} ({len(batch_records)} records).")
                    time.sleep(0.1) # Jeda kecil antar batch INSERT
                except Exception as batch_e:
                    print(f"     -> Gagal memasukkan batch {i//batch_size_insert + 1} (records {i}-{i+len(batch_records)-1}): {batch_e}")
                    pass # Melanjutkan meskipun ada error pada batch
            
        else: # Tabel utama (mahasiswa, transportasi, elektronik, sampah_makanan) menggunakan upsert
              # Upsert sudah cukup efisien untuk sebagian besar kasus, tidak selalu butuh batching.
              # Namun jika records sangat banyak (>10k-50k tergantung lebar baris), bisa pertimbangkan batching juga.
            supabase.table(table_name).upsert(records, on_conflict=pk_column).execute()
        print(f"   -> Berhasil.")
    except Exception as e:
        print(f"   -> Gagal total saat memuat ke '{table_name}': {e}")

def transform_all_data(df_raw):
    """Melakukan semua proses transformasi data."""
    print("🔄 Memulai proses transformasi data...")

    # --- Persiapan Awal: Mengganti nama kolom sesuai struktur yang diinginkan ---
    # Ini adalah mapping manual, jika struktur Google Form berubah, ini perlu diupdate
    new_column_names = [
        'timestamp', 'nama_raw', 'prodi_raw', 'whatsapp', 'transportasi', 'estimasi_jarak', 
        'jenis_bbm', 'parkir', 'perangkat_list', 'durasi_hp_raw', 'durasi_laptop_raw', 
        'durasi_tab_raw', 'tempat_makan_raw'
    ] + [f'keg_senin_{i}' for i in range(10)] + ['lokasi_kelas_senin', 'lokasi_lain_senin'] \
      + [f'keg_selasa_{i}' for i in range(10)] + ['lokasi_kelas_selasa', 'lokasi_lain_selasa'] \
      + [f'keg_rabu_{i}' for i in range(10)] + ['lokasi_kelas_rabu', 'lokasi_lain_rabu'] \
      + [f'keg_kamis_{i}' for i in range(10)] + ['lokasi_kelas_kamis', 'lokasi_lain_kamis'] \
      + [f'keg_jumat_{i}' for i in range(10)] + ['lokasi_kelas_jumat', 'lokasi_lain_jumat'] \
      + [f'keg_sabtu_{i}' for i in range(10)] + ['lokasi_kelas_sabtu', 'lokasi_lain_sabtu'] \
      + [f'keg_minggu_{i}' for i in range(10)] + ['lokasi_kelas_minggu', 'lokasi_lain_minggu'] \
      + ['angkatan', 'kecamatan']
    
    if len(df_raw.columns) != len(new_column_names):
        raise ValueError(f"Jumlah kolom tidak cocok! Diharapkan {len(new_column_names)}, tapi sheet memiliki {len(df_raw.columns)}.")

    df_raw.columns = new_column_names
    
    # Memberi ID unik untuk setiap responden, dimulai dari 1
    # Ini akan menjadi PK untuk mahasiswa dan FK untuk tabel lain
    df_raw['id_mahasiswa'] = [i + 1 for i in range(len(df_raw))]
    
    # Mapping untuk kolom kegiatan harian per hari
    hari_map_kegiatan = {
        'Senin': [f'keg_senin_{i}' for i in range(10)], 'Selasa': [f'keg_selasa_{i}' for i in range(10)],
        'Rabu': [f'keg_rabu_{i}' for i in range(10)], 'Kamis': [f'keg_kamis_{i}' for i in range(10)],
        'Jumat': [f'keg_jumat_{i}' for i in range(10)], 'Sabtu': [f'keg_sabtu_{i}' for i in range(10)],
        'Minggu': [f'keg_minggu_{i}' for i in range(10)]
    }

    # --- Transformasi Data untuk Tabel 'mahasiswa' ---
    print("   - Memproses 'mahasiswa'...")
    df_responden = df_raw[['id_mahasiswa', 'nama_raw', 'prodi_raw']].copy()
    df_responden.rename(columns={'nama_raw': 'nama', 'prodi_raw': 'program_studi'}, inplace=True)
    
    # Menentukan hari_datang berdasarkan kegiatan "Tidak di kampus"
    hari_datang_list = df_raw.apply(
        lambda row: ", ".join([hari for hari, cols in hari_map_kegiatan.items() if any(row[c] and str(row[c]).strip().lower() != 'tidak di kampus' for c in cols)]),
        axis=1
    )
    df_responden['hari_datang'] = hari_datang_list
    df_responden.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last') # Pastikan unik per id_mahasiswa

    # --- Transformasi Data untuk Tabel 'aktivitas_harian' (Log Kegiatan per Slot Waktu) ---
    print("   - Memproses 'aktivitas_harian'...")
    all_activities = []
    waktu_slots = ["00-06", "06-08", "08-10", "10-12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]
    for _, row in df_raw.iterrows():
        for hari_name, keg_cols in hari_map_kegiatan.items():
            for i, keg_col in enumerate(keg_cols):
                kegiatan = row[keg_col]
                # Hanya proses aktivitas yang tidak kosong dan bukan 'Tidak di kampus'
                if kegiatan and str(kegiatan).strip() and str(kegiatan).lower() != "tidak di kampus":
                    lokasi = None
                    if 'Kelas' in kegiatan: lokasi_raw = row[f'lokasi_kelas_{hari_name.lower()}']
                    elif 'Makan/Minum' in kegiatan: lokasi_raw = row['tempat_makan_raw']
                    else: lokasi_raw = row[f'lokasi_lain_{hari_name.lower()}']
                    
                    # Jika ada beberapa lokasi, pilih acak satu
                    if isinstance(lokasi_raw, str) and lokasi_raw.strip() not in ['-', '']: 
                        # Handle multiple locations separated by commas
                        cleaned_locations = [loc.strip() for loc in lokasi_raw.split(',') if loc.strip()]
                        lokasi = random.choice(cleaned_locations) if cleaned_locations else None
                    
                    is_facility_intensive = 'Kelas' in kegiatan or 'Makan/Minum' in kegiatan

                    # Perhitungan Emisi AC dan Lampu per slot waktu (2 jam) jika kegiatan intensif fasilitas
                    # Asumsi:
                    # AC: 0.5 kW per unit. 2 unit per ruangan. Faktor emisi 0.829 kgCO2/kWh. Durasi slot 2 jam.
                    # Emisi AC = 0.5 * 2 * 0.829 * 2 = 1.658 kg CO2 (dibulatkan menjadi 1.66)
                    emisi_ac_val = 1.66 if is_facility_intensive else 0 
                    
                    # Lampu: 0.036 kW per unit. 4 unit per ruangan. Faktor emisi 0.829 kgCO2/kWh. Durasi slot 2 jam.
                    # Emisi Lampu = 0.036 * 4 * 0.829 * 2 = 0.238752 kg CO2 (dibulatkan menjadi 0.24)
                    emisi_lampu_val = 0.24 if is_facility_intensive else 0
                    
                    # Emisi Sampah Makanan per waktu (per slot kegiatan Makan/Minum)
                    emisi_sampah_makanan_per_waktu_val = 0.95 if 'Makan/Minum' in kegiatan else 0

                    all_activities.append({
                        'id_mahasiswa': row['id_mahasiswa'], 
                        'hari': hari_name,
                        'waktu': waktu_slots[i],
                        'kegiatan': kegiatan,
                        'lokasi': lokasi,
                        'penggunaan_ac': is_facility_intensive,
                        'emisi_ac': emisi_ac_val,
                        'emisi_lampu': emisi_lampu_val,
                        'emisi_sampah_makanan_per_waktu': emisi_sampah_makanan_per_waktu_val
                    })

    df_aktivitas = pd.DataFrame(all_activities)
    print(f"   - Berhasil membuat {len(df_aktivitas)} baris log aktivitas.")
    
    # --- Transformasi Data untuk Tabel 'transportasi' ---
    print("   - Memproses 'transportasi'...")
    df_transport = df_raw[['id_mahasiswa', 'transportasi', 'kecamatan', 'estimasi_jarak', 'jenis_bbm']].copy()
    df_transport = pd.merge(df_transport, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    # Mapping estimasi jarak ke nilai numerik rata-rata
    df_transport['jarak'] = pd.to_numeric(df_transport['estimasi_jarak'].map({"< 1 km": 0.5, "1 - 3 km": 2, "3 - 5 km": 4, "5 - 10 km": 7.5, "> 10 km": 12}), errors='coerce').fillna(0)
    
    # Konsumsi bahan bakar per km berdasarkan moda
    df_transport['konsumsi'] = df_transport['transportasi'].map({"Mobil": 0.1, "Angkutan Umum": 0.1, "Ojek Online": 0.035, "Motor": 0.035}).fillna(0)
    
    # NCV (Net Calorific Value) dan FE_TJ (Faktor Emisi per TeraJoule) dari ESDM
    # Perhatikan mappingnya menggunakan 'in str(x)' karena format input kuesioner mungkin berbeda
    ncv_map = {"Ron 90": 44.61, "Ron 92": 44.61, "Ron 95": 44.62, "Ron 98": 44.62}
    fe_tj_map = {"Ron 90": 69.67, "Ron 92": 69.04, "Ron 95": 68.97, "Ron 98": 68.91}
    df_transport['ncv'] = df_transport['jenis_bbm'].apply(lambda x: next((v for k, v in ncv_map.items() if k in str(x)), 0))
    df_transport['fe_tj'] = df_transport['jenis_bbm'].apply(lambda x: next((v for k, v in fe_tj_map.items() if k in str(x)), 0))
    
    # Faktor Emisi per KM = (NCV * 0.74) * (FE_TJ / 1000)
    df_transport['faktor_emisi_per_km'] = (pd.to_numeric(df_transport['ncv'], errors='coerce') * 0.74) * (pd.to_numeric(df_transport['fe_tj'], errors='coerce') / 1000)
    
    # Emisi Transportasi = Jarak (satu arah) * Konsumsi (Liter/km) * Faktor Emisi per KM * 2 (pulang-pergi)
    df_transport['emisi_transportasi'] = df_transport['jarak'] * (df_transport['konsumsi'] * df_transport['faktor_emisi_per_km']) * 2
    
    df_transport.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')

    # --- Transformasi Data untuk Tabel 'elektronik' ---
    print("   - Memproses 'elektronik'...")
    df_elektronik = df_raw[['id_mahasiswa', 'perangkat_list', 'durasi_hp_raw', 'durasi_laptop_raw', 'durasi_tab_raw']].copy()
    df_elektronik = pd.merge(df_elektronik, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    # Menentukan penggunaan perangkat berdasarkan kolom 'perangkat_list'
    df_elektronik['penggunaan_hp'] = df_elektronik['perangkat_list'].str.contains('HP', na=False)
    df_elektronik['penggunaan_laptop'] = df_elektronik['perangkat_list'].str.contains('Laptop', na=False)
    df_elektronik['penggunaan_tab'] = df_elektronik['perangkat_list'].str.contains('Tab', na=False)
    
    # Fungsi untuk membersihkan durasi (misal '0-60 menit' menjadi 60)
    def clean_duration(text): 
        match = re.findall(r'\d+', str(text)) # Ambil angka pertama dari string
        return int(match[0]) if match else 0
    
    # Konversi durasi mentah ke numerik (dalam menit)
    df_elektronik['durasi_hp'] = pd.to_numeric(df_elektronik['durasi_hp_raw'].apply(clean_duration), errors='coerce').fillna(0)
    df_elektronik['durasi_laptop'] = pd.to_numeric(df_elektronik['durasi_laptop_raw'].apply(clean_duration), errors='coerce').fillna(0)
    df_elektronik['durasi_tab'] = pd.to_numeric(df_elektronik['durasi_tab_raw'].apply(clean_duration), errors='coerce').fillna(0)
    
    # Hitung jumlah hari datang ke kampus dari hari_datang string
    jumlah_hari_datang = df_elektronik['hari_datang'].apply(
        lambda x: len([h.strip() for h in str(x).split(',') if h.strip()]) 
        if pd.notna(x) and str(x).strip() else 0
    )
    
    # Emisi elektronik pribadi = (Watt * Menit) / (1000 * 60) -> kWh * Faktor Emisi Listrik * Jumlah Hari Datang
    # Daya per perangkat: HP=4W, Laptop=50W, Tablet=10W. Faktor Emisi Listrik = 0.829 kgCO2/kWh
    emisi_pribadi_harian_per_menit = ((df_elektronik['durasi_hp'] * 4) + \
                                      (df_elektronik['durasi_laptop'] * 50) + \
                                      (df_elektronik['durasi_tab'] * 10)) * 0.829 / (1000 * 60)
    df_elektronik['emisi_elektronik_pribadi'] = emisi_pribadi_harian_per_menit * jumlah_hari_datang
    
    # Menambahkan emisi fasilitas (AC/Lampu) dari df_aktivitas
    if not df_aktivitas.empty:
        # Menjumlahkan emisi_ac dan emisi_lampu per id_mahasiswa dari aktivitas_harian
        # Ini akan menjadi total emisi fasilitas yang digunakan oleh mahasiswa tersebut
        emisi_fasilitas_total = df_aktivitas.groupby('id_mahasiswa')[['emisi_ac', 'emisi_lampu']].sum().sum(axis=1)
        df_elektronik = df_elektronik.merge(emisi_fasilitas_total.rename('emisi_fasilitas'), on='id_mahasiswa', how='left').fillna(0)
    else:
        df_elektronik['emisi_fasilitas'] = 0
    
    df_elektronik['emisi_elektronik'] = df_elektronik['emisi_elektronik_pribadi'] + df_elektronik['emisi_fasilitas']
    df_elektronik.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')

    # --- Transformasi Data untuk Tabel 'sampah_makanan' ---
    print("   - Memproses 'sampah_makanan'...")
    df_makanan = df_raw[['id_mahasiswa', 'tempat_makan_raw']].copy()
    df_makanan.rename(columns={'tempat_makan_raw': 'tempat_makan'}, inplace=True)
    df_makanan = pd.merge(df_makanan, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    # Inisialisasi kolom emisi sampah harian
    emisi_harian_cols = ['emisi_sampah_makanan_senin', 'emisi_sampah_makanan_selasa', 'emisi_sampah_makanan_rabu', 
                        'emisi_sampah_makanan_kamis', 'emisi_sampah_makanan_jumat', 'emisi_sampah_makanan_sabtu', 
                        'emisi_sampah_makanan_minggu']
    for col in emisi_harian_cols:
        df_makanan[col] = 0.0 # Default ke 0.0

    # Mengisi emisi sampah harian dari df_aktivitas
    if not df_aktivitas.empty:
        # Menjumlahkan emisi_sampah_makanan_per_waktu per responden dan per hari
        emisi_per_responden_hari = df_aktivitas.groupby(['id_mahasiswa', 'hari'])['emisi_sampah_makanan_per_waktu'].sum().reset_index()
        
        # Mapping nama hari ke nama kolom
        hari_to_col = {
            'Senin': 'emisi_sampah_makanan_senin', 'Selasa': 'emisi_sampah_makanan_selasa',
            'Rabu': 'emisi_sampah_makanan_rabu', 'Kamis': 'emisi_sampah_makanan_kamis',
            'Jumat': 'emisi_sampah_makanan_jumat', 'Sabtu': 'emisi_sampah_makanan_sabtu',
            'Minggu': 'emisi_sampah_makanan_minggu'
        }
        
        # Iterasi untuk mengisi nilai ke kolom yang sesuai
        for _, row in emisi_per_responden_hari.iterrows():
            id_mahasiswa = row['id_mahasiswa']
            hari = row['hari']
            emisi_value = row['emisi_sampah_makanan_per_waktu']
            
            if hari in hari_to_col:
                col_name = hari_to_col[hari]
                df_makanan.loc[df_makanan['id_mahasiswa'] == id_mahasiswa, col_name] = emisi_value
    
    df_makanan.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')
    
    # Memilih kolom akhir untuk setiap DataFrame yang akan dimuat ke database
    final_transport_cols = ['id_mahasiswa', 'transportasi', 'kecamatan', 'hari_datang', 'jarak', 'konsumsi', 'jenis_bbm', 'faktor_emisi_per_km', 'emisi_transportasi']
    final_elektronik_cols = ['id_mahasiswa', 'hari_datang', 'penggunaan_hp', 'durasi_hp', 'penggunaan_laptop', 'durasi_laptop', 'penggunaan_tab', 'durasi_tab', 'emisi_elektronik_pribadi', 'emisi_elektronik']
    final_makanan_cols = [
        'id_mahasiswa', 'hari_datang', 'tempat_makan', 
        'emisi_sampah_makanan_senin', 'emisi_sampah_makanan_selasa', 'emisi_sampah_makanan_rabu',
        'emisi_sampah_makanan_kamis', 'emisi_sampah_makanan_jumat', 'emisi_sampah_makanan_sabtu',
        'emisi_sampah_makanan_minggu'
    ]
    
    return {
        "mahasiswa": df_responden[['id_mahasiswa', 'nama', 'program_studi', 'hari_datang']],
        "transportasi": df_transport[[col for col in final_transport_cols if col in df_transport.columns]],
        "elektronik": df_elektronik[[col for col in final_elektronik_cols if col in df_elektronik.columns]],
        "sampah_makanan": df_makanan[[col for col in final_makanan_cols if col in df_makanan.columns]],
        "aktivitas_harian": df_aktivitas
    }

def main():
    """Fungsi utama untuk menjalankan proses ETL."""
    print("Memulai proses ETL...\n")
    
    # Inisialisasi koneksi Supabase
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("Kredensial Supabase tidak ditemukan. Harap atur di file .env"); return
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Langkah 0: Bersihkan tabel di Supabase (FULL RESET)
    clear_supabase_tables(supabase)

    # Langkah 1: Ekstraksi data dari Google Sheet
    worksheet = connect_to_gsheet(SHEET_URL, RAW_DATA_WORKSHEET_NAME)
    if not worksheet: return
    
    raw_dataframe = extract_data_to_df(worksheet)
    if raw_dataframe.empty: return

    # Langkah 2: Transformasi data
    transformed_data = transform_all_data(raw_dataframe)
    
    # Langkah 3: Pemuatan data ke Supabase
    load_order = ["mahasiswa", "transportasi", "elektronik", "sampah_makanan", "aktivitas_harian"]
    
    for table_name in load_order:
        df = transformed_data.get(table_name)
        if df is not None:
            is_log_table = table_name == "aktivitas_harian"
            # Semua tabel menggunakan id_mahasiswa sebagai primary key atau foreign key utama
            load_to_supabase(supabase, table_name, df, 'id_mahasiswa', is_log=is_log_table)
        else:
            print(f"Peringatan: DataFrame untuk tabel '{table_name}' tidak ditemukan.")
    
    print("\n🎉 Semua proses ETL selesai.")

if __name__ == "__main__":
    main()