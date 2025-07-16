import streamlit as st
from src.components.loading import loading, loading_decorator
import time

def show():
    with loading():
        st.markdown("""
        <div class="wow-header">
            <div class="header-bg-pattern"></div>
            <div class="header-float-1"></div>
            <div class="header-float-2"></div>
            <div class="header-float-3"></div>
            <div class="header-float-4"></div>  
            <div class="header-float-5"></div>              
            <div class="header-content">
                <h1 class="header-title">Tentang Dashboard</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.2)

    st.markdown("""
    <style>
    /* === CIRCLE TEMPLATE - DESKRIPSI === */
    .hero-circle {
        background: radial-gradient(circle at center, #f0fdf4 0%, #dcfce7 50%, #bbf7d0 100%);
        border-radius: 50%;
        width: 100%;
        height: 240px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 
            0 20px 40px rgba(5, 150, 105, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        border: 4px solid rgba(34, 197, 94, 0.3);
        margin: 0 auto;
        position: relative;
        overflow: hidden;
    }
    
    .hero-circle::before {
        content: '';
        position: absolute;
        top: 10%;
        left: 10%;
        right: 10%;
        bottom: 10%;
        border: 2px dashed rgba(5, 150, 105, 0.3);
        border-radius: 50%;
        pointer-events: none;
    }
    
    .hero-circle::after {
        content: '';
        position: absolute;
        top: 20%;
        left: 20%;
        right: 20%;
        bottom: 20%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    
    .hero-title {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #064e3b, #065f46, #047857);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.8rem;
        z-index: 1;
        position: relative;
        text-shadow: 0 2px 8px rgba(6, 78, 59, 0.2);
    }
    
    .hero-desc {
        font-size: 0.85rem;
        color: #374151;
        line-height: 1.5;
        z-index: 1;
        position: relative;
        padding: 0 1.5rem;
        font-weight: 500;
    }
    
    /* === BOX TEMPLATE 1 - TUJUAN === */
    .tujuan-box {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%);
        border-radius: 20px;
        padding: 1.2rem;
        height: 300px;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.08),
            0 5px 15px rgba(5, 150, 105, 0.1);
        border: 2px solid rgba(34, 197, 94, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .tujuan-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #059669, #10b981, #22c55e, #34d399);
    }
    
    .tujuan-box::after {
        content: '';
        position: absolute;
        top: 1rem;
        right: 1rem;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(5, 150, 105, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    
    .section-title {
        text-align: center;
        font-size: 1.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #064e3b, #065f46, #047857);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .section-title::after {
        content: '';
        position: absolute;
        bottom: -0.3rem;
        left: 50%;
        transform: translateX(-50%);
        width: 50px;
        height: 3px;
        background: linear-gradient(90deg, #059669, #22c55e);
        border-radius: 2px;
    }
    
    .tujuan-list {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        position: relative;
        z-index: 1;
    }
    
    .tujuan-item {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.6rem 0.8rem;
        background: rgba(240, 253, 244, 0.8);
        border-radius: 12px;
        border-left: 3px solid #22c55e;
    }
    
    .tujuan-icon {
        width: 20px;
        height: 20px;
        stroke: #047857;
        stroke-width: 2.5;
        flex-shrink: 0;
    }
    
    .tujuan-text {
        font-size: 0.8rem;
        color: #1f2937;
        font-weight: 500;
        line-height: 1.4;
    }
    
    .tujuan-text strong {
        color: #064e3b;
        font-weight: 700;
    }
    
    /* LAYOUT */
    .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        min-height: 100vh !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    .stColumns {
        gap: 1.5rem !important;
        flex: 1 !important;
        display: flex !important;
        align-items: stretch !important;
    }
    
    .stColumn {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    
    /* Additional spacing */
    .stColumn > div:first-child {
        margin-bottom: 2rem !important;
    }
    
    /* Make sure everything fills the viewport */
    .main > div {
        min-height: calc(100vh - 120px) !important;
        display: flex !important;
        flex-direction: column !important;
    }
    </style>
    """, unsafe_allow_html=True)

    
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("""
        <div class="hero-circle">
            <div class="hero-title">ITB Carbon Dashboard</div>
            <div class="hero-desc">
                Dashboard analisis jejak karbon mahasiswa dengan visualisasi real-time 
                untuk mendukung transformasi kampus berkelanjutan dan mencapai target net-zero carbon.
                Platform ini mengintegrasikan berbagai aspek kehidupan kampus untuk monitoring
                komprehensif terhadap emisi karbon dari aktivitas sehari-hari civitas akademika.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tujuan-box" style="height: 360px;">
            <div class="section-title">Tujuan Utama</div>
            <div class="tujuan-list">
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <div class="tujuan-text"><strong>Smart Analytics:</strong> Analisis emisi karbon aktivitas kampus secara berkala dengan sistem otomatis terintegrasi</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <div class="tujuan-text"><strong>Data Insights:</strong> Keputusan strategis berbasis data untuk sustainability dengan prediksi tren dan analisis mendalam</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div class="tujuan-text"><strong>Green Campus:</strong> Transformasi ITB menuju institusi net-zero carbon dengan roadmap berkelanjutan</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <div class="tujuan-text"><strong>Community Engagement:</strong> Melibatkan seluruh civitas akademika dalam program sustainability kampus</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="tujuan-box" style="margin-bottom: 1.5rem;">
            <div class="section-title">Halaman</div>
            <div class="tujuan-list">
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2v0" />
                    </svg>
                    <div class="tujuan-text"><strong>Dashboard Utama:</strong> Overview emisi & perbandingan fakultas dengan visualisasi interaktif dan KPI real-time</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div class="tujuan-text"><strong>Transportasi:</strong> Analisis mendalam emisi moda transportasi dengan breakdown per jenis kendaraan dan rute</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <div class="tujuan-text"><strong>Elektronik:</strong> Pelacakan konsumsi energi perangkat elektronik dengan tracking usage patterns</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    <div class="tujuan-text"><strong>Sampah:</strong> Tracking jejak karbon konsumsi makanan dan pengelolaan waste management</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tujuan-box">
            <div class="section-title">Fitur</div>
            <div class="tujuan-list">
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <div class="tujuan-text"><strong>Visualisasi Interaktif:</strong> Charts dinamis dengan drill-down capabilities dan filter multi-dimensi</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                    </svg>
                    <div class="tujuan-text"><strong>Filter Advanced:</strong> Segmentasi fakultas, periode waktu, dan kategori emisi dengan kombinasi kompleks</div>
                </div>
                <div class="tujuan-item">
                    <svg class="tujuan-icon" fill="none" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div class="tujuan-text"><strong>Export Multi-Format:</strong> CSV, PNG, PDF professional dengan customizable templates dan branding</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    show()