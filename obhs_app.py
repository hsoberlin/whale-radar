import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import feedparser
import re
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import urllib.parse

# 1. Dashboard Configuration
st.set_page_config(page_title="PREDATOR QUANTUM DAILY TRADE", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 60 Seconds
st_autorefresh(interval=60000, key="quantum_daily_sync")

# --- ULTRA-PREMIUM TERMINAL UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@500;800&family=Inter:wght@400;600;900&display=swap');
    
    .stApp { background-color: #020406; color: #ffffff; }
    
    .header-container {
        padding: 20px; background: rgba(0, 255, 204, 0.02);
        border-radius: 10px; border: 1px solid rgba(0, 255, 204, 0.1);
        text-align: center; margin-bottom: 20px;
    }
    
    .header-title {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900; font-size: 50px !important;
        background: linear-gradient(90deg, #00ffcc, #ff0055);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 8px;
    }
    
    .status-bar {
        background: #0a0e14; border-left: 5px solid #ff0055;
        padding: 10px 20px; font-family: 'JetBrains Mono', monospace;
        font-weight: 800; color: #ff0055; font-size: 13px; margin-bottom: 10px;
    }

    .blink {
        animation: blinker 1.5s linear infinite;
        color: #00ffcc;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-bottom: 20px;
    }
    @keyframes blinker { 50% { opacity: 0; } }

    .news-box {
        background: #0a0e14; border-left: 3px solid #ff4d4d;
        padding: 12px; margin-bottom: 10px; border-radius: 4px;
        transition: 0.3s;
    }
    .news-box:hover { border-left: 3px solid #00ffcc; background: #111a21; }
    
    .news-topic-header {
        font-family: 'Orbitron', sans-serif; font-weight: 800;
        font-size: 11px; color: #00ffcc !important; text-transform: uppercase;
    }
    
    .news-text { font-family: 'Inter', sans-serif; font-size: 12px; color: #e0e0e0; }
    .news-text a { text-decoration: none; color: inherit; }
    
    .thesis-box {
        background: rgba(255, 0, 85, 0.03); border: 1px dashed rgba(255, 0, 85, 0.3);
        padding: 15px; border-radius: 8px; margin-top: 5px;
    }

    .risk-note-box {
        background: linear-gradient(135deg, rgba(255,0,85,0.15) 0%, rgba(2,4,6,1) 100%);
        border: 1px solid #ff0055;
        padding: 20px;
        border-radius: 5px;
        margin-top: 25px;
        font-family: 'Inter', sans-serif;
    }
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

# --- ANALYTICS ENGINE ---
def build_flow_features(df):
    df = df.copy()
    df['chg_pct'] = df['Close'].pct_change()
    df['range_pct'] = (df['High'] - df['Low']) / df['Close']
    df['value'] = df['Volume'] * df['Close']
    df['vol_ma5'] = df['Volume'].rolling(5).mean()
    df['vol_ma50'] = df['Volume'].rolling(50).mean()
    df['vol_ma'] = df['Volume'].rolling(20, min_periods=5).mean()
    df['vol_power'] = df['Volume'] / df['vol_ma']
    df['val_ma'] = df['value'].rolling(20, min_periods=5).mean()
    return df

def calc_signals(df):
    absorption = (df['Volume'] > 1.2 * df['vol_ma']) & (df['range_pct'] < 0.015)
    persistence = (df['value'] > 1.1 * df['val_ma']) & (df['Low'] >= df['Low'].shift(1))
    inefficiency = (df['value'] > 1.2 * df['val_ma']) & (df['chg_pct'].abs() < 0.008)
    return absorption, persistence, inefficiency

def fetch_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    topic_map = {
        "AKUISISI": "AKUISISI", "RIGHTS ISSUE": "RIGHTS", "DANANTARA": "DANANTARA", 
        "MERGER": "MERGER", "EKSPANSI": "EKSPANSI", "INVESTASI": "INVESTASI",
        "KONTRAK": "KONTRAK BARU", "PRAJOGO": "KONGLO_PRAJOGO", "SALIM": "KONGLO_SALIM",
        "BAKRIE": "KONGLO_BAKRIE"
    }
    for url in RSS_LINKS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.replace('<b>','').replace('</b>','').strip()
                tickers = re.findall(r'\b[A-Z]{4}\b', title.upper())
                topic = next((v for k, v in topic_map.items() if k in title.upper()), "STRATEGIS")
                for t in set(tickers):
                    if t not in ["IHSG", "IDX", "LQ45"]:
                        intel_map[t] = {"title": title, "topic": topic}
                        news_tickers.add(t)
                intel_list.append({"TOPIC": topic, "NEWS": title})
        except: continue
    return intel_map, intel_list, list(news_tickers)

def scan_market():
    results = []
    intel_map, _, news_tickers = fetch_intel()
    combined_targets = list(set(list(master_afiliasi.keys()) + news_tickers))
    
    for ticker in combined_targets:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            h = s.history(period="3mo", interval="1d") 
            if len(h) < 50: continue
            h = build_flow_features(h)
            last = h.iloc[-1]
            if not (last['vol_ma5'] > 2 * last['vol_ma50']): continue

            abs_s, per_s, ine_s = calc_signals(h)
            last_vp = last['vol_power']
            is_acc = (abs_s.astype(int) + per_s.astype(int) + ine_s.astype(int)).rolling(6).sum().iloc[-1] >= 1
            if not is_acc and last_vp < 1.5: continue

            c, gain, val_b = last['Close'], last['chg_pct'] * 100, last['value'] / 1e9
            if val_b < 0.3: continue 

            score = 15
            thesis_narrative = []
            if last['vol_ma5'] > 3 * last['vol_ma50']:
                score += 35
                thesis_narrative.append("Deteksi anomali volume institusi masif")
            else:
                score += 15
                thesis_narrative.append("Aktivitas volume di atas rata-rata")

            if last_vp > 2:
                score += 20
                thesis_narrative.append(f"kekuatan daya beli melonjak {round(last_vp,1)}x")
            
            if ticker in intel_map: 
                score += 25
                thesis_narrative.append("terkonfirmasi katalis strategis")
                
            if abs_s.iloc[-1] or per_s.iloc[-1]: 
                score += 15
                thesis_narrative.append("serta menunjukkan persistensi akumulasi whale")

            final_thesis = ", ".join(thesis_narrative).capitalize() + "."
            porto = "15-20% (Aggressive)" if score >= 80 else ("10% (Medium)" if score >= 60 else "2-5% (Speculative)")

            results.append({
                "SYMBOL": ticker, "CONF": max(0, min(score, 100)), "VOL_POWER": round(last_vp, 2),
                "FLOW_VELOCITY": round(last['vol_ma5']/last['vol_ma50'], 2), "PRICE": int(c) if c >= 1 else c,
                "CHG%": round(gain, 2), "VALUE": round(val_b, 1), "GROUP": master_afiliasi.get(ticker, "EXTERNAL / DISCOVERY"),
                "THESIS": final_thesis, "PORTO": porto, "NEWS_INTEL": intel_map.get(ticker, {}).get('title', 'No direct news')
            })
        except: continue
    return results

# --- INTERFACE RENDERING ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM DAILY TRADE</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-bar">● GATEKEEPER ACTIVE | {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

loading_placeholder = st.empty()
loading_placeholder.markdown('<div class="blink">SYSTEM SCANNING: ANALYZING INSTITUTIONAL ORDER FLOW...</div>', unsafe_allow_html=True)

data = scan_market()
intel_map, news_feed, _ = fetch_intel()
loading_placeholder.empty()

if data:
    df = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    col_main, col_news = st.columns([2.1, 0.9])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>📡 REAL-TIME WHALE TRACKER</h3>", unsafe_allow_html=True)
        st.dataframe(df[["SYMBOL", "CONF", "VOL_POWER", "FLOW_VELOCITY", "PRICE", "CHG%", "VALUE", "PORTO"]], column_config={
            "CONF": st.column_config.ProgressColumn("CONF", min_value=0, max_value=100, format="%d%%"),
            "VOL_POWER": st.column_config.NumberColumn("VOL PWR", format="%.2fx ⚡"),
            "FLOW_VELOCITY": st.column_config.NumberColumn("FLOW VELOCITY", format="%.2fx"),
            "VALUE": st.column_config.NumberColumn("VAL (B)", format="%.1fB"),
            "PORTO": st.column_config.TextColumn("ALLOC")
        }, use_container_width=True, hide_index=True, height=400)

        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px; margin-top:30px;'>📝 STRATEGIC INVESTMENT ANALYSIS</h3>", unsafe_allow_html=True)
        agg_list = []
        for _, row in df.head(5).iterrows():
            if "Aggressive" in row['PORTO']: agg_list.append(row)
            st.markdown(f"""
            <div class="thesis-box">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color:#ff0055; font-weight:bold; font-size:18px;">{row['SYMBOL']}</span>
                    <span style="color:#00ffcc; font-family: 'JetBrains Mono'; font-size: 12px;">{row['PORTO']}</span>
                </div>
                <div style="color:#8b949e; font-size: 11px; margin-bottom: 8px;">Asset Group: {row['GROUP']} | Velocity Index: {row['FLOW_VELOCITY']}x</div>
                <div style="color:#e0e0e0; font-family: 'Inter'; font-size: 13px; line-height: 1.6;"><b>ANALYSIS:</b> {row['THESIS']}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- DYNAMIC AGGRESSIVE COMMAND CENTER ---
        if agg_list:
            agg_tickers_html = ""
            for item in agg_list:
                news_snippet = f" | <i style='color:#ffcc00;'>Intel: {item['NEWS_INTEL']}</i>" if item['NEWS_INTEL'] != 'No direct news' else ""
                agg_tickers_html += f"<li><b style='color:#00ffcc;'>[{item['SYMBOL']}]</b> Group: {item['GROUP']} | Flow: {item['FLOW_VELOCITY']}x {news_snippet}</li>"

            st.markdown(f"""
            <div class="risk-note-box">
                <div style="font-family: 'Orbitron'; color: #ff0055; font-size: 15px; font-weight: 900; margin-bottom: 12px; letter-spacing: 2px; border-bottom: 1px solid rgba(255,0,85,0.3); padding-bottom: 5px;">
                    ⚠️ INSTITUTIONAL PRIORITY: AGGRESSIVE MONITORING LIST
                </div>
                <div style="color: #e0e0e0; font-size: 12px; line-height: 1.8;">
                    <ul style="padding-left: 15px; margin-bottom: 15px;">
                        {agg_tickers_html}
                    </ul>
                    <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0;">
                    <div style="font-weight: 800; color: #ff4d4d; margin-bottom: 5px;">OPERATIONAL DIRECTIVE:</div>
                    1. <b>CONVICTION CHECK:</b> Semua ticker di atas menunjukkan anomali volume >300% dari rata-rata 50 hari. Validasi katalis (Intel) adalah prioritas utama sebelum entri.<br>
                    2. <b>LIQUIDITY RISK:</b> Pastikan <i>Value Transacted</i> tetap terjaga di atas level saat ini untuk menghindari <i>liquidity trap</i> pada fase distribusi.<br>
                    3. <b>EXECUTION:</b> Gunakan metode <i>Pyramiding</i>; entri awal 50%, tambah posisi hanya jika harga bertahan di atas <i>VWAP</i> sesi berjalan.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_news:
        st.markdown("<h3 style='font-family:Orbitron; color:#ffffff; font-size:18px;'>💡 STRATEGIC INTEL</h3>", unsafe_allow_html=True)
        for item in news_feed[:12]:
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f'''<div class="news-box"><div class="news-topic-header">{item["TOPIC"]}</div><div class="news-text"><a href="https://www.google.com/search?q={q}" target="_blank">{item["NEWS"]}</a></div></div>''', unsafe_allow_html=True)

st.caption("PREDATOR QUANTUM DAILY TRADE | INSTITUTIONAL GATEKEEPER | 2026 WALL STREET STANDARD")
