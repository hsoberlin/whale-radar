import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. VISUAL SETUP (DARK MODE + SNIPPET)
# ==========================================
st.set_page_config(page_title="CA X-RAY V37", layout="wide", page_icon="🧬")

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
        margin-bottom: 15px;
        font-size: 18px;
        font-weight: bold;
        color: #00FF41;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* KARTU BERITA */
    .news-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 10px;
        transition: transform 0.1s;
    }
    .news-card:hover { border-color: #58A6FF; }
    
    .news-top-row { display: flex; align-items: flex-start; justify-content: space-between; }
    
    /* JUDUL BERITA */
    .news-link {
        color: #58A6FF; font-size: 15px; font-weight: bold; text-decoration: none;
    }
    .news-link:hover { text-decoration: underline; color: #79C0FF; }
    
    /* TANGGAL & SUMBER */
    .meta-tag { font-size: 11px; color: #8B949E; margin-right: 10px; }
    .src-badge { 
        font-size: 10px; background-color: #21262D; color: #C9D1D9; 
        padding: 2px 6px; border-radius: 4px; border: 1px solid #30363D; 
    }
    
    /* SNIPPET / ISI BERITA (ABU-ABU) */
    .news-snippet {
        font-size: 13px;
        color: #C9D1D9;
        margin-top: 8px;
        line-height: 1.4;
        border-left: 3px solid #30363D;
        padding-left: 8px;
    }
    
    /* HIGHLIGHTS */
    .money { color: #D2A8FF; font-weight: bold; } /* Ungu untuk Uang */
    .ticker { background-color: #0969DA; color: white; padding: 0 4px; border-radius: 3px; font-weight: bold; font-size: 12px; } /* Biru untuk Saham */
    .action { color: #00FF41; font-weight: bold; border-bottom: 1px dashed #00FF41; } /* Hijau untuk Aksi */

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC: X-RAY SCANNER (TITLE + BODY)
# ==========================================

# Keyword Sampah (Tetap aktif biar bersih)
NOISE = ["sinopsis", "film", "zodiak", "cara", "tips", "resep", "trik", "panduan", "jadwal bioskop", "review"]

def highlight_content(text):
    # 1. Highlight UANG
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money'>\1</span>", text, flags=re.IGNORECASE)
    # 2. Highlight TICKER (Kode Saham 4 Huruf Kapital)
    # Regex ini mencari huruf kapital 4 digit yg berdiri sendiri (misal: BBCA, bukan KATA)
    # Kita filter manual nanti biar gak nge-highlight kata umum
    text = re.sub(r"\b([A-Z]{4})\b", r"<span class='ticker'>\1</span>", text)
    # 3. Highlight AKSI (Akuisisi, dll)
    actions = ["akuisisi", "merger", "rights issue", "private placement", "tender offer", "rups", "dividen"]
    for act in actions:
        text = re.sub(f"({act})", r"<span class='action'>\1</span>", text, flags=re.IGNORECASE)
    return text

def extract_snippet(html_content):
    # Google News deskripsinya format HTML, kita bersihkan tag-nya
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    # Kadang ada teks aneh "Baca selengkapnya...", kita buang
    text = text.replace("Baca selengkapnya...", "").replace("Google Berita", "")
    return text[:250] + "..." # Ambil 250 karakter aja

def hunt_xray(keywords):
    SITES = "site:cnbcindonesia.com OR site:kontan.co.id OR site:idxchannel.com OR site:katadata.co.id"
    full_query = f"({SITES}) AND ({keywords}) when:14d"
    
    url = f"https://news.google.com/rss/search?q={full_query.replace(' ', '+')}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        valid_news = []
        seen_titles = []
        cutoff = datetime.utcnow() - timedelta(days=14)
        
        for item in items:
            title = item.title.text
            raw_desc = item.description.text if item.description else ""
            clean_desc = extract_snippet(raw_desc)
            
            # --- FILTER ---
            
            # 1. TANGGAL
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except: continue
            if dt < cutoff: continue
            
            # 2. NOISE
            if any(n in title.lower() for n in NOISE): continue

            # 3. GABUNGAN SCAN (JUDUL + ISI)
            # Kita scan Ticker di Judul ATAU di Isi
            full_text_scan = title + " " + clean_desc
            
            # Cek Deduplikasi
            if any(difflib.SequenceMatcher(None, title, s).ratio() > 0.7 for s in seen_titles): continue
            seen_titles.append(title)
            
            # Format Source
            src = item.source.text if item.source else "Media"
            src = src.replace(".id","").replace(".com","").upper()
            
            valid_news.append({
                "title": title,
                "snippet": clean_desc, # Kita simpan snippetnya
                "link": item.link.text,
                "dt": dt,
                "src": src
            })
            
        return sorted(valid_news, key=lambda x: x['dt'], reverse=True)
    except:
        return []

# ==========================================
# 3. DASHBOARD EXECUTION
# ==========================================
st.title("🧬 CA X-RAY V37 (BODY SCANNER)")
wib = datetime.utcnow() + timedelta(hours=7)
start_date = wib - timedelta(days=14)
st.caption(f"SCANNING: TITLE + BODY TEXT | 14 DAYS FEED | UPDATE: {wib.strftime('%H:%M')} WIB")

if st.button("🔥 SCAN DEEP (REFRESH)"):
    st.cache_data.clear()
    st.rerun()

topics = {
    "🤝 MERGER & AKUISISI": "akuisisi OR merger OR caplok OR ambil alih OR pengendali baru",
    "💰 RIGHTS ISSUE & MODAL": "rights issue OR hmetd OR private placement OR setoran modal",
    "🚨 TENDER OFFER & GO PRIVATE": "tender offer OR go private OR delisting OR penawaran tender",
    "🗣️ MEMINTA PERSETUJUAN (RUPS/RESTU)": "rupslb OR rapat umum pemegang saham OR minta restu OR agenda rups"
}

for label, query in topics.items():
    st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner(f"X-Ray Scanning {label}..."):
        news_list = hunt_xray(query)
    
    if news_list:
        for news in news_list:
            local_time = news['dt'] + timedelta(hours=7)
            date_str = local_time.strftime("%d/%m %H:%M")
            
            # Format Title & Snippet (Kasih warna)
            fmt_title = highlight_content(news['title'])
            fmt_snippet = highlight_content(news['snippet'])
            
            st.markdown(f"""
            <div class='news-card'>
                <div class='news-top-row'>
                    <div>
                        <span class='meta-tag'>{date_str}</span>
                        <a href='{news['link']}' target='_blank' class='news-link'>{fmt_title}</a>
                    </div>
                    <span class='src-badge'>{news['src']}</span>
                </div>
                <div class='news-snippet'>{fmt_snippet}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada data ditemukan.")

st.markdown("<br><br>", unsafe_allow_html=True)
