# etl_script.py

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

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json'
SHEET_URL = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4"
RAW_DATA_WORKSHEET_NAME = "Form Responses 1 RAW (Dummy)" # Menggunakan sheet dummy untuk data besar

def connect_to_gsheet(url, worksheet_name):
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
    if not sheet: return pd.DataFrame()
    print(f"📥 Mengekstrak data dari sheet '{sheet.title}'...")
    data = sheet.get_all_values()
    if not data or len(data) < 2:
        print("   -> Sheet kosong atau hanya berisi header.")
        return pd.DataFrame()
    headers = data.pop(0)
    df = pd.DataFrame(data, columns=headers)
    print(f"   -> Ditemukan {len(df)} baris data mentah.")
    return df

def get_fakultas_mapping():
    return {'Meteorologi':'FITB','Oseanografi':'FITB','Teknik Geodesi dan Geomatika':'FITB','Teknik Geologi':'FITB','Aktuaria':'FMIPA','Astronomi':'FMIPA','Fisika':'FMIPA',
            'Kimia':'FMIPA','Matematika':'FMIPA','Desain Interior':'FSRD','Desain Komunikasi Visual':'FSRD','Desain Produk':'FSRD','Kriya':'FSRD','Seni Rupa':'FSRD',
            'Manajemen Rekayasa Industri':'FTI','Teknik Fisika':'FTI','Teknik Industri':'FTI','Teknik Kimia':'FTI','Teknik Geofisika':'FTTM','Teknik Metalurgi':'FTTM',
            'Teknik Perminyakan':'FTTM','Teknik Pertambangan':'FTTM','Teknik Dirgantara':'FTMD','Teknik Material':'FTMD','Teknik Mesin':'FTMD','Teknik Kelautan':'FTSL',
            'Teknik Lingkungan':'FTSL','Teknik Sipil':'FTSL','Arsitektur':'SAPPK','Perencanaan Wilayah dan Kota':'SAPPK','Kewirausahaan':'SBM','Manajemen':'SBM',
            'Farmasi Klinik dan Komunitas':'SF','Sains dan Teknologi Farmasi':'SF','Biologi':'SITH','Mikrobiologi':'SITH','Sistem dan Teknologi Informasi':'STEI',
            'Teknik Biomedis':'STEI','Teknik Elektro':'STEI','Informatika':'STEI','Teknik Telekomunikasi':'STEI','Teknik Tenaga Listrik':'STEI'}

def clear_supabase_tables(supabase: Client):
    print("\n🧹 Membersihkan tabel di Supabase sebelum memuat data baru...")
    
    tables_to_clear = ["aktivitas_harian", "transportasi", "elektronik", "sampah_makanan", "mahasiswa"]
    
    for table_name in tables_to_clear:
        try:
            response = supabase.table(table_name).delete().neq('id_mahasiswa', 0).execute() 
            
            if response.data is not None:
                print(f"   -> Berhasil membersihkan tabel '{table_name}'. Dihapus: {len(response.data)} baris.")
            else:
                print(f"   -> Berhasil membersihkan tabel '{table_name}'. (Tidak ada baris yang cocok atau tabel sudah kosong).")

        except Exception as e:
            print(f"   -> Gagal membersihkan tabel '{table_name}': {e}")
            pass

    print("✅ Proses pembersihan tabel selesai.")


def load_to_supabase(supabase: Client, table_name: str, df: pd.DataFrame, pk_column: str, is_log=False):
    if df.empty:
        print(f"Tidak ada data untuk dimuat ke '{table_name}'.")
        return
    
    df_cleaned = df.replace({np.nan: None, '': None})
    records = df_cleaned.to_dict(orient="records")
    
    print(f"Memuat {len(records)} baris ke tabel '{table_name}'...")
    
    batch_size_delete = 500
    batch_size_insert = 1000
    
    try:
        if is_log:
            ids_to_delete_all = df_cleaned[pk_column].unique().tolist()
            if ids_to_delete_all:
                print(f"   - Menghapus log lama untuk {len(ids_to_delete_all)} responden (batching DELETE)...")
                
                for i in range(0, len(ids_to_delete_all), batch_size_delete):
                    batch_ids = ids_to_delete_all[i:i + batch_size_delete]
                    try:
                        supabase.table(table_name).delete().in_(pk_column, batch_ids).execute()
                        print(f"     -> Berhasil menghapus batch {i//batch_size_delete + 1} dari {len(ids_to_delete_all)//batch_size_delete + 1} ({len(batch_ids)} IDs).")
                        time.sleep(0.1)
                    except Exception as batch_e:
                        print(f"     -> Gagal menghapus batch {i//batch_size_delete + 1} (IDs: {batch_ids[0]}-{batch_ids[-1]}): {batch_e}")
                        pass
                
            print("   - Memasukkan log baru (batching INSERT)...")
            for i in range(0, len(records), batch_size_insert):
                batch_records = records[i:i + batch_size_insert]
                try:
                    supabase.table(table_name).insert(batch_records).execute()
                    print(f"     -> Berhasil memasukkan batch {i//batch_size_insert + 1} dari {len(records)//batch_size_insert + 1} ({len(batch_records)} records).")
                    time.sleep(0.1)
                except Exception as batch_e:
                    print(f"     -> Gagal memasukkan batch {i//batch_size_insert + 1} (records {i}-{i+len(batch_records)-1}): {batch_e}")
                    pass
            
        else:
            supabase.table(table_name).upsert(records, on_conflict=pk_column).execute()
        print(f"   -> Berhasil.")
    except Exception as e:
        print(f"   -> Gagal total saat memuat ke '{table_name}': {e}")

def transform_all_data(df_raw):
    print("🔄 Memulai proses transformasi data...")

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
    
    df_raw['id_mahasiswa'] = [i + 1 for i in range(len(df_raw))]
    
    hari_map_kegiatan = {
        'Senin': [f'keg_senin_{i}' for i in range(10)], 'Selasa': [f'keg_selasa_{i}' for i in range(10)],
        'Rabu': [f'keg_rabu_{i}' for i in range(10)], 'Kamis': [f'keg_kamis_{i}' for i in range(10)],
        'Jumat': [f'keg_jumat_{i}' for i in range(10)], 'Sabtu': [f'keg_sabtu_{i}' for i in range(10)],
        'Minggu': [f'keg_minggu_{i}' for i in range(10)]
    }

    print("   - Memproses 'mahasiswa'...")
    df_responden = df_raw[['id_mahasiswa', 'nama_raw', 'prodi_raw']].copy()
    df_responden.rename(columns={'nama_raw': 'nama', 'prodi_raw': 'program_studi'}, inplace=True)
    
    hari_datang_list = df_raw.apply(
        lambda row: ", ".join([hari for hari, cols in hari_map_kegiatan.items() if any(row[c] and str(row[c]).strip().lower() != 'tidak di kampus' for c in cols)]),
        axis=1
    )
    df_responden['hari_datang'] = hari_datang_list
    df_responden.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')

    print("   - Memproses 'aktivitas_harian'...")
    all_activities = []
    waktu_slots = ["00-06", "06-08", "08-10", "10-12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]
    for _, row in df_raw.iterrows():
        for hari_name, keg_cols in hari_map_kegiatan.items():
            for i, keg_col in enumerate(keg_cols):
                kegiatan = row[keg_col]
                if kegiatan and str(kegiatan).strip() and str(kegiatan).lower() != "tidak di kampus":
                    lokasi = None
                    if 'Kelas' in kegiatan: lokasi_raw = row[f'lokasi_kelas_{hari_name.lower()}']
                    elif 'Makan' in kegiatan: lokasi_raw = row['tempat_makan_raw']
                    else: lokasi_raw = row[f'lokasi_lain_{hari_name.lower()}']
                    
                    if isinstance(lokasi_raw, str) and lokasi_raw.strip() not in ['-', '']: 
                        cleaned_locations = [loc.strip() for loc in lokasi_raw.split(',') if loc.strip()]
                        lokasi = random.choice(cleaned_locations) if cleaned_locations else None
                    
                    is_kelas = 'Kelas' in kegiatan
                    is_makan = 'Makan' in kegiatan
                    
                    # Logika: AC hanya jika 'Kelas'
                    emisi_ac_val = 1.66 if is_kelas else 0 
                    
                    # Logika: Lampu jika 'Kelas' ATAU 'Makan'
                    is_light_intensive = is_kelas or is_makan
                    emisi_lampu_val = 0.24 if is_light_intensive else 0
                    
                    # Emisi Sampah Makanan hanya jika 'Makan'
                    emisi_sampah_makanan_per_waktu_val = 0.95 if is_makan else 0

                    all_activities.append({
                        'id_mahasiswa': row['id_mahasiswa'], 
                        'hari': hari_name,
                        'waktu': waktu_slots[i],
                        'kegiatan': kegiatan,
                        'lokasi': lokasi,
                        'penggunaan_ac': emisi_ac_val > 0, 
                        'emisi_ac': emisi_ac_val,
                        'emisi_lampu': emisi_lampu_val,
                        'emisi_sampah_makanan_per_waktu': emisi_sampah_makanan_per_waktu_val
                    })

    df_aktivitas = pd.DataFrame(all_activities)
    print(f"   - Berhasil membuat {len(df_aktivitas)} baris log aktivitas.")
    
    print("   - Memproses 'transportasi'...")
    df_transport = df_raw[['id_mahasiswa', 'transportasi', 'kecamatan', 'estimasi_jarak', 'jenis_bbm']].copy()
    df_transport = pd.merge(df_transport, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    df_transport['jarak'] = pd.to_numeric(df_transport['estimasi_jarak'].map({"< 1 km": 0.5, "1 - 3 km": 2, "3 - 5 km": 4, "5 - 10 km": 7.5, "> 10 km": 12}), errors='coerce').fillna(0)
    
    df_transport['konsumsi'] = df_transport['transportasi'].map({"Mobil": 0.1, "Angkutan Umum": 0.1, "Ojek Online": 0.035, "Motor": 0.035}).fillna(0)
    
    ncv_map = {"Ron 90": 44.61, "Ron 92": 44.61, "Ron 95": 44.62, "Ron 98": 44.62}
    fe_tj_map = {"Ron 90": 69.67, "Ron 92": 69.04, "Ron 95": 68.97, "Ron 98": 68.91}
    df_transport['ncv'] = df_transport['jenis_bbm'].apply(lambda x: next((v for k, v in ncv_map.items() if k in str(x)), 0))
    df_transport['fe_tj'] = df_transport['jenis_bbm'].apply(lambda x: next((v for k, v in fe_tj_map.items() if k in str(x)), 0))
    
    df_transport['faktor_emisi_per_km'] = (pd.to_numeric(df_transport['ncv'], errors='coerce') * 0.74) * (pd.to_numeric(df_transport['fe_tj'], errors='coerce') / 1000)
    
    df_transport['emisi_transportasi'] = df_transport['jarak'] * (df_transport['konsumsi'] * df_transport['faktor_emisi_per_km']) * 2
    
    df_transport.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')

    print("   - Memproses 'elektronik'...")
    df_elektronik = df_raw[['id_mahasiswa', 'perangkat_list', 'durasi_hp_raw', 'durasi_laptop_raw', 'durasi_tab_raw']].copy()
    df_elektronik = pd.merge(df_elektronik, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    df_elektronik['penggunaan_hp'] = df_elektronik['perangkat_list'].str.contains('HP', na=False)
    df_elektronik['penggunaan_laptop'] = df_elektronik['perangkat_list'].str.contains('Laptop', na=False)
    df_elektronik['penggunaan_tab'] = df_elektronik['perangkat_list'].str.contains('Tab', na=False)
    
    def clean_duration(text): 
        match = re.findall(r'\d+', str(text))
        return int(match[0]) if match else 0
    
    df_elektronik['durasi_hp'] = pd.to_numeric(df_elektronik['durasi_hp_raw'].apply(clean_duration), errors='coerce').fillna(0)
    df_elektronik['durasi_laptop'] = pd.to_numeric(df_elektronik['durasi_laptop_raw'].apply(clean_duration), errors='coerce').fillna(0)
    df_elektronik['durasi_tab'] = pd.to_numeric(df_elektronik['durasi_tab_raw'].apply(clean_duration), errors='coerce').fillna(0)
    
    jumlah_hari_datang = df_elektronik['hari_datang'].apply(
        lambda x: len([h.strip() for h in str(x).split(',') if h.strip()]) 
        if pd.notna(x) and str(x).strip() else 0
    )
    
    emisi_pribadi_harian_per_menit = ((df_elektronik['durasi_hp'] * 4) + \
                                      (df_elektronik['durasi_laptop'] * 50) + \
                                      (df_elektronik['durasi_tab'] * 10)) * 0.829 / (1000 * 60)
    df_elektronik['emisi_elektronik_pribadi'] = emisi_pribadi_harian_per_menit * jumlah_hari_datang
    
    if not df_aktivitas.empty:
        emisi_fasilitas_total = df_aktivitas.groupby('id_mahasiswa')[['emisi_ac', 'emisi_lampu']].sum().sum(axis=1)
        df_elektronik = df_elektronik.merge(emisi_fasilitas_total.rename('emisi_fasilitas'), on='id_mahasiswa', how='left').fillna(0)
    else:
        df_elektronik['emisi_fasilitas'] = 0
    
    df_elektronik['emisi_elektronik'] = df_elektronik['emisi_elektronik_pribadi'] + df_elektronik['emisi_fasilitas']
    df_elektronik.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')

    print("   - Memproses 'sampah_makanan'...")
    df_makanan = df_raw[['id_mahasiswa', 'tempat_makan_raw']].copy()
    df_makanan.rename(columns={'tempat_makan_raw': 'tempat_makan'}, inplace=True)
    df_makanan = pd.merge(df_makanan, df_responden[['id_mahasiswa', 'hari_datang']], on='id_mahasiswa', how='left')
    
    emisi_harian_cols = ['emisi_sampah_makanan_senin', 'emisi_sampah_makanan_selasa', 'emisi_sampah_makanan_rabu', 
                        'emisi_sampah_makanan_kamis', 'emisi_sampah_makanan_jumat', 'emisi_sampah_makanan_sabtu', 
                        'emisi_sampah_makanan_minggu']
    for col in emisi_harian_cols:
        df_makanan[col] = 0.0

    if not df_aktivitas.empty:
        emisi_per_responden_hari = df_aktivitas.groupby(['id_mahasiswa', 'hari'])['emisi_sampah_makanan_per_waktu'].sum().reset_index()
        
        hari_to_col = {
            'Senin': 'emisi_sampah_makanan_senin', 'Selasa': 'emisi_sampah_makanan_selasa',
            'Rabu': 'emisi_sampah_makanan_rabu', 'Kamis': 'emisi_sampah_makanan_kamis',
            'Jumat': 'emisi_sampah_makanan_jumat', 'Sabtu': 'emisi_sampah_makanan_sabtu',
            'Minggu': 'emisi_sampah_makanan_minggu'
        }
        
        for _, row in emisi_per_responden_hari.iterrows():
            id_mahasiswa = row['id_mahasiswa']
            hari = row['hari']
            emisi_value = row['emisi_sampah_makanan_per_waktu']
            
            if hari in hari_to_col:
                col_name = hari_to_col[hari]
                df_makanan.loc[df_makanan['id_mahasiswa'] == id_mahasiswa, col_name] = emisi_value
    
    df_makanan.drop_duplicates(subset=['id_mahasiswa'], inplace=True, keep='last')
    
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
    print("Memulai proses ETL...\n")
    
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("Kredensial Supabase tidak ditemukan. Harap atur di file .env"); return
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Langkah 1: Ekstraksi data dari Google Sheet
    worksheet = connect_to_gsheet(SHEET_URL, RAW_DATA_WORKSHEET_NAME)
    if not worksheet: return
    
    raw_dataframe = extract_data_to_df(worksheet)
    if raw_dataframe.empty:
        print("🛑 Data mentah dari Google Sheet kosong atau hanya berisi header. Tidak ada data yang akan diproses atau dimuat ke database.")
        return # Menghentikan eksekusi jika tidak ada data

    # Langkah 0: Bersihkan tabel di Supabase (FULL RESET) - Pindahkan setelah validasi sheet tidak kosong
    clear_supabase_tables(supabase)

    # Langkah 2: Transformasi data
    transformed_data = transform_all_data(raw_dataframe)
    
    # Langkah 3: Pemuatan data ke Supabase
    load_order = ["mahasiswa", "transportasi", "elektronik", "sampah_makanan", "aktivitas_harian"]
    
    for table_name in load_order:
        df = transformed_data.get(table_name)
        if df is not None:
            is_log_table = table_name == "aktivitas_harian"
            load_to_supabase(supabase, table_name, df, 'id_mahasiswa', is_log=is_log_table)
        else:
            print(f"Peringatan: DataFrame untuk tabel '{table_name}' tidak ditemukan.")
    
    print("\n🎉 Semua proses ETL selesai.")

if __name__ == "__main__":
    main()