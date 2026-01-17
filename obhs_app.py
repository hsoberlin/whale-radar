import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import difflib # Untuk mendeteksi judul berita yang mirip (Deduplikasi)

# ==========================================
# 1. CONFIG & TAMPILAN (TERMINAL MODE)
# ==========================================
st.set_page_config(page_title="CA INTEL v28.0", layout="wide", page_icon="📡")

# CSS: Tampilan Terminal Bloomberg/Reuters Style
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #000000; color: #E0E0E0; font-family: 'Consolas', 'Courier New', monospace; }
    
    /* Header Kategori */
    .cat-header {
        border-bottom: 2px solid #00FF41;
        color: #00FF41;
        font-size: 20px;
        font-weight: bold;
        margin-top: 30px;
        padding-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Kartu Berita */
    .news-card {
        background-color: #111;
        border: 1px solid #333;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #555;
        transition: all 0.2s;
    }
    .news-card:hover {
        background-color: #1A1A1A;
        border-left-color: #00FF41;
        transform: translateX(5px);
    }
    
    .news-title {
        color: #FFFFFF !important;
        text-decoration: none;
        font-weight: 600;
        font-size: 15px;
        display: block;
        margin-bottom: 6px;
    }
    
    .news-meta {
        font-size: 11px;
        color: #888;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .badge-source {
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 10px;
        color: #000;
    }
    /* Warna Badge per Media */
    .src-cnbc { background-color: #005599; color: white; }
    .src-kontan { background-color: #009900; color: white; }
    .src-idx { background-color: #CC0000; color: white; }
    .src-data { background-color: #FF9900; color: black; }
    .src-other { background-color: #555; color: white; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MESIN PENCARI & FILTER (THE BRAIN)
# ==========================================

# Hanya izinkan 4 website ini
TRUSTED_SITES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"

def clean_source_name(raw_source):
    raw = raw_source.lower()
    if "cnbc" in raw: return "CNBC INDONESIA", "src-cnbc"
    if "kontan" in raw: return "KONTAN", "src-kontan"
    if "idx" in raw: return "IDX CHANNEL", "src-idx"
    if "katadata" in raw: return "KATADATA", "src-data"
    return raw_source.upper(), "src-other"

def is_duplicate(new_title, existing_titles):
    # Cek kemiripan judul (threshold 0.6 artinya 60% mirip dianggap sama)
    # Ini supaya berita "BUMI Rights Issue" di CNBC dan "BUMI Gelar Rights Issue" di Kontan cuma muncul 1
    for title in existing_titles:
        similarity = difflib.SequenceMatcher(None, new_title.lower(), title.lower()).ratio()
        if similarity > 0.55: # Jika kemiripan di atas 55%, anggap duplikat
            return True
    return False

def hunt_intel(category_keyword):
    # Query gabungan: Website Terpercaya + Keyword Kategori
    query = f"({TRUSTED_SITES}) AND ({category_keyword}) when:7d"
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        results = []
        seen_titles = [] # Penampung untuk cek duplikat
        
        for item in items:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source_raw = item.source.text if item.source else "Media"
            
            # 1. Bersihkan Nama Source
            source_name, source_class = clean_source_name(source_raw)
            
            # 2. Cek Duplikasi (Jika sudah ada berita mirip, skip)
            if is_duplicate(title, seen_titles):
                continue
            
            # 3. Masukkan ke list "Seen"
            seen_titles.append(title)
            
            # 4. Parsing Tanggal
            try:
                dt_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                dt_obj = datetime.utcnow()
                
            results.append({
                "title": title,
                "link": link,
                "dt": dt_obj,
                "source": source_name,
                "class": source_class
            })
            
        # Urutkan berdasarkan waktu terbaru
        return sorted(results, key=lambda x: x['dt'], reverse=True)[:5] # Ambil 5 teratas per kategori
        
    except:
        return []

# ==========================================
# 3. DASHBOARD EXECUTION
# ==========================================
st.markdown("<h1 style='text-align:center; color:#00FF41;'>📡 CORPORATE ACTION INTELLIGENCE</h1>", unsafe_allow_html=True)
wib_now = datetime.utcnow() + timedelta(hours=7)
st.markdown(f"<p style='text-align:center; color:#666;'>TRUSTED SOURCES ONLY | UPDATE: {wib_now.strftime('%H:%M:%S')} WIB</p>", unsafe_allow_html=True)

if st.button("🔄 SCAN MARKET (REFRESH)"):
    st.cache_data.clear()
    st.rerun()

# --- DEFINISI KATEGORI ---
# Kita kelompokkan berita berdasarkan jenis aksi korporasinya
categories = {
    "🔥 AKUISISI & MERGER (M&A)": "akuisisi saham OR caplok saham OR merger emiten OR pengendali baru",
    "💰 RIGHTS ISSUE & PRIVATE PLACEMENT": "rights issue OR hmetd OR private placement OR tambah modal",
    "🚨 TENDER OFFER": "tender offer OR penawaran tender wajib",
    "🏭 EKSPANSI & BELANJA MODAL": "ekspansi pabrik OR belanja modal capex OR proyek baru emiten",
    "💸 DIVIDEN & RUPS": "pembagian dividen OR jadwal rupslb OR restu pemegang saham"
}

# --- RENDER KOLOM ---
# Kita pakai container biar rapi ke bawah
for label, keyword in categories.items():
    st.markdown(f"<div class='cat-header'>{label}</div>", unsafe_allow_html=True)
    
    # Ambil data
    news_data = hunt_intel(keyword)
    
    if news_data:
        # Gunakan kolom grid (3 kolom per baris) biar muat banyak
        cols = st.columns(3)
        for i, news in enumerate(news_data):
            with cols[i % 3]: # Loop kolom 0, 1, 2
                
                # Format Waktu
                local_time = news['dt'] + timedelta(hours=7)
                time_str = local_time.strftime("%d/%m %H:%M")
                
                st.markdown(f"""
                <div class="news-card">
                    <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                    <div class="news-meta">
                        <span class="badge-source {news['class']}">{news['source']}</span>
                        <span>{time_str} WIB</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada sinyal signifikan dari 4 media utama dalam 7 hari terakhir.")

st.markdown("---")
st.caption("System v28.0 | Filtered by: CNBC, Kontan, IDX Channel, Katadata")
