import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. VISUAL BLACK THEME (SAMA SEPERTI TADI)
# ==========================================
st.set_page_config(page_title="CA SNIPER V34 (CLEAN)", layout="wide", page_icon="☠️")

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
    
    .news-date { color: #666; font-size: 12px; min-width: 60px; font-weight:bold; }
    .news-link { color: #FFF !important; text-decoration: none; font-size: 14px; margin-left: 10px; flex-grow: 1; }
    .news-link:hover { color: #FFFF00 !important; }
    
    .money-tag { color: #FFD700; font-weight: bold; }
    .stock-tag { color: #00FFFF; font-weight: bold; }
    .trash-count { color: #444; font-size: 10px; font-style: italic; margin-left: 10px; }
    .src-badge { font-size: 9px; border: 1px solid #444; padding: 1px 4px; border-radius: 3px; color: #888; margin-left: 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC FILTER "ANTI-TAI" (V34.0)
# ==========================================

# DAFTAR KATA HARAM (JIKA ADA INI = LANGSUNG BUANG)
SAMPAH_KEYWORDS = [
    # Kategori Bisnis Ecek-ecek (YANG BOS BENCI)
    "peluang usaha", "ide bisnis", "modal kecil", "modal dengkul", "modal nikah", 
    "usaha rumahan", "jualan", "bisnis kuliner", "franchise", "waralaba", "umkm", 
    "pedagang", "kaki lima", "lapak", "toko kelontong",
    
    # Kategori Keuangan Personal (Bukan Korporasi)
    "kur bri", "pinjol", "pinjaman online", "gaji", "tunjangan", "pns", "asn", 
    "lowongan", "loker", "karir", "rekrutmen", "phk", "pesangon", "thr",
    "cara transfer", "biaya admin", "saldo", "rekening", "kartu kredit",
    
    # Kategori Clickbait Umum
    "tips", "cara", "rahasia", "trik", "panduan", "daftar", "syarat", 
    "sinopsis", "zodiak", "film", "drama", "viral", "heboh", "cek fakta"
]

def clean_filter(title):
    t_low = title.lower()
    
    # 1. CEK KATA SAMPAH (Strict Blacklist)
    for sampah in SAMPAH_KEYWORDS:
        if sampah in t_low:
            return False # Ada kata sampah -> TENDANG
            
    # 2. CEK KONTEKS "MODAL" (Biar gak salah baca lagi)
    # Kalau ada kata "Modal", pastikan bukan "Modal Kecil" atau "Modal Usaha" (tanpa konteks emiten)
    if "modal" in t_low:
        if "modal kecil" in t_low or "modal usaha" in t_low or "tanpa modal" in t_low:
            return False
            
    # 3. CEK IDENTITAS (Harus Berbau Pasar Modal)
    # Minimal ada: Tbk, Emiten, Saham, Kode Saham (ABCD), RUPS, Dividen, Triliun, Miliar
    keywords_wajib = [
        "saham", "tbk", "emiten", "perseroan", "bursa", "bei", "ihsg", "investor",
        "dividen", "rups", "ipo", "triliun", "miliar", "akuisisi", "merger",
        "tender offer", "rights issue", "private placement", "hmetd", "waran"
    ]
    
    # Cek Regex Kode Saham (Misal: BBCA, GOTO)
    has_stock_code = bool(re.search(r'\b[A-Z]{4}\b', title))
    
    has_context = False
    for k in keywords_wajib:
        if k in t_low:
            has_context = True
            break
            
    if has_stock_code: has_context = True
    
    return has_context

def formatting(text):
    # Highlight Uang (Kuning)
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money-tag'>\1</span>", text, flags=re.IGNORECASE)
    # Highlight Kode Saham (Cyan)
    text = re.sub(r"\b([A-Z]{4})\b", r"<span class='stock-tag'>\1</span>", text)
    return text

# ==========================================
# 3. ENGINE PENCARI (DEEP DIVE 14 HARI)
# ==========================================
def hunt(query_list):
    SITES = "site:kontan.co.id OR site:cnbcindonesia.com OR site:idxchannel.com OR site:katadata.co.id"
    # Gabung semua query list jadi satu string panjang OR
    # Google batasi query length, jadi kita ambil query utamanya aja
    q_str = " OR ".join(query_list)
    full_q = f"({SITES}) AND ({q_str}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={full_q.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=12)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        valid_news = []
        seen = []
        trash_counter = 0
        
        for item in items:
            title = item.title.text
            
            # --- FILTER ---
            if not clean_filter(title):
                trash_counter += 1
                continue
                
            # Deduplikasi
            is_dup = False
            for s in seen:
                if difflib.SequenceMatcher(None, title, s).ratio() > 0.7:
                    is_dup = True
                    break
            if is_dup: continue
            seen.append(title)
            
            # Date
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                dt = datetime.utcnow()
                
            src = item.source.text if item.source else "Media"
            src = src.replace(".id","").replace(".com","").upper()
            
            valid_news.append({"title": title, "link": item.link.text, "dt": dt, "src": src})
            
        return sorted(valid_news, key=lambda x: x['dt'], reverse=True), trash_counter
    except:
        return [], 0

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.title("☠️ CA SNIPER V34 (ANTI-NOISE)")
wib = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SCOPE: 14 DAYS | FILTER: STRICT NO 'PELUANG USAHA' | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔥 SCAN ULANG (KILL TRASH)"):
    st.cache_data.clear()
    st.rerun()

# DEFINISI TARGET (QUERY DIPERKETAT)
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
            data, trash = hunt(targets[key])
        
        if data:
            st.markdown(f"<span class='trash-count'>Dibuang: {trash} berita sampah</span>", unsafe_allow_html=True)
            for news in data[:30]: # Max 30 biar ga kepanjangan
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
            st.info("Nihil. Bersih dari sampah.")

st.markdown("<br>", unsafe_allow_html=True)
