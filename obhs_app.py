import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. KONFIGURASI VISUAL (RUPS EDITION)
# ==========================================
st.set_page_config(page_title="QUANTUM TITAN V41 (RUPS)", layout="wide", page_icon="🗳️")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #E0E0E0; font-family: 'Consolas', monospace; }
    
    /* JUDUL */
    .titan-title { 
        color: #00FFFF; /* Cyan Neon */
        font-size: 32px; 
        font-weight: 900; 
        text-align: center; 
        margin-bottom: 20px; 
        border-bottom: 3px solid #00FFFF;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
    }
    
    /* CARD */
    .signal-card { 
        background-color: #0A0A0A; 
        border: 1px solid #333; 
        padding: 12px; 
        border-radius: 6px; 
        margin-bottom: 10px; 
        transition: transform 0.1s;
    }
    .signal-card:hover { border-color: #00FF41; background-color: #111; transform: scale(1.01); }
    
    .ticker-head { font-size: 22px; font-weight: bold; color: #00FF41; }
    .price-tag { font-size: 18px; color: #FFF; float: right; font-weight:bold; }
    
    /* BADGES */
    .badge-sq { background-color: #FF00FF; color: white; padding: 2px 8px; font-size: 11px; font-weight:bold; border-radius:4px; }
    .badge-bo { background-color: #00FF41; color: black; padding: 2px 8px; font-size: 11px; font-weight:bold; border-radius:4px; }
    
    .details { font-size: 12px; color: #AAA; margin-top: 5px; }
    .highlight { color: #FFFF00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. WATCHLIST RAKSASA + RUPS LIST
# ==========================================

# --- GENG BARU: MINTA RESTU (RUPSLB/AKSI KORPORASI) ---
# Saham-saham ini sering minta persetujuan untuk Merger, RI, atau Restrukturisasi
G_RUPS_ACTION = "FREN, EXCL, NOBU, BABP, WIKA, PTPP, WSKT, GIAA, GMFI, KAEF, BUMI, ADRO, ITMG, JSMR, TPI"

# --- GENG LAMA (KONGLOMERAT) ---
G_DANANTARA = "BBRI, BMRI, BBNI, BBTN, TLKM, PGEO, ANTM, TINS, PTBA, INCO, SMGR, JSMR"
G_PRAJOGO = "BREN, TPIA, BRPT, CUAN, PTRO"
G_ISAM_HASHIM = "JARR, PTON, PSAB, DKFT, PMMP"
G_BAKRIE = "BUMI, BRMS, ENRG, DEWA, BNBR, UNSP, VIVA"
G_SALIM = "AMMN, INDF, ICBP, LSIP, SIMP, META, DNET"
G_SINARMAS = "INKP, TKIM, BSDE, DMAS, FREN, SMAR"
G_ASTRA = "ASII, UNTR, AALI, AUTO"
G_TRIPUTRA = "TAPG, DSNG, DRMA, ASSA, ADRO"
G_TANOKO = "CLEO, AVIA, PEVE"
G_DJARUM = "BBCA, TOWR, BELI"
G_LIPPO = "LPKR, LPPF, MLPL, MPPA, SILO"
G_MNC = "KPIG, BHIT, MNCN, IPTV"
G_PANIN = "PNLF, PNBN, PNIN, PANS"
G_VIRAL = "GOTO, ARTO, BUKA, EMTK, DADA, RMKE, FAST, MUTU, CBRE, IMPC"

# Gabungkan Semua (Ada duplikasi gpp, nanti mesin otomatis handle)
FULL_TITAN_LIST = f"{G_RUPS_ACTION}, {G_DANANTARA}, {G_PRAJOGO}, {G_ISAM_HASHIM}, {G_BAKRIE}, {G_SALIM}, {G_SINARMAS}, {G_ASTRA}, {G_TRIPUTRA}, {G_TANOKO}, {G_DJARUM}, {G_LIPPO}, {G_MNC}, {G_PANIN}, {G_VIRAL}"

# ==========================================
# 3. ENGINE (QUANTUM LOGIC)
# ==========================================
def scan_stock(ticker):
    try:
        # Tarik Data
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        
        # --- INDIKATOR ---
        # 1. Trend
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # 2. RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. BB Squeeze
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        df['Width'] = ((df['Upper'] - df['Lower']) / df['MA20']) * 100
        
        # 4. Volume
        df['VolMA'] = df['Volume'].rolling(20).mean()
        df['VolRatio'] = df['Volume'] / df['VolMA']
        
        last = df.iloc[-1]
        
        # --- LOGIC ---
        trend_ok = last['Close'] > last['EMA50']
        rsi_ok = (last['RSI'] > 45) and (last['RSI'] < 80)
        
        status = ""
        
        # TIPE 1: SQUEEZE (AKUMULASI/NGETEM)
        if trend_ok and rsi_ok and last['Width'] < 15:
            status = "SQUEEZE"
            
        # TIPE 2: BREAKOUT (MELEDAK)
        elif trend_ok and last['RSI'] > 50 and last['VolRatio'] > 1.3:
            status = "BREAKOUT"
            
        if status:
            change_pct = ((last['Close'] - last['Open']) / last['Open']) * 100
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Price": int(last['Close']),
                "Change": round(change_pct, 2),
                "RSI": round(last['RSI'], 1),
                "Vol": round(last['VolRatio'], 1),
                "Width": round(last['Width'], 1),
                "Status": status
            }
        return None
        
    except:
        return None

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.markdown("<div class='titan-title'>🗳️ QUANTUM TITAN V41 (RUPS)</div>", unsafe_allow_html=True)
st.caption("SCANNING: SAHAM KONGLO + SAHAM 'MINTA RESTU' (RUPSLB/MERGER/RI)")

with st.expander("📝 EDIT WATCHLIST", expanded=False):
    tickers_input = st.text_area("DAFTAR SAHAM:", FULL_TITAN_LIST, height=200)

if st.button("🚀 SCAN MARKET SEKARANG", type="primary"):
    # Bersihkan input (Remove duplicate)
    raw_list = tickers_input.replace("\n", "").split(",")
    # Set() untuk membuang saham dobel (misal BUMI ada di Bakrie & RUPS)
    stock_list = list(set([t.strip().upper() + ".JK" for t in raw_list if t.strip()]))
    
    st.write(f"🔍 Membedah {len(stock_list)} saham potensial...")
    
    bar = st.progress(0)
    results = []
    
    for i, stock in enumerate(stock_list):
        data = scan_stock(stock)
        if data: results.append(data)
        bar.progress((i + 1) / len(stock_list))
        
    bar.empty()
    
    if results:
        sq_list = [r for r in results if r['Status'] == "SQUEEZE"]
        bo_list = [r for r in results if r['Status'] == "BREAKOUT"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### ⚛️ SQUEEZE ({len(sq_list)})")
            st.caption("Fase Ngetem/Sideways. Menunggu Hasil RUPS/Pengumuman.")
            if sq_list:
                sq_list = sorted(sq_list, key=lambda x: x['Width'])
                for r in sq_list:
                    color = "#00FF41" if r['Change'] >= 0 else "#FF0000"
                    st.markdown(f"""
                    <div class='signal-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span class='ticker-head'>{r['Ticker']}</span>
                            <span class='badge-sq'>SQUEEZE</span>
                        </div>
                        <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
                            <div class='details'>
                                BB Width: <span class='highlight'>{r['Width']}%</span><br>
                                RSI: {r['RSI']}
                            </div>
                            <div style='text-align:right;'>
                                <span class='price-tag'>Rp {r['Price']}</span><br>
                                <small style='color:{color}'>{r['Change']}%</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("Tidak ada saham Squeeze.")
                
        with col2:
            st.markdown(f"### 🚀 BREAKOUT ({len(bo_list)})")
            st.caption("Volume Masuk. Pasar Merespon Berita.")
            if bo_list:
                bo_list = sorted(bo_list, key=lambda x: x['Vol'], reverse=True)
                for r in bo_list:
                    color = "#00FF41" if r['Change'] >= 0 else "#FF0000"
                    st.markdown(f"""
                    <div class='signal-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span class='ticker-head'>{r['Ticker']}</span>
                            <span class='badge-bo'>BREAKOUT</span>
                        </div>
                        <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
                            <div class='details'>
                                Volume: <span class='highlight'>{r['Vol']}x</span> Avg<br>
                                RSI: {r['RSI']}
                            </div>
                            <div style='text-align:right;'>
                                <span class='price-tag'>Rp {r['Price']}</span><br>
                                <small style='color:{color}'>{r['Change']}%</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("Tidak ada saham Terbang.")
                
    else:
        st.warning("Pasar sepi, Bos. Tidak ada sinyal valid.")
