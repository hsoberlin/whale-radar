import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ==========================================
# 1. CORE CONFIG & ANONIM MODE
# ==========================================
st.set_page_config(page_title="CA TERMINAL v26.1", layout="wide", page_icon="🎯")

# Sembunyikan jejak developer (Main Menu & Footer)
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #050505; color: #FAFAFA; font-family: 'Consolas', monospace; }
    
    .topic-header {
        color: #00FF41; font-size: 18px; font-weight: bold;
        border-bottom: 2px solid #333; margin-top: 20px; padding-bottom: 5px;
    }
    .news-card {
        background-color: #0D0D0D; padding: 12px; border: 1px solid #222;
        margin-bottom: 8px; border-left: 4px solid #00FF41; border-radius: 4px;
    }
    .news-title { color: #58A6FF !important; text-decoration: none; font-weight: 600; font-size: 14px; display: block; }
    .news-meta { color: #8B949E; font-size: 11px; margin-top: 5px; }
    .badge-source { background-color: #238636; color: white; padding: 1px 6px; border-radius: 3px; font-size: 10px; margin-right: 5px; }
    .badge-new { background-color: #CC0000; color: white; padding: 1px 6px; border-radius: 3px; font-weight: bold; animation: blink 1s infinite; }
    @keyframes blink { 50% { opacity: 0; } }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. SNIPER ENGINE (CHRONO-SORTING)
# ==========================================
def hunt_realtime(topic):
    # Mencari berita 24 jam terakhir agar selalu segar
    query = f"{topic} when:1d"
    formatted_query = query.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={formatted_query}&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.content, features="xml")
        items = soup.find_all('item')
        
        results = []
        for item in items:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            source = item.source.text if item.source else "MEDIA"
            
            # Konversi waktu ke datetime object untuk sorting
            dt_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            
            results.append({
                "title": title, "link": link, "dt": dt_obj, "source": source
            })
        
        # URUTKAN BERDASARKAN WAKTU (Paling baru di atas)
        return sorted(results, key=lambda x: x['dt'], reverse=True)[:6]
    except:
        return []

# ==========================================
# 3. DASHBOARD RENDER
# ==========================================
st.markdown("<h2 style='text-align:center;'>🎯 TOPIC SNIPER: CORPORATE ACTION</h2>", unsafe_allow_html=True)

# Jam WIB Real-time
wib_now = datetime.utcnow() + timedelta(hours=7)
st.caption(f"Real-Time Hunter | Server Sync: {wib_now.strftime('%H:%M:%S')} WIB")

if st.button("🔥 FORCE RE-SCAN MARKET (BERSIHKAN CACHE)"):
    st.cache_data.clear()
    st.rerun()

# Kategori target aksi korporasi
targets = {
    "💰 RIGHTS ISSUE & PP": "rights issue OR hmetd OR private placement saham",
    "🤝 AKUISISI & MERGER": "akuisisi saham baru OR merger emiten OR pengendali baru",
    "🚨 TENDER OFFER": "tender offer wajib OR penawaran tender saham",
    "🏛️ RUPSLB & DIVIDEN": "hasil RUPSLB emiten OR jadwal dividen saham"
}

col1, col2 = st.columns(2)
cols = [col1, col2]

for i, (label, query) in enumerate(targets.items()):
    with cols[i % 2]:
        st.markdown(f"<div class='topic-header'>{label}</div>", unsafe_allow_html=True)
        news_data = hunt_realtime(query)
        
        if news_data:
            for n in news_data:
                # Format jam tayang berita
                news_time = n['dt'] + timedelta(hours=7)
                time_display = news_time.strftime("%d/%m %H:%M")
                
                # Tag NEW jika berita kurang dari 4 jam lalu
                is_new = (datetime.utcnow() - n['dt']).total_seconds() < 14400
                badge = "<span class='badge-new'>NEW</span> " if is_new else ""
                
                st.markdown(f"""
                    <div class="news-card">
                        <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                        <div class="news-meta">
                            {badge}<span class="badge-source">{n['source']}</span> {time_display} WIB
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("Sinyal belum terdeteksi dalam 24 jam terakhir.")
