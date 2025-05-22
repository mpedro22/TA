import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=622151341"
    return pd.read_csv(url)

def show():
    st.markdown("""
        <h1 style='margin-bottom:0;'>Electronic Emissions</h1>
        <p style='margin-top:0; color: gray;'>
            Estimasi emisi karbon dari pengisian daya perangkat elektronik mahasiswa (HP, laptop, tablet) di kampus ITB.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()

    with st.sidebar:
        st.subheader("Filter Data")
        hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        selected_day = st.multiselect("Hari Datang", hari_list, default=hari_list)

    filtered_df = df[df['hari_datang'].apply(lambda x: isinstance(x, str) and any(day in x for day in selected_day))]

    # KPI Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Emisi Mingguan", f"{filtered_df['emisi_elektronik_mingguan'].sum():,.2f} kg CO₂")
    with col2:
        avg = filtered_df['emisi_elektronik_mingguan'].mean()
        st.metric("Rata-rata Emisi / Responden", f"{avg:.2f} kg CO₂")

    st.markdown("<br>", unsafe_allow_html=True)

    # Pie Chart: device usage proportion
    st.subheader("Distribusi Penggunaan Perangkat Elektronik")
    st.caption("Menampilkan jumlah responden yang menggunakan masing-masing perangkat.")
    device_counts = {
        "HP": filtered_df['penggunaan_hp'].str.lower().eq("iya").sum(),
        "Laptop": filtered_df['penggunaan_laptop'].str.lower().eq("iya").sum(),
        "Tablet": filtered_df['penggunaan_tab'].str.lower().eq("iya").sum()
    }
    fig1 = px.pie(names=list(device_counts.keys()), values=list(device_counts.values()), hole=0.3)
    st.plotly_chart(fig1, use_container_width=True)

    # Bar Chart: emissions per respondent
    st.subheader("Emisi Elektronik Mingguan per Responden")
    st.caption("Semakin tinggi emisi, semakin lama dan banyak perangkat yang diisi daya.")
    fig2 = px.bar(filtered_df, x="id_responden", y="emisi_elektronik_mingguan",
                  labels={"emisi_elektronik_mingguan": "Emisi (kg CO₂)"},
                  hover_name="id_responden")
    st.plotly_chart(fig2, use_container_width=True)

    # Box Plot: durasi charging per perangkat
    st.subheader("Distribusi Durasi Charging per Perangkat")
    st.caption("Memperlihatkan variasi durasi pengisian daya untuk masing-masing jenis perangkat.")
    durasi_df = filtered_df[["id_responden", "durasi_hp", "durasi_laptop", "durasi_tab"]].copy()
    durasi_melted = durasi_df.melt(id_vars="id_responden", 
                                   value_vars=["durasi_hp", "durasi_laptop", "durasi_tab"],
                                   var_name="Perangkat", value_name="Durasi (menit)")
    durasi_melted["Perangkat"] = durasi_melted["Perangkat"].replace({
        "durasi_hp": "HP", "durasi_laptop": "Laptop", "durasi_tab": "Tablet"
    })
    fig3 = px.box(durasi_melted, x="Perangkat", y="Durasi (menit)", points="all")
    st.plotly_chart(fig3, use_container_width=True)

    # Scatter Plot: duration vs emission (all devices combined)
    st.subheader("Korelasi Durasi Charging vs Emisi Elektronik")
    st.caption("Menganalisis hubungan antara durasi pengisian daya dan emisi karbon yang dihasilkan.")
    scatter_df = filtered_df[["id_responden", "durasi_hp", "durasi_laptop", "durasi_tab", "emisi_elektronik"]].copy()
    melted = scatter_df.melt(id_vars=["id_responden", "emisi_elektronik"],
                             value_vars=["durasi_hp", "durasi_laptop", "durasi_tab"],
                             var_name="Perangkat", value_name="Durasi (menit)")
    melted["Perangkat"] = melted["Perangkat"].replace({
        "durasi_hp": "HP", "durasi_laptop": "Laptop", "durasi_tab": "Tablet"
    })
    fig4 = px.scatter(melted, x="Durasi (menit)", y="emisi_elektronik", color="Perangkat", trendline="ols")
    st.plotly_chart(fig4, use_container_width=True)

    # Line Chart: total daily emissions
    st.subheader("Total Emisi Elektronik per Hari")
    hari_cols = [
        'emisi_elektronik_senin', 'emisi_elektronik_selasa', 'emisi_elektronik_rabu',
        'emisi_elektronik_kamis', 'emisi_elektronik_jumat', 'emisi_elektronik_sabtu', 'emisi_elektronik_minggu'
    ]
    daily_sum = filtered_df[hari_cols].sum().reset_index()
    daily_sum.columns = ['Hari', 'Total Emisi (kg CO₂)']
    daily_sum['Hari'] = daily_sum['Hari'].str.replace('emisi_elektronik_', '').str.capitalize()
    fig5 = px.line(daily_sum, x='Hari', y='Total Emisi (kg CO₂)', markers=True)
    st.plotly_chart(fig5, use_container_width=True)

    # Data Table
    st.subheader("Tabel Data Penggunaan Elektronik")
    st.dataframe(filtered_df, use_container_width=True)

    st.caption("Sumber: Kuisioner Emisi Elektronik Civitas ITB")
