import streamlit as st

def show():
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

    # Fixed CSS for aligned layout
    st.markdown("""
    <style>
    /* Main container for equal height columns */
    .main-container {
        display: flex;
        gap: 1rem;
        align-items: stretch;
        min-height: 600px;
    }
    
    .column-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    /* Section styling with consistent heights */
    .clean-section {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.8));
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(5, 150, 105, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    
    .clean-section:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.12);
    }
    
    /* Title styling */
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #059669;
        margin-bottom: 1.5rem;
        text-align: center;
        position: relative;
        flex-shrink: 0;
    }
    
    .section-title::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 40px;
        height: 2px;
        background: linear-gradient(90deg, #059669, #10b981);
        border-radius: 1px;
    }
    
    /* Description section */
    .description {
        font-size: 0.95rem;
        color: #374151;
        line-height: 1.6;
        text-align: justify;
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.05), rgba(16, 185, 129, 0.03));
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid rgba(5, 150, 105, 0.1);
        flex: 1;
    }
    
    /* Grid layouts */
    .grid-content {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    
    .grid-2x2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        flex: 1;
    }
    
    .grid-2x3 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        flex: 1;
    }
    
    .grid-2x3-features {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        flex: 1;
    }
    
    /* Card styling */
    .card {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.08), rgba(16, 185, 129, 0.05));
        border: 1px solid rgba(5, 150, 105, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100px;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(5, 150, 105, 0.15);
        border-color: rgba(5, 150, 105, 0.4);
    }
    
    .card-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #059669;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.2;
    }
    
    .card-desc {
        font-size: 0.8rem;
        color: #6b7280;
        line-height: 1.4;
        font-weight: 400;
    }
    
    /* Page cards */
    .page-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.06), rgba(52, 211, 153, 0.04));
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100px;
        position: relative;
    }
    
    .page-card::before {
        content: '';
        position: absolute;
        top: 8px;
        right: 8px;
        width: 6px;
        height: 6px;
        background: #059669;
        border-radius: 50%;
        opacity: 0.6;
    }
    
    .page-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
        border-color: rgba(16, 185, 129, 0.4);
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(52, 211, 153, 0.08), rgba(110, 231, 183, 0.05));
        border: 1px solid rgba(52, 211, 153, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100px;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 211, 153, 0.15);
        border-color: rgba(52, 211, 153, 0.4);
    }
    
    /* Info section at bottom */
    .info-section {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.8));
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(5, 150, 105, 0.1);
        margin-top: 1rem;
    }
    
    .info-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    
    .info-card {
        background: linear-gradient(135deg, rgba(110, 231, 183, 0.08), rgba(167, 243, 208, 0.05));
        border: 1px solid rgba(110, 231, 183, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .info-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(110, 231, 183, 0.15);
        border-color: rgba(110, 231, 183, 0.4);
    }
    
    .info-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #059669;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .info-desc {
        font-size: 0.75rem;
        color: #6b7280;
        line-height: 1.3;
    }
    
    /* Separator */
    .separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, #059669, #10b981, #059669, transparent);
        margin: 1rem 0;
        opacity: 0.4;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-container {
            flex-direction: column;
        }
        
        .grid-2x2, .grid-2x3, .grid-2x3-features, .info-grid {
            grid-template-columns: 1fr;
        }
        
        .clean-section {
            padding: 1.2rem;
        }
        
        .section-title {
            font-size: 1.2rem;
        }
        
        .description {
            padding: 1.2rem;
            font-size: 0.9rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Separator
    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)
    
    # Main layout with equal height columns
    st.markdown("""
    <div class="main-container">
        <!-- Column 1: Deskripsi & Tujuan -->
        <div class="column-container">
            <div class="clean-section">
                <div class="section-title">Deskripsi</div>
                <div class="description">
                    Platform monitoring dan analisis jejak karbon komprehensif dari aktivitas mahasiswa Institut Teknologi Bandung dengan visualisasi data real-time untuk mendukung inisiatif kampus berkelanjutan dan pengambilan keputusan berbasis data.
                </div>
            </div>
            
            <div class="clean-section">
                <div class="section-title">Tujuan</div>
                <div class="grid-content">
                    <div class="grid-2x2">
                        <div class="card">
                            <div class="card-title">Monitoring Berkala</div>
                            <div class="card-desc">Memantau dan melacak emisi karbon dari berbagai aktivitas kampus secara terjadwal dan berkelanjutan</div>
                        </div>
                        <div class="card">
                            <div class="card-title">Analisis Mendalam</div>
                            <div class="card-desc">Menyediakan insight mendalam dan actionable untuk pengambilan keputusan berkelanjutan</div>
                        </div>
                        <div class="card">
                            <div class="card-title">Kesadaran Lingkungan</div>
                            <div class="card-desc">Meningkatkan awareness komunitas kampus tentang jejak karbon dan dampak lingkungan</div>
                        </div>
                        <div class="card">
                            <div class="card-title">Kampus Berkelanjutan</div>
                            <div class="card-desc">Mendukung target ITB menjadi institusi pendidikan ramah lingkungan dan net-zero carbon</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Column 2: Halaman -->
        <div class="column-container">
            <div class="clean-section">
                <div class="section-title">Halaman</div>
                <div class="grid-content">
                    <div class="grid-2x3">
                        <div class="page-card">
                            <div class="card-title">Overview</div>
                            <div class="card-desc">Ringkasan komprehensif emisi kampus, perbandingan fakultas, dan trend emisi harian</div>
                        </div>
                        <div class="page-card">
                            <div class="card-title">Transportasi</div>
                            <div class="card-desc">Analisis detail emisi dari moda transportasi, jarak tempuh, dan pola perjalanan</div>
                        </div>
                        <div class="page-card">
                            <div class="card-title">Elektronik</div>
                            <div class="card-desc">Monitoring konsumsi energi perangkat elektronik dan dampak emisi karbonnya</div>
                        </div>
                        <div class="page-card">
                            <div class="card-title">Sampah Makanan</div>
                            <div class="card-desc">Jejak karbon dari pola konsumsi makanan, waste management, dan frekuensi konsumsi</div>
                        </div>
                        <div class="page-card">
                            <div class="card-title">Perbandingan</div>
                            <div class="card-desc">Perbandingan kinerja emisi antar fakultas dengan ranking dan analisis kompetitif</div>
                        </div>
                        <div class="page-card">
                            <div class="card-title">Tentang Dashboard</div>
                            <div class="card-desc">Informasi lengkap tentang dashboard, tujuan project, dan penjelasan fitur</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Column 3: Fitur -->
        <div class="column-container">
            <div class="clean-section">
                <div class="section-title">Fitur</div>
                <div class="grid-content">
                    <div class="grid-2x3-features">
                        <div class="feature-card">
                            <div class="card-title">Visualisasi Interaktif</div>
                            <div class="card-desc">Charts dan grafik dinamis dengan kemampuan drill-down untuk analisis mendalam</div>
                        </div>
                        <div class="feature-card">
                            <div class="card-title">Multi-Filter System</div>
                            <div class="card-desc">Filter data berdasarkan waktu, fakultas, dan kategori emisi untuk analisis spesifik</div>
                        </div>
                        <div class="feature-card">
                            <div class="card-title">Export & Reporting</div>
                            <div class="card-desc">Ekspor data dalam format CSV dan generate laporan PDF komprehensif</div>
                        </div>
                        <div class="feature-card">
                            <div class="card-title">Data Real-Time</div>
                            <div class="card-desc">Data diperbarui secara berkala dengan sinkronisasi otomatis dari sumber data</div>
                        </div>
                        <div class="feature-card">
                            <div class="card-title">Responsive Design</div>
                            <div class="card-desc">Interface yang mobile-friendly dan dapat diakses dari berbagai perangkat</div>
                        </div>
                        <div class="feature-card">
                            <div class="card-title">High Performance</div>
                            <div class="card-desc">Loading cepat dengan sistem caching dan optimasi database yang efisien</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bottom info section
    st.markdown("""
    <div class="info-section">
        <div class="section-title">Informasi Teknis</div>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-title">Data Source</div>
                <div class="info-desc">Google Sheets integration dengan update otomatis</div>
            </div>
            <div class="info-card">
                <div class="info-title">Tech Stack</div>
                <div class="info-desc">Streamlit, Plotly, Pandas untuk visualisasi data</div>
            </div>
            <div class="info-card">
                <div class="info-title">Update Frequency</div>
                <div class="info-desc">Data refresh setiap 1 jam untuk akurasi terkini</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show()