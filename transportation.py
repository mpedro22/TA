import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    return pd.read_csv(url)

def show():
    st.markdown("""
        <h1 style='margin-bottom:0;'>Transportation Emissions</h1>
        <p style='margin-top:0; color: gray;'>
            Explore carbon emissions based on campus commuting behavior. This includes vehicle type, fuel used, distance, and day-by-day emissions breakdown.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()

    # Sidebar filters
    with st.sidebar:
        st.subheader("Filter Data")
        transport_options = df['transportasi'].dropna().unique().tolist()
        bbm_options = df['jenis_bbm'].dropna().unique().tolist()

        selected_transport = st.multiselect("Jenis Transportasi", transport_options, default=transport_options)
        selected_bbm = st.multiselect("Jenis BBM", bbm_options, default=bbm_options)

    # Apply filters
    filtered_df = df[
        df['transportasi'].isin(selected_transport)
    ]

    # KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Emisi Mingguan", f"{filtered_df['emisi_mingguan'].sum():,.2f} kg CO₂")
    with col2:
        rata2 = filtered_df['emisi_mingguan'].mean()
        st.metric("Rata-rata Emisi / Responden", f"{rata2:.2f} kg CO₂")

    st.markdown("<br>", unsafe_allow_html=True)

    # Pie chart: transportasi distribution
    st.subheader("Distribusi Moda Transportasi")
    fig1 = px.pie(filtered_df, names='transportasi', title='Proporsi Moda Transportasi', hole=0.4)
    st.plotly_chart(fig1, use_container_width=True)

    # Bar chart: average emission by transport
    st.subheader("Rata-rata Emisi Mingguan per Moda")
    avg_df = filtered_df.groupby("transportasi")["emisi_mingguan"].mean().reset_index()
    fig2 = px.bar(avg_df, x='transportasi', y='emisi_mingguan', labels={'emisi_mingguan': 'Emisi (kg CO₂)'})
    st.plotly_chart(fig2, use_container_width=True)

    # Line chart: Emisi harian total semua responden
    st.subheader("Total Emisi Harian")
    daily_cols = ['emisi_senin','emisi_selasa','emisi_rabu','emisi_kamis','emisi_jumat','emisi_sabtu','emisi_minggu']
    daily_total = filtered_df[daily_cols].sum().reset_index()
    daily_total.columns = ['Hari', 'Total Emisi (kg CO₂)']
    daily_total['Hari'] = daily_total['Hari'].str.replace('emisi_', '').str.capitalize()
    fig3 = px.line(daily_total, x='Hari', y='Total Emisi (kg CO₂)', markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # Data table
    st.subheader("Tabel Data Lengkap")
    st.dataframe(filtered_df, use_container_width=True)

    st.caption("Sumber: Data Kuisioner Emisi Transportasi Civitas ITB")
