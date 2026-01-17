import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. KONFIGURASI TAMPILAN (BLACK TERMINAL)
# ==========================================
st.set_page_config(page_title="CA SNIPER V33", layout="wide", page_icon="💀")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #000000; color: #CCCCCC; font-family: 'Consolas', monospace; }
    
    /* JUDUL KATEGORI */
    .cat-header {
        border-left: 5px solid #FF0000;
        padding-left: 10px;
        margin-top: 25px;
        margin-bottom: 10px;
        font-size: 16px;
        font-weight: bold;
        color: #FF0000; /* Merah biar galak */
        text-transform: uppercase;
    }
    
    /* BARIS BERITA */
    .news-row {
        border-bottom: 1px solid #222;
        padding: 8px 0;
        display: flex;
        align-items: center;
    }
    .news-row:hover { background-color: #0F0F0F; }
    
    .news-date { color: #555; font-size: 11px; min-width: 50px; }
    
    .news-link {
        color: #EEE !important; text-decoration: none; font-size: 14px; font-weight: 500; margin-left: 10px; flex-grow: 1;
    }
    .news-link:hover { color: #00FF41 !important; }
    
    /* Highlight Uang & Kode Saham */
    .money-tag { color: #FFD700; font-weight: bold; } /* Emas */
    .stock-tag { color: #00FFFF; font-weight: bold; } /* Cyan */
    
    .badge-src { font-size: 9px; color: #666; border: 1px solid #333; padding: 2px 4px; border-radius: 3px; margin-left: 8px; }
    
    .reject-msg { font-size: 10px; color: #333; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FILTER "SATPAM GALAK" (RUTHLESS LOGIC)
# ==========================================

# 1. LIST SAMPAH (Kalau ada ini, LANGSUNG BUANG)
NOISE_KEYWORDS = [
    "china", "amerika", "as", "inggris", "global", "dunia", "asing", # Luar Negeri
    "cara", "tips", "trik", "panduan", "syarat", "dokumen", "tutorial", # Tutorial
    "buka rekening", "lupa pin", "blokir", "call center", "promo", # Customer Service
    "ihsg", "rupiah", "kurs", "emas", "bitcoin", "crypto", "forex", # Makro/Komoditas
    "rekomendasi", "prediksi", "analisis", "potensi", "target harga", # Opini Analis
    "review", "sinopsis", "film", "drama", "zodiak", "ramalan", "viral" # Hiburan
]

# 2. LIST WAJIB (Harus ada identitas perusahaan)
IDENTITY_KEYWORDS = [
    "tbk", "emiten", "perseroan", "pt ", "group", "korporasi",
    "(", ")" # Biasanya kode saham ada di dalam kurung misal (BBCA)
]

# 3. LIST AKSI (Harus ada kata kerjanya)
ACTION_KEYWORDS = [
    "akuisisi", "merger", "caplok", "beli saham", "ambil alih", "divestasi", # M&A
    "rights issue", "private placement", "hmetd", "suntik modal", "tambah modal", # Modal
    "tender offer", "go private", "delisting", "pengendali baru", # Tender
    "dividen", "rups", "suspensi", "capex", "ekspansi" # Lainnya
]

def ruthles_filter(title):
    t_low = title.lower()
    
    # RULE 1: Cek Noise (Langsung Kill)
    for noise in NOISE_KEYWORDS:
        if f" {noise} " in f" {t_low} ": return False
    
    # RULE 2: Cek Identitas (Harus kelihatan kayak berita perusahaan)
    # Kita cari pola kode saham 4 huruf kapital, misal "BBCA" atau "(GOTO)"
    has_stock_code = bool(re.search(r'\b[A-Z]{4}\b', title)) 
    
    has_identity = False
    for ident in IDENTITY_KEYWORDS:
        if ident in t_low:
            has_identity = True
            break
            
    if not (has_stock_code or has_identity):
        return False # Tidak ada kode saham atau kata "Emiten/Tbk" -> BUANG
        
    return True

def format_title(text):
    # Highlight Uang (Kuning)
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money-tag'>\1</span>", text, flags=re.IGNORECASE)
    # Highlight Kode Saham 4 Huruf (Cyan)
    text = re.sub(r"\b([A-Z]{4})\b", r"<span class='stock-tag'>\1</span>", text)
    return text

# ==========================================
# 3. ENGINE PENCARI (14 HARI)
# ==========================================
def fetch_news(query_group):
    # Kita persempit query di Google biar yang ditarik udah lumayan bersih
    # "intitle:saham" memaksa kata saham ada di judul
    SITES = "site:kontan.co.id OR site:cnbcindonesia.com OR site:idxchannel.com OR site:katadata.co.id"
    base_query = f"({SITES}) AND ({query_group}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={base_query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        results = []
        seen_titles = []
        rejected = 0
        
        for item in items:
            title = item.title.text
            
            # --- FILTER ---
            if not ruthles_filter(title):
                rejected += 1
                continue # Kicked by Satpam
            
            # Deduplikasi
            is_dup = False
            for s in seen_titles:
                if difflib.SequenceMatcher(None, title, s).ratio() > 0.65:
                    is_dup = True
                    break
            if is_dup: continue
            seen_titles.append(title)
            
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                dt = datetime.utcnow()
                
            src = item.source.text if item.source else "Media"
            src = src.replace(".id","").replace(".com","").upper()
            
            results.append({"title": title, "link": item.link.text, "dt": dt, "src": src})
            
        return sorted(results, key=lambda x: x['dt'], reverse=True), rejected
    except:
        return [], 0

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.title("💀 CA SNIPER V33 (NO NOISE)")
wib = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SCOPE: 14 DAYS | FILTER: STRICT | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔄 SCAN MARKET"):
    st.cache_data.clear()
    st.rerun()

# GROUP KATEGORI (Query dibuat sangat spesifik)
targets = {
    "🔥 MERGER & AKUISISI (REAL)": "akuisisi emiten OR caplok saham OR merger tbk OR ambil alih saham",
    "💰 RIGHTS ISSUE (DANANYA JELAS)": "rights issue emiten OR private placement tbk OR hmetd",
    "🚨 TENDER OFFER & PENGENDALI": "tender offer wajib OR pengendali baru saham OR go private",
    "🏗️ CAPEX & EKSPANSI": "belanja modal capex OR ekspansi pabrik emiten OR kontrak baru tbk",
    "💸 DIVIDEN & RUPS": "pembagian dividen tunai OR hasil rupslb emiten"
}

for label, query in targets.items():
    st.markdown(f"<div class='cat-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner("Filtering..."):
        data, rejected_count = fetch_news(query)
    
    if data:
        st.markdown(f"<span class='reject-msg'>Ditemukan: {len(data)} | Dibuang: {rejected_count} sampah (Tutorial/China/Opini)</span>", unsafe_allow_html=True)
        
        for news in data: # Tampilkan semua yg lolos filter
            local_time = news['dt'] + timedelta(hours=7)
            d_str = local_time.strftime("%d/%m")
            formatted_title = format_title(news['title'])
            
            st.markdown(f"""
            <div class='news-row'>
                <div class='news-date'>{d_str}</div>
                <a href='{news['link']}' target='_blank' class='news-link'>
                    {formatted_title}
                    <span class='badge-src'>{news['src']}</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='color:#333; padding:10px;'>Hening. {rejected_count} berita terdeteksi tapi semuanya sampah/tidak relevan.</div>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
