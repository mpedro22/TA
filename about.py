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

    # CSS untuk layout yang lebih compact dan static
    st.markdown("""
    <style>
    .compact-section {
        background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(248,250,252,0.9));
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        margin-bottom: 0.8rem;
        border-left: 4px solid var(--border-color);
    }
    .compact-section-desc {
        background: linear-gradient(145deg, #059669, #16a34a);
        color: white;
        --border-color: #059669;
    }
    .compact-section-cards {
        --border-color: #16a34a;
    }
    .compact-section-fitur {
        --border-color: #22c55e;
    }
    .compact-title {
        font-size: 1rem;
        font-weight: 700;
        color: #059669;
        margin-bottom: 0.6rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: 'Poppins', sans-serif;
    }
    .compact-title-white {
        color: white !important;
    }
    .compact-desc {
        font-size: 0.85rem;
        line-height: 1.4;
        color: rgba(255,255,255,0.95);
        text-align: justify;
        font-family: 'Poppins', sans-serif;
    }
    .compact-card {
        background: var(--card-bg);
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 0.6rem;
        border-left: 3px solid var(--card-border);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    .compact-card-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--title-color);
        margin-bottom: 0.4rem;
        font-family: 'Poppins', sans-serif;
    }
    .compact-card-desc {
        font-size: 0.7rem;
        line-height: 1.3;
        color: var(--desc-color);
        font-family: 'Poppins', sans-serif;
    }
    .tujuan-theme {
        --card-bg: linear-gradient(135deg, #d1fae5, #a7f3d0);
        --card-border: #059669;
        --title-color: #059669;
        --desc-color: #065f46;
    }
    .halaman-theme {
        --card-bg: linear-gradient(135deg, #bbf7d0, #86efac);
        --card-border: #16a34a;
        --title-color: #16a34a;
        --desc-color: #14532d;
    }
    .fitur-theme {
        --card-bg: linear-gradient(135deg, #a7f3d0, #6ee7b7);
        --card-border: #22c55e;
        --title-color: #22c55e;
        --desc-color: #064e3b;
    }
    </style>
    """, unsafe_allow_html=True)

    # Row 1: Deskripsi + Halaman (2 kolom)
    with loading():
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            # Deskripsi
            st.markdown("""
            <div class="compact-section compact-section-desc">
                <div class="compact-title compact-title-white">Deskripsi</div>
                <div class="compact-desc">
                    Platform analisis jejak karbon komprehensif dari aktivitas mahasiswa Institut Teknologi Bandung dengan visualisasi data real-time untuk mendukung inisiatif kampus berkelanjutan.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Tujuan
            st.markdown("""
            <div class="compact-section compact-section-cards">
                <div class="compact-title">Tujuan</div>
                <div class="compact-card tujuan-theme">
                    <div class="compact-card-title">Analisis Berkala</div>
                    <div class="compact-card-desc">Menganalisis emisi karbon aktivitas kampus secara terjadwal dan berkelanjutan</div>
                </div>
                <div class="compact-card tujuan-theme">
                    <div class="compact-card-title">Insight Mendalam</div>
                    <div class="compact-card-desc">Data actionable untuk pengambilan keputusan berkelanjutan</div>
                </div>
                <div class="compact-card tujuan-theme">
                    <div class="compact-card-title">Kampus Berkelanjutan</div>
                    <div class="compact-card-desc">Mendukung target ITB menjadi institusi net-zero carbon</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            # Halaman
            st.markdown("""
            <div class="compact-section compact-section-cards">
                <div class="compact-title">Halaman</div>
                <div class="compact-card halaman-theme">
                    <div class="compact-card-title">Overview</div>
                    <div class="compact-card-desc">Ringkasan komprehensif emisi kampus, perbandingan fakultas, dan trend harian</div>
                </div>
                <div class="compact-card halaman-theme">
                    <div class="compact-card-title">Transportasi</div>
                    <div class="compact-card-desc">Analisis detail emisi dari moda transportasi dan jarak tempuh</div>
                </div>
                <div class="compact-card halaman-theme">
                    <div class="compact-card-title">Elektronik</div>
                    <div class="compact-card-desc">Konsumsi energi perangkat elektronik mahasiswa</div>
                </div>
                <div class="compact-card halaman-theme">
                    <div class="compact-card-title">Sampah Makanan</div>
                    <div class="compact-card-desc">Jejak karbon dari pola konsumsi dan waste management</div>
                </div>
                <div class="compact-card halaman-theme">
                    <div class="compact-card-title">Tentang Dashboard</div>
                    <div class="compact-card-desc">Informasi lengkap dashboard, tujuan project, dan fitur</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(0.1)

    # Row 2: Fitur (4 kolom)
    with loading():
        # Fitur section header
        st.markdown("""
        <div class="compact-section compact-section-fitur">
            <div class="compact-title">Fitur</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 4 kolom untuk fitur cards
        fitur_col1, fitur_col2, fitur_col3, fitur_col4 = st.columns([1, 1, 1, 1])
        
        with fitur_col1:
            st.markdown("""
            <div class="compact-card fitur-theme">
                <div class="compact-card-title">Visualisasi Interaktif</div>
                <div class="compact-card-desc">Charts dan grafik dinamis dengan kemampuan drill-down</div>
            </div>
            """, unsafe_allow_html=True)
        
        with fitur_col2:
            st.markdown("""
            <div class="compact-card fitur-theme">
                <div class="compact-card-title">Multi-Filter System</div>
                <div class="compact-card-desc">Filter data berdasarkan waktu, fakultas, dan kategori emisi</div>
            </div>
            """, unsafe_allow_html=True)
        
        with fitur_col3:
            st.markdown("""
            <div class="compact-card fitur-theme">
                <div class="compact-card-title">Export & Reporting</div>
                <div class="compact-card-desc">Ekspor data CSV dan generate laporan PDF komprehensif</div>
            </div>
            """, unsafe_allow_html=True)
        
        with fitur_col4:
            st.markdown("""
            <div class="compact-card fitur-theme">
                <div class="compact-card-title">Update Berkala</div>
                <div class="compact-card-desc">Data diperbarui berkala dengan sinkronisasi otomatis</div>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(0.05)
    
if __name__ == "__main__":
    show()