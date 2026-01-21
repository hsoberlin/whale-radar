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
    
    .macro-strip { display: flex; justify-content: space-around; background: #0a0e14; padding: 10px; border-radius: 5px; border: 1px solid #333; margin-bottom: 20px; }
    .macro-item { font-family: 'JetBrains Mono'; font-size: 12px; text-align: center; }
    .macro-label { font-size: 9px; color: #888; display: block; margin-bottom: 2px; }
    .macro-val-up { color: #00ffcc; font-weight: bold; }
    .macro-val-down { color: #ff0055; font-weight: bold; }

    .blink {
        animation: blinker 1.5s linear infinite;
        color: #00ffcc;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-bottom: 20px; text-align: center;
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
        background: rgba(2, 20, 20, 0.6); 
        border-left: 2px solid #00ffcc; border-right: 1px solid #333;
        border-top: 1px solid #333; border-bottom: 1px solid #333;
        padding: 12px; border-radius: 4px; margin-top: 8px; 
        font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.5; color: #cccccc;
    }
    .thesis-header {
        font-family: 'Orbitron'; font-size: 10px; color: #00ffcc; margin-bottom: 5px; letter-spacing: 1px;
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

# --- DATABASE ENGINE ---
master_afiliasi = {
    # --- 1. GENG BARITO (PRAJOGO PANGESTU) ---
    "BREN": "PRAJOGO PANGESTU", "TPIA": "PRAJOGO PANGESTU", 
    "CUAN": "PRAJOGO PANGESTU", "BRPT": "PRAJOGO PANGESTU", 
    "PTRO": "PRAJOGO PANGESTU", "CGAS": "PRAJOGO PANGESTU",
    "CDIA": "PRAJOGO PANGESTU", "GZCO": "PRAJOGO PANGESTU",

    # --- 2. GENG BAKRIE (THE LEGENDS) ---
    "BUMI": "BAKRIE & SALIM",   "BRMS": "BAKRIE GROUP", 
    "ENRG": "BAKRIE GROUP",     "DEWA": "BAKRIE GROUP", 
    "BNBR": "BAKRIE GROUP",     "UNSP": "BAKRIE GROUP",
    "VIVA": "BAKRIE GROUP",     "MDIA": "BAKRIE GROUP", 
    "JGLE": "BAKRIE GROUP",     "ALII": "BAKRIE GROUP", 
    "ELTY": "BAKRIE GROUP",     "BTEL": "BAKRIE GROUP",
    "VKTR": "BAKRIE GROUP",

    # --- 3. GENG SALIM (THE TITANS) ---
    "AMMN": "SALIM & PANIGORO", "INDF": "SALIM GROUP", 
    "ICBP": "SALIM GROUP",      "LSIP": "SALIM GROUP", 
    "SIMP": "SALIM GROUP",      "META": "SALIM GROUP", 
    "ROTI": "SALIM GROUP",      "IMAS": "SALIM GROUP",
    "DNET": "SALIM GROUP",      "MEDC": "SALIM & PANIGORO",

    # --- 4. GENG SINAR MAS (THE GIANTS) ---
    "DSSA": "SINAR MAS",        "BSDE": "SINAR MAS", 
    "INKP": "SINAR MAS",        "TKIM": "SINAR MAS", 
    "SMMA": "SINAR MAS",        "DUTI": "SINAR MAS",
    "SMAR": "SINAR MAS",        "FREN": "SINAR MAS",
    "DMAS": "SINAR MAS",

    # --- 5. GENG AGUAN / AGUNG SEDAYU (PIK 2) ---
    "PANI": "AGUAN (PIK 2)",    "MKPI": "AGUAN GROUP",
    "ASRI": "AGUAN GROUP",      "CBDK": "AGUAN (SEDAYU)",

    # --- 6. GENG ADARO / BOY THOHIR ---
    "ADRO": "BOY THOHIR",       "ADMR": "BOY THOHIR", 
    "ESSA": "BOY THOHIR",       "MBMA": "BOY THOHIR", 
    "MDKA": "BOY THOHIR (SANDI)",

    # --- 7. GENG TRIPUTRA (TP RACHMAT) ---
    "DRMA": "TP RACHMAT",       "TAPG": "TP RACHMAT", 
    "DSNG": "TP RACHMAT",       "ASSA": "TP RACHMAT", 
    "ASLC": "TP RACHMAT",

    # --- 8. GENG HAPPY HAPSORO ---
    "RAJA": "HAPPY HAPSORO",    "CBRE": "HAPPY HAPSORO", 
    "PSAB": "HAPPY HAPSORO",    "MINA": "HAPPY HAPSORO",
    "OASA": "HAPPY HAPSORO",

    # --- 9. GENG TOMY WINATA (ARTHA GRAHA) ---
    "JIHD": "TOMY WINATA",      "SCBD": "TOMY WINATA",
    "TINY": "TOMY WINATA",

    # --- 10. GENG MNC (HARY TANOE) ---
    "KPIG": "MNC GROUP",        "BHIT": "MNC GROUP",
    "MNCN": "MNC GROUP",        "IPTV": "MNC GROUP",
    "BABP": "MNC GROUP",        "BCAP": "MNC GROUP",

    # --- 11. GENG LIPPO (RIADY) ---
    "LPKR": "LIPPO GROUP",      "LPPF": "LIPPO GROUP",
    "MLPL": "LIPPO GROUP",      "MPPA": "LIPPO GROUP",
    "SILO": "LIPPO GROUP",

    # --- 12. TECH & NEW ECONOMY ---
    "GOTO": "GOTO / TECH",      "EMTK": "EMTEK GROUP",
    "SCMA": "EMTEK GROUP",      "BUKA": "BUKALAPAK",
    "ARTO": "JAGO (GOTO)",

    # --- 13. BUMN (THE STATE MOVERS) ---
    "BBRI": "STATE OWNED",      "BMRI": "STATE OWNED", 
    "BBNI": "STATE OWNED",      "BBTN": "STATE OWNED", 
    "BRIS": "STATE OWNED",      "TLKM": "STATE OWNED", 
    "ANTM": "STATE OWNED",      "PTBA": "STATE OWNED", 
    "TINS": "STATE OWNED",      "PGAS": "STATE OWNED",
    "SMGR": "STATE OWNED",      "JSMR": "STATE OWNED",
    "GIAA": "STATE OWNED",      "GMFI": "STATE OWNED", 
    "WIKA": "STATE OWNED",      "PTPP": "STATE OWNED", 
    "ADHI": "STATE OWNED",      "KRAS": "STATE OWNED", 
    "ELSA": "STATE OWNED"       
}

RSS_LINKS = [
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640953919",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/701647301640956058",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/17720372188069162265",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/4715023400486420700",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/6157427371671042291",
    "https://www.google.co.id/alerts/feeds/16876890487441803706/8676695815866551512"
]

# --- ROBUST MACRO (CACHED - NATIVE YF) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_macro_context():
    macro_data = {}
    try:
        tickers = ["^JKSE", "CL=F", "GC=F"] 
        df = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=False)
        
        # Handle yfinance MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            close_df = df.xs('Close', level=0, axis=1, drop_level=False)
            if close_df.empty: close_df = df.xs('Close', level=1, axis=1, drop_level=False)
        else:
            close_df = df['Close'] if 'Close' in df else df

        for ticker, name in [('^JKSE', 'IHSG'), ('CL=F', 'OIL'), ('GC=F', 'GOLD')]:
            try:
                col = [c for c in close_df.columns if ticker in str(c)]
                if col:
                    series = close_df[col[0]].dropna()
                    if not series.empty:
                        now, prev = series.iloc[-1], series.iloc[-2]
                        macro_data[name] = {"val": now, "chg": (now - prev)/prev*100}
            except: pass
    except Exception: pass
    return macro_data

# --- FEATURES ---
def build_flow_features(df):
    df = df.copy()
    df['chg_pct'] = df['Close'].pct_change()
    df['value'] = df['Volume'] * df['Close']
    df['vol_ma5'] = df['Volume'].rolling(5).mean()
    df['vol_ma50'] = df['Volume'].rolling(50).mean()
    df['vol_ma20'] = df['Volume'].rolling(20, min_periods=5).mean()
    df['vol_power'] = df['Volume'] / df['vol_ma20']
    
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA20_Slope'] = df['MA20'] > df['MA20'].shift(1)
    df['Trend_State'] = np.where(df['Close'] > df['MA20'], "BULLISH", "BEARISH")
    
    # --- STOCHASTIC 10, 5, 5 CALCULATION ---
    # 1. Raw Stochastic %K (Lookback 10)
    low_min = df['Low'].rolling(10).min()
    high_max = df['High'].rolling(10).max()
    # Handle division by zero
    diff = high_max - low_min
    df['Raw_K'] = np.where(diff == 0, 50, 100 * ((df['Close'] - low_min) / diff))
    
    # 2. Slow %K (Smoothing Raw K with SMA 5) -> Ini yang jadi Garis Utama
    df['Stoch_K'] = df['Raw_K'].rolling(5).mean().fillna(50)
    
    # 3. Slow %D (Smoothing Slow K with SMA 5) -> Ini yang jadi Signal Line
    df['Stoch_D'] = df['Stoch_K'].rolling(5).mean().fillna(50)
    
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    df['Flow_State'] = np.where((typical * df['Volume'] * np.where(typical > typical.shift(1), 1, -1)).rolling(5).sum() > 0, "INFLOW", "OUTFLOW")
    return df

def calculate_trade_plan(df):
    last_close = df['Close'].iloc[-1]
    last_atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    if pd.isna(last_atr): last_atr = last_close * 0.05
    
    stop_loss = int(last_close - (2 * last_atr))
    target_price = int(last_close + ((last_close - stop_loss) * 2.0))
    risk_pct = round(((last_close - stop_loss) / last_close) * 100, 1)
    reward_pct = round(((target_price - last_close) / last_close) * 100, 1)
    return stop_loss, target_price, risk_pct, reward_pct

def fetch_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    topic_map = {
        "AKUISISI": "AKUISISI", 
        "LABA": "EARNINGS", 
        "RUGI": "EARNINGS", 
        "DIVIDEN": "DIVIDEN", 
        "KONTRAK": "KONTRAK",
        "RIGHT ISSUE": "RIGHTS ISSUE", 
        "HMETD": "RIGHTS ISSUE"
    }
    for url in RSS_LINKS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.replace('<b>','').replace('</b>','').strip()
                tickers = re.findall(r'\b[A-Z]{4}\b', title.upper())
                topic = "STRATEGIS"
                for k, v in topic_map.items():
                    if k in title.upper(): topic = v; break
                for t in set(tickers):
                    if t not in ["IHSG", "IDX", "LQ45"]:
                        intel_map[t] = {"title": title, "topic": topic}
                        news_tickers.add(t)
                intel_list.append({"TOPIC": topic, "NEWS": title})
        except: continue
    return intel_map, intel_list, list(news_tickers)

# --- BULK SCANNER ENGINE (ANTI-BLOCK) ---
def scan_market(macro_data):
    results = []
    intel_map, _, news_tickers = fetch_intel()
    raw_tickers = list(set(list(master_afiliasi.keys()) + news_tickers))
    
    # Format for Yahoo (Bulk)
    yf_tickers = [f"{t}.JK" for t in raw_tickers]
    
    try:
        # BULK DOWNLOAD (Native YF)
        bulk_data = yf.download(yf_tickers, period="6mo", interval="1d", group_by='ticker', progress=False, threads=True)
    except Exception as e:
        st.error(f"DATA FETCH ERROR: {str(e)}. Try refreshing.")
        return []

    for ticker_raw in raw_tickers:
        ticker_fmt = f"{ticker_raw}.JK"
        try:
            if len(yf_tickers) == 1: 
                df = bulk_data
            else:
                if ticker_fmt not in bulk_data.columns.levels[0]: continue
                df = bulk_data[ticker_fmt].copy()
            
            df = df.dropna(how='all')
            if len(df) < 60: continue
            
            # PROCESS
            h = build_flow_features(df)
            if h.iloc[-1].isnull().any(): continue
            last = h.iloc[-1]
            
            # --- FILTERS (Logic Tetap: Struktur ATAU Reversal + Volume ATAU News) ---
            # 1. Structure (Uptrend OR Bottom Reversal)
            is_uptrend = last['Close'] > last['MA20']
            is_reversal = (last['Close'] < last['MA20']) and (last['Stoch_K'] < 20)
            if not (is_uptrend or is_reversal): continue
            
            # 2. Trigger (Vol Spike OR News)
            is_vol_spike = last['vol_ma5'] > 1.2 * last['vol_ma50']
            has_news = ticker_raw in intel_map
            if not (is_vol_spike or has_news): continue
            
            # --- SCORING ---
            score = 10
            thesis_points = []
            strategy_tag = "TREND FOLLOWING" if is_uptrend else "BOTTOM FISHING"
            
            if last['vol_power'] > 3.0: score += 40; thesis_points.append(f"🌊 <b>WHALE:</b> Vol {last['vol_power']:.1f}x avg.")
            elif last['vol_power'] > 1.2: score += 20; thesis_points.append(f"💧 <b>ACCUM:</b> Vol steady > avg.")
            
            if is_uptrend: score += 20; thesis_points.append("📈 <b>MA20:</b> Bullish Structure.")
            if last['MA20_Slope']: score += 10; thesis_points.append("🚀 <b>MOMENTUM:</b> Strong Trend.")
            if has_news: score += 20; thesis_points.append("📰 <b>NEWS:</b> Sentiment Driver.")
            
            stop_loss, target_price, risk_pct, reward_pct = calculate_trade_plan(h)
            plan_html = f"<div style='margin-top:5px; padding:5px; border-top:1px dashed #333; font-size:11px;'>🛡️ BUY {int(last['Close'])} | <span style='color:#ff4d4d'>SL {stop_loss}</span> | <span style='color:#00ffcc'>TP {target_price}</span></div>"
            thesis_points.append(plan_html)

            results.append({
                "SYMBOL": ticker_raw, "CONF": min(score, 100), "VOL_POWER": round(last['vol_power'], 2),
                "PRICE": int(last['Close']), "CHG%": round(last['chg_pct']*100, 2), "VALUE": round(last['value']/1e9, 1),
                "GROUP": master_afiliasi.get(ticker_raw, "EXTERNAL"), "THESIS": "<br>".join(thesis_points),
                "PORTO": "HIGH" if score>=70 else "MED", "STRATEGY": strategy_tag, "RAW_DATA": h,
                "PIXEL_TREND": last['Trend_State'], "FLOW_STATE": last['Flow_State']
            })
        except: continue
    return results

# --- CHART RENDERING (FIXED: STOCHASTIC 10,5,5 REPLACES RSI) ---
def render_chart(target):
    df_raw = target['RAW_DATA'].tail(60) 
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
    
    # 1. CANDLESTICK (CLEAN - NO MA20 LINE)
    fig.add_trace(go.Candlestick(x=df_raw.index, open=df_raw['Open'], high=df_raw['High'], low=df_raw['Low'], close=df_raw['Close'], name=target['SYMBOL'], increasing_line_color='#00ffcc', decreasing_line_color='#ff0055'), row=1, col=1)
    
    # --- TRENDLINES (2 GARIS TEGAS ONLY) ---
    df_50 = df_raw.tail(50)
    if len(df_50) >= 2:
        idx_max = df_50['High'].idxmax() 
        val_max = df_50['High'].max()
        sub_after_max = df_50.loc[idx_max:].iloc[1:]
        if not sub_after_max.empty:
            idx_next = sub_after_max['High'].idxmax()
            val_next = sub_after_max['High'].max()
            fig.add_trace(go.Scatter(x=[idx_max, idx_next], y=[val_max, val_next], mode='lines', line=dict(color='#ff0055', width=2), name='Res'), row=1, col=1)

    df_20 = df_raw.tail(20)
    if len(df_20) >= 2:
        idx_min = df_20['Low'].idxmin()
        val_min = df_20['Low'].min()
        sub_after_min = df_20.loc[idx_min:].iloc[1:]
        if not sub_after_min.empty:
            idx_next_min = sub_after_min['Low'].idxmin()
            val_next_min = sub_after_min['Low'].min()
            fig.add_trace(go.Scatter(x=[idx_min, idx_next_min], y=[val_min, val_next_min], mode='lines', line=dict(color='#00ffcc', width=2), name='Sup'), row=1, col=1)

    # 3. VOLUME (CLEAN - NO LINES)
    fig.add_trace(go.Bar(x=df_raw.index, y=df_raw['Volume'], marker_color=['#00ffcc' if r>=o else '#ff0055' for r,o in zip(df_raw['Close'],df_raw['Open'])], name='Vol'), row=2, col=1)
    
    # 4. STOCHASTIC (10, 5, 5) - REPLACING RSI
    # %K Line (Blue)
    fig.add_trace(go.Scatter(x=df_raw.index, y=df_raw['Stoch_K'], line=dict(color='#0088ff', width=1.5), name='%K'), row=3, col=1)
    # %D Line (Orange - Signal)
    fig.add_trace(go.Scatter(x=df_raw.index, y=df_raw['Stoch_D'], line=dict(color='#ffaa00', width=1.5), name='%D'), row=3, col=1)
    
    # Limits
    fig.add_hline(y=20, line_dash="dot", line_color="rgba(255,255,255,0.3)", row=3, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="rgba(255,255,255,0.3)", row=3, col=1)

    # --- CLEAN THEME ---
    fig.update_layout(
        template="plotly_dark", height=400, margin=dict(l=0,r=0,t=40,b=0), showlegend=False,
        title=dict(text=f"{target['SYMBOL']} [{target['STRATEGY']}]", x=0.02, y=0.96, font=dict(color="white")),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='#020406', 
        xaxis_rangeslider_visible=False 
    )
    
    # Remove ALL Gridlines & Extra Axes
    fig.update_xaxes(showgrid=False, showticklabels=False, row=1, col=1)
    fig.update_xaxes(showgrid=False, showticklabels=False, row=2, col=1) 
    fig.update_xaxes(showgrid=False, row=3, col=1)
    fig.update_yaxes(showgrid=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, showticklabels=False, row=2, col=1) 
    fig.update_yaxes(showgrid=False, range=[0, 100], row=3, col=1) # Fix Stochastic Scale
    
    return fig

# --- RENDER UI ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM DAILY</div></div>', unsafe_allow_html=True)
macro_data = fetch_macro_context()
loading = st.empty()
loading.markdown('<div class="blink">INITIATING ULTIMATE SCAN... PLEASE WAIT...</div>', unsafe_allow_html=True)

data = scan_market(macro_data)
_, news_feed, _ = fetch_intel()
loading.empty()

if macro_data:
    cols = st.columns(len(macro_data))
    html_macro = "<div class='macro-strip'>"
    for k, v in macro_data.items():
        html_macro += f"<div class='macro-item'><span class='macro-label'>{k}</span><br><span class='{'macro-val-up' if v['chg']>=0 else 'macro-val-down'}'>{v['val']:.2f} ({v['chg']:.2f}%)</span></div>"
    st.markdown(html_macro+"</div>", unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("ASSETS FOUND", len(df_display))
    col_m2.metric("AVG SCORE", f"{int(df_display['CONF'].mean())}")
    
    col_main, col_news = st.columns([3, 1])
    with col_main:
        st.dataframe(df_display[["SYMBOL","STRATEGY","CONF","VOL_POWER","PRICE","CHG%","VALUE"]], 
                     column_config={"CONF": st.column_config.ProgressColumn("SCORE", max_value=100, format="%d")}, use_container_width=True, hide_index=True)
        st.markdown("---"); st.markdown("### 📊 TOP CONVICTION CHARTS")
        top_picks = df_display.head(4).to_dict('records')
        for i in range(0, len(top_picks), 2):
            cols = st.columns(2)
            for idx, target in enumerate(top_picks[i:i+2]):
                with cols[idx]:
                    st.plotly_chart(render_chart(target), use_container_width=True)
                    st.markdown(f"<div class='thesis-box'><div class='thesis-header'>{target['GROUP']} | SCORE: {target['CONF']}</div>{target['THESIS']}</div>", unsafe_allow_html=True)
    with col_news:
        st.markdown("### 💡 INTEL FEED")
        st.markdown('<div class="news-scroll-box">', unsafe_allow_html=True)
        for item in news_feed[:20]:
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f"<div class='news-box'><div class='news-topic-header'>{item['TOPIC']}</div><div class='news-text'><a href='https://www.google.com/search?q={q}' target='_blank'>{item['NEWS']}</a></div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("SCAN COMPLETE. NO ASSETS FOUND (Try refreshing in 5 minutes if you suspect connection issues).")
