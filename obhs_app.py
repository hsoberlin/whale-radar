import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import difflib
import re

# ==========================================
# 1. KONFIGURASI VISUAL (TEMA GAMBAR BOS)
# ==========================================
st.set_page_config(page_title="CA TERMINAL ULTIMATE", layout="wide", page_icon="📊")

st.markdown("""
<style>
    /* HIDE STREAMLIT UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* GLOBAL THEME: BLACK & SHARP */
    .stApp { 
        background-color: #000000; 
        color: #E0E0E0; 
        font-family: 'Consolas', 'Courier New', monospace; 
    }
    
    /* HEADER KATEGORI (Hijau Neon ala Terminal) */
    .cat-header {
        border-bottom: 2px solid #00FF41;
        padding-bottom: 5px;
        margin-top: 30px;
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: 900;
        color: #00FF41;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* LIST ITEM (Mirip Screenshot) */
    .news-row {
        padding: 6px 0;
        border-bottom: 1px solid #222;
        display: flex;
        align-items: flex-start;
        font-size: 14px;
        line-height: 1.4;
    }
    .news-row:hover { background-color: #0A0A0A; }
    
    /* NOMOR URUT / TANGGAL (Warna Hijau) */
    .news-prefix {
        color: #00FF41;
        font-weight: bold;
        min-width: 85px;
        margin-right: 10px;
        font-size: 13px;
    }
    
    /* JUDUL BERITA (Putih) */
    .news-link {
        color: #FFFFFF !important;
        text-decoration: none;
        font-weight: 500;
        flex-grow: 1;
    }
    .news-link:hover { color: #80FF80 !important; }
    
    /* HIGHLIGHT UANG (Kuning Emas) */
    .money-tag {
        color: #FFD700;
        font-weight: bold;
    }
    
    /* BADGE SUMBER */
    .src-badge {
        font-size: 9px;
        padding: 1px 4px;
        border: 1px solid #444;
        border-radius: 3px;
        color: #888;
        margin-left: 8px;
        white-space: nowrap;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC: 14 HARI + FORMATTER "RP/TRILIUN"
# ==========================================

# Pola Regex untuk mewarnai Uang/Angka Penting jadi Kuning
def highlight_money(text):
    # Cari kata: Rp, Triliun, Miliar, Juta, Angka%, US$
    pattern = r"(Rp\s?[\d\.,]+|[\d\.,]+\s?Triliun|[\d\.,]+\s?Miliar|[\d\.,]+\s?Juta|US\$\s?[\d\.,]+|[\d\.,]+%)"
    # Ganti dengan span berwarna kuning
    highlighted = re.sub(pattern, r"<span class='money-tag'>\1</span>", text, flags=re.IGNORECASE)
    return highlighted

# Filter Kata Sampah (Biar bersih dari sinopsis film)
BLACKLIST = ["sinopsis", "film", "drama", "zodiak", "cara", "tips", "resep", "review", "game", "shio"]
# Filter Wajib (Harus ada bau pasar modal)
WHITELIST = ["saham", "emiten", "tbk", "bursa", "investor", "dividen", "ipo", "rups", "modal", "triliun", "miliar", "rp", "akuisisi", "tender"]

def is_valid_news(title):
    t = title.lower()
    # 1. Cek Haram
    for bad in BLACKLIST:
        if bad in t: return False
    # 2. Cek Wajib
    for good in WHITELIST:
        if good in t: return True
    return False

def hunt_data(keywords):
    # Query: 14 Hari (Deep Dive) + 4 Sumber Terpercaya
    SITES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"
    query = f"({SITES}) AND ({keywords}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=12)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        results = []
        seen = []
        
        for item in items:
            title = item.title.text
            
            # Filter Deduplikasi & Validasi
            if not is_valid_news(title): continue
            
            # Cek Kemiripan Judul > 70% (Buang Double)
            is_dup = False
            for s in seen:
                if difflib.SequenceMatcher(None, title, s).ratio() > 0.7:
                    is_dup = True
                    break
            if is_dup: continue
            seen.append(title)
            
            # Parsing Waktu
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                dt = datetime.utcnow()
                
            # Bersihkan Nama Source
            src = item.source.text if item.source else "Media"
            src = src.replace(".id", "").replace(".com", "").upper()
            
            results.append({
                "raw_title": title,
                "link": item.link.text,
                "dt": dt,
                "source": src
            })
            
        # Sortir: Terbaru Paling Atas
        return sorted(results, key=lambda x: x['dt'], reverse=True)
    except:
        return []

# ==========================================
# 3. DASHBOARD EXECUTION
# ==========================================
st.title("📊 CORPORATE ACTION TRACKER v32")
wib = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SCOPE: 14 HARI TERAKHIR | SUMBER: CNBC, KONTAN, IDX, KATADATA | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔄 REFRESH DATA (TEBAR JARING)"):
    st.cache_data.clear()
    st.rerun()

# KATEGORI LENGKAP
targets = {
    "1. 💰 RIGHTS ISSUE & PRIVATE PLACEMENT": "rights issue OR private placement OR hmetd OR tambah modal",
    "2. 🔥 AKUISISI, MERGER & PENGENDALI": "akuisisi saham OR merger emiten OR pengendali baru OR caplok saham",
    "3. 🚨 TENDER OFFER & GO PRIVATE": "tender offer OR go private OR delisting",
    "4. 💸 DIVIDEN, RUPS & SUSPENSI": "dividen tunai OR hasil rupslb OR suspensi saham OR jadwal cum date",
    "5. 🏗️ EKSPANSI & BELANJA MODAL": "belanja modal capex OR ekspansi pabrik OR proyek baru emiten"
}

# RENDER LOOP
for label, query in targets.items():
    st.markdown(f"<div class='cat-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner("Scanning..."):
        data = hunt_data(query)
    
    if data:
        # Loop semua data (Unlimited)
        for i, news in enumerate(data):
            # Format Tanggal (11/01)
            loc_time = news['dt'] + timedelta(hours=7)
            date_str = loc_time.strftime("%d/%m")
            
            # Format Judul (Highlight Uang)
            formatted_title = highlight_money(news['raw_title'])
            
            st.markdown(f"""
            <div class='news-row'>
                <div class='news-prefix'>{date_str}</div>
                <a href='{news['link']}' target='_blank' class='news-link'>
                    {formatted_title}
                    <span class='src-badge'>{news['source']}</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#555; font-size:12px; font-style:italic;'>Tidak ada data valid 14 hari terakhir.</div>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
