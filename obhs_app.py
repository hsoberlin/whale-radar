import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import difflib

# ==========================================
# 1. VISUAL SETUP (HIGH CONTRAST MODE)
# ==========================================
st.set_page_config(page_title="CA X-RAY V38", layout="wide", page_icon="👁️")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* BACKGROUND HITAM PEKAT, TEKS PUTIH TERANG */
    .stApp { background-color: #000000; color: #FFFFFF; font-family: 'Verdana', sans-serif; }
    
    /* JUDUL KATEGORI - HIJAU NEON */
    .topic-header {
        border-bottom: 3px solid #00FF00;
        padding-bottom: 5px;
        margin-top: 35px;
        margin-bottom: 15px;
        font-size: 22px;
        font-weight: 900;
        color: #00FF00;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0px 0px 10px rgba(0, 255, 0, 0.4);
    }
    
    /* KOTAK BERITA */
    .news-card {
        background-color: #121212; /* Abu Sangat Gelap */
        border: 1px solid #444;
        border-radius: 0px; /* Kotak Tegas */
        padding: 15px;
        margin-bottom: 15px;
    }
    .news-card:hover { border: 1px solid #FFFFFF; background-color: #1A1A1A; }
    
    /* JUDUL BERITA - PUTIH MUTLAK */
    .news-link {
        color: #FFFFFF !important; 
        font-size: 18px; 
        font-weight: 800; /* Extra Bold */
        text-decoration: none;
        display: block;
        margin-bottom: 5px;
        line-height: 1.3;
    }
    .news-link:hover { color: #FFFF00 !important; text-decoration: underline; }
    
    /* META DATA (TANGGAL) - HIJAU TERANG */
    .meta-row { display: flex; align-items: center; margin-bottom: 8px; }
    .meta-date { color: #00FF00; font-size: 12px; font-weight: bold; font-family: monospace; }
    .src-badge { 
        background-color: #FFFFFF; color: #000000; 
        font-size: 11px; font-weight: bold; padding: 1px 6px; 
        margin-left: 10px; border-radius: 2px;
    }
    
    /* SNIPPET / ISI BERITA - ABU TERANG BIAR KONTRAS */
    .news-snippet {
        font-size: 14px;
        color: #DDDDDD; /* Hampir Putih */
        line-height: 1.5;
        border-left: 4px solid #00FF00; /* Garis Hijau di Kiri */
        padding-left: 10px;
        background-color: #000000;
        padding: 8px;
    }
    
    /* HIGHLIGHTS YANG MENYALA */
    .money { color: #FFFF00; font-weight: 900; border-bottom: 1px dotted #FFFF00; } /* KUNING NYALA */
    .ticker { background-color: #00FFFF; color: #000000; padding: 0 4px; font-weight: 900; } /* CYAN NYALA */
    .action { color: #FF00FF; font-weight: bold; text-decoration: underline; } /* MAGENTA NYALA */

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC: X-RAY SCANNER (SAMA SEPERTI V37)
# ==========================================

NOISE = ["sinopsis", "film", "zodiak", "cara", "tips", "resep", "trik", "panduan", "jadwal bioskop", "review"]

def highlight_content(text):
    # Highlight Uang (Kuning Emas)
    text = re.sub(r"(Rp\s?[\d\.,]+\s?[TM]riliun|Rp\s?[\d\.,]+\s?Miliar|US\$\s?[\d\.,]+)", r"<span class='money'>\1</span>", text, flags=re.IGNORECASE)
    # Highlight Ticker (Cyan Background)
    text = re.sub(r"\b([A-Z]{4})\b", r"<span class='ticker'>\1</span>", text)
    # Highlight Aksi (Magenta)
    actions = ["akuisisi", "merger", "rights issue", "private placement", "tender offer", "rups", "dividen"]
    for act in actions:
        text = re.sub(f"({act})", r"<span class='action'>\1</span>", text, flags=re.IGNORECASE)
    return text

def extract_snippet(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    text = text.replace("Baca selengkapnya...", "").replace("Google Berita", "")
    return text[:280] + "..." 

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
            
            # FILTER DATE
            try:
                dt = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
            except: continue
            if dt < cutoff: continue
            
            # FILTER NOISE
            if any(n in title.lower() for n in NOISE): continue

            # DEDUPLIKASI
            if any(difflib.SequenceMatcher(None, title, s).ratio() > 0.7 for s in seen_titles): continue
            seen_titles.append(title)
            
            # FORMAT SOURCE
            src = item.source.text if item.source else "MEDIA"
            src = src.replace(".id","").replace(".com","").upper()
            
            valid_news.append({
                "title": title,
                "snippet": clean_desc,
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
st.title("👁️ CA X-RAY V38 (HIGH CONTRAST)")
wib = datetime.utcnow() + timedelta(hours=7)
start_date = wib - timedelta(days=14)
st.caption(f"UPDATE: {wib.strftime('%H:%M')} WIB | RANGE: {start_date.strftime('%d %b')} - {wib.strftime('%d %b')}")

if st.button("🔄 SCAN ULANG (REFRESH)"):
    st.cache_data.clear()
    st.rerun()

topics = {
    "🤝 MERGER & AKUISISI": "akuisisi OR merger OR caplok OR ambil alih OR pengendali baru",
    "💰 RIGHTS ISSUE & MODAL": "rights issue OR hmetd OR private placement OR setoran modal",
    "🚨 TENDER OFFER & GO PRIVATE": "tender offer OR go private OR delisting OR penawaran tender",
    "🗣️ MEMINTA PERSETUJUAN (RUPS)": "rupslb OR rapat umum pemegang saham OR minta restu OR agenda rups"
}

for label, query in topics.items():
    st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
    
    with st.spinner(f"Scanning {label}..."):
        news_list = hunt_xray(query)
    
    if news_list:
        for news in news_list:
            local_time = news['dt'] + timedelta(hours=7)
            date_str = local_time.strftime("%d/%m %H:%M")
            
            fmt_title = highlight_content(news['title'])
            fmt_snippet = highlight_content(news['snippet'])
            
            st.markdown(f"""
            <div class='news-card'>
                <div class='meta-row'>
                    <span class='meta-date'>{date_str} WIB</span>
                    <span class='src-badge'>{news['src']}</span>
                </div>
                <a href='{news['link']}' target='_blank' class='news-link'>{fmt_title}</a>
                <div class='news-snippet'>{fmt_snippet}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada data baru.")

st.markdown("<br><br>", unsafe_allow_html=True)
