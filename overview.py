import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data(ttl=60)
def load_data():
    base_url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid="
    return {
        "responden": pd.read_csv(base_url + "1606042726"),
        "transport": pd.read_csv(base_url + "155140281"),
        "electronic": pd.read_csv(base_url + "622151341"),
        "food": pd.read_csv(base_url + "994176057"),
        "daily": pd.read_csv(base_url + "1749257811")
    }

def show():
    st.title("Overview Emisi Karbon Mahasiswa ITB")
    data = load_data()

    df_responden = data["responden"]
    df_transport = data["transport"]
    df_electronic = data["electronic"]
    df_food = data["food"]
    df_daily = data["daily"]

    df_transport["emisi_mingguan"] = pd.to_numeric(df_transport["emisi_mingguan"], errors='coerce')
    df_electronic["emisi_elektronik_mingguan"] = pd.to_numeric(df_electronic["emisi_elektronik_mingguan"], errors='coerce')
    df_food["emisi_makanminum_mingguan"] = pd.to_numeric(df_food["emisi_makanminum_mingguan"], errors='coerce')

    total_emisi_transport = df_transport["emisi_mingguan"].sum()
    total_emisi_electronic = df_electronic["emisi_elektronik_mingguan"].sum()
    total_emisi_food = df_food["emisi_makanminum_mingguan"].sum()

    total_emisi = total_emisi_transport + total_emisi_electronic + total_emisi_food
    avg_emisi_per_mahasiswa = total_emisi / df_responden.shape[0]

    # METRICS
    st.subheader("Ringkasan Emisi")
    col1, col2 = st.columns(2)
    col1.metric("Total Emisi Karbon", f"{total_emisi / 1000:.2f} kg CO2")
    col2.metric("Rata-rata Emisi per Mahasiswa", f"{avg_emisi_per_mahasiswa / 1000:.2f} kg CO2")

    # PIE CHART - Distribusi Emisi
    distribusi = pd.DataFrame({
        "Kategori": ["Transportasi", "Elektronik", "Makanan & Minuman"],
        "Emisi": [total_emisi_transport, total_emisi_electronic, total_emisi_food]
    })
    fig_pie = px.pie(distribusi, names="Kategori", values="Emisi", title="Distribusi Emisi Berdasarkan Aktivitas")
    st.plotly_chart(fig_pie, use_container_width=True)

    # LINE CHART - Tren Emisi Harian
    st.subheader("Tren Emisi Harian")
    harian = df_daily.groupby("hari")["kegiatan"].count().reset_index(name="Jumlah Aktivitas")
    fig_line = px.line(harian, x="hari", y="Jumlah Aktivitas", markers=True,
                       title="Jumlah Aktivitas Mahasiswa per Hari (Sebagai Indikator Emisi)")
    st.plotly_chart(fig_line, use_container_width=True)

    # HEATMAP - Aktivitas Mahasiswa
    st.subheader("Heatmap Aktivitas Mahasiswa")
    heatmap_data = df_daily.groupby(["hari", "lokasi"]).size().reset_index(name="Jumlah")
    heatmap_pivot = heatmap_data.pivot(index="lokasi", columns="hari", values="Jumlah").fillna(0)

    fig_heatmap = px.imshow(heatmap_pivot,
                            labels=dict(x="Hari", y="Lokasi", color="Jumlah Aktivitas"),
                            title="Heatmap Aktivitas Mahasiswa: Hari × Lokasi")
    st.plotly_chart(fig_heatmap, use_container_width=True)


    # BAR CHART - Lokasi Teraktif
    st.subheader("Lokasi Terbanyak Digunakan")
    lokasi = df_daily["lokasi"].value_counts().reset_index()
    lokasi.columns = ["Lokasi", "Frekuensi"]
    fig_lokasi = px.bar(lokasi.head(10), x="Lokasi", y="Frekuensi",
                        title="10 Lokasi Kampus Paling Sering Digunakan")
    st.plotly_chart(fig_lokasi, use_container_width=True)
