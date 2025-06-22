import streamlit as st
import os
from loading import loading, loading_decorator
import time

def load_css(file_name):
    """Load CSS file"""
    css_file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def show():
    # Header dengan loading
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

    # CSS untuk styling cards - compact
    st.markdown("""
    <style>
    /* Override streamlit default spacing */
    .stColumns {
        gap: 0.6rem !important;
    }
    
    .about-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 0.8rem;
        box-shadow: 0 3px 12px rgba(5, 150, 105, 0.08);
        border: 1px solid rgba(34, 197, 94, 0.15);
        margin-bottom: 0.6rem;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .hero-card {
        background: linear-gradient(135deg, #059669, #16a34a);
        color: white;
        text-align: center;
        border: none;
        margin-bottom: 0.6rem;
    }
    
    .content-card {
        border-left: 4px solid #16a34a;
        margin-bottom: 0;
    }
    
    .pages-card {
        border-left: 4px solid #22c55e;
        margin-bottom: 0.6rem;
    }
    
    .features-card {
        border-left: 4px solid #34d399;
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,253,244,0.9));
        margin-bottom: 0;
    }
    
    .card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #059669;
        margin-bottom: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: 'Poppins', sans-serif;
        text-align: center;
    }
    
    .card-title-white {
        color: white !important;
    }
    
    .card-desc {
        font-size: 0.8rem;
        line-height: 1.4;
        color: rgba(255,255,255,0.95);
        text-align: justify;
        font-family: 'Poppins', sans-serif;
        margin-bottom: 0;
    }
    
    .card-desc-dark {
        color: #374151;
    }
    
    .item-box {
        background: var(--box-bg);
        border-radius: 6px;
        padding: 0.6rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid var(--box-border);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    
    .item-box:hover {
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
    }
    
    .item-box:last-child {
        margin-bottom: 0;
    }
    
    .item-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--item-title-color);
        margin-bottom: 0.3rem;
        font-family: 'Poppins', sans-serif;
    }
    
    .item-desc {
        font-size: 0.68rem;
        line-height: 1.3;
        color: var(--item-desc-color);
        font-family: 'Poppins', sans-serif;
        margin: 0;
    }
    
    .theme-goals {
        --box-bg: linear-gradient(135deg, #d1fae5, #a7f3d0);
        --box-border: #059669;
        --item-title-color: #059669;
        --item-desc-color: #065f46;
    }
    
    .theme-pages {
        --box-bg: linear-gradient(135deg, #bbf7d0, #86efac);
        --box-border: #16a34a;
        --item-title-color: #16a34a;
        --item-desc-color: #14532d;
    }
    
    .theme-features {
        --box-bg: linear-gradient(135deg, #a7f3d0, #6ee7b7);
        --box-border: #22c55e;
        --item-title-color: #22c55e;
        --item-desc-color: #064e3b;
    }
    </style>
    """, unsafe_allow_html=True)

    # Row 1: Layout sejajar dengan gap sama
    with loading():
        col_left, col_right = st.columns([1, 1], gap="medium")
        
        with col_left:
            # Deskripsi
            st.markdown("""
            <div class="about-card hero-card">
                <div class="card-title card-title-white">Deskripsi Project</div>
                <div class="card-desc">
                    Platform analisis jejak karbon komprehensif dari aktivitas mahasiswa Institut Teknologi Bandung dengan visualisasi data real-time untuk mendukung inisiatif kampus berkelanjutan dan mencapai target net-zero carbon.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Tujuan
            st.markdown("""
            <div class="about-card content-card">
                <div class="card-title">Tujuan Utama</div>
                <div class="item-box theme-goals">
                    <div class="item-title">Monitoring Berkelanjutan</div>
                    <div class="item-desc">Menganalisis emisi karbon aktivitas kampus secara terjadwal</div>
                </div>
                <div class="item-box theme-goals">
                    <div class="item-title">Data-Driven Insights</div>
                    <div class="item-desc">Menyediakan data actionable untuk keputusan berkelanjutan</div>
                </div>
                <div class="item-box theme-goals">
                    <div class="item-title">Green Campus Initiative</div>
                    <div class="item-desc">Mendukung transformasi ITB menjadi institusi net-zero carbon</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            # Halaman Dashboard
            st.markdown("""
            <div class="about-card pages-card">
                <div class="card-title">Struktur Dashboard</div>
                <div class="item-box theme-pages">
                    <div class="item-title">Dashboard Utama</div>
                    <div class="item-desc">Overview komprehensif emisi kampus dengan perbandingan fakultas</div>
                </div>
                <div class="item-box theme-pages">
                    <div class="item-title">Modul Transportasi</div>
                    <div class="item-desc">Analisis emisi dari berbagai moda transportasi dan mobilitas</div>
                </div>
                <div class="item-box theme-pages">
                    <div class="item-title">Modul Elektronik</div>
                    <div class="item-desc">Monitoring konsumsi energi perangkat dan infrastruktur kampus</div>
                </div>
                <div class="item-box theme-pages">
                    <div class="item-title">Modul Sampah Makanan</div>
                    <div class="item-desc">Tracking jejak karbon konsumsi makanan dan waste management</div>
                </div>
                <div class="item-box theme-pages">
                    <div class="item-title">Informasi Project</div>
                    <div class="item-desc">Dokumentasi lengkap tujuan, metodologi, dan panduan penggunaan</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(0.1)

    # Row 2: Fitur dengan gap sama
    with loading():
        st.markdown("""
        <div class="about-card features-card">
            <div class="card-title">Fitur & Kemampuan</div>
        </div>
        """, unsafe_allow_html=True)
        
        feature_col1, feature_col2, feature_col3, feature_col4 = st.columns(4, gap="medium")
        
        with feature_col1:
            st.markdown("""
            <div class="item-box theme-features">
                <div class="item-title">Interactive Visualization</div>
                <div class="item-desc">Charts dan grafik dinamis dengan drill-down capability untuk eksplorasi data</div>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_col2:
            st.markdown("""
            <div class="item-box theme-features">
                <div class="item-title">Advanced Filtering</div>
                <div class="item-desc">Multi-layer filter berdasarkan waktu, fakultas, kategori emisi, dan parameter custom</div>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_col3:
            st.markdown("""
            <div class="item-box theme-features">
                <div class="item-title">Export & Reporting</div>
                <div class="item-desc">Export raw data CSV dan auto-generate comprehensive PDF reports untuk stakeholders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_col4:
            st.markdown("""
            <div class="item-box theme-features">
                <div class="item-title">Real-time Sync</div>
                <div class="item-desc">Automatic data synchronization dengan update berkala dari integrated data sources</div>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(0.05)
    
if __name__ == "__main__":
    show()