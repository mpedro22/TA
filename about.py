import streamlit as st
import os

def load_css(file_name):
    """Load CSS file"""
    css_file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def show():


    # Header - Keep original
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

    # Main Content menggunakan green grid layout
    st.markdown("""
    <div class="about-container-green">
        <div class="about-card-green">
            <!-- Deskripsi -->
            <div class="about-section-green about-section-desc-green">
                <div class="about-title-green about-title-white-green">Deskripsi</div>
                <div class="about-desc-green">
                    Platform monitoring dan analisis jejak karbon komprehensif dari aktivitas mahasiswa Institut Teknologi Bandung dengan visualisasi data real-time untuk mendukung inisiatif kampus berkelanjutan.
                </div>
            </div>
            
            <!-- Tujuan -->
            <div class="about-section-green about-section-cards-green">
                <div class="about-title-green">Tujuan</div>
                <div class="about-cards-green">
                    <div class="about-card-green tujuan-card-green">
                        <div class="about-card-title-green">Monitoring Berkala</div>
                        <div class="about-card-desc-green">Memantau emisi karbon aktivitas kampus secara terjadwal dan berkelanjutan</div>
                    </div>
                    <div class="about-card-green tujuan-card-green">
                        <div class="about-card-title-green">Analisis Mendalam</div>
                        <div class="about-card-desc-green">Insight actionable untuk pengambilan keputusan berkelanjutan</div>
                    </div>
                    <div class="about-card-green tujuan-card-green">
                        <div class="about-card-title-green">Kampus Berkelanjutan</div>
                        <div class="about-card-desc-green">Mendukung target ITB menjadi institusi net-zero carbon</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="about-card-green">
            <!-- Halaman -->
            <div class="about-section-green about-section-cards-green">
                <div class="about-title-green">Halaman</div>
                <div class="about-cards-green">
                    <div class="about-card-green halaman-card-green">
                        <div class="about-card-title-green">Overview</div>
                        <div class="about-card-desc-green">Ringkasan komprehensif emisi kampus, perbandingan fakultas, dan trend harian</div>
                    </div>
                    <div class="about-card-green halaman-card-green">
                        <div class="about-card-title-green">Transportasi</div>
                        <div class="about-card-desc-green">Analisis detail emisi dari moda transportasi dan jarak tempuh</div>
                    </div>
                    <div class="about-card-green halaman-card-green">
                        <div class="about-card-title-green">Elektronik</div>
                        <div class="about-card-desc-green">Monitoring konsumsi energi perangkat elektronik</div>
                    </div>
                    <div class="about-card-green halaman-card-green">
                        <div class="about-card-title-green">Sampah Makanan</div>
                        <div class="about-card-desc-green">Jejak karbon dari pola konsumsi dan waste management</div>
                    </div>
                    <div class="about-card-green halaman-card-green">
                        <div class="about-card-title-green">Tentang Dashboard</div>
                        <div class="about-card-desc-green">Informasi lengkap dashboard, tujuan project, dan fitur</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="about-card-green">
            <!-- Fitur -->
            <div class="about-section-green about-cards-green">
                <div class="about-title-green">Fitur</div>
                <div class="about-cards-green">
                    <div class="about-card-green fitur-card-green">
                        <div class="about-card-title-green">Visualisasi Interaktif</div>
                        <div class="about-card-desc-green">Charts dan grafik dinamis dengan kemampuan drill-down mendalam</div>
                    </div>
                    <div class="about-card-green fitur-card-green">
                        <div class="about-card-title-green">Multi-Filter System</div>
                        <div class="about-card-desc-green">Filter data berdasarkan waktu, fakultas, dan kategori emisi</div>
                    </div>
                    <div class="about-card-green fitur-card-green">
                        <div class="about-card-title-green">Export & Reporting</div>
                        <div class="about-card-desc-green">Ekspor data CSV dan generate laporan PDF komprehensif</div>
                    </div>
                    <div class="about-card-green fitur-card-green">
                        <div class="about-card-title-green">Update Berkala</div>
                        <div class="about-card-desc-green">Data diperbarui berkala dengan sinkronisasi otomatis</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
if __name__ == "__main__":
    show()