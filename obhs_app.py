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

# --- 1. DASHBOARD CONFIGURATION ---
st.set_page_config(page_title="QUANTUM PRO - UNIFIED TJL ENGINE", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 5 Menit
st_autorefresh(interval=300000, key="quantum_intraday_sync")

# --- 2. ULTRA-PREMIUM TERMINAL UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@500;800&family=Inter:wght@400;600;900&display=swap');
    
    .stApp { background-color: #020406; color: #ffffff; }
    
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
    
    .pixel-container {
        display: flex; gap: 5px; margin-bottom: 5px;
        background: #0a0e14; padding: 5px; border-radius: 5px; border: 1px solid #333;
    }
    .pixel-metric { flex: 1; text-align: center; font-family: 'JetBrains Mono'; }
    .pixel-title { font-size: 8px; color: #888; display: block; margin-bottom: 2px; }
    .pixel-value-up { color: #00ffcc; font-weight: 900; font-size: 12px; text-shadow: 0 0 5px rgba(0,255,204,0.5); }
    .pixel-value-down { color: #ff0055; font-weight: 900; font-size: 12px; text-shadow: 0 0 5px rgba(255,0,85,0.5); }
    .pixel-value-neutral { color: #ffd166; font-weight: 900; font-size: 12px; }
    
    .thesis-box {
        background: rgba(2, 20, 20, 0.6); 
        border-left: 2px solid #00ffcc; border-right: 1px solid #333;
        border-top: 1px solid #333; border-bottom: 1px solid #333;
        padding: 12px; border-radius: 4px; margin-top: 8px; 
        font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.5; color: #cccccc;
    }
    .thesis-header { font-family: 'Orbitron'; font-size: 10px; color: #00ffcc; margin-bottom: 5px; letter-spacing: 1px; }
    
    .news-scroll-box { max-height: 600px; overflow-y: auto; }
    .news-box {
        background: #0a0e14; border-left: 3px solid #ff4d4d;
        padding: 8px; margin-bottom: 8px; border-radius: 4px; transition: 0.3s;
    }
    .news-box:hover { border-left: 3px solid #00ffcc; background: #111a21; }
    .news-topic-header { font-family: 'Orbitron'; font-size: 9px; color: #00ffcc; font-weight:bold;}
    .news-text { font-family: 'Inter', sans-serif; font-size: 11px; color: #e0e0e0; }
    .news-text a { text-decoration: none; color: inherit; }

    @keyframes blinker { 50% { opacity: 0.4; color: #00ffcc; } }
    .blink { 
        animation: blinker 0.8s linear infinite; 
        font-family: 'Orbitron'; font-size: 14px; color: #ff0055; 
        text-align: center; letter-spacing: 2px; margin: 20px 0;
    }

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

# --- 3. MASSIVE TICKER DATABASE (450+ EMITEN TANPA GRUP) ---
MASTER_TICKERS = [
    "AALI", "ABBA", "ABMM", "ACES", "ADCP", "ADMR", "ADRO", "AGRO", "AHA", "AKRA", "ALDO", "ALII", 
    "AMAR", "AMMN", "AMRT", "ANTM", "APLN", "ARTO", "ASII", "ASLC", "ASRI", "ASSA", "AUTO", "AWAN",
    "BABP", "BACA", "BANK", "BBYB", "BBCA", "BBNI", "BBRI", "BBTN", "BDEE", "BDMN", "BEKS", "BELI", 
    "BEST", "BFIN", "BGTG", "BHIT", "BIRD", "BISI", "BJBR", "BJTM", "BKDP", "BKSL", "BMHS", "BMRI", 
    "BMTR", "BNBA", "BNBR", "BNGA", "BNII", "BNLI", "BOGA", "BREN", "BRIS", "BRMS", "BRPT", "BSBK", 
    "BSDE", "BSML", "BSSR", "BTEL", "BTPS", "BUKA", "BULL", "BUMI", "BWPT", "BYAN", "CAMP", "CARE", 
    "CARS", "CASS", "CCSI", "CEKA", "CENT", "CFIN", "CGAS", "CINT", "CITA", "CITY", "CLEO", "CMNP", 
    "CMPP", "COAL", "CPIN", "CPRO", "CSAP", "CSIS", "CTRA", "CUAN", "DAYA", "DCII", "DEAL", "DEWA", 
    "DGIK", "DILD", "DIVA", "DKFT", "DLTA", "DMAS", "DMMX", "DOID", "DRMA", "DSSA", "DUTI", "DVLA", 
    "EAST", "ECII", "ELSA", "ELTY", "EMTK", "ENAK", "ENRG", "ERAA", "ESSA", "ESTA", "EXCL", "FAST", 
    "FASW", "FILM", "FIRE", "FISH", "FPNI", "FREN", "GAMA", "GDST", "GEMA", "GEMS", "GGRM", "GIAA", 
    "GJTL", "GLOB", "GLVA", "GMFI", "GOTO", "GPRA", "GTBO", "GWSA", "GZCO", "HEAL", "HEXA", "HITS", 
    "HMSP", "HOKI", "HOME", "HOMI", "HRTA", "HRUM", "IATA", "ICBP", "ICON", "IGAR", "IIKP", "IMAS", 
    "IMJS", "IMPC", "INAF", "INAI", "INCO", "INDF", "INDO", "INDR", "INDS", "INDY", "INKP", "INPC", 
    "INTA", "INTP", "IPCC", "IPCM", "IPPE", "IPTV", "IRRA", "ISAT", "ISSP", "ITIC", "ITMG", "JAST", 
    "JCCW", "JCON", "JGLE", "JIHD", "JKON", "JMAS", "JPFA", "JSPT", "JTPE", "KAEF", "KBLI", "KBLM", 
    "KBLV", "KDSI", "KEEN", "KEJU", "KIAS", "KIJA", "KINO", "KIOS", "KKGI", "KLBF", "KOBX", "KOIN", 
    "KOPI", "KPAL", "KPIG", "KRAM", "KRAS", "KREN", "LABA", "LAND", "LCGP", "LEAD", "LFIN", "LINK", 
    "LION", "LPCK", "LPGI", "LPIN", "LPKR", "LPPF", "LSIP", "LTLS", "LUCK", "MAIN", "MAPA", "MAPB", 
    "MAPI", "MARI", "MARK", "MASA", "MAYA", "MBAP", "MBMA", "MBSS", "MCAS", "MCOR", "MDIA", "MDKA", 
    "MDKI", "MDLN", "MEDC", "MEGA", "META", "MFIN", "MICE", "MIDI", "MIKA", "MINA", "MIRA", "MITI", 
    "MKNT", "MKPI", "MLBI", "MLIA", "MLPL", "MLPT", "MNCN", "MORA", "MPMX", "MPPA", "MRAT", "MSIN", 
    "MSKY", "MTDL", "MTEL", "MTLA", "MTMH", "MTPS", "MYOH", "MYOR", "MYRX", "MYTX", "NANO", "NAPS", 
    "NATO", "NCKL", "NELY", "NFCX", "NICK", "NICL", "NIKL", "NISP", "NOBU", "NRCE", "NTPN", "NUSA", 
    "NZIA", "OASA", "OBMD", "OCAP", "OENT", "OKAS", "OMED", "PADI", "PALM", "PAMG", "PANI", "PANR", 
    "PANS", "PBID", "PBRX", "PBSA", "PEGE", "PGAS", "PGEO", "PICO", "PJAA", "PLIN", "PMMP", "PNBN", 
    "PNBS", "PNIN", "PNLF", "POLA", "POLL", "POLU", "POLY", "PORT", "POWER", "PPGL", "PPRE", "PPRO", 
    "PTPP", "PRAS", "PRDA", "PSAB", "PSDN", "PSGO", "PSKT", "PTBA", "PTIS", "PTPW", "PTRO", "PUDP", 
    "PURA", "PZZA", "RAJA", "RALS", "RANC", "RBMS", "RDTX", "REAL", "RELI", "RICY", "RIGS", "RIMO", 
    "ROCK", "ROTI", "RSGK", "SAFE", "SAME", "SAMF", "SAPX", "SBMA", "SCCO", "SCMA", "SCNP", "SDMU", 
    "SDPC", "SDRA", "SGER", "SGRO", "SHID", "SIDO", "SILO", "SIMA", "SIMP", "SINI", "SKBM", "SKLT", 
    "SKRN", "SMAR", "SMBR", "SMCB", "SMDM", "SMGR", "SMKL", "SMMA", "SMRA", "SMRU", "SMSM", "SOCI", 
    "SONA", "SPMA", "SPTO", "SRIL", "SRSN", "SRTG", "SSIA", "SSMS", "SSTC", "STTP", "SULA", "SULI", 
    "SUPR", "SWAT", "TACO", "TAMU", "TAPG", "TARA", "TAXI", "TAYS", "TBIG", "TBLA", "TCID", "TCPI", 
    "TEBE", "TECH", "TELE", "TFAS", "TGKA", "TINS", "TIRA", "TKIM", "TLKM", "TMAS", "TOBA", "TOTL", 
    "TOTO", "TOWR", "TPIA", "TPMA", "TRAM", "TRIL", "TRIM", "TRIN", "TRIS", "TRJA", "TRST", "TRUE", 
    "TRUK", "TSPC", "TUGU", "TURI", "UFOE", "ULTJ", "UNIC", "UNIT", "UNSP", "UNTR", "UNVR", "URBN", 
    "VICI", "VICO", "VINS", "VIVA", "VKTR", "VOKS", "VRNA", "VTNY", "WAPO", "WASK", "WEGE", "WEHA", 
    "WGSH", "WIKA", "WIM", "WINS", "WIRG", "WMUU", "WOMF", "WOOD", "WSBP", "WSKT", "WTON", "YELO", 
    "ZATA", "ZINC", "ZONE", "ZYRX"
]

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
                tickers = re.findall(r'\b[A-Z]{4}\b', title.upper())
                for t in set(tickers):
                    if t not in ["IHSG", "IDX", "LQ45"]:
                        intel_map[t] = {"title": title, "topic": "CATALYST"}
                        news_tickers.add(t)
                intel_list.append({"TOPIC": "NEWS ALERT", "NEWS": title})
        except: continue
    return intel_map, intel_list, list(news_tickers)

# --- 5. DUAL-TIMEFRAME TJL SCANNER ENGINE (BATCH OPTIMIZED) ---
def scan_tjl_market():
    results = []
    intel_map, _, news_tickers = fetch_intel()
    
    # Menggabungkan list ticker utama dengan ticker yang sedang ada berita hari ini
    all_tickers = list(set(MASTER_TICKERS + news_tickers))
    tickers_jk = [f"{t}.JK" for t in all_tickers]
    
    # 5.1 BATCH DOWNLOAD HARIAN (Ekstrak 450+ saham sekaligus agar tidak diblokir & cepat)
    try:
        batch_data = yf.download(tickers_jk, period="1y", interval="1d", group_by='ticker', progress=False)
    except Exception as e:
        return [], f"ERROR DOWNLOADING DATA: {e}"

    # 5.2 FILTERING HARIAN (Hanya menyisakan yang Gap Up)
    surviving_tickers = []
    
    for ticker in all_tickers:
        try:
            ticker_jk = f"{ticker}.JK"
            if ticker_jk not in batch_data.columns.levels[0]:
                continue
                
            df_d = batch_data[ticker_jk].dropna(how='all')
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
            
            # Jika lolos, masukkan ke daftar survivor untuk diproses Intraday
            surviving_tickers.append({
                "ticker": ticker,
                "prev_close": prev_close,
                "prev_high": prev_high,
                "today_open": today_open,
                "gap_pct": gap_pct
            })
        except:
            continue

    # 5.3 INTRADAY SCAN (Hanya diunduh untuk segelintir saham yang lolos filter)
    for survivor in surviving_tickers:
        ticker = survivor["ticker"]
        prev_high = survivor["prev_high"]
        today_open = survivor["today_open"]
        gap_pct = survivor["gap_pct"]
        
        try:
            s = yf.Ticker(f"{ticker}.JK")
            df_intra = s.history(period="1d", interval="5m")
            if df_intra.empty or len(df_intra) < 2: continue
            
            # Proxy for Pre-Market High / Opening Range High (First 30 mins)
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
            is_hod_break = curr_price >= hod * 0.995
            
            if is_ydh_break:
                score += 20
                thesis_points.append(f"🔥 <b>BREAKOUT YDH:</b> Menembus level tertinggi kemarin (Rp {prev_high:,.0f}).")
            if is_orh_break:
                score += 15
                thesis_points.append(f"⚡ <b>BREAKOUT ORH:</b> Menembus Opening Range High (Rp {orh:,.0f}).")
            if is_hod_break and vol_spike > 1.5:
                score += 15
                thesis_points.append(f"🌊 <b>VPA TRIGGER:</b> Volume meledak {vol_spike:.1f}x di level HOD!")
            
            has_news = ticker in intel_map
            if has_news:
                score += 10
                thesis_points.append(f"📰 <b>CATALYST DETECTED:</b> {intel_map[ticker]['title'][:65]}...")
                
            final_thesis = "<br>".join(thesis_points)
            porto = "TJL EXECUTE (Aggressive)" if score >= 80 else ("MONITOR (Medium)" if score >= 65 else "WAITING")
            
            # Risk Management Generation
            stop_loss = orh if curr_price > orh else today_open
            risk_pct = round(abs(curr_price - stop_loss) / curr_price * 100, 1)
            target_price = curr_price + ((curr_price - stop_loss) * 2)
            
            plan_html = (
                f"<div style='margin-top:8px; padding:5px; border-top:1px dashed #333; font-family:JetBrains Mono; font-size:11px;'>"
                f"🛡️ <b>PLAN:</b> BUY {int(curr_price)} | "
                f"<span style='color:#ff4d4d'>STOP {int(stop_loss)} (-{risk_pct}%)</span> | "
                f"<span style='color:#00ffcc'>TARGET {int(target_price)}</span>"
                f"</div>"
            )
            final_thesis += plan_html
            
            if score >= 65:
                results.append({
                    "SYMBOL": ticker, "CONF": min(score, 100), 
                    "GAP_PCT": float(gap_pct), "VOL_SPIKE": float(vol_spike), 
                    "PRICE": int(curr_price), "YDH": int(prev_high), "ORH": int(orh),
                    "THESIS": final_thesis, "PORTO": porto,
                    "RAW_INTRA": df_intra, "TJL_STATUS": "HOD BREAKOUT" if is_hod_break else "CONSOLIDATION"
                })
        except: continue
        
    return results, "MASSIVE MARKET SCANNING ACTIVE"

# --- 6. INTRADAY PIXEL CHART (5-MINUTE) ---
def render_intraday_chart(target):
    df = target['RAW_INTRA']
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.75, 0.25])

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#00ffcc', decreasing_line_color='#ff0055', name="Price"), row=1, col=1)
    
    fig.add_hline(y=target['YDH'], line_dash="dash", line_color="#ff0055", line_width=2, 
                  annotation_text="YDH", annotation_position="top right", 
                  annotation_font_color="#ff0055", row=1, col=1)
    
    fig.add_hline(y=target['ORH'], line_dash="dash", line_color="#ffd166", line_width=2, 
                  annotation_text="ORH", annotation_position="bottom right", 
                  annotation_font_color="#ffd166", row=1, col=1)

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
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM PRO - UNIFIED TJL</div></div>', unsafe_allow_html=True)

loading_placeholder = st.empty()
loading_placeholder.markdown(f'<div class="blink">SCANNING {len(MASTER_TICKERS)}+ TICKERS: INTRADAY TJL ENGINE...</div>', unsafe_allow_html=True)

data, market_pulse = scan_tjl_market()
_, news_feed, _ = fetch_intel()
loading_placeholder.empty()

st.markdown(f"<div style='text-align:center; margin-bottom:20px; color:#00ffcc; font-family:Orbitron; letter-spacing:2px; font-size:14px;'>📡 {market_pulse}</div>", unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="CONF", ascending=False)
    col_main, col_news = st.columns([3, 1])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>⚡ TJL BREAKOUT SCANNER (REAL-TIME)</h3>", unsafe_allow_html=True)
        # Menampilkan tabel tanpa kolom afiliasi grup
        st.dataframe(df_display[["SYMBOL", "CONF", "GAP_PCT", "VOL_SPIKE", "PRICE", "YDH", "TJL_STATUS", "PORTO"]], column_config={
            "CONF": st.column_config.ProgressColumn("CONF", min_value=0, max_value=100, format="%d%%"),
            "GAP_PCT": st.column_config.NumberColumn("GAP UP", format="%.2f%%"),
            "VOL_SPIKE": st.column_config.NumberColumn("VOL PWR", format="%.1fx 🌊"),
            "PRICE": st.column_config.NumberColumn("PRICE (Rp)"),
            "YDH": st.column_config.NumberColumn("YDH (Rp)"),
            "TJL_STATUS": st.column_config.TextColumn("ACTION STATE"),
            "PORTO": st.column_config.TextColumn("ALLOCATION")
        }, use_container_width=True, hide_index=True, height=250)

        top_targets = df_display.head(4).to_dict('records')
        
        if top_targets:
            st.markdown("<h3 style='font-family:Orbitron; color:#00ffcc; font-size:18px; margin-top:20px;'>📊 INTRADAY BATTLEFIELD (5-MINUTES)</h3>", unsafe_allow_html=True)
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
        for item in news_feed[:20]: 
            q = urllib.parse.quote(item['NEWS'])
            st.markdown(f'''
            <div class="news-box">
                <div class="news-topic-header">{item["TOPIC"]}</div>
                <div class="news-text"><a href="https://www.google.com/search?q={q}" target="_blank">{item["NEWS"]}</a></div>
            </div>''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Scanner sedang berjalan namun belum ada saham yang lolos kriteria agresif TJL saat ini.")

st.caption("PREDATOR QUANTUM PRO | UNIFIED INTRADAY SCALPING ENGINE")
