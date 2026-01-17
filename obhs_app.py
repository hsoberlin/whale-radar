import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import email.utils # Library khusus untuk baca jam RSS dengan akurat

# ==========================================
# 1. KONFIGURASI TAMPILAN (ANONIM & GELAP)
# ==========================================
st.set_page_config(page_title="REALTIME TERMINAL", layout="wide", page_icon="⚡")

# CSS: Hapus Menu Streamlit, Buat Tampilan Seperti Terminal Hacker
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #000000; color: #00FF00; font-family: 'Courier New', monospace; }
    
    .news-card {
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 8px;
        background-color: #0A0A0A;
        border-left: 5px solid #00FF00;
    }
    
    .news-title {
        color: #FFFFFF !important;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
    }
    
    .news-meta {
        font-size: 11px;
        color: #888;
        margin-top: 5px;
    }
    
    .badge-time {
        background-color: #222;
        color: #00FF00;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #00FF00;
        font-weight: bold;
    }
    
    /* Tombol Refresh */
    div.stButton > button {
        width: 100%;
        background-color: #003300;
        color: #00FF00;
        border: 1px solid #00FF00;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MESIN PENCARI (BRUTAL SORTING LOGIC)
# ==========================================
def parse_date(date_str):
    # Mengubah format tanggal RSS (RFC 822) menjadi objek Python yang bisa diurutkan
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except:
        return datetime.now().astimezone()

def get_realtime_news(query):
    # Parameter URL ditambah 'when:1d' untuk memaksa berita 24 jam terakhir
    # Dan ditambah 'ceid=ID:id' untuk server Indonesia
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:1d&hl=id-ID&gl=ID&ceid=ID:id"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all('item')
        
        news_basket = []
        
        for item in items:
            title = item.title.text
            link = item.link.text
            pub_date_str = item.pubDate.text
            source = item.source.text if item.source else "Google News"
            
            # 1. Konversi text tanggal jadi Obyek Waktu
            dt_object = parse_date(pub_date_str)
            
            # 2. Masukkan ke keranjang
            news_basket.append({
                'title': title,
                'link': link,
                'source': source,
                'raw_date': dt_object # Ini dipakai untuk menyortir
            })
            
        # 3. SORTING MANUAL (PENTING!)
        # Kita urutkan list berdasarkan 'raw_date' dari yang paling besar (Terbaru) ke Kecil
        sorted_news = sorted(news_basket, key=lambda x: x['raw_date'], reverse=True)
        
        # 4. Ambil 5 teratas setelah diurutkan
        return sorted_news[:6]
        
    except Exception as e:
        return []

# ==========================================
# 3. DASHBOARD UTAMA
# ==========================================
st.markdown("<h2 style='text-align:center;'>⚡ TERMINAL AKSI KORPORASI (REAL-TIME)</h2>", unsafe_allow_html=True)

# Jam Server UTC diubah ke WIB
wib_now = datetime.utcnow() + timedelta(hours=7)
st.caption(f"SYSTEM TIME: {wib_now.strftime('%H:%M:%S')} WIB | MODE: STRICT CHRONOLOGICAL")

if st.button("🔄 PAKSA UPDATE BERITA (REFRESH)"):
    st.cache_data.clear()
    st.rerun()

# DAFTAR KEYWORD (Diperketat biar gak lari kemana-mana)
targets = {
    "🔥 AKUISISI & MERGER": "akuisisi saham OR merger perusahaan",
    "💰 TENDER OFFER": "tender offer saham OR penawaran tender wajib",
    "📈 RIGHTS ISSUE": "rights issue saham OR hmetd emiten",
    "⚠️ SUSPENSI & RUPS": "suspensi saham BEI OR hasil RUPSLB emiten"
}

col1, col2 = st.columns(2)
cols = [col1, col2]

for i, (label, keyword) in enumerate(targets.items()):
    with cols[i % 2]:
        st.markdown(f"### {label}")
        
        # Panggil fungsi pencari
        results = get_realtime_news(keyword)
        
        if results:
            for news in results:
                # Hitung selisih waktu (Berapa jam/menit yang lalu)
                news_time_wib = news['raw_date'] + timedelta(hours=7)
                time_str = news_time_wib.strftime('%H:%M')
                date_str = news_time_wib.strftime('%d/%m')
                
                # Tampilkan
                st.markdown(f"""
                <div class="news-card">
                    <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                    <div class="news-meta">
                        <span class="badge-time">{time_str} WIB</span> 
                        <span>{date_str}</span> | 
                        <span style="color:#00AA00;">{news['source']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#555; border:1px dashed #333; padding:10px;'>Hening. Tidak ada aktivitas 24 jam terakhir.</div>", unsafe_allow_html=True)

