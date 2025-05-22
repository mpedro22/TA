import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=994176057"
    df = pd.read_csv(url)

    # Pastikan kolom numerik dikonversi ke float
    emisi_cols = [col for col in df.columns if col.startswith("emisi_")]
    jumlah_cols = [col for col in df.columns if col.startswith("jumlah_makan")]
    df[emisi_cols + jumlah_cols] = df[emisi_cols + jumlah_cols].apply(pd.to_numeric, errors="coerce")

    return df

def show():
    st.markdown("""
        <h1 style='margin-bottom:0;'>Food & Drink Waste Emissions</h1>
        <p style='margin-top:0; color: gray;'>
            Estimasi emisi karbon akibat konsumsi makanan dan minuman di kampus berdasarkan waktu makan setiap hari.
        </p>
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()

    # Sidebar filters
    with st.sidebar:
        st.subheader("Filter Data")
        hari_list = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        selected_day = st.multiselect("Hari Datang", hari_list, default=hari_list)

    # Filter berdasarkan hari_datang (string check to avoid float error)
    filtered_df = df[df['hari_datang'].apply(lambda x: isinstance(x, str) and any(day in x for day in selected_day))]

    # KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        total_emisi = filtered_df['emisi_makanminum_mingguan'].sum()
        st.metric("Total Emisi Mingguan", f"{total_emisi:,.2f} kg CO₂")
    with col2:
        st.metric("Jumlah Responden", f"{filtered_df['id_responden'].nunique()}")
    with col3:
        avg = filtered_df['emisi_makanminum_mingguan'].mean()
        st.metric("Rata-rata Emisi / Responden", f"{avg:.2f} kg CO₂")

    st.markdown("<br>", unsafe_allow_html=True)

    # Pie chart: Frekuensi konsumsi per hari
    st.subheader("Frekuensi Konsumsi Makan/Minum per Hari")
    frekuensi = {
        "Senin": filtered_df['jumlah_makan_senin'].sum(),
        "Selasa": filtered_df['jumlah_makan_selasa'].sum(),
        "Rabu": filtered_df['jumlah_makan_rabu'].sum(),
        "Kamis": filtered_df['jumlah_makan_kamis'].sum(),
        "Jumat": filtered_df['jumlah_makan_jumat'].sum(),
        "Sabtu": filtered_df['jumlah_makan_sabtu'].sum(),
        "Minggu": filtered_df['jumlah_makan_minggu'].sum()
    }
    fig1 = px.pie(names=list(frekuensi.keys()), values=list(frekuensi.values()), hole=0.3)
    st.plotly_chart(fig1, use_container_width=True)

    # Bar chart: Emisi per hari
    st.subheader("Total Emisi Harian dari Makan/Minum")
    emisi_harian = {
        "Senin": filtered_df['emisi_makanminum_senin'].sum(),
        "Selasa": filtered_df['emisi_makanminum_selasa'].sum(),
        "Rabu": filtered_df['emisi_makanminum_rabu'].sum(),
        "Kamis": filtered_df['emisi_makanminum_kamis'].sum(),
        "Jumat": filtered_df['emisi_makanminum_jumat'].sum(),
        "Sabtu": filtered_df['emisi_makanminum_sabtu'].sum(),
        "Minggu": filtered_df['emisi_makanminum_minggu'].sum()
    }
    fig2 = px.bar(x=list(emisi_harian.keys()), y=list(emisi_harian.values()),
                  labels={"x": "Hari", "y": "Emisi (kg CO₂)"})
    st.plotly_chart(fig2, use_container_width=True)

    # Histogram: Emisi mingguan per responden
    st.subheader("Distribusi Emisi Mingguan per Responden")
    fig3 = px.histogram(filtered_df, x="emisi_makanminum_mingguan", nbins=10,
                        labels={"emisi_makanminum_mingguan": "Emisi (kg CO₂)"})
    st.plotly_chart(fig3, use_container_width=True)

    # Data Table
    st.subheader("Tabel Data Emisi Makan & Minum")
    st.dataframe(filtered_df, use_container_width=True)

    st.caption("Sumber: Kuisioner Emisi Makan dan Minum Civitas ITB")
