import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import difflib # Untuk membuang berita kembar

# ==========================================
# 1. VISUAL TERMINAL CONFIG
# ==========================================
st.set_page_config(page_title="CA TRAWLER v29.0", layout="wide", page_icon="⚓")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #0F1116; color: #C9D1D9; font-family: 'Consolas', 'Courier New', monospace; }
    
    /* Header Kategori */
    .cat-header {
        background-color: #161B22;
        border-left: 5px solid #238636;
        padding: 10px;
        margin-top: 30px;
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: bold;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Kartu Berita Compact */
    .news-row {
        border-bottom: 1px solid #30363D;
        padding: 8px 0;
        display: flex;
        align-items: center;
        transition: background 0.2s;
    }
    .news-row:hover { background-color: #1C2128; }
    
    .news-date {
        font-size: 11px;
        color: #8B949E;
        min-width: 90px;
        font-family: monospace;
    }
    
    .news-link {
        color: #58A6FF;
        text-decoration: none;
        font-weight: 500;
        font-size: 14px;
        flex-grow: 1;
        margin-left: 10px;
    }
    .news-link:hover { text-decoration: underline; color: #79C0FF; }
    
    .badge-src {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        color: #fff;
        font-weight: bold;
        min-width: 60px;
        text-align: center;
    }
    .bg-cnbc { background-color: #0044CC; }
    .bg-kontan { background-color: #007700; }
    .bg-idx { background-color: #CC0000; }
    .bg-kata { background-color: #E67300; }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MESIN PUKAT HARIMAU (TRAWLER ENGINE)
# ==========================================

SOURCES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"

def clean_source_style(source_text):
    s = source_text.lower()
    if "cnbc" in s: return "CNBC", "bg-cnbc"
    if "kontan" in s: return "KONTAN", "bg-kontan"
    if "idx" in s: return "IDX", "bg-idx"
    if "katadata" in s: return "DATA", "bg-kata"
    return "MEDIA", "bg-idx"

def fetch_deep_dive(keywords):
    # Parameter when:5d untuk 5 hari ke belakang
    query = f"({SOURCES}) AND ({keywords}) when:5d"
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=15) # Timeout diperlama karena data banyak
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        raw_news = []
        seen_titles = [] # Filter Duplikat
        
        for item in items:
            title = item.title.text
            
            # 1. Deduplikasi Cerdas (Buang berita kembar identik)
            # Menggunakan difflib untuk cek kemiripan judul > 60%
            is_dup = False
            for seen in seen_titles:
                if difflib.SequenceMatcher(None, title.lower(), seen.lower()).ratio() > 0.60:
                    is_dup = True
                    break
            if is_dup: continue
            
            seen_titles.append(title)
            
            # 2. Parsing Data
            pub_date = item.pubDate.text
            try:
                dt_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                dt_obj = datetime.utcnow()
                
            source_label, source_class = clean_source_style(item.source.text if item.source else "")
            
            raw_news.append({
                "title": title,
                "link": item.link.text,
                "dt": dt_obj,
                "src_label": source_label,
                "src_class": source_class
            })
            
        # 3. Urutkan Waktu (Terbaru diatas)
        sorted_news = sorted(raw_news, key=lambda x: x['dt'], reverse=True)
        
        return sorted_news # KITA KEMBALIKAN SEMUA (TANPA LIMIT [:5])
        
    except Exception as e:
        return []

# ==========================================
# 3. DASHBOARD UI
# ==========================================
st.title("⚓ CA TRAWLER v29.0 (DEEP DIVE)")
wib_now = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SCOPE: 5 DAYS BACK | SOURCES: CNBC, KONTAN, IDX, KATADATA | UPDATE: {wib_now.strftime('%H:%M')} WIB")

if st.button("🌊 TEBAR JARING (REFRESH DATA)"):
    st.cache_data.clear()
    st.rerun()

# KATEGORI LENGKAP
targets = {
    "🔥 MERGER, AKUISISI & PENGENDALI": "akuisisi saham OR merger perusahaan OR pengendali baru emiten",
    "💰 RIGHTS ISSUE & PRIVATE PLACEMENT": "rights issue OR hmetd OR private placement OR setoran modal",
    "🚨 TENDER OFFER & GO PRIVATE": "tender offer OR go private OR delisting",
    "🏗️ EKSPANSI, CAPEX & PROYEK": "belanja modal capex OR ekspansi pabrik OR proyek strategis emiten",
    "💸 DIVIDEN, RUPS & SUSPENSI": "pembagian dividen OR hasil rupslb OR suspensi saham"
}

# TAMPILAN FULL WIDTH (Biar muat banyak)
for label, query in targets.items():
    st.markdown(f"<div class='cat-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner(f"Sedang menyelam mencari data {label}..."):
        results = fetch_deep_dive(query)
    
    if results:
        # Tampilkan Counter
        st.markdown(f"<small style='color:#888; margin-left:10px;'>Ditemukan: {len(results)} berita</small>", unsafe_allow_html=True)
        
        # Tampilkan List (Looping semua hasil)
        for news in results:
            local_time = news['dt'] + timedelta(hours=7)
            date_display = local_time.strftime("%d/%m %H:%M")
            
            st.markdown(f"""
            <div class="news-row">
                <span class="news-date">{date_display}</span>
                <span class="badge-src {news['src_class']}">{news['src_label']}</span>
                <a href="{news['link']}" target="_blank" class="news-link">{news['title']}</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Zonk. Tidak ada berita relevan dalam 5 hari terakhir untuk kategori ini.")

st.markdown("<br><br><div style='text-align:center; color:#333;'>POWERED BY GOOGLE NEWS ENGINE</div>", unsafe_allow_html=True)
