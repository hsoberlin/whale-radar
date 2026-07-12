import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
import feedparser
import re
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import urllib.parse

# 1. Dashboard Configuration
st.set_page_config(page_title="PREDATOR QUANTUM v2.8", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 60 Seconds
st_autorefresh(interval=60000, key="quantum_auto_link")

# --- PREMIUM GLASSMORPHISM UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@500;800&family=Inter:wght@400;600;900&display=swap');
    .stApp { background: radial-gradient(circle at top right, #0a0e1a, #05070a); color: #ffffff; }
    .header-container {
        padding: 20px; background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(10px);
        border-radius: 15px; border: 1px solid rgba(0, 255, 204, 0.1); margin-bottom: 25px; text-align: center;
    }
    .header-title {
        font-family: 'Orbitron', sans-serif !important; font-weight: 900; font-size: 50px !important;
        background: linear-gradient(90deg, #00ffcc, #0099ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 255, 204, 0.3); letter-spacing: 8px; margin-bottom: 0px;
    }
    .status-bar {
        background: rgba(0, 255, 204, 0.05); border-left: 5px solid #00ffcc;
        padding: 10px 20px; font-family: 'JetBrains Mono', monospace;
        font-weight: 800; color: #00ffcc; font-size: 14px; margin-bottom: 30px;
    }
    .metric-container {
        background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px; padding: 25px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .metric-lbl { color: #8b949e; font-family: 'Orbitron', sans-serif; font-size: 11px; letter-spacing: 2px; }
    .metric-val { font-family: 'Orbitron', sans-serif; font-size: 35px; font-weight: 900; color: #00ffcc; margin-top: 10px; }
    .news-box {
        background: rgba(255, 255, 255, 0.02); border-radius: 10px; border-left: 4px solid #ff4d4d;
        padding: 15px; margin-bottom: 12px; transition: 0.2s;
    }
    .news-box:hover { background: rgba(255, 255, 255, 0.05); border-left: 4px solid #00ffcc; }
    .news-topic-header { font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 12px; color: #00ffcc !important; }
    .news-text { font-family: 'Inter', sans-serif; font-size: 12px; color: #e6edf3; margin-top: 5px; }
    /* Style link agar tidak bergaris bawah kecuali di-hover */
    .news-text a { text-decoration: none; color: #e6edf3; transition: 0.2s; }
    .news-text a:hover { color: #00ffcc; text-shadow: 0 0 10px rgba(0, 255, 204, 0.5); }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
master_afiliasi = {
    "BRPT": "PRAJOGO PANGESTU", "TPIA": "PRAJOGO PANGESTU", "CUAN": "PRAJOGO PANGESTU", 
    "BREN": "PRAJOGO PANGESTU", "PTRO": "PRAJOGO PANGESTU", "CGAS": "PRAJOGO PANGESTU",
    "CDIA": "PRAJOGO PANGESTU", "GZCO": "PRAJOGO PANGESTU",
    "BNBR": "BAKRIE GROUP", "BUMI": "BAKRIE & SALIM", "UNSP": "BAKRIE GROUP",
    "ENRG": "BAKRIE GROUP", "DEWA": "BAKRIE GROUP", "BRMS": "BAKRIE GROUP", 
    "VIVA": "BAKRIE GROUP", "MDIA": "BAKRIE GROUP", "JGLE": "BAKRIE GROUP", 
    "ALII": "BAKRIE GROUP", "ELTY": "BAKRIE GROUP", "BTEL": "BAKRIE GROUP",
    "AMMN": "SALIM & PANIGORO", "DNET": "SALIM GROUP", "INDF": "SALIM GROUP", 
    "ICBP": "SALIM GROUP", "LSIP": "SALIM GROUP", "SIMP": "SALIM GROUP",
    "META": "SALIM GROUP", "ROTI": "SALIM GROUP", "IMAS": "SALIM GROUP",
    "DSSA": "SINAR MAS", "BSDE": "SINAR MAS", "INKP": "SINAR MAS", 
    "TKIM": "SINAR MAS", "SMMA": "SINAR MAS", "DUTI": "SINAR MAS",
    "SMAR": "SINAR MAS", "FREN": "SINAR MAS",
    "PANI": "AGUAN (PIK 2)", "CBDK": "AGUAN (SEDAYU)", "ASRI": "AGUAN GROUP",
    "JIHD": "TOMY WINATA", "AGRO": "TOMY WINATA",
    "HITS": "TOMMY SOEHARTO", "HUMI": "TOMMY SOEHARTO", "GOLF": "TOMMY SOEHARTO",
    "ADRO": "BOY THOHIR", "ADMR": "BOY THOHIR", "ESSA": "BOY THOHIR",
    "MBMA": "BOY THOHIR", "MDKA": "BOY THOHIR (SANDI)",
    "RAJA": "HAPPY HAPSORO", "CBRE": "HAPPY HAPSORO", "PSAB": "HAPPY HAPSORO",
    "MEDC": "ARIFIN PANIGORO", "DRMA": "TP RACHMAT", "ASLC": "TP RACHMAT", "TAPG": "TP RACHMAT",
    "TOBA": "LUHUT GROUP", "PGAS": "STATE OWNED", "BBRI": "STATE OWNED", 
    "BMRI": "STATE OWNED", "BBNI": "STATE OWNED", "TLKM": "STATE OWNED", "ANTM": "STATE OWNED"
}

RSS_LINKS = [
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640953919",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640956058",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/17720372188069162265",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/4715023400486420700",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/6157427371671042291",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/8676695815866551512"
]

def fetch_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    topic_map = {"AKUISISI": "AKUISISI", "RIGHTS ISSUE": "RIGHTS", "DANANTARA": "DANANTARA", "ASSET": "ASSET"}
    now = datetime.now()
    seen_news = set()

    for url in RSS_LINKS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                clean_title = entry.title.replace('<b>','').replace('</b>','').strip()
                if clean_title in seen_news: continue
                
                title_upper = clean_title.upper()
                tickers = re.findall(r'\b[A-Z]{4}\b', title_upper)
                
                detected_topic = next((label for key, label in topic_map.items() if key in title_upper), "STRATEGIS")
                
                for t in tickers:
                    if t not in ["IHSG", "LQ45", "BEII", "IDX"]:
                        intel_map[t] = clean_title
                        news_tickers.add(t) 
                
                intel_list.append({"TOPIC": detected_topic, "NEWS": clean_title, "TIME": entry.get('published', 'RECENT')})
                seen_news.add(clean_title)
        except: continue
    return intel_map, intel_list, list(news_tickers)

def scan_market():
    results = []
    intel_map, _, news_tickers = fetch_intel()
    combined_targets = list(set(list(master_afiliasi.keys()) + news_tickers))
    
    for ticker in combined_targets:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            h = s.history(period="50d")
            if len(h) < 10: continue
            
            v_ma50 = h['Volume'].mean()
            v_today = h['Volume'].iloc[-1]
            c = h['Close'].iloc[-1]
            p = h['Close'].iloc[-2]
            gain = ((c - p) / p) * 100
            val_b = (v_today * c) / 1e9
            p_factor = v_today / v_ma50 if v_ma50 > 0 else 1
            
            if val_b < 1.0 or gain < -5: continue 
            
            score = 10
            if ticker in intel_map: score += 30 
            if p_factor > 1.5: score += 20
            if gain > 3: score += 20
            if val_b > 10: score += 20

            group_info = master_afiliasi.get(ticker, f"⭐ NEWS: {intel_map.get(ticker, 'Active Sentiment')[:40]}...")

            results.append({
                "SYMBOL": ticker, "CONF": max(0, min(score, 100)), "PRICE": int(c) if c >= 1 else c, 
                "CHG%": round(gain, 2), "VALUE": round(val_b, 1), "PWR": round(p_factor, 1), 
                "GROUP / SENTIMEN": group_info
            })
        except: continue
    return results

# --- INTERFACE RENDERING ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-bar">● RADAR SYNCED WITH NEWS FEED | {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

data = scan_market()
_, news_feed, _ = fetch_intel()

if data:
    df = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-container"><span class="metric-lbl">ACTIVE SIGNALS</span><br><span class="metric-val">{len(df)}</span></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-container"><span class="metric-lbl">TOTAL VALUE</span><br><span class="metric-val">{df["VALUE"].sum():.1f}B</span></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-container"><span class="metric-lbl">TOP CONFIDENCE</span><br><span class="metric-val">{df["CONF"].max()}%</span></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-container"><span class="metric-lbl">HOT NEWS UNITS</span><br><span class="metric-val">{len(df[df["GROUP / SENTIMEN"].str.contains("⭐")])}</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_main, col_news = st.columns([1.8, 1.2])
    with col_main:
        st.markdown("<h2 style='color:#00ffcc; font-family:Orbitron; font-size: 20px;'>📡 INTEGRATED TRACKER (MARKET + NEWS)</h2>", unsafe_allow_html=True)
        st.dataframe(df, column_config={
            "CONF": st.column_config.ProgressColumn("CONF", min_value=0, max_value=100, format="%d%%"),
            "VALUE": st.column_config.NumberColumn("VALUE", format="%.1fB"),
        }, use_container_width=True, hide_index=True, height=700)
    with col_news:
        st.markdown("<h2 style='color:#ff4d4d; font-family:Orbitron; font-size: 18px;'>💡 LIVE INTEL STREAM</h2>", unsafe_allow_html=True)
        for item in news_feed[:15]:
            # KOREKSI DISINI: Membuat link dinamis ke Google Search berdasarkan judul berita
            search_q = urllib.parse.quote(item['NEWS'])
            google_link = f"https://www.google.com/search?q={search_q}"
            
            st.markdown(f'''
                <div class="news-box">
                    <div class="news-topic-header">{item["TOPIC"]}</div>
                    <div class="news-text">
                        <a href="{google_link}" target="_blank">{item["NEWS"]}</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
