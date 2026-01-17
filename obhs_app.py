import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. VISUAL TERMINAL (TETAP SAMA)
# ==========================================
st.set_page_config(page_title="CA SNIPER V35 (STRICT DATE)", layout="wide", page_icon="📆")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #000000; color: #CCCCCC; font-family: 'Consolas', monospace; }
    
    .cat-header {
        border-left: 5px solid #00FF41; padding-left: 10px; margin-top: 25px; margin-bottom: 10px;
        font-size: 16px; font-weight: bold; color: #00FF41; text-transform: uppercase;
    }
    
    .news-row { border-bottom: 1px solid #222; padding: 6px 0; display: flex; align-items: center; }
    .news-row:hover { background-color: #111; }
    
    .news-date { color: #FFF; font-size: 12px; min-width: 60px; font-weight:bold; }
    .news-link { color: #BBB !important; text-decoration: none; font-size: 14px; margin-left: 10px; flex-grow: 1; }
    .news-link:hover { color: #FFFF00 !important; }
    
    .money-tag { color: #FFD700; font-weight: bold; }
    .stock-tag { color: #00FFFF; font-weight: bold; }
    .info-stats { color: #444; font-size: 10px; font-style: italic; margin-left: 10px; }
    .src-badge { font-size: 9px; border: 1px solid #444; padding: 1px 4px; border-radius: 3px; color: #888; margin-left: 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC FILTER "ANTI-TAI" & "ANTI-BASI"
# ==========================================

# DAFTAR KATA SAMPAH (TETAP AKTIF)
SAMPAH_KEYWORDS = [
    "peluang usaha", "ide bisnis", "modal kecil", "modal dengkul", "modal nikah", 
    "usaha rumahan", "jualan", "bisnis kuliner", "franchise", "waralaba", "umkm", 
    "pedagang", "kaki lima", "lapak", "toko kelontong", "kur bri", "pinjol", 
    "gaji", "tunjangan", "pns", "asn", "lowongan", "loker", "karir", "phk", 
    "cara transfer", "biaya admin", "saldo", "rekening", "kartu kredit",
    "tips", "cara", "rahasia", "trik", "panduan", "syarat", 
    "sinopsis", "zodiak", "film", "drama", "viral", "heboh", "cek fakta"
]

def clean_filter(title):
    t_low = title.lower()
    for sampah in SAMPAH_KEYWORDS:
        if sampah in t_low: return False
    if "modal" in t_low:
        if "modal kecil" in t_low or "modal usaha" in t_low or "tanpa modal" in t_low: return False
    
    # Identitas Wajib
    keywords_wajib = [
        "saham", "tbk", "emiten", "perseroan", "bursa", "bei", "ihsg", "investor",
        "dividen", "rups", "ipo", "triliun", "miliar", "akuisisi", "merger",
        "tender offer", "rights issue", "private placement", "hmetd", "waran"
    ]
    has_stock_code = bool(re.search(r'\b[A-Z]{4}\b', title))
    has_context = False
    for k in keywords_wajib:
        if k in t_low:
            has_context = True
            break
    if has_stock_code: has_context = True
    return has_context

def formatting(text):
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money-tag'>\1</span>", text, flags=re.IGNORECASE)
    text = re.sub(r"\b([A-Z]{4})\b", r"<span class='stock-tag'>\1</span>", text)
    return text

# ==========================================
# 3. ENGINE PENCARI (HARD DATE FILTER)
# ==========================================
def hunt(query_list):
    SITES = "site:kontan.co.id OR site:cnbcindonesia.com OR site:idxchannel.com OR site:katadata.co.id"
    q_str = " OR ".join(query_list)
    # Tetap minta Google 14 hari, tapi nanti kita cek ulang
    full_q = f"({SITES}) AND ({q_str}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={full_q.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=12)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        valid_news = []
        seen = []
        stats_trash = 0
        stats_old = 0
        
        # --- HITUNG CUT-OFF DATE (14 Hari yang lalu dari HARI INI) ---
        now_utc = datetime.utcnow()
        cutoff_date = now_utc - timedelta(days=14)
        
        for item in items:
            title = item.title.text
            
            # 1. PARSING TANGGAL DULUAN
            try:
                # Format: Fri, 17 Jan 2026 10:00:00 GMT
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue # Kalau tanggal error, skip aja biar aman
            
            # 2. HARD FILTER TANGGAL (SATPAM WAKTU)
            # Jika tanggal berita LEBIH KECIL (TUA) dari cutoff -> BUANG
            if dt < cutoff_date:
                stats_old += 1
                continue
            
            # 3. FILTER SAMPAH (ANTI-TAI)
            if not clean_filter(title):
                stats_trash += 1
                continue
                
            # 4. DEDUPLIKASI
            is_dup = False
            for s in seen:
                if difflib.SequenceMatcher(None, title, s).ratio() > 0.7:
                    is_dup = True
                    break
            if is_dup: continue
            seen.append(title)
            
            src = item.source.text if item.source else "Media"
            src = src.replace(".id","").replace(".com","").upper()
            
            valid_news.append({"title": title, "link": item.link.text, "dt": dt, "src": src})
            
        return sorted(valid_news, key=lambda x: x['dt'], reverse=True), stats_trash, stats_old
    except:
        return [], 0, 0

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.title("📆 CA SNIPER V35 (STRICT 14 DAYS)")
wib = datetime.utcnow() + timedelta(hours=7)
# Tampilkan rentang tanggal valid
start_date = wib - timedelta(days=14)
st.caption(f"VALID DATE RANGE: {start_date.strftime('%d %b')} - {wib.strftime('%d %b %Y')} | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔥 SCAN & FILTER WAKTU"):
    st.cache_data.clear()
    st.rerun()

targets = {
    "🔥 MERGER & AKUISISI": [
        "akuisisi saham", "merger emiten", "caplok saham", "ambil alih saham", "pengendali baru"
    ],
    "💰 RIGHTS ISSUE & MODAL": [
        "rights issue", "private placement", "hmetd", "suntik modal", "penambahan modal", "belanja modal capex"
    ],
    "🚨 TENDER OFFER & GO PRIVATE": [
        "tender offer", "go private", "delisting", "penawaran tender"
    ],
    "💸 DIVIDEN & RUPS": [
        "dividen tunai", "hasil rupslb", "jadwal cum date"
    ]
}

col1, col2 = st.columns(2)
keys = list(targets.keys())

for i, key in enumerate(keys):
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"<div class='cat-header'>{key}</div>", unsafe_allow_html=True)
        
        with st.spinner("Filtering..."):
            data, trash, old = hunt(targets[key])
        
        if data:
            st.markdown(f"<span class='info-stats'>Sampah Dibuang: {trash} | <b>Berita Basi (>14 hari) Dibuang: {old}</b></span>", unsafe_allow_html=True)
            for news in data[:30]: 
                d_str = (news['dt'] + timedelta(hours=7)).strftime("%d/%m")
                fmt_title = formatting(news['title'])
                
                st.markdown(f"""
                <div class='news-row'>
                    <div class='news-date'>{d_str}</div>
                    <a href='{news['link']}' target='_blank' class='news-link'>
                        {fmt_title}
                        <span class='src-badge'>{news['src']}</span>
                    </a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"Nihil. (Sampah: {trash}, Basi: {old})")

st.markdown("<br>", unsafe_allow_html=True)
