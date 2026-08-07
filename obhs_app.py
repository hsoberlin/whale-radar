import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import feedparser
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import urllib.parse
from collections import Counter

# --- 1. DASHBOARD CONFIGURATION ---
st.set_page_config(page_title="QUANTUM PRO - TJL ENGINE", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 5 Menit (Sesuai interval chart intraday)
st_autorefresh(interval=300000, key="quantum_intraday_sync")

# --- 2. ULTRA-PREMIUM TERMINAL UI (STABLE DARK THEME) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@500;800&family=Inter:wght@400;600;900&display=swap');
    
    .stApp { background-color: #020406; color: #ffffff; }
    
    /* Header Styling */
    .header-container {
        padding: 15px; background: rgba(0, 255, 204, 0.02);
        border-radius: 10px; border: 1px solid rgba(0, 255, 204, 0.1);
        text-align: center; margin-bottom: 20px;
    }
    .header-title {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900; font-size: 35px !important;
        background: linear-gradient(90deg, #00ffcc, #ff0055);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 4px;
    }
    
    /* Pixel Box for TJL Metrics */
    .pixel-container {
        display: flex; gap: 5px; margin-bottom: 5px;
        background: #0a0e14; padding: 5px; border-radius: 5px; border: 1px solid #333;
    }
    .pixel-metric {
        flex: 1; text-align: center; font-family: 'JetBrains Mono';
    }
    .pixel-title { font-size: 8px; color: #888; display: block; margin-bottom: 2px; }
    .pixel-value-up { color: #00ffcc; font-weight: 900; font-size: 12px; text-shadow: 0 0 5px rgba(0,255,204,0.5); }
    .pixel-value-down { color: #ff0055; font-weight: 900; font-size: 12px; text-shadow: 0 0 5px rgba(255,0,85,0.5); }
    .pixel-value-neutral { color: #ffd166; font-weight: 900; font-size: 12px; }
    
    /* Thesis Box */
    .thesis-box {
        background: rgba(2, 20, 20, 0.6); 
        border-left: 2px solid #00ffcc; border-right: 1px solid #333;
        border-top: 1px solid #333; border-bottom: 1px solid #333;
        padding: 12px; border-radius: 4px; margin-top: 8px; 
        font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.5; color: #cccccc;
    }
    .thesis-header {
        font-family: 'Orbitron'; font-size: 10px; color: #00ffcc; margin-bottom: 5px; letter-spacing: 1px;
    }
    
    /* News Box */
    .news-scroll-box { max-height: 600px; overflow-y: auto; }
    .news-box {
        background: #0a0e14; border-left: 3px solid #ff4d4d;
        padding: 8px; margin-bottom: 8px; border-radius: 4px; transition: 0.3s;
    }
    .news-box:hover { border-left: 3px solid #00ffcc; background: #111a21; }
    .news-topic-header { font-family: 'Orbitron'; font-size: 9px; color: #00ffcc; font-weight:bold;}
    .news-text { font-family: 'Inter', sans-serif; font-size: 11px; color: #e0e0e0; }
    .news-text a { text-decoration: none; color: inherit; }

    /* Blink Animation */
    @keyframes blinker { 50% { opacity: 0.4; color: #00ffcc; } }
    .blink { 
        animation: blinker 0.8s linear infinite; 
        font-family: 'Orbitron'; font-size: 14px; color: #ff0055; 
        text-align: center; letter-spacing: 2px; margin: 20px 0;
    }

    /* FORCED DARK TABLE STYLE */
    [data-testid="stDataFrame"] { border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #0a0e14 !important; color: #00ffcc !important;
        font-family: 'Orbitron' !important; font-weight: 800 !important;
        border-bottom: 1px solid #444 !important;
    }
    [data-testid="stDataFrame"] div[role="gridcell"] {
        background-color: #020406 !important; color: #e0e0e0 !important;
        font-family: 'JetBrains Mono' !important; border-bottom: 1px solid #222 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE KONGLOMERASI & SEKTORAL BEI (EXPANDED) ---
master_afiliasi = {
    # BARITO PACIFIC GROUP
    "BREN": "PRAJOGO PANGESTU", "TPIA": "PRAJOGO PANGESTU", "CUAN": "PRAJOGO PANGESTU", 
    "BRPT": "PRAJOGO PANGESTU", "PTRO": "PRAJOGO PANGESTU", "CGAS": "PRAJOGO PANGESTU",
    
    # BAKRIE GROUP
    "BUMI": "BAKRIE & SALIM", "BRMS": "BAKRIE GROUP", "ENRG": "BAKRIE GROUP", 
    "DEWA": "BAKRIE GROUP", "BNBR": "BAKRIE GROUP", "VKTR": "BAKRIE GROUP",
    
    # SALIM GROUP
    "AMMN": "SALIM & PANIGORO", "INDF": "SALIM GROUP", "ICBP": "SALIM GROUP", 
    "LSIP": "SALIM GROUP", "META": "SALIM GROUP", "ROTI": "SALIM GROUP",
    
    # SINAR MAS GROUP
    "DSSA": "SINAR MAS", "BSDE": "SINAR MAS", "INKP": "SINAR MAS", 
    "TKIM": "SINAR MAS", "SMAR": "SINAR MAS", "FREN": "SINAR MAS",
    
    # AGUAN / SEDAYU GROUP
    "PANI": "AGUAN (PIK 2)", "ASRI": "AGUAN GROUP", "BSBK": "AGUAN GROUP",
    
    # ADARO / THOHIR & SANDIAGA
    "ADRO": "BOY THOHIR", "ADMR": "BOY THOHIR", "ESSA": "BOY THOHIR",
    "MBMA": "BOY THOHIR", "MDKA": "BOY THOHIR (SANDI)", "SRTG": "SANDIAGA UNO",
    
    # MNC & LIPPO GROUP
    "KPIG": "MNC GROUP", "BHIT": "MNC GROUP", "MNCN": "MNC GROUP", 
    "BMTR": "MNC GROUP", "LPKR": "LIPPO GROUP", "LPPF": "LIPPO GROUP", 
    "SILO": "LIPPO GROUP", "MLPL": "LIPPO GROUP",
    
    # OTHER TYCOONS
    "DRMA": "TP RACHMAT", "TAPG": "TP RACHMAT", "ASSA": "TP RACHMAT",
    "RAJA": "HAPPY HAPSORO", "CBRE": "HAPPY HAPSORO", "PSAB": "HAPPY HAPSORO",
    "JIHD": "TOMY WINATA", "SCBD": "TOMY WINATA",
    
    # TECH & DIGITAL
    "GOTO": "GOTO / TECH", "ARTO": "JAGO (GOTO)", "BUKA": "BUKALAPAK", 
    "EMTK": "EMTEK GROUP", "SCMA": "EMTEK GROUP", "WIRG": "TECH / METAVERSE",
    
    # STATE OWNED ENTERPRISES (BUMN)
    "BBRI": "STATE OWNED", "BMRI": "STATE OWNED", "BBNI": "STATE OWNED", 
    "BBTN": "STATE OWNED", "BRIS": "STATE OWNED", 
    "TLKM": "STATE OWNED", "ANTM": "STATE OWNED", "PGAS": "STATE OWNED",
    "PTBA": "STATE OWNED", "TINS": "STATE OWNED", "SMGR": "STATE OWNED", 
    "JSMR": "STATE OWNED", "PTPP": "STATE OWNED", "ADHI": "STATE OWNED",

    # TOP PRIVATE FINANCIALS, CONSUMER, & ENERGY
    "BBCA": "HARTONO / DJARUM", "BDMN": "FINANCE", "PNBN": "FINANCE",
    "UNVR": "CONSUMER", "MYOR": "CONSUMER", "AMRT": "CONSUMER", "MIDI": "CONSUMER",
    "KLBF": "HEALTHCARE", "ACES": "RETAIL", "MAPI": "RETAIL",
    "ITMG": "ENERGY", "UNTR": "ASTRA GROUP", "INDY": "ENERGY", 
    "HRUM": "ENERGY", "AKRA": "ENERGY", "DOID": "ENERGY",
    "INCO": "BASIC MATERIALS", "NCKL": "BASIC MATERIALS"
}

RSS_LINKS = [
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640953919"
]

# --- 4. CATALYST INTEL FETCHER ---
def fetch_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    for url in RSS_LINKS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.replace('<b>','').replace('</b>','').strip()
                # REGEX: Ekstrak semua kata 4 huruf kapital sebagai Ticker Saham
                tickers = re.findall(r'\b[A-Z]{4}\b', title.upper())
                for t in set(tickers):
                    if t not in ["IHSG", "IDX", "LQ45"]:
                        intel_map[t] = {"title": title, "topic": "CATALYST"}
                        news_tickers.add(t)
                intel_list.append({"TOPIC": "NEWS ALERT", "NEWS": title})
        except: continue
    return intel_map, intel_list, list(news_tickers)

# --- 5. DUAL-TIMEFRAME TJL SCANNER ENGINE ---
def scan_tjl_market():
    results = []
    intel_map, _, news_tickers = fetch_intel()
    
    # Gabungkan semua ticker master dan ticker yang masuk berita hari ini
    combined_targets = list(set(list(master_afiliasi.keys()) + news_tickers))
    detected_groups = []

    for ticker in combined_targets:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            
            # STAGE 1: DAILY FILTER (SMA 200 & YESTERDAY LEVELS)
            df_d = s.history(period="1y", interval="1d")
            if len(df_d) < 200: continue
            
            df_d['SMA200'] = df_d['Close'].rolling(200).mean()
            if pd.isna(df_d['SMA200'].iloc[-2]): continue
            
            prev_close = df_d['Close'].iloc[-2]
            prev_high = df_d['High'].iloc[-2]
            sma200 = df_d['SMA200'].iloc[-2]
            today_open = df_d['Open'].iloc[-1]
            
            # TJL Rule 1: Uptrend Check (Close kemarin > SMA200)
            if prev_close < sma200: continue
            
            # TJL Rule 2: Pre-Market Gap Up >= 2% (Scanner A)
            gap_pct = ((today_open - prev_close) / prev_close) * 100
            if gap_pct < 2.0: continue
            
            # STAGE 2: INTRADAY 5-MINUTES (Scanner B)
            df_intra = s.history(period="1d", interval="5m")
            if df_intra.empty or len(df_intra) < 2: continue
            
            # Proxy for Pre-Market High / Opening Range High (First 30 mins = 6 candles)
            # Pastikan dataframe intraday tidak kurang dari 6 sebelum memotong
            orh_limit = min(6, len(df_intra))
            orh = df_intra['High'].iloc[:orh_limit].max() 
            curr_price = df_intra['Close'].iloc[-1]
            hod = df_intra['High'].max()
            
            # Volume Price Analysis (VPA)
            avg_vol_5m = df_intra['Volume'].mean()
            last_vol = df_intra['Volume'].iloc[-1]
            vol_spike = last_vol / avg_vol_5m if avg_vol_5m > 0 else 0
            
            score = 50
            thesis_points = []
            
            thesis_points.append(f"🚀 <b>SCANNER A (PRE-MARKET):</b> Lolos filter! Gap Up <b>+{gap_pct:.2f}%</b>.")
            thesis_points.append(f"📈 <b>MACRO TREND:</b> Valid Uptrend (Harga di atas SMA 200).")
            
            # Breakout Logic Validation
            is_ydh_break = curr_price > prev_high
            is_orh_break = curr_price > orh
            is_hod_break = curr_price >= hod * 0.995 # Toleransi dekat HOD
            
            if is_ydh_break:
                score += 20
                thesis_points.append(f"🔥 <b>BREAKOUT YDH:</b> Berhasil menembus level tertinggi kemarin (Rp {prev_high:,.0f}).")
            
            if is_orh_break:
                score += 15
                thesis_points.append(f"⚡ <b>BREAKOUT ORH:</b> Momentum menguat menembus Opening Range High (Rp {orh:,.0f}).")
                
            if is_hod_break and vol_spike > 1.5:
                score += 15
                thesis_points.append(f"🌊 <b>VPA TRIGGER:</b> Volume meledak {vol_spike:.1f}x di level HOD. Eksekusi aktif!")
            
            # CATALYST CHECK INJECTION
            has_news = ticker in intel_map
            if has_news:
                score += 10 # Tambahan skor konfirmasi dari katalis fundamental
                thesis_points.append(f"📰 <b>CATALYST DETECTED:</b> {intel_map[ticker]['title'][:65]}...")
                
            final_thesis = "<br>".join(thesis_points)
            porto = "TJL EXECUTE (Aggressive)" if score >= 80 else ("MONITOR (Medium)" if score >= 65 else "WAITING")
            
            # Risk Management Generation
            stop_loss = orh if curr_price > orh else today_open
            risk_pct = round(abs(curr_price - stop_loss) / curr_price * 100, 1)
            target_price = curr_price + ((curr_price - stop_loss) * 2) # Risk to Reward 1:2
            
            plan_html = (
                f"<div style='margin-top:8px; padding:5px; border-top:1px dashed #333; font-family:JetBrains Mono; font-size:11px;'>"
                f"🛡️ <b>PLAN:</b> BUY {int(curr_price)} | "
                f"<span style='color:#ff4d4d'>STOP {int(stop_loss)} (-{risk_pct}%)</span> | "
                f"<span style='color:#00ffcc'>TARGET {int(target_price)}</span>"
                f"</div>"
            )
            final_thesis += plan_html
            
            # Final Assignment Filtering
            if score >= 65:
                group_name = master_afiliasi.get(ticker, "NEWS / EXTERNAL")
                if group_name != "NEWS / EXTERNAL": detected_groups.append(group_name)
                
                results.append({
                    "SYMBOL": ticker, "CONF": min(score, 100), 
                    "GAP_PCT": float(gap_pct), "VOL_SPIKE": float(vol_spike), 
                    "PRICE": int(curr_price), "YDH": int(prev_high), "ORH": int(orh),
                    "GROUP": group_name, "THESIS": final_thesis, "PORTO": porto,
                    "RAW_INTRA": df_intra, "TJL_STATUS": "HOD BREAKOUT" if is_hod_break else "CONSOLIDATION"
                })
        except: continue
        
    # Identifikasi Arus Rotasi Konglomerat
    pulse = "MIXED INTRADAY FLOW"
    if detected_groups:
        counts = Counter(detected_groups)
        most_common = counts.most_common(1)[0]
        if most_common[1] >= 2: # Jika ada >= 2 emiten dari 1 grup yang jalan bareng
            pulse = f"ROTATION: {most_common[0]} GROUP DETECTED"
        
    return results, pulse

# --- 6. INTRADAY PIXEL CHART (5-MINUTE) ---
def render_intraday_chart(target):
    df = target['RAW_INTRA']
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.75, 0.25])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#00ffcc', decreasing_line_color='#ff0055', name="Price"), row=1, col=1)
    
    # Yesterday High (YDH) - Red Dashed
    fig.add_hline(y=target['YDH'], line_dash="dash", line_color="#ff0055", line_width=2, 
                  annotation_text="Yesterday High (YDH)", annotation_position="top right", 
                  annotation_font_color="#ff0055", row=1, col=1)
    
    # Opening Range High (ORH) - Yellow Dashed
    fig.add_hline(y=target['ORH'], line_dash="dash", line_color="#ffd166", line_width=2, 
                  annotation_text="Opening Range High (ORH)", annotation_position="bottom right", 
                  annotation_font_color="#ffd166", row=1, col=1)

    # Volume Profile
    colors_vol = ['#00ffcc' if r >= o else '#ff0055' for r, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='Volume'), row=2, col=1)

    title_text = f"<b style='color: white; font-size: 20px;'>{target['SYMBOL']} (5-Min Chart)</b> <span style='color: #00ffcc; font-size:12px;'>| STATUS: {target['TJL_STATUS']}</span>"
    
    fig.update_layout(
        template="plotly_dark", height=450, 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=50, b=10), title=dict(text=title_text, x=0.02, y=0.96)
    )
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    return fig

# --- 7. INTERFACE RENDERING LOGIC ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM PRO - TJL EDITION</div></div>', unsafe_allow_html=True)

loading_placeholder = st.empty()
loading_placeholder.markdown('<div class="blink">EXECUTING SCANNER A & B: INTRADAY TJL ENGINE...</div>', unsafe_allow_html=True)

# Eksekusi Pemindaian
data, market_pulse = scan_tjl_market()
_, news_feed, _ = fetch_intel()
loading_placeholder.empty()

st.markdown(f"<div style='text-align:center; margin-bottom:20px; color:#00ffcc; font-family:Orbitron; letter-spacing:2px; font-size:14px;'>📡 INTRADAY PULSE: {market_pulse}</div>", unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    col_main, col_news = st.columns([3, 1])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>⚡ TJL BREAKOUT SCANNER (REAL-TIME)</h3>", unsafe_allow_html=True)
        st.dataframe(df_display[["SYMBOL", "CONF", "GAP_PCT", "VOL_SPIKE", "PRICE", "YDH", "TJL_STATUS", "PORTO"]], column_config={
            "CONF": st.column_config.ProgressColumn("CONF", min_value=0, max_value=100, format="%d%%"),
            "GAP_PCT": st.column_config.NumberColumn("GAP UP", format="%.2f%%"),
            "VOL_SPIKE": st.column_config.NumberColumn("VOL PWR", format="%.1fx 🌊"),
            "PRICE": st.column_config.NumberColumn("PRICE (Rp)"),
            "YDH": st.column_config.NumberColumn("YDH (Rp)"),
            "TJL_STATUS": st.column_config.TextColumn("ACTION STATE"),
            "PORTO": st.column_config.TextColumn("ALLOCATION")
        }, use_container_width=True, hide_index=True, height=250)

        # Ambil maksimal 4 target teratas untuk divisualisasikan
        top_targets = df_display.head(4).to_dict('records')
        
        if top_targets:
            st.markdown("<h3 style='font-family:Orbitron; color:#00ffcc; font-size:18px; margin-top:20px;'>📊 INTRADAY BATTLEFIELD (5-MINUTES)</h3>", unsafe_allow_html=True)
            
            # Rendering Grid 2 Kolom untuk Chart
            for i in range(0, len(top_targets), 2):
                cols = st.columns(2) 
                batch = top_targets[i:i+2] 
                for idx, target in enumerate(batch):
                    with cols[idx]:
                        css_status = "pixel-value-up" if "BREAKOUT" in target['TJL_STATUS'] else "pixel-value-neutral"
                        st.markdown(f"""
                        <div class="pixel-container">
                            <div class="pixel-metric"><span class="pixel-title">GAP UP</span><span class="pixel-value-up">+{target['GAP_PCT']:.2f}%</span></div>
                            <div class="pixel-metric"><span class="pixel-title">VOL SURGE</span><span class="pixel-value-up">{target['VOL_SPIKE']:.1f}x</span></div>
                            <div class="pixel-metric"><span class="pixel-title">VS YDH</span><span class="{ 'pixel-value-up' if target['PRICE'] > target['YDH'] else 'pixel-value-down' }">{'BREAK' if target['PRICE'] > target['YDH'] else 'REJECT'}</span></div>
                            <div class="pixel-metric"><span class="pixel-title">MOMENTUM</span><span class="{css_status}">{target['TJL_STATUS']}</span></div>
                        </div>""", unsafe_allow_html=True)
                        
                        fig = render_intraday_chart(target)
                        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px; margin-top:10px;'>📝 ALGORITHMIC EXECUTION THESIS</h3>", unsafe_allow_html=True)
        for row in top_targets:
            st.markdown(f"""
            <div class="thesis-box">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color:#ff0055; font-weight:bold; font-size:14px;">{row['SYMBOL']}</span>
                    <span style="color:#00ffcc; font-family: 'JetBrains Mono'; font-size: 10px;">{row['PORTO']}</span>
                </div>
                <div class="thesis-header">TJL ENTRY LOGIC:</div>
                <div style="color:#e0e0e0;">{row['THESIS']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_news:
        st.markdown("<h3 style='font-family:Orbitron; color:#ffffff; font-size:18px;'>💡 STRATEGIC INTEL</h3>", unsafe_allow_html=True)
        st.markdown('<div class="news-scroll-box">', unsafe_allow_html=True)
        # Tampilkan 20 berita terbaru
        for item in news_feed[:20]: 
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f'''
            <div class="news-box">
                <div class="news-topic-header">{item["TOPIC"]}</div>
                <div class="news-text"><a href="https://www.google.com/search?q={q}" target="_blank">{item["NEWS"]}</a></div>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Scanner sedang berjalan namun belum ada saham yang lolos kriteria agresif TJL hari ini. Silakan tunggu update volume berikutnya.")

st.caption("PREDATOR QUANTUM PRO - TJL EDITION | INTRADAY SCALPING ENGINE")
