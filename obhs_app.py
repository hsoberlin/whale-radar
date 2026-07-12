import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
from bs4 import BeautifulSoup
import re
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import urllib.parse
from collections import Counter

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="SWING TRADE MOMENTUM V1.0", layout="wide", page_icon="🚀")
warnings.filterwarnings("ignore")

# Refresh Rate: 5 Menit
st_autorefresh(interval=300000, key="swing_trade_momentum_v1")

# --- ULTRA-PREMIUM TERMINAL UI (DARK THEME) ---
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
        font-weight: 900; font-size: 40px !important;
        background: linear-gradient(90deg, #00ffcc, #ff0055);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 5px;
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

    /* Pixel Box */
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

    /* --- FORCED DARK TABLE STYLE --- */
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
    [data-testid="stDataFrame"] div[role="row"]:hover div[role="gridcell"] {
        background-color: rgba(0, 255, 204, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & LOGIC ENGINE
# ==========================================

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
    "ADRO": "BOY THOHIR", "ADMR": "BOY THOHIR", "ESSA": "BOY THOHIR",
    "MBMA": "BOY THOHIR", "MDKA": "BOY THOHIR (SANDI)",
    "RAJA": "HAPPY HAPSORO", "CBRE": "HAPPY HAPSORO", "PSAB": "HAPPY HAPSORO",
    "MEDC": "ARIFIN PANIGORO", "DRMA": "TP RACHMAT", "ASLC": "TP RACHMAT", "TAPG": "TP RACHMAT",
    "TOBA": "LUHUT GROUP", "PGAS": "STATE OWNED", "BBRI": "STATE OWNED", 
    "BMRI": "STATE OWNED", "BBNI": "STATE OWNED", "TLKM": "STATE OWNED", "ANTM": "STATE OWNED"
}

SECTOR_MAP = {
    "BBCA": "FINANCE", "BBRI": "FINANCE", "BMRI": "FINANCE", "BBNI": "FINANCE", "BBTN": "FINANCE",
    "ADRO": "ENERGY", "PTBA": "ENERGY", "ITMG": "ENERGY", "HRUM": "ENERGY", "MEDC": "ENERGY",
    "ANTM": "BASIC-MAT", "MDKA": "BASIC-MAT", "INCO": "BASIC-MAT", "TINS": "BASIC-MAT", "MBMA": "BASIC-MAT",
    "TLKM": "INFRA", "ISAT": "INFRA", "EXCL": "INFRA", "JSMR": "INFRA", "TOWR": "INFRA",
    "ICBP": "CONSUMER", "INDF": "CONSUMER", "UNVR": "CONSUMER", "AMRT": "CONSUMER", "ACES": "CONSUMER",
    "BSDE": "PROPERTY", "CTRA": "PROPERTY", "SMRA": "PROPERTY", "PANI": "PROPERTY", "ASRI": "PROPERTY",
    "GOTO": "TECH", "BUKA": "TECH", "EMTK": "TECH", "SCMA": "TECH",
    "ASSA": "TRANS", "BIRD": "TRANS", "SMDR": "TRANS"
}

def get_sector(ticker):
    if ticker in SECTOR_MAP: return SECTOR_MAP[ticker]
    return "OTHERS"

# === SUMBER BERITA (3 WEB UTAMA) ===
URLS = {
    "EmitenNews": "https://emitennews.com",
    "CNBC Market": "https://www.cnbcindonesia.com/market",
    "Katadata Fin": "https://katadata.co.id/finansial/bursa"
}

KEYWORDS = [
    "Akuisisi", "Private Placement", "Rights Issue", "Right Issue", 
    "MTO", "Tender Offer", "Ekspansi", "Penambahan Modal", 
    "Rencana IPO", "IPO", "Buyback", "Saham Treasury", 
    "Suspensi", "Unusual Market Activity", "Negosiasi", 
    "Laba", "Rugi", "Kontrak", "Dividen"
]

def fetch_macro_context():
    macro_data = {}
    try:
        tickers = ["^JKSE", "IDR=X", "CL=F", "GC=F", "BTC-USD", "^IXIC"] 
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
            safe_extract('BTC-USD', 'BITCOIN')
            safe_extract('^IXIC', 'NASDAQ')
            
    except Exception as e: pass
    return macro_data

def build_flow_features(df):
    df = df.copy()
    df['chg_pct'] = df['Close'].pct_change()
    df['value'] = df['Volume'] * df['Close']
    df['vol_ma5'] = df['Volume'].rolling(5).mean()
    df['vol_ma50'] = df['Volume'].rolling(50).mean()
    df['vol_ma'] = df['Volume'].rolling(20, min_periods=5).mean()
    df['vol_power'] = df['Volume'] / df['vol_ma'] # Ini Ratio MA5/MA20 (Standard)
    
    # Velocity Specific Ratio (MA5 / MA50)
    df['velocity_ratio'] = df['vol_ma5'] / df['vol_ma50']
    
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Trend_State'] = np.where(df['Close'] > df['MA20'], "BULLISH", "BEARISH")
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    stoch_min = df['RSI'].rolling(14).min()
    stoch_max = df['RSI'].rolling(14).max()
    df['Stoch_K'] = 100 * (df['RSI'] - stoch_min) / (stoch_max - stoch_min)
    
    df['Stoch_K'] = df['Stoch_K'].fillna(50)
    df['Full_K'] = df['Stoch_K'].rolling(3).mean().fillna(50) 
    df['Full_D'] = df['Full_K'].rolling(3).mean().fillna(50)
    
    df['Mom_State'] = np.where(df['Full_K'] > 80, "STRONG", np.where(df['Full_K'] < 20, "WEAK", "NEUTRAL"))
    
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    raw_money_flow = typical_price * df['Volume']
    flow_dir = np.where(typical_price > typical_price.shift(1), 1, -1)
    df['Net_Flow'] = raw_money_flow * flow_dir
    df['Flow_Sentiment'] = df['Net_Flow'].rolling(5).sum() 
    df['Flow_State'] = np.where(df['Flow_Sentiment'] > 0, "INFLOW", "OUTFLOW")
    
    return df

def get_precise_trendlines(df, window=50):
    df_recent = df.tail(window).copy()
    df_recent['idx_num'] = np.arange(len(df_recent))
    mid_point = window // 2
    zone_left = df_recent.iloc[:mid_point]
    zone_right = df_recent.iloc[mid_point:]
    
    h1_idx = zone_left['High'].idxmax(); h1_val = zone_left['High'].max(); h1_x = df_recent.loc[h1_idx, 'idx_num']
    h2_idx = zone_right['High'].idxmax(); h2_val = zone_right['High'].max(); h2_x = df_recent.loc[h2_idx, 'idx_num']
    
    l1_idx = zone_left['Low'].idxmin(); l1_val = zone_left['Low'].min(); l1_x = df_recent.loc[l1_idx, 'idx_num']
    l2_idx = zone_right['Low'].idxmin(); l2_val = zone_right['Low'].min(); l2_x = df_recent.loc[l2_idx, 'idx_num']
    
    slope_upper = (h2_val - h1_val) / (h2_x - h1_x) if h2_x != h1_x else 0
    slope_lower = (l2_val - l1_val) / (l2_x - l1_x) if l2_x != l1_x else 0
    
    x_line = np.arange(window) 
    y_upper_line = [h1_val + slope_upper * (i - h1_x) for i in x_line]
    y_lower_line = [l1_val + slope_lower * (i - l1_x) for i in x_line]
    
    if slope_upper < 0 and slope_lower > 0: pattern = "SYMM TRIANGLE"
    elif slope_upper < 0 and slope_lower < 0: pattern = "FALLING WEDGE"
    elif slope_upper > 0 and slope_lower > 0: pattern = "RISING WEDGE"
    elif slope_upper == 0 and slope_lower > 0: pattern = "ASC TRIANGLE"
    else: pattern = "CONSOLIDATION"

    return {
        "dates": df_recent.index,
        "y_upper": y_upper_line,
        "y_lower": y_lower_line,
        "pattern_name": pattern
    }

def calculate_trade_plan(df):
    df = df.copy()
    df['TR'] = df[['High', 'Low', 'Close']].apply(lambda x: max(x['High'] - x['Low'], abs(x['High'] - df['Close'].shift(1).iloc[-1]), abs(x['Low'] - df['Close'].shift(1).iloc[-1])), axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()
    
    last_close = df['Close'].iloc[-1]
    last_atr = df['ATR'].iloc[-1] if not pd.isna(df['ATR'].iloc[-1]) else (last_close * 0.05)
    
    stop_loss = int(last_close - (2 * last_atr))
    risk = last_close - stop_loss
    target_price = int(last_close + (risk * 2.0))
    
    risk_pct = round((risk / last_close) * 100, 1)
    reward_pct = round(((target_price - last_close) / last_close) * 100, 1)
    return stop_loss, target_price, risk_pct, reward_pct

def get_catalyst_tag(headline, existing_topic):
    text = headline.upper()
    if existing_topic and existing_topic not in ["STRATEGIS", "LAINNYA"]: return existing_topic
    if 'LABA' in text or 'PROFIT' in text or 'EARNINGS' in text: return "EARNINGS UPDATE"
    if 'DIVIDEN' in text: return "DIVIDEND INFO"
    if 'AKUISISI' in text or 'CPL' in text: return "M&A / AKUISISI"
    if 'KONTRAK' in text: return "NEW CONTRACT"
    return "MARKET MOVER"

# === FETCH INTEL (DIRECT SCRAPING) ===
def fetch_realtime_intel():
    intel_map, intel_list, news_tickers = {}, [], set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    all_targets = list(set(list(master_afiliasi.keys())))

    for source_name, url in URLS.items():
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                text = a.get_text().strip()
                if len(text) < 20: continue
                
                link = a['href']
                if not link.startswith('http'):
                    if 'cnbc' in url: link = f"https://www.cnbcindonesia.com{link}"
                    elif 'katadata' in url: link = f"https://katadata.co.id{link}"
                    else: link = url + link

                text_upper = text.upper()
                matched_topic = "STRATEGIS"
                for kw in KEYWORDS:
                    if kw.upper() in text_upper:
                        matched_topic = kw.upper(); break
                
                is_relevant = False
                if matched_topic != "STRATEGIS": is_relevant = True
                
                for t in all_targets:
                    if f" {t} " in f" {text_upper} " or f"({t})" in text_upper:
                        intel_map[t] = {"title": text, "topic": matched_topic}
                        news_tickers.add(t)
                        is_relevant = True
                
                if is_relevant and not any(d['NEWS'] == text for d in intel_list):
                    intel_list.append({"TOPIC": matched_topic, "NEWS": text, "LINK": link})
        except: continue
    return intel_map, intel_list, list(news_tickers)

def analyze_correlation(ticker, stock_chg, macro_data):
    reasons = []
    sector = get_sector(ticker)
    
    oil_chg = macro_data.get('OIL', {}).get('chg', 0)
    if stock_chg > 0 and oil_chg > 0.5 and sector == "ENERGY":
        reasons.append(f"🛢️ <b>COMMODITY PLAY:</b> Diuntungkan kenaikan harga Minyak (+{oil_chg:.2f}%).")

    gold_chg = macro_data.get('GOLD', {}).get('chg', 0)
    if stock_chg > 0 and gold_chg > 0.5 and (sector == "BASIC-MAT" or sector == "METAL"):
        reasons.append(f"🛡️ <b>GOLD PROXY:</b> Mengikuti reli harga Emas (+{gold_chg:.2f}%).")

    btc_chg = macro_data.get('BITCOIN', {}).get('chg', 0)
    if stock_chg > 0 and btc_chg > 2.0 and (sector == "TECH" or sector == "FINANCE"):
        reasons.append(f"🚀 <b>RISK-ON SENTIMENT:</b> Terdorong sentimen Tech/Crypto (+{btc_chg:.2f}%).")

    if not reasons:
        ihsg_chg = macro_data.get('IHSG', {}).get('chg', 0)
        if stock_chg > 0 and ihsg_chg > 0: reasons.append(f"🔗 <b>MARKET SYNC:</b> Bergerak harmonis dengan IHSG.")
        elif stock_chg > 0 and ihsg_chg < 0: reasons.append(f"🦄 <b>ALPHA MOVER:</b> Melawan arus market (Strong Divergence).")
        else: reasons.append(f"🎯 <b>IDIOSYNCRATIC:</b> Pergerakan didorong faktor spesifik emiten.")
            
    return "<br>".join(reasons)

# --- INTI LOGIKA SCREENING (SWING TRADE MOMENTUM V1.0) ---
def scan_market(macro_data):
    results = []
    intel_map, _, news_tickers = fetch_realtime_intel()
    combined_targets = list(set(list(master_afiliasi.keys()) + news_tickers))
    detected_groups = []

    for ticker in combined_targets:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            h = s.history(period="6mo", interval="1d") 
            if len(h) < 60: continue
            h = build_flow_features(h)
            if h.iloc[-1].isnull().any(): continue
            last = h.iloc[-1]
            
            # --- STAGE 1: GATEKEEPER (Filter Mutlak) ---
            # 1. Likuiditas: Min 1 Miliar
            current_value = last['Close'] * last['Volume']
            if current_value < 1_000_000_000: continue 
            
            # 2. Harga: Min Rp 1 (FCA Masuk)
            if last['Close'] < 1: continue 
            
            # 3. VELOCITY: Wajib ada ledakan volume (MA5 > 1.2x MA50)
            is_velocity_spike = last['velocity_ratio'] > 1.2
            if not is_velocity_spike: continue

            # --- STAGE 2: SECONDARY FILTER ---
            # 4. ANTI-DISTRIBUSI: Jika harga minus (Merah), tendang (karena volume tinggi + merah = bahaya)
            if last['chg_pct'] < 0: continue

            # --- PEMBOBOTAN (SCORING) ---
            score = 15 # Base Score (Lolos Gatekeeper)
            thesis_points = []
            
            news_info = intel_map.get(ticker, {})
            news_headline = news_info.get('title', '')
            news_topic_raw = news_info.get('topic', '')
            has_news = ticker in intel_map
            group_name = master_afiliasi.get(ticker, "EXTERNAL")
            
            if score > 15 and group_name != "EXTERNAL": detected_groups.append(group_name)
            catalyst_tag = get_catalyst_tag(news_headline, news_topic_raw) if has_news else "TECHNICAL MOVER"
            
            # 1. WHALE POWER
            if last['vol_power'] > 3.0:
                score += 35 # Whale Boost
                thesis_points.append(f"🌊 <b>LIQUIDITY INJECTION:</b> Deteksi akumulasi volume ekstrem ({last['vol_power']:.1f}x).")
                if not has_news: catalyst_tag = "WHALE INFLOW"
            else:
                score += 15 # Standard Velocity Flow
                thesis_points.append(f"💧 <b>FLOW ACTIVITY:</b> Volume & Velocity Valid ({last['velocity_ratio']:.2f}x).")

            # 2. BERITA (Catalyst)
            if has_news: 
                score += 40 # News Boost
                topic_display = news_topic_raw if news_topic_raw != "STRATEGIS" else "NEWS UPDATE"
                thesis_points.append(f"📰 <b>EVENT: {topic_display}</b> - {news_headline[:60]}...")

            # 3. KORELASI MAKRO
            beta_thesis = analyze_correlation(ticker, last['chg_pct'], macro_data)
            thesis_points.append(beta_thesis)

            # Trade Plan
            stop_loss, target_price, risk_pct, reward_pct = calculate_trade_plan(h)
            entry_price = int(last['Close'])
            
            plan_html = (
                f"<div style='margin-top:8px; padding:5px; border-top:1px dashed #333; font-family:JetBrains Mono; font-size:11px;'>"
                f"🛡️ <b>EXECUTION:</b> BUY {entry_price} | <span style='color:#ff4d4d'>STOP {stop_loss} (-{risk_pct}%)</span> | "
                f"<span style='color:#00ffcc'>TARGET {target_price} (+{reward_pct}%)</span>"
                f"</div>"
            )
            thesis_points.append(plan_html)
            final_thesis = "<br>".join(thesis_points)
            
            porto = "15-20% (Aggressive)" if score >= 80 else ("10% (Medium)" if score >= 60 else "2-5% (Speculative)")

            results.append({
                "SYMBOL": ticker, "CONF": max(0, min(score, 100)), "VOL_POWER": round(last['vol_power'], 2),
                "FLOW_VELOCITY": round(last['velocity_ratio'], 2), "PRICE": int(last['Close']),
                "CHG%": round(last['chg_pct']*100, 2), "VALUE": round(last['value']/1e9, 1), 
                "GROUP": group_name, "THESIS": final_thesis, "PORTO": porto, 
                "NEWS_INTEL": news_headline, "CATALYST_TAG": catalyst_tag, "RAW_DATA": h,
                "PIXEL_TREND": last['Trend_State'], "PIXEL_MOMENTUM": last['Mom_State'], "FLOW_STATE": last['Flow_State']
            })
        except: continue
        
    market_pulse_text = "MIXED MARKET"
    if detected_groups:
        counts = Counter(detected_groups)
        most_common = counts.most_common(1)[0]
        if most_common[1] >= 2: market_pulse_text = f"ROTATION: {most_common[0]} GROUP"
    return results, market_pulse_text

def render_quantum_pixel_chart(target):
    df = target['RAW_DATA'].tail(50) 
    t_data = get_precise_trendlines(target['RAW_DATA'], window=50)
    
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.50, 0.15, 0.05, 0.30],
                        specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]])

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 name=target['SYMBOL'], increasing_line_color='#00ffcc', decreasing_line_color='#ff0055'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=t_data['y_upper'], mode='lines', line=dict(color='rgba(0, 255, 204, 0.3)', width=8), hoverinfo='skip', showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=t_data['y_upper'], mode='lines', line=dict(color='#00ffcc', width=2), name='Res'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=t_data['y_lower'], mode='lines', line=dict(color='rgba(255, 0, 85, 0.3)', width=8), hoverinfo='skip', showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=t_data['y_lower'], mode='lines', line=dict(color='#ff0055', width=2), name='Sup'), row=1, col=1)

    group_info = target['GROUP']
    header_label = f"FOCUS: {target['CATALYST_TAG']}" if group_info == "EXTERNAL" else f"AFFILIATION: {group_info}"
    header_color = "#cccccc" if group_info == "EXTERNAL" else "#00ffcc"

    last_candle_idx = df.index[-1]
    last_high_price = df['High'].iloc[-1]
    
    label_text = (f"<b>{target['SYMBOL']}</b><br><span style='font-size: 10px; color: {header_color};'>{header_label}</span><br>"
                  f"<span style='font-size: 10px; color: #ff0055;'><b>{t_data['pattern_name']}</b></span>")
    
    fig.add_annotation(x=last_candle_idx, y=last_high_price, text=label_text, showarrow=True, arrowhead=2, ax=0, ay=-50, bgcolor="rgba(10, 14, 20, 0.8)", bordercolor="#00ffcc", row=1, col=1)

    colors_vol = ['#00ffcc' if r >= o else '#ff0055' for r, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='Volume'), row=2, col=1)
    
    colors = ['#00ffcc' if x == "BULLISH" else '#ff0055' for x in df['Trend_State']]
    fig.add_trace(go.Bar(x=df.index, y=[1]*len(df), marker_color=colors, width=1, name='STATE'), row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['Full_K'], line=dict(color='#0088ff', width=2), name='%K'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Full_D'], line=dict(color='#ff5500', width=2), name='%D'), row=4, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="gray", row=4, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="gray", row=4, col=1)

    fig.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=10, r=10, t=60, b=10))
    fig.update_xaxes(showticklabels=False, row=1, col=1); fig.update_xaxes(showticklabels=False, row=2, col=1); fig.update_xaxes(showticklabels=False, row=3, col=1)
    return fig

# --- MAIN EXECUTION ---
st.markdown('<div class="header-container"><div class="header-title">SWING TRADE MOMENTUM V1.0</div></div>', unsafe_allow_html=True)

macro_data = fetch_macro_context()
loading_placeholder = st.empty()
loading_placeholder.markdown('<div class="blink">SYSTEM SCANNING: PROCESSING GLOBAL MACRO & FLOW...</div>', unsafe_allow_html=True)

data, market_pulse = scan_market(macro_data)
_, news_feed, _ = fetch_realtime_intel()
loading_placeholder.empty()

if macro_data:
    st.markdown(f"<div style='text-align:center; margin-bottom:10px; color:#00ffcc; font-family:Orbitron; letter-spacing:2px; font-size:12px;'>📡 MARKET PULSE: {market_pulse}</div>", unsafe_allow_html=True)
    cols = st.columns(len(macro_data))
    html_macro = "<div class='macro-strip'>"
    for k, v in macro_data.items():
        color = "macro-val-up" if v['chg'] >= 0 else "macro-val-down"
        arrow = "▲" if v['chg'] >= 0 else "▼"
        val_str = f"{v['val']:.2f}" if v['val'] is not None else "N/A"
        chg_str = f"{v['chg']:.2f}%" if v['val'] is not None else "0.00%"
        html_macro += f"<div class='macro-item'><span class='macro-label'>{k}</span><br><span class='{color}'>{val_str} ({arrow} {chg_str})</span></div>"
    html_macro += "</div>"
    st.markdown(html_macro, unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    col_main, col_news = st.columns([3, 1])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>📡 REAL-TIME WHALE TRACKER</h3>", unsafe_allow_html=True)
        st.dataframe(df_display[["SYMBOL", "CONF", "VOL_POWER", "FLOW_VELOCITY", "PRICE", "CHG%", "VALUE", "PORTO"]], column_config={
            "CONF": st.column_config.ProgressColumn("CONF", min_value=0, max_value=100, format="%d%%"),
            "VOL_POWER": st.column_config.NumberColumn("VOL PWR", format="%.2fx ⚡"),
            "FLOW_VELOCITY": st.column_config.NumberColumn("FLOW VELOCITY", format="%.2fx"),
            "VALUE": st.column_config.NumberColumn("VAL (B)", format="%.1fB"),
            "PORTO": st.column_config.TextColumn("ALLOC")
        }, use_container_width=True, hide_index=True, height=350)

        top_targets = df_display.head(4).to_dict('records')
        
        if top_targets:
            st.markdown("<h3 style='font-family:Orbitron; color:#00ffcc; font-size:18px; margin-top:20px;'>📊 QUAD-CORE PIXEL MONITORING (TOP 4)</h3>", unsafe_allow_html=True)
            for i in range(0, len(top_targets), 2):
                cols = st.columns(2) 
                batch = top_targets[i:i+2] 
                for idx, target in enumerate(batch):
                    with cols[idx]:
                        st.markdown(f"""
                        <div class="pixel-container">
                            <div class="pixel-metric"><span class="pixel-title">TREND</span><span class="{ 'pixel-value-up' if target['PIXEL_TREND']=='BULLISH' else 'pixel-value-down' }">{target['PIXEL_TREND']}</span></div>
                            <div class="pixel-metric"><span class="pixel-title">FLOW</span><span class="{ 'pixel-value-up' if target['FLOW_STATE']=='INFLOW' else 'pixel-value-down' }">{target['FLOW_STATE']}</span></div>
                             <div class="pixel-metric"><span class="pixel-title">WHALE</span><span class="pixel-value-up">{target['VOL_POWER']}x</span></div>
                        </div>""", unsafe_allow_html=True)
                        fig = render_quantum_pixel_chart(target)
                        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px; margin-top:30px;'>📝 STRATEGIC INVESTMENT ANALYSIS</h3>", unsafe_allow_html=True)
        for row in top_targets:
            st.markdown(f"""
            <div class="thesis-box">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color:#ff0055; font-weight:bold; font-size:14px;">{row['SYMBOL']}</span>
                    <span style="color:#00ffcc; font-family: 'JetBrains Mono'; font-size: 10px;">{row['PORTO']}</span>
                </div>
                <div class="thesis-header">INSTITUTIONAL THESIS:</div>
                <div style="color:#e0e0e0;">{row['THESIS']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_news:
        st.markdown("<h3 style='font-family:Orbitron; color:#ffffff; font-size:18px;'>💡 STRATEGIC INTEL</h3>", unsafe_allow_html=True)
        st.markdown('<div class="news-scroll-box">', unsafe_allow_html=True)
        for item in news_feed[:15]: 
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f'''<div class="news-box"><div class="news-topic-header">{item["TOPIC"]}</div><div class="news-text"><a href="https://www.google.com/search?q={q}" target="_blank">{item["NEWS"]}</a></div></div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.caption("SWING TRADE MOMENTUM V1.0 | INSTITUTIONAL GRADE ANALYTICS | 2026 WALL STREET STANDARD")
