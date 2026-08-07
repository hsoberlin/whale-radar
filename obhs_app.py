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
st.set_page_config(page_title="QUANTUM PRO - LVP 900+ ENGINE", layout="wide")
warnings.filterwarnings("ignore")

# High Frequency Refresh: 5 Menit
st_autorefresh(interval=300000, key="quantum_lvp_900_sync")

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
        font-weight: 900; font-size: 30px !important;
        background: linear-gradient(90deg, #00ffcc, #ff0055);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
    }
    
    .pixel-container {
        display: flex; gap: 5px; margin-bottom: 5px;
        background: #0a0e14; padding: 5px; border-radius: 5px; border: 1px solid #333;
    }
    .pixel-metric { flex: 1; text-align: center; font-family: 'JetBrains Mono'; }
    .pixel-title { font-size: 8px; color: #888; display: block; margin-bottom: 2px; }
    .pixel-value-up { color: #00ffcc; font-weight: 900; font-size: 12px; }
    .pixel-value-down { color: #ff0055; font-weight: 900; font-size: 12px; }
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

# --- 3. DATABASE 900+ TICKER BEI LENGKAP ---
MASTER_TICKERS = [
    "AALI", "ABBA", "ABMM", "ACES", "ACST", "ADCP", "ADMR", "ADRO", "AGAR", "AGII", "AGRO", "AHAP", "AIMS", "AKKU", "AKPI", "AKRA", "ALDO", "ALKA", "ALII", "AMAR", "AMFG", "AMIN", "AMMN", "AMRT", "ANJT", "ANTM", "APEX", "APIC", "APLN", "ARCI", "ARka", "ARKO", "ARMY", "ARNA", "ARTA", "ARTI", "ARTO", "ASBI", "ASD", "ASHA", "ASII", "ASJT", "ASLC", "ASMI", "ASRI", "ASSA", "ATIC", "AUTO", "AVIA", "AWAN", "AXIO",
    "BABP", "BACA", "BAJA", "BANK", "BAUT", "BBCA", "BBHI", "BBKP", "BBNI", "BBRI", "BBRM", "BBSI", "BBTN", "BBYB", "BCAP", "BCIC", "BDMN", "BEBS", "BEEF", "BEKS", "BELI", "BELL", "BESS", "BEST", "BFIN", "BGTG", "BHIT", "BIGI", "BIKA", "BINA", "BINO", "BIPI", "BIRD", "BISI", "BJBR", "BJTM", "BKDP", "BKSL", "BLTZ", "BLUE", "BMAS", "BMBL", "BMHS", "BMRI", "BMSR", "BMTR", "BNBA", "BNBR", "BNGA", "BNII", "BNLI", "BOBA", "BOGA", "BOLA", "BOLT", "BOSS", "BPTR", "BRAM", "BRIS", "BRMS", "BRPT", "BSBK", "BSDE", "BSML", "BSSR", "BSWD", "BTEL", "BTPS", "BUAH", "BUKA", "BULL", "BUMI", "BUVA", "BWPT", "BYAN",
    "CAKK", "CAMP", "CARE", "CARS", "CASS", "CBRE", "CCSI", "CEKA", "CENT", "CFIN", "CGAS", "CINT", "CITA", "CITY", "CLEO", "CLPI", "CMNP", "CMPP", "CMRy", "CNKO", "CNTX", "COAL", "COIN", "CPIN", "CPRO", "CRAB", "CSAP", "CSIS", "CTAR", "CTRA", "CUAN",
    "DAJK", "DATA", "DAYA", "DCII", "DEAL", "DEWA", "DFAM", "DGIK", "DGNS", "DILD", "DIVA", "DKFT", "DLTA", "DMAS", "DMMX", "DNAR", "DOID", "DPNS", "DRMA", "DSNG", "DSSA", "DUCK", "DUTI", "DVLA", "DYAN",
    "EAST", "ECII", "EDGE", "EDong", "ELSA", "ELTY", "EMDE", "EMTK", "ENAK", "ENRG", "ENZO", "EPAC", "ERAA", "ERTX", "ESIP", "ESSA", "ESTA", "ETWA", "EXCL",
    "FAPA", "FAST", "FASW", "FILM", "FIRE", "FISH", "FITT", "FPNI", "FREN", "FUTR",
    "GAMA", "GDST", "GEPS", "GEMS", "GGRM", "GIAA", "GJTL", "GLOB", "GLVA", "GMFI", "GMTD", "GOLD", "GOTO", "GPRA", "GPSO", "GRPH", "GTBO", "GTSI", "GULA", "GWSA", "GZCO",
    "HAIS", "HALO", "HADE", "HEAL", "HELI", "HERO", "HEXA", "HITS", "HKMU", "HMSP", "HOKI", "HOME", "HOMI", "HOST", "HRME", "HRTA", "HRUM",
    "IATA", "IBFN", "IBST", "ICBP", "ICON", "IDPR", "IGAR", "IIKP", "IKAN", "IMAS", "IMJS", "IMPC", "INAF", "INAI", "INCF", "INCO", "INDF", "INDO", "INDR", "INDS", "INDY", "INKP", "INPC", "INPP", "INPS", "INTA", "INTP", "IPCC", "IPCM", "IPPE", "IPTV", "IRRA", "ISAT", "ISSP", "ITIC", "ITMA", "ITMG",
    "JAST", "JATI", "JAYA", "JAYS", "JECC", "JGLE", "JIHD", "JKON", "JMAS", "JPFA", "JRPT", "JSPT", "JTPE",
    "KAEF", "KARW", "KAYU", "KBLI", "KBLM", "KBLV", "KDSI", "KEEN", "KEJU", "KELO", "KENN", "KIAS", "KIJA", "KINO", "KIOS", "KJEN", "KKGI", "KLBF", "KOBX", "KOIN", "KOPI", "KOTA", "KPAL", "KPIG", "KRAH", "KRAS", "KREN",
    "LABA", "LAND", "LAPD", "LCGP", "LCKM", "LEAD", "LFLO", "LGIS", "LINK", "LION", "LPCK", "LPGI", "LPIN", "LPKR", "LPPF", "LPPS", "LRNA", "LSIP", "LTLS", "LUCK", "LUCY",
    "MAMI", "MAIN", "MAPA", "MAPB", "MAPI", "MARI", "MARK", "MASA", "MAYA", "MBAP", "MBMA", "MBSS", "MCAS", "MCOR", "MDKA", "MDKI", "MDLA", "MDLN", "MEDC", "MEGA", "MEJA", "MENN", "MERK", "META", "MFIN", "MFMI", "MGLV", "MICE", "MIDI", "MIKA", "MINA", "MIRA", "MITI", "MKNT", "MKPI", "MLBI", "MLIA", "MLPL", "MLPT", "MMIX", "MNCN", "MOLI", "MORA", "MPMX", "MPPA", "MPRO", "MRAT", "MREI", "MSIN", "MSKY", "MTDL", "MTEL", "MTLA", "MTMH", "MTPS", "MTRY", "MUBA", "MASA", "MYOH", "MYOR", "MYRX", "MYTX",
    "NANO", "NAPS", "NASA", "NATO", "NCKL", "NELY", "NEST", "NFCX", "NICK", "NICL", "NIKL", "NINE", "NISP", "NOBU", "NPGF", "NRCA", "NUSA", "NZIA",
    "OASA", "OBMD", "OCAP", "OASA", "OILS", "OKAS", "OMED", "PADI", "PALM", "PAMG", "PANI", "PANR", "PANS", "PBID", "PBRX", "PBSA", "PCAR", "PEGE", "PEHA", "PGAS", "PGEO", "PICO", "PJAA", "PKPK", "PLIN", "PMMP", "PNBN", "PNBS", "PNIN", "PNLF", "POLA", "POLL", "POLU", "POLY", "POOL", "PORT", "POWER", "PPGL", "PPRE", "PPRO", "PTPP", "PRAS", "PRDA", "PSAB", "PSDN", "PSGO", "PSKT", "PTBA", "PTIS", "PTPW", "PTRO", "PUDP", "PURA", "PZZA",
    "RAJA", "RALS", "RANC", "RBMS", "RDTX", "REAL", "RELI", "RICY", "RIGS", "RIMO", "RISE", "ROCK", "ROTI", "RSGK", "RUIS",
    "SAFE", "SAGE", "SAME", "SAMF", "SAPX", "SBAT", "SBMA", "SCCO", "SCMA", "SCNP", "SCPI", "SDMU", "SDPC", "SDRA", "SEMA", "SGER", "SGRO", "SHIP", "SHID", "SIDO", "SILO", "SIMA", "SIMP", "SINI", "SKBM", "SKLT", "SKRN", "SKYB", "SLIS", "SMAR", "SMBR", "SMCB", "SMDM", "SMDR", "SMGR", "SMKL", "SMMA", "SMRA", "SMRU", "SMSM", "SOCI", "SOFA", "SONA", "SPMA", "SPTO", "SRIL", "SRSN", "SRTG", "SSIA", "SSMS", "SSTC", "STAA", "STTP", "SULA", "SULI", "SUPR", "SURI", "SWAT",
    "TACO", "TAMU", "TAPG", "TARA", "TAXI", "TAYS", "TBIG", "TBLA", "TCID", "TCPI", "TEBE", "TECH", "TELE", "TFAS", "TGKA", "TGRA", "TIFA", "TINS", "TIRA", "TKIM", "TLKM", "TMAS", "TOBA", "TOOL", "TOPR", "TOTL", "TOTO", "TOWR", "TPIA", "TPMA", "TRAM", "TRIL", "TRIM", "TRIN", "TRIS", "TRJA", "TRST", "TRUE", "TRUK", "TSPC", "TUGU", "TURI",
    "UFOE", "ULTJ", "UNIC", "UNIQ", "UNIT", "UNSP", "UNTR", "UNVR", "URBN",
    "VAST", "VICI", "VICO", "VINS", "VIVA", "VKTR", "VOKS", "VRNA", "VTNY",
    "WAPO", "WARE", "WART", "WASI", "WASK", "WEGE", "WEHA", "WGSH", "WIKA", "WIM", "WINS", "WIRG", "WIIM", "WMUU", "WOMF", "WOOD", "WOWS", "WSBP", "WSKT", "WTON",
    "XASI",
    "YELO", "PACK",
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

# --- 5. LOW VOLUME PULLBACK (LVP) SCANNER ENGINE (BATCH 900+) ---
def scan_lvp_market():
    results = []
    intel_map, _, news_tickers = fetch_intel()
    all_tickers = list(set(MASTER_TICKERS + news_tickers))
    tickers_jk = [f"{t}.JK" for t in all_tickers]
    
    # 5.1 BATCH DOWNLOAD 900+ TICKERS (Dibagi per blok 200 ticker agar tidak timeout di yfinance)
    batch_daily_frames = []
    chunk_size = 200
    
    for i in range(0, len(tickers_jk), chunk_size):
        chunk = tickers_jk[i:i+chunk_size]
        try:
            df_chunk = yf.download(chunk, period="1d", interval="1d", group_by='ticker', progress=False)
            if not df_chunk.empty:
                batch_daily_frames.append(df_chunk)
        except: continue
        
    if not batch_daily_frames:
        return [], "ERROR: Gagal mengunduh data bursa."

    surviving_tickers = []
    
    # Proses penyaringan Value > 50 Miliar
    for ticker in all_tickers:
        try:
            ticker_jk = f"{ticker}.JK"
            df_d = None
            
            for df_b in batch_daily_frames:
                if ticker_jk in df_b.columns.levels[0]:
                    df_d = df_b[ticker_jk].dropna(how='all')
                    break
                    
            if df_d is None or df_d.empty: continue
            
            last_vol = df_d['Volume'].iloc[-1]
            last_close = df_d['Close'].iloc[-1]
            total_value = last_vol * last_close
            
            # FILTER 1: VALUE DI ATAS 50 MILIAR RUPIAH
            if total_value >= 50_000_000_000:
                surviving_tickers.append(ticker)
        except:
            continue

    # 5.2 INTRADAY SCAN (Hanya untuk emiten likuid yang lolos filter > 50M)
    for ticker in surviving_tickers:
        try:
            s = yf.Ticker(f"{ticker}.JK")
            df_intra = s.history(period="1d", interval="5m")
            if df_intra.empty or len(df_intra) < 3: continue
            
            df_intra['Candle_Value'] = df_intra['Volume'] * df_intra['Close']
            
            hod_val = df_intra['High'].max()
            hod_idx = df_intra['High'].idxmax()
            curr_price = df_intra['Close'].iloc[-1]
            
            # FILTER 2: HARGA SEDANG TURUN DARI HOD
            if curr_price >= hod_val: continue
                
            phase_up = df_intra.loc[:hod_idx]
            phase_down = df_intra.loc[hod_idx:].iloc[1:]
            
            if len(phase_down) == 0: continue
            
            val_up = phase_up['Candle_Value'].sum()
            val_down = phase_down['Candle_Value'].sum()
            
            if val_up == 0: continue
            
            # FILTER 3: VALUE TURUN DI BAWAH 1/5 (20%) DARI VALUE NAIK
            ratio = val_down / val_up
            if ratio >= 0.20: continue
            
            score = 80 - (ratio * 100)
            
            thesis_points = []
            thesis_points.append(f"🏢 <b>LIQUIDITY:</b> Emiten lapis atas/likuid. Total transaksi tembus <b>Rp {(val_up+val_down)/1_000_000_000:,.1f} Miliar</b>.")
            thesis_points.append(f"📈 <b>ACCUMULATION:</b> Didorong ke HOD (Rp {hod_val:,.0f}) dengan suntikan dana <b>Rp {val_up/1_000_000_000:,.1f} Miliar</b>.")
            
            color_ratio = "#00ffcc" if ratio < 0.10 else "#ffd166"
            thesis_points.append(f"📉 <b>LOW VOL RETRACEMENT:</b> Koreksi ke Rp {curr_price:,.0f} dengan tekanan jual minim. "
                                 f"Value buangan hanya <b>Rp {val_down/1_000_000_000:,.1f} Miliar (<span style='color:{color_ratio}'>{ratio*100:.1f}%</span> dari fase naik)</b>.")
            
            has_news = ticker in intel_map
            if has_news:
                score += 20
                thesis_points.append(f"📰 <b>CATALYST DETECTED:</b> {intel_map[ticker]['title'][:65]}...")
                
            thesis_points.append(f"<div style='margin-top:8px; padding:5px; border-top:1px dashed #333; font-family:JetBrains Mono; font-size:11px;'>"
                                 f"💎 <b>KESIMPULAN:</b> Koreksi sehat di bawah 1/5 volume akumulasi. Potensi pantulan tinggi di area Rp {curr_price:,.0f}."
                                 f"</div>")

            final_thesis = "<br>".join(thesis_points)
            porto = "STRONG BUY (LVP)" if ratio < 0.10 else "BUY (LVP)"
            
            results.append({
                "SYMBOL": ticker, "CONF": min(score, 100), 
                "VAL_UP_B": round(val_up / 1_000_000_000, 1), 
                "VAL_DOWN_B": round(val_down / 1_000_000_000, 1),
                "RATIO": round(ratio * 100, 1), 
                "PRICE": int(curr_price), "HOD": int(hod_val), 
                "THESIS": final_thesis, "PORTO": porto,
                "RAW_INTRA": df_intra
            })
        except: continue
        
    return results, f"SCANNING {len(MASTER_TICKERS)}+ BEI STOCKS ACTIVE"

# --- 6. INTRADAY PIXEL CHART (5-MINUTE) ---
def render_intraday_chart(target):
    df = target['RAW_INTRA']
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.75, 0.25])

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#00ffcc', decreasing_line_color='#ff0055', name="Price"), row=1, col=1)
    
    fig.add_hline(y=target['HOD'], line_dash="dash", line_color="#ff0055", line_width=2, 
                  annotation_text="High of Day (HOD)", annotation_position="top right", 
                  annotation_font_color="#ff0055", row=1, col=1)
    
    colors_vol = ['#00ffcc' if r >= o else '#ff0055' for r, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_vol, name='Volume'), row=2, col=1)

    title_text = f"<b style='color: white; font-size: 18px;'>{target['SYMBOL']}</b> <span style='color: #00ffcc; font-size:11px;'>| RATIO: {target['RATIO']}%</span>"
    
    fig.update_layout(
        template="plotly_dark", height=430, 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=45, b=10), title=dict(text=title_text, x=0.02, y=0.96)
    )
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    return fig

# --- 7. INTERFACE RENDERING LOGIC ---
st.markdown('<div class="header-container"><div class="header-title">PREDATOR QUANTUM PRO - LVP 900+ ENGINE</div></div>', unsafe_allow_html=True)

loading_placeholder = st.empty()
loading_placeholder.markdown(f'<div class="blink">SCANNING 900+ BEI STOCKS: VALUE > 50B & PULLBACK < 20%...</div>', unsafe_allow_html=True)

data, market_pulse = scan_lvp_market()
_, news_feed, _ = fetch_intel()
loading_placeholder.empty()

st.markdown(f"<div style='text-align:center; margin-bottom:20px; color:#00ffcc; font-family:Orbitron; letter-spacing:2px; font-size:13px;'>📡 {market_pulse}</div>", unsafe_allow_html=True)

if data:
    df_display = pd.DataFrame(data).sort_values(by="RATIO", ascending=True)
    col_main, col_news = st.columns([3, 1])
    
    with col_main:
        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px;'>📉 LVP RETRACEMENT SCANNER (900+ UNIVERSE)</h3>", unsafe_allow_html=True)
        st.dataframe(df_display[["SYMBOL", "RATIO", "VAL_UP_B", "VAL_DOWN_B", "PRICE", "HOD", "PORTO"]], column_config={
            "RATIO": st.column_config.ProgressColumn("DUMP RATIO", min_value=0, max_value=20, format="%.1f%%"),
            "VAL_UP_B": st.column_config.NumberColumn("VALUE NAIK", format="Rp %.1f B"),
            "VAL_DOWN_B": st.column_config.NumberColumn("VALUE TURUN", format="Rp %.1f B 💧"),
            "PRICE": st.column_config.NumberColumn("CURR PRICE"),
            "HOD": st.column_config.NumberColumn("HOD"),
            "PORTO": st.column_config.TextColumn("ACTION")
        }, use_container_width=True, hide_index=True, height=250)

        top_targets = df_display.head(4).to_dict('records')
        
        if top_targets:
            st.markdown("<h3 style='font-family:Orbitron; color:#00ffcc; font-size:18px; margin-top:20px;'>📊 INTRADAY BATTLEFIELD (5-MINUTES)</h3>", unsafe_allow_html=True)
            for i in range(0, len(top_targets), 2):
                cols = st.columns(2) 
                batch = top_targets[i:i+2] 
                for idx, target in enumerate(batch):
                    with cols[idx]:
                        st.markdown(f"""
                        <div class="pixel-container">
                            <div class="pixel-metric"><span class="pixel-title">DUMP RATIO</span><span class="pixel-value-up">{target['RATIO']}%</span></div>
                            <div class="pixel-metric"><span class="pixel-title">VAL ACCUM</span><span class="pixel-value-up">{target['VAL_UP_B']}M</span></div>
                            <div class="pixel-metric"><span class="pixel-title">VAL DISTRO</span><span class="pixel-value-neutral">{target['VAL_DOWN_B']}M</span></div>
                            <div class="pixel-metric"><span class="pixel-title">VS HOD</span><span class="pixel-value-down">-{round(((target['HOD'] - target['PRICE'])/target['HOD'])*100, 1)}%</span></div>
                        </div>""", unsafe_allow_html=True)
                        fig = render_intraday_chart(target)
                        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<h3 style='font-family:Orbitron; color:#ff0055; font-size:18px; margin-top:10px;'>📝 INSTITUTIONAL ANALYSIS THESIS</h3>", unsafe_allow_html=True)
        for row in top_targets:
            st.markdown(f"""
            <div class="thesis-box">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color:#ff0055; font-weight:bold; font-size:14px;">{row['SYMBOL']}</span>
                    <span style="color:#00ffcc; font-family: 'JetBrains Mono'; font-size: 10px;">{row['PORTO']}</span>
                </div>
                <div class="thesis-header">LVP ENTRY LOGIC:</div>
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
    st.info("Scanner 900+ aktif. Belum ada saham dengan transaksi > 50 Miliar yang mengalami koreksi kering di bawah 20% saat ini.")

st.caption("PREDATOR QUANTUM PRO | 900+ UNIVERSE LVP SCALPING ENGINE")
