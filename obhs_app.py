# --- SEMBUNYIKAN MENU & FOOTER (BIAR ANONIM) ---
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    
    /* Tombol Refresh */
    div.stButton > button {
        width: 100%;
        background-color: #238636;
        color: white;
        font-weight: bold;
        border: 1px solid #30363D;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
        border-color: #8b949e;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SNIPER ENGINE (GOOGLE NEWS RSS)
# ==========================================
def hunt_specific_topic(topic):
    # Format query agar URL valid
    formatted_topic = topic.replace(" ", "+")
    # URL Google News RSS (Bahasa Indonesia)
    url = f"https://news.google.com/rss/search?q={formatted_topic}+when:7d&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=8)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        news_list = []
        # Ambil maksimal 5 berita per topik
        for item in items[:5]: 
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source = item.source.text if item.source else "Google News"
            
            # Konversi Tanggal agar mudah dibaca
            try:
                # Format asli: Fri, 17 Jan 2026 07:00:00 GMT
                dt_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                # Tambah 7 jam manual untuk tampilan per berita (opsional, karena ini GMT)
                dt_wib = dt_obj + timedelta(hours=7)
                date_str = dt_wib.strftime("%d/%m %H:%M")
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

# --- FIX JAM WIB (UTC + 7 JAM) ---
# Kita pakai utcnow() biar pasti ngambil jam server nol (0), lalu tambah 7.
utc_now = datetime.utcnow()
wib_now = utc_now + timedelta(hours=7)
jam_update = wib_now.strftime('%H:%M')

st.caption(f"Real-Time Hunter via Google News Feed | Update: {jam_update} WIB")

if st.button("🔥 BURU BERITA SEKARANG (REFRESH)"):
    st.rerun()

# --- DAFTAR TARGET BURUAN ---
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
    with columns[i % 2]: 
        st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
        
        with st.spinner(f"Memburu {label}..."):
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

