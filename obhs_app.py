import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. VISUAL SETUP (TOPIC FOCUSED)
# ==========================================
st.set_page_config(page_title="CA TOPIC STREAM V36", layout="wide", page_icon="📢")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #0E1117; color: #E6E6E6; font-family: 'Consolas', monospace; }
    
    /* JUDUL KATEGORI */
    .topic-header {
        border-bottom: 2px solid #00FF41;
        padding-bottom: 5px;
        margin-top: 30px;
        margin-bottom: 10px;
        font-size: 20px;
        font-weight: bold;
        color: #00FF41;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* LIST BERITA SIMPEL */
    .news-item {
        padding: 8px 0;
        border-bottom: 1px solid #30363D;
        display: flex;
        align-items: flex-start;
    }
    .news-item:hover { background-color: #161B22; }
    
    .date-badge {
        background-color: #21262D;
        color: #8B949E;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        min-width: 80px;
        text-align: center;
        margin-right: 12px;
        margin-top: 2px;
    }
    
    .news-content { flex-grow: 1; }
    
    .news-link {
        color: #58A6FF;
        text-decoration: none;
        font-size: 15px;
        font-weight: 500;
        display: block;
        margin-bottom: 3px;
    }
    .news-link:hover { color: #79C0FF; text-decoration: underline; }
    
    .source-tag {
        font-size: 10px;
        color: #888;
        border: 1px solid #30363D;
        padding: 1px 5px;
        border-radius: 3px;
        margin-right: 5px;
    }
    
    /* Highlight Uang */
    .money { color: #D2A8FF; font-weight: bold; }
    
    /* Stats Kecil */
    .stats { font-size: 11px; color: #555; margin-bottom: 20px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC: TOPIC HUNTER (LOOSE FILTER)
# ==========================================

# Hanya buang sampah mutlak (Film/Tutorial). Sisanya MASUK.
NOISE = ["sinopsis", "film", "zodiak", "cara", "tips", "resep", "trik", "panduan", "jadwal bioskop"]

def format_text(text):
    # Highlight Angka Uang (Triliun/Miliar) dengan warna Ungu Terang
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money'>\1</span>", text, flags=re.IGNORECASE)
    return text

def hunt_topic(keywords):
    # SITE: 4 Website Keuangan Utama
    SITES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"
    # Query: (SITES) AND (TOPIC) when:14d
    full_query = f"({SITES}) AND ({keywords}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={full_query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=12)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        valid_news = []
        seen_titles = []
        
        # TIME FILTER (14 HARI STRICT)
        cutoff = datetime.utcnow() - timedelta(days=14)
        
        for item in items:
            title = item.title.text
            
            # 1. PARSING TANGGAL
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue
                
            # 2. BUANG BERITA LAMA (Time Travel Blocker)
            if dt < cutoff: continue
            
            # 3. BUANG SAMPAH MUTLAK (Anti-Sinopsis)
            is_noise = False
            for n in NOISE:
                if n in title.lower(): 
                    is_noise = True
                    break
            if is_noise: continue
            
            # 4. DEDUPLIKASI (Biar gak dobel-dobel)
            is_dup = False
            for s in seen_titles:
                if difflib.SequenceMatcher(None, title, s).ratio() > 0.7:
                    is_dup = True
                    break
            if is_dup: continue
            
            seen_titles.append(title)
            
            # BERSIHKAN SOURCE
            src = item.source.text if item.source else "Media"
            src = src.replace(".id","").replace(".com","").upper()
            
            valid_news.append({
                "title": title,
                "link": item.link.text,
                "dt": dt,
                "src": src
            })
            
        # URUTKAN DR TERBARU
        return sorted(valid_news, key=lambda x: x['dt'], reverse=True)
    except:
        return []

# ==========================================
# 3. MAIN DASHBOARD
# ==========================================
st.title("📢 MARKET TOPIC STREAM")
wib = datetime.utcnow() + timedelta(hours=7)
start_date = wib - timedelta(days=14)
st.caption(f"LIVE FEED (14 HARI TERAKHIR) | {start_date.strftime('%d %b')} - {wib.strftime('%d %b %Y')} | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔄 REFRESH FEED"):
    st.cache_data.clear()
    st.rerun()

# --- DEFINISI TOPIK (SEMUANYA TANPA TERKECUALI) ---
topics = {
    "🤝 MERGER & AKUISISI (M&A)": "akuisisi OR merger OR caplok OR ambil alih OR pengendali baru",
    "💰 RIGHTS ISSUE & MODAL": "rights issue OR hmetd OR private placement OR setoran modal OR tambah modal",
    "🚨 TENDER OFFER & GO PRIVATE": "tender offer OR go private OR delisting OR penawaran tender",
    "🗣️ MEMINTA PERSETUJUAN (RUPS/RESTU)": "rupslb OR rapat umum pemegang saham OR minta restu OR minta persetujuan OR agenda rups"
}

# TAMPILAN FULL 1 KOLOM (BIAR LEGA DAFTARNYA)
for label, query in topics.items():
    st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner(f"Mencari topik {label}..."):
        news_list = hunt_topic(query)
    
    if news_list:
        st.markdown(f"<div class='stats'>Total: {len(news_list)} berita ditemukan</div>", unsafe_allow_html=True)
        # LOOP SEMUA DATA (NO LIMIT)
        for news in news_list:
            local_time = news['dt'] + timedelta(hours=7)
            date_str = local_time.strftime("%d %b %H:%M")
            fmt_title = format_text(news['title'])
            
            st.markdown(f"""
            <div class='news-item'>
                <div class='date-badge'>{date_str}</div>
                <div class='news-content'>
                    <a href='{news['link']}' target='_blank' class='news-link'>{fmt_title}</a>
                    <span class='source-tag'>{news['src']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada berita ditemukan untuk topik ini dalam 14 hari terakhir.")

st.markdown("<br><br>", unsafe_allow_html=True)
