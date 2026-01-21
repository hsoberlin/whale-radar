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

# 1. Dashboard Configuration
st.set_page_config(page_title="PREDATOR QUANTUM PRO | MTI REVISED", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 5 Minutes (300000ms)
st_autorefresh(interval=300000, key="quantum_daily_sync")

# --- ULTRA-PREMIUM TERMINAL UI (STABLE DARK THEME) ---
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
        font-weight: 900; font-size: 36px !important;
        background: linear-gradient(90deg, #00ffcc, #ff0055);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 4px;
    }
    .header-subtitle {
        font-family: 'JetBrains Mono'; font-size: 10px; color: #888; letter-spacing: 2px;
    }
    
    /* Macro Strip */
    .macro-strip {
        display: flex; justify-content: space-around; background: #0a0e14;
        padding: 10px; border-radius: 5px; border: 1px solid #333; margin-bottom: 20px;
    }
    .macro-item { font-family: 'JetBrains Mono'; font-size: 12px; text-align: center; }
    .macro-label { font-size: 9px; color: #888; display: block; margin-bottom: 2px; }
    .macro-val-up { color: #00ffcc; font-weight: bold; }
    .macro-val-down { color: #ff0055; font-weight: bold; }

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
    
    /* Tag Labels */
    .tag-trend { background: #004d40; color: #00ffcc; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; border: 1px solid #00ffcc; }
    .tag-bottom { background: #4a148c; color: #ea80fc; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; border: 1px solid #ea80fc; }
    
    /* News Box */
    .news-scroll-box { max-height: 500px; overflow-y: auto; }
    .news-box {
        background: #0a0e14; border-left: 3px solid #ff4d4d;
        padding: 6px; margin-bottom: 6px; border-radius: 4px; transition: 0.3s;
    }
    .news-box:hover { border-left: 3px solid #00ffcc; background: #111a21; }
    .news-topic-header { font-family: 'Orbitron'; font-size: 9px; color: #00ffcc; font-weight:bold;}
    .news-text { font-family: 'Inter', sans-serif; font-size: 10px; color: #e0e0e0; }
    .news-text a { text-decoration: none; color: inherit; }

    /* Blink Animation */
    @keyframes blinker { 50% { opacity: 0.4; color: #00ffcc; } }
    .blink { 
        animation: blinker 0.8s linear infinite; 
        font-family: 'Orbitron'; font-size: 14px; color: #ff0055; 
        text-align: center; letter-spacing: 2px; margin: 20px 0;
    }

    /* Table Override */
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

# --- DATABASE ENGINE (GROUP AFILIASI) ---
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

# --- SECTOR MAPPING ---
SECTOR_MAP = {
    "BBCA": "FINANCE", "BBRI": "FINANCE", "BMRI": "FINANCE", "BBNI": "FINANCE",
    "BBTN": "FINANCE", "BRIS": "FINANCE", "ARTO": "FINANCE", "ADRO": "ENERGY", 
    "PTBA": "ENERGY", "ITMG": "ENERGY", "BYAN": "ENERGY", "HRUM": "ENERGY", 
    "MEDC": "ENERGY", "ELSA": "ENERGY", "PGAS": "ENERGY", "ANTM": "BASIC-MAT", 
    "MDKA": "BASIC-MAT", "INCO": "BASIC-MAT", "TINS": "BASIC-MAT", "MBMA": "BASIC-MAT", 
    "INKP": "BASIC-MAT", "TKIM": "BASIC-MAT", "SMGR": "BASIC-MAT", "INTP": "BASIC-MAT",
    "TPIA": "BASIC-MAT", "BRPT": "BASIC-MAT", "TLKM": "INFRA", "ISAT": "INFRA", 
    "EXCL": "INFRA", "JSMR": "INFRA", "TOWR": "INFRA", "ICBP": "CONSUMER", 
    "INDF": "CONSUMER", "UNVR": "CONSUMER", "MYOR": "CONSUMER", "AMRT": "CONSUMER",
    "BSDE": "PROPERTY", "CTRA": "PROPERTY", "SMRA": "PROPERTY", "PWON": "PROPERTY",
    "PANI": "PROPERTY", "GOTO": "TECH", "BUKA": "TECH", "EMTK": "TECH"
}

def get_sector(ticker):
    return SECTOR_MAP.get(ticker, "OTHERS")

RSS_LINKS = [
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640953919",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640956058",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/17720372188069162265"
]

# --- ROBUST MACRO CONTEXT (REVISED: BITCOIN REMOVED) ---
def fetch_macro_context():
    macro_data = {}
    try:
        # BITCOIN REMOVED FROM LIST
        tickers = ["^JKSE", "IDR=X", "CL=F", "GC=F"] 
        df = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=False)['Close']
        
        def safe_extract(col_part, name):
            try:
                cols = [c for c in df.columns if col_part in str(c)]
                if cols:
                    series = df[cols[0]].dropna()
                    if not series.empty:
                        now = series.iloc[-1]
                        prev = series.iloc[-2]
                        macro_data[name] = {"val": now, "chg": (now - prev)/prev*100}
            except: pass

        if not df.empty:
            safe_extract('^JKSE', 'IHSG')
            safe_extract('IDR=X', 'USDIDR')
            safe_extract('CL=F', 'OIL')
            safe_extract('GC=F', 'GOLD')
            
    except Exception: pass
    return macro_data

# --- ANALYTICS ENGINE ---
def build_flow_features(df):
    df = df.copy()
    df['chg_pct'] = df['Close'].pct_change()
    df['value'] = df['Volume'] * df['Close']
    
    # Volume MA
    df['vol_ma5'] = df['Volume'].rolling(5).mean()
    df['vol_ma50'] = df['Volume'].rolling(50).mean()
    df['vol_ma20'] = df['Volume'].rolling(20, min_periods=5).mean()
    df['vol_power'] = df['Volume'] / df['vol_ma20']
    df['val_ma'] = df['value'].rolling(20, min_periods=5).mean()
    
    # Trend Analysis (MA20)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA20_Slope'] = df['MA20'] > df['MA20'].shift(1) # Is MA rising?
    df['Trend_State'] = np.where(df['Close'] > df['MA20'], "BULLISH", "BEARISH")
    
    # Stochastic
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    stoch_min = df['RSI'].rolling(14).min()
    stoch_max = df['RSI'].rolling(14).max()
    df['Stoch_K'] = 100 * (df['RSI'] - stoch_min) / (stoch_max - stoch_min)
    df['Stoch_K'] = df['Stoch_K'].fillna(50)
    
    # Flow Sentiment (Proxy)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    raw_money_flow = typical_price * df['Volume']
    flow_dir = np.where(typical_price > typical_price.shift(1), 1, -1)
    df['Net_Flow'] = raw_money_flow * flow_dir
    df['Flow_State'] = np.where(df['Net_Flow'].rolling(5).sum() > 0, "INFLOW", "OUTFLOW")

    df['Buy_Sig'] = (df['Close'] > df['MA20']) & (df['Close'].shift(1) <= df['MA20'].shift(1)) & (df['Volume'] > df['vol_ma20'])
    
    return df

# --- ATR-BASED TRADE PLAN ---
def calculate_trade_plan(df):
    df = df.copy()
    df['TR'] = df[['High', 'Low', 'Close']].apply(lambda x: max(x['High']-x['Low'], abs(x['High']-x.name), abs(x['Low']-x.name)), axis=1) # Simplified TR
    df['ATR'] = df['TR'].rolling(14).mean()
    
    last_close = df['Close'].iloc[-1]
    last_atr = df['ATR'].iloc[-1] if not pd.isna(df['ATR'].iloc[-1]) else (last_close * 0.05)
    
    stop_loss = int(last_close - (2 * last_atr))
    risk = last_close - stop_loss
    target_price = int(last_close + (risk * 2.0))
    
    risk_pct = round((risk / last_close) * 100, 1)
    reward_pct = round(((target_price - last_close) / last_close) * 100, 1)
    
    return stop_loss, target_price, risk_pct, reward_pct

def fetch_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    topic_map = {
        "AKUISISI": "AKUISISI", "LABA": "EARNINGS", "RUGI": "EARNINGS", 
        "DIVIDEN": "DIVIDEN", "KONTRAK": "KONTRAK", "INVESTASI": "INVESTASI"
    }
    
    for url in RSS_LINKS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.replace('<b>','').replace('</b>','').strip()
                tickers = re.findall(r'\b[A-Z]{4}\b', title.upper())
                topic = "STRATEGIS"
                for k, v in topic_map.items():
                    if k in title.upper():
                        topic = v
                        break
                for t in set(tickers):
                    if t not in ["IHSG", "IDX", "LQ45"]:
                        intel_map[t] = {"title": title, "topic": topic}
                        news_tickers.add(t)
                intel_list.append({"TOPIC": topic, "NEWS": title})
        except: continue
    return intel_map, intel_list, list(news_tickers)

# --- SCANNER ENGINE (REVISED LOGIC: LIQUIDITY FILTER REMOVED) ---
def scan_market(macro_data):
    results = []
    intel_map, _, news_tickers = fetch_intel()
    combined_targets = list(set(list(master_afiliasi.keys()) + news_tickers))
    
    for ticker in combined_targets:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            h = s.history(period="6mo", interval="1d") 
            if len(h) < 60: continue
            
            h = build_flow_features(h)
            if h.iloc[-1].isnull().any(): continue
            
            last = h.iloc[-1]
            prev = h.iloc[-2]

            # ----------------------------------------------------
            # SCREENING GATE 1: LIQUIDITY FILTER (REMOVED)
            # ----------------------------------------------------
            # Note: Filter 5 Miliar dihapus sesuai request agar saham 
            # second liner tetap masuk walau pasar sepi.
            # if last['value'] < 5_000_000_000: continue

            # ----------------------------------------------------
            # SCREENING GATE 2: STRUCTURE CHECK
            # ----------------------------------------------------
            # Logic: Hanya terima saham UPTREND atau REVERSAL (Bottom)
            is_uptrend = last['Close'] > last['MA20']
            is_reversal = (last['Close'] < last['MA20']) and (last['Stoch_K'] < 20)
            
            if not (is_uptrend or is_reversal):
                continue

            # ----------------------------------------------------
            # SCREENING GATE 3: TRIGGER ACTION
            # ----------------------------------------------------
            # Logic: Tetap gunakan Volume Spike OR News sebagai pemicu
            is_vol_spike = last['vol_ma5'] > 1.2 * last['vol_ma50']
            has_news = ticker in intel_map
            
            if not (is_vol_spike or has_news):
                continue
            
            # ----------------------------------------------------
            # MTI SCORING SYSTEM (BASE = 10)
            # ----------------------------------------------------
            score = 10
            thesis_points = []
            strategy_tag = "TREND FOLLOWING" if is_uptrend else "BOTTOM FISHING"
            
            # 1. VOLUME SCORING (Max +40)
            if last['vol_power'] > 3.0:
                score += 40
                thesis_points.append(f"🌊 <b>WHALE ALERT:</b> Volume ekstrem {last['vol_power']:.1f}x rata-rata.")
            elif last['vol_power'] > 1.2:
                score += 20
                thesis_points.append(f"💧 <b>ACCUMULATION:</b> Volume naik stabil di atas rata-rata.")
            
            # 2. TECHNICAL SCORING (Max +30)
            if is_uptrend:
                score += 20
                thesis_points.append("📈 <b>STRUCTURE:</b> Harga di atas MA20 (Bullish).")
            if last['MA20_Slope']: # MA20 Sloping Up
                score += 10
                thesis_points.append("🚀 <b>MOMENTUM:</b> Garis MA20 menanjak (Strong Trend).")
            if is_reversal:
                thesis_points.append("🎣 <b>REVERSAL:</b> Oversold (Stoch < 20) + Volume. Potensi pantulan.")

            # 3. NEWS SCORING (Max +20)
            if has_news:
                score += 20
                news_info = intel_map.get(ticker, {})
                thesis_points.append(f"📰 <b>NEWS:</b> {news_info.get('title')[:60]}...")
            
            # 4. MACRO CORRELATION
            oil_chg = macro_data.get('OIL', {}).get('chg', 0)
            if get_sector(ticker) == "ENERGY" and oil_chg > 0.5:
                thesis_points.append(f"🛢️ <b>OIL PLAY:</b> Didukung kenaikan harga minyak (+{oil_chg:.1f}%).")
            
            # EXECUTION PLAN
            stop_loss, target_price, risk_pct, reward_pct = calculate_trade_plan(h)
            
            plan_html = (
                f"<div style='margin-top:8px; padding:5px; border-top:1px dashed #333; font-family:JetBrains Mono; font-size:11px;'>"
                f"🛡️ <b>PLAN:</b> BUY {int(last['Close'])} | <span style='color:#ff4d4d'>SL {stop_loss} (-{risk_pct}%)</span> | "
                f"<span style='color:#00ffcc'>TP {target_price} (+{reward_pct}%)</span>"
                f"</div>"
            )
            thesis_points.append(plan_html)
            
            final_thesis = "<br>".join(thesis_points)
            porto = "HIGH CONVICTION" if score >= 70 else ("MODERATE" if score >= 50 else "SPECULATIVE")

            results.append({
                "SYMBOL": ticker, "CONF": max(0, min(score, 100)), 
                "VOL_POWER": round(last['vol_power'], 2),
                "PRICE": int(last['Close']), "CHG%": round(last['chg_pct']*100, 2),
                "VALUE": round(last['value']/1e9, 1), 
                "GROUP": master_afiliasi.get(ticker, "EXTERNAL"),
                "THESIS": final_thesis, "PORTO": porto, 
                "STRATEGY": strategy_tag,
                "RAW_DATA": h,
                "PIXEL_TREND": last['Trend_State'],
                "FLOW_STATE": last['Flow_State']
            })
        except: continue
        
    return results

def render_chart(target):
    df = target['RAW_DATA'].tail(50)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    # Price & MA20
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 name=target['SYMBOL'], increasing_line_color='#00ffcc', decreasing_line_color='#ff0055'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#ffff00', width=1), name='MA20'), row=1, col=1)
    
    # Volume
    colors_vol = ['#00ffcc' if r >= o else '#ff0055' for r, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='Volume'), row=2, col=1)
    
    # Stochastic
    fig.add_trace(go.Scatter(x=df.index, y=df['Stoch_K'], line=dict(color='#0088ff', width=2), name='Stoch K'), row=3, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="gray", row=3, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="gray", row=3, col=1)

    tag_color = "#00ffcc" if target['STRATEGY'] == "TREND FOLLOWING" else "#ea80fc"
    title_text = f"<b style='color: white; font-size: 16px;'>{target['SYMBOL']}</b> <span style='color:{tag_color}; font-size:12px;'>[{target['STRATEGY']}]</span>"
    
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), title=dict(text=title_text, x=0.02, y=0.96), showlegend=False)
    fig.update_xaxes(showticklabels=False, row=1, col=1); fig.update_xaxes(showticklabels=False, row=2, col=1)
    return fig

# --- INTERFACE RENDERING ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM PRO</div><div class="header-subtitle">MTI REVISED EDITION | SCREENER & SCORING PROTOCOL V2.1</div></div>', unsafe_allow_html=True)

macro_data = fetch_macro_context()
loading_placeholder = st.empty()
loading_placeholder.markdown('<div class="blink">SYSTEM INITIALIZING... SCANNING MARKET STRUCTURE...</div>', unsafe_allow_html=True)

data = scan_market(macro_data)
_, news_feed, _ = fetch_intel()
loading_placeholder.empty()

# MACRO STRIP
if macro_data:
    cols = st.columns(len(macro_data))
    html_macro = "<div class='macro-strip'>"
    for k, v in macro_data.items():
        color = "macro-val-up" if v['chg'] >= 0 else "macro-val-down"
        arrow = "▲" if v['chg'] >= 0 else "▼"
        html_macro += f"<div class='macro-item'><span class='macro-label'>{k}</span><br><span class='{color}'>{v['val']:.2f} ({arrow} {v['chg']:.2f}%)</span></div>"
    html_macro += "</div>"
    st.markdown(html_macro, unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    
    # METRICS SUMMARY
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("TOTAL SCREENED", len(df_display))
    col_m2.metric("AVG CONFIDENCE", f"{int(df_display['CONF'].mean())}%")
    trend_count = len(df_display[df_display['STRATEGY']=="TREND FOLLOWING"])
    col_m3.metric("MARKET REGIME", "BULLISH" if trend_count > len(df_display)/2 else "BEARISH")

    col_main, col_news = st.columns([3, 1])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>📡 ACTIVE OPPORTUNITIES</h3>", unsafe_allow_html=True)
        
        # TABLE
        st.dataframe(df_display[["SYMBOL", "STRATEGY", "CONF", "VOL_POWER", "PRICE", "CHG%", "VALUE", "PORTO"]], column_config={
            "STRATEGY": st.column_config.TextColumn("SETUP", width="medium"),
            "CONF": st.column_config.ProgressColumn("SCORE", min_value=0, max_value=100, format="%d"),
            "VOL_POWER": st.column_config.NumberColumn("VOL (xAvg)", format="%.1fx"),
            "VALUE": st.column_config.NumberColumn("VAL (B)", format="%.1fB"),
        }, use_container_width=True, hide_index=True, height=350)

        # CHARTS FOR TOP PICKS
        st.markdown("---")
        st.markdown("<h3 style='font-family:Orbitron; color:#00ffcc; font-size:18px;'>📊 TOP CONVICTION CHARTS</h3>", unsafe_allow_html=True)
        
        top_picks = df_display.head(4).to_dict('records')
        for i in range(0, len(top_picks), 2):
            cols = st.columns(2)
            batch = top_picks[i:i+2]
            for idx, target in enumerate(batch):
                with cols[idx]:
                    # Render Strategy Tag
                    tag_class = "tag-trend" if target['STRATEGY'] == "TREND FOLLOWING" else "tag-bottom"
                    st.markdown(f"<span class='{tag_class}'>{target['STRATEGY']}</span>", unsafe_allow_html=True)
                    
                    # Render Chart
                    fig = render_chart(target)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Render Thesis
                    st.markdown(f"""
                    <div class="thesis-box">
                        <div class="thesis-header">{target['GROUP']} | SCORE: {target['CONF']}</div>
                        {target['THESIS']}
                    </div>
                    """, unsafe_allow_html=True)

    with col_news:
        st.markdown("<h3 style='font-family:Orbitron; color:#ffffff; font-size:18px;'>💡 INTEL FEED</h3>", unsafe_allow_html=True)
        st.markdown('<div class="news-scroll-box">', unsafe_allow_html=True)
        for item in news_feed[:20]: 
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f'''<div class="news-box"><div class="news-topic-header">{item["TOPIC"]}</div><div class="news-text"><a href="https://www.google.com/search?q={q}" target="_blank">{item["NEWS"]}</a></div></div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("SYSTEM SCAN COMPLETE: NO ASSETS MATCHED THE CRITERIA. MARKET MAY BE DORMANT OR OFFLINE.")

st.caption("PREDATOR QUANTUM PRO | MTI REVISED EDITION | 2026")
