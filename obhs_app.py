import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import difflib

# ==========================================
# 1. KONFIGURASI VISUAL (DEEP SEA MODE)
# ==========================================
st.set_page_config(page_title="CA TRAWLER v30.0", layout="wide", page_icon="🦈")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #080C10; color: #C9D1D9; font-family: 'Consolas', 'Courier New', monospace; }
    
    /* Header Kategori */
    .cat-header {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        border-left: 5px solid #00FF41;
        padding: 12px;
        margin-top: 35px;
        margin-bottom: 15px;
        font-size: 16px;
        font-weight: bold;
        color: #00FF41;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Baris Berita */
    .news-row {
        padding: 8px 10px;
        border-bottom: 1px solid #21262D;
        display: flex;
        align-items: center;
        transition: background 0.2s;
    }
    .news-row:hover { background-color: #1F242C; }
    
    .news-date {
        font-size: 11px;
        color: #8B949E;
        min-width: 85px;
        font-family: monospace;
    }
    
    .news-link {
        color: #E6EDF3;
        text-decoration: none;
        font-size: 14px;
        flex-grow: 1;
        margin-left: 12px;
        font-weight: 500;
    }
    .news-link:hover { color: #58A6FF; text-decoration: underline; }
    
    /* Badges */
    .badge-src { font-size: 9px; padding: 2px 6px; border-radius: 3px; font-weight: bold; min-width: 55px; text-align: center; color: white;}
    .bg-cnbc { background-color: #00509E; }
    .bg-kontan { background-color: #008000; }
    .bg-idx { background-color: #B30000; }
    .bg-kata { background-color: #CC6600; }
    
    /* Statistik */
    .stat-box { font-size:10px; color:#555; margin-left: 10px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MESIN PENCARI MULTI-LAYER (14 HARI)
# ==========================================

SOURCES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"

def clean_source(text):
    t = text.lower()
    if "cnbc" in t: return "CNBC", "bg-cnbc"
    if "kontan" in t: return "KONTAN", "bg-kontan"
    if "idx" in t: return "IDX", "bg-idx"
    if "katadata" in t: return "DATA", "bg-kata"
    return "MEDIA", "bg-idx"

def fetch_data_layer(sub_queries):
    """
    Melakukan pencarian berlapis untuk 1 kategori agar data maksimal.
    Google membatasi 1 RSS max ~100 item. Dengan memecah query, kita bisa dapat 100 x N item.
    """
    aggregated_news = []
    seen_titles = [] # Penampung deduplikasi global
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for q in sub_queries:
        # QUERY 14 HARI (when:14d) & STRICT INDONESIA (ceid=ID:id)
        full_query = f"({SOURCES}) AND ({q}) when:14d"
        url = f"https://news.google.com/rss/search?q={full_query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, features="xml")
            items = soup.find_all('item')
            
            for item in items:
                title = item.title.text
                
                # --- FILTER DEDUPLIKASI (Judul Mirip Dibuang) ---
                is_exist = False
                for seen in seen_titles:
                    # Jika kemiripan > 65%, anggap sama
                    if difflib.SequenceMatcher(None, title.lower(), seen.lower()).ratio() > 0.65:
                        is_exist = True
                        break
                
                if is_exist: continue
                
                seen_titles.append(title)
                
                # Parsing
                try:
                    dt_obj = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    dt_obj = datetime.utcnow()
                
                src_lbl, src_cls = clean_source(item.source.text if item.source else "")
                
                aggregated_news.append({
                    "title": title,
                    "link": item.link.text,
                    "dt": dt_obj,
                    "src_lbl": src_lbl,
                    "src_cls": src_cls
                })
        except:
            continue
            
    # SORTING FINAL (Waktu Terbaru)
    return sorted(aggregated_news, key=lambda x: x['dt'], reverse=True)

# ==========================================
# 3. STRATEGI KATA KUNCI "TAJAM"
# ==========================================
# Setiap kategori dipecah jadi list query biar hasil pencarian makin dalam

target_layers = {
    "🔥 MERGER & AKUISISI (CORP ACTION)": [
        "akuisisi saham emiten",
        "pengambilalihan saham pengendali",
        "merger perusahaan tercatat",
        "transaksi material afiliasi",
        "negosiasi saham jumbo"
    ],
    "💰 RIGHTS ISSUE & MODAL (CASH CALL)": [
        "rights issue emiten",
        "private placement saham",
        "HMETD prospektus",
        "setoran modal saham",
        "pelaksanaan waran saham"
    ],
    "🚨 TENDER OFFER & PENGENDALI": [
        "tender offer wajib",
        "penawaran tender sukarela",
        "perubahan pengendali saham",
        "go private delisting"
    ],
    "🏗️ CAPEX, PROYEK & EKSPANSI": [
        "belanja modal capex emiten",
        "ekspansi pabrik baru saham",
        "kontrak baru emiten konstruksi",
        "proyek strategis emiten"
    ],
    "💸 DIVIDEN, SUSPENSI & RUPS": [
        "jadwal cum dividen tunai",
        "hasil RUPSLB emiten",
        "suspensi saham BEI",
        "unusual market activity UMA"
    ]
}

# ==========================================
# 4. DASHBOARD EKSEKUSI
# ==========================================
st.title("🦈 CA TRAWLER v30.0 (14-DAY DEEP DRAGNET)")
wib_now = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SCOPE: 14 HARI KEBELAKANG | MODE: MULTI-LAYER QUERY | UPDATE: {wib_now.strftime('%H:%M')} WIB")

if st.button("🌊 TEBAR JARING (FORCE REFRESH)"):
    st.cache_data.clear()
    st.rerun()

col1, col2 = st.columns(2)
# Kita bagi kategori ke 2 kolom biar padat
keys = list(target_layers.keys())
half = len(keys)//2 + 1

with col1:
    for cat in keys[:half]:
        queries = target_layers[cat]
        st.markdown(f"<div class='cat-header'>{cat}</div>", unsafe_allow_html=True)
        
        with st.spinner(f"Menarik data 14 hari..."):
            results = fetch_data_layer(queries)
        
        if results:
            st.markdown(f"<div class='stat-box'>Found: {len(results)} records</div>", unsafe_allow_html=True)
            # Tampilkan Max 20 Berita per Kategori biar halaman gak kepanjangan
            for news in results[:20]: 
                loc_time = news['dt'] + timedelta(hours=7)
                date_str = loc_time.strftime("%d/%m")
                
                st.markdown(f"""
                <div class="news-row">
                    <span class="news-date">{date_str}</span>
                    <span class="badge-src {news['src_cls']}">{news['src_lbl']}</span>
                    <a href="{news['link']}" target="_blank" class="news-link">{news['title']}</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nihil. Tidak ada data valid 14 hari terakhir.")

with col2:
    for cat in keys[half:]:
        queries = target_layers[cat]
        st.markdown(f"<div class='cat-header'>{cat}</div>", unsafe_allow_html=True)
        
        with st.spinner(f"Menarik data 14 hari..."):
            results = fetch_data_layer(queries)
        
        if results:
            st.markdown(f"<div class='stat-box'>Found: {len(results)} records</div>", unsafe_allow_html=True)
            for news in results[:20]:
                loc_time = news['dt'] + timedelta(hours=7)
                date_str = loc_time.strftime("%d/%m")
                
                st.markdown(f"""
                <div class="news-row">
                    <span class="news-date">{date_str}</span>
                    <span class="badge-src {news['src_cls']}">{news['src_lbl']}</span>
                    <a href="{news['link']}" target="_blank" class="news-link">{news['title']}</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nihil. Tidak ada data valid 14 hari terakhir.")

