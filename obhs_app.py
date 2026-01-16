import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# ==========================================
# 1. VISUAL CONFIG
# ==========================================
st.set_page_config(page_title="TOPIC SNIPER", layout="wide", page_icon="🎯")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Consolas', monospace; }
    
    .topic-header {
        color: #00FF41;
        font-size: 18px;
        font-weight: bold;
        border-bottom: 1px solid #30363D;
        margin-top: 20px;
        margin-bottom: 10px;
        padding-bottom: 5px;
    }
    
    .news-item {
        background-color: #161B22;
        padding: 10px;
        margin-bottom: 8px;
        border-left: 3px solid #30363D;
        border-radius: 4px;
    }
    .news-item:hover { border-left-color: #00FF41; background-color: #1C2128; }
    
    .news-title {
        color: #58A6FF !important;
        text-decoration: none;
        font-weight: 600;
        font-size: 15px;
        display: block;
    }
    .news-meta {
        color: #8B949E;
        font-size: 11px;
        margin-top: 4px;
    }
    .source-badge {
        background-color: #238636;
        color: white;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 10px;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SNIPER ENGINE (GOOGLE NEWS RSS)
# ==========================================
def hunt_specific_topic(topic):
    # Menggunakan Google News RSS Feed untuk akurasi topik
    # q = query, when:7d = 7 hari terakhir, hl = bahasa ID
    formatted_topic = topic.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={formatted_topic}+when:7d&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.content, features="xml") # Parsing XML
        items = soup.find_all('item')
        
        news_list = []
        for item in items[:5]: # Ambil 5 berita teratas per topik biar gak kepenuhan
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source = item.source.text if item.source else "Google News"
            
            # Format Tanggal Sederhana
            try:
                # Contoh: Fri, 17 Jan 2026 07:00:00 GMT
                dt_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                date_str = dt_obj.strftime("%d/%m %H:%M")
            except:
                date_str = "Baru Saja"

            news_list.append({
                "title": title,
                "link": link,
                "date": date_str,
                "source": source
            })
        return news_list
        
    except Exception as e:
        return []

# ==========================================
# 3. DASHBOARD UI
# ==========================================
st.title("🎯 TOPIC SNIPER: CORPORATE ACTION")
st.caption(f"Real-Time Hunter via Google News Feed | Update: {datetime.now().strftime('%H:%M WIB')}")

if st.button("🔥 BURU BERITA SEKARANG"):
    st.rerun()

# --- DAFTAR TARGET BURUAN (KEYWORDS) ---
# Ini topik spesifik yang Bos minta. Bukan berita sampah.
targets = {
    "💰 RIGHTS ISSUE & PRIVATE PLACEMENT": "Saham Rights Issue OR Private Placement Indonesia",
    "🤝 AKUISISI & MERGER": "Saham Akuisisi OR Merger Emiten Indonesia",
    "🚨 TENDER OFFER": "Saham Tender Offer Wajib",
    "🏛️ DANANTARA & BUMN": "Danantara BUMN Saham",
    "⚠️ SUSPENSI & UMA (OJK)": "Saham Suspensi BEI OR UMA",
    "🏗️ KONTRAK & PROYEK JUMBO": "Emiten Kontrak Baru OR Menang Tender"
}

# --- EKSEKUSI ---
col1, col2 = st.columns(2)
columns = [col1, col2]

for i, (label, query) in enumerate(targets.items()):
    with columns[i % 2]: # Bagi 2 kolom
        st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
        
        results = hunt_specific_topic(query)
        
        if results:
            for news in results:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                    <div class="news-meta">
                        <span class="source-badge">{news['source']}</span>
                        {news['date']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#555; font-size:12px;'>Zonk. Belum ada berita baru minggu ini.</span>", unsafe_allow_html=True)
