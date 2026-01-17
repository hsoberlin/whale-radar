import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. VISUAL SETUP (MONITOR MODE)
# ==========================================
st.set_page_config(page_title="QUANTUM TITAN V42", layout="wide", page_icon="📡")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #E0E0E0; font-family: 'Consolas', monospace; }
    
    /* JUDUL */
    .titan-title { 
        color: #00FFFF; font-size: 30px; font-weight: 900; text-align: center; 
        margin-bottom: 20px; border-bottom: 2px solid #00FFFF;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    
    /* SIGNAL CARD */
    .signal-card { background-color: #111; border: 1px solid #333; padding: 12px; border-radius: 5px; margin-bottom: 10px; }
    .ticker-head { font-size: 20px; font-weight: bold; color: #00FF41; }
    .price-tag { font-size: 16px; color: #FFF; float: right; font-weight:bold; }
    .badge-sq { background-color: #D300D3; color: white; padding: 2px 6px; font-size: 10px; border-radius:3px; }
    .badge-bo { background-color: #00CC00; color: black; padding: 2px 6px; font-size: 10px; border-radius:3px; }
    
    /* TABLE MONITOR */
    .monitor-table { font-size: 12px; width: 100%; border-collapse: collapse; }
    .monitor-table th { text-align: left; color: #888; border-bottom: 1px solid #444; padding: 5px; }
    .monitor-table td { padding: 5px; border-bottom: 1px solid #222; color: #DDD; }
    .val-vol { color: #FFFF00; font-weight: bold; }
    .val-width { color: #00FFFF; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. WATCHLIST (FULL RUPS + KONGLO)
# ==========================================
G_RUPS = "FREN, EXCL, NOBU, BABP, WIKA, PTPP, WSKT, GIAA, GMFI, KAEF, BUMI, ADRO, ITMG"
G_DANANTARA = "BBRI, BMRI, BBNI, BBTN, TLKM, PGEO, ANTM, TINS, PTBA, INCO, SMGR, JSMR"
G_PRAJOGO = "BREN, TPIA, BRPT, CUAN, PTRO"
G_ISAM = "JARR, PTON, PSAB, DKFT, PMMP"
G_BAKRIE = "BUMI, BRMS, ENRG, DEWA, BNBR, VIVA"
G_SALIM = "AMMN, INDF, ICBP, LSIP, META"
G_SINARMAS = "INKP, TKIM, BSDE, FREN"
G_ASTRA = "ASII, UNTR, AALI, AUTO"
G_TRIPUTRA = "TAPG, DSNG, DRMA, ADRO"
G_TANOKO = "CLEO, AVIA, PEVE"
G_DJARUM = "BBCA, TOWR, BELI"
G_LIPPO = "LPKR, LPPF, MLPL, SILO"
G_MNC = "KPIG, BHIT, MNCN, IPTV"
G_PANIN = "PNLF, PNBN, PNIN"
G_VIRAL = "GOTO, ARTO, EMTK, DADA, RMKE, FAST, MUTU, CBRE, IMPC"

FULL_TITAN_LIST = f"{G_RUPS}, {G_DANANTARA}, {G_PRAJOGO}, {G_ISAM}, {G_BAKRIE}, {G_SALIM}, {G_SINARMAS}, {G_ASTRA}, {G_TRIPUTRA}, {G_TANOKO}, {G_DJARUM}, {G_LIPPO}, {G_MNC}, {G_PANIN}, {G_VIRAL}"

# ==========================================
# 3. ENGINE
# ==========================================
def scan_stock(ticker, risky_mode=False):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        
        # Indikator
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        df['Width'] = ((df['Upper'] - df['Lower']) / df['MA20']) * 100
        
        df['VolMA'] = df['Volume'].rolling(20).mean()
        df['VolRatio'] = df['Volume'] / df['VolMA']
        
        last = df.iloc[-1]
        
        # LOGIC
        # Kalau Risky Mode ON, kita abaikan filter EMA50 (Trend)
        trend_ok = True if risky_mode else (last['Close'] > last['EMA50'])
        
        # Sinyal Strict
        status = ""
        if trend_ok and (40 < last['RSI'] < 80) and last['Width'] < 15:
            status = "SQUEEZE"
        elif trend_ok and last['RSI'] > 50 and last['VolRatio'] > 1.3:
            status = "BREAKOUT"
            
        change_pct = ((last['Close'] - last['Open']) / last['Open']) * 100
        
        return {
            "Ticker": ticker.replace(".JK", ""),
            "Price": int(last['Close']),
            "Change": round(change_pct, 2),
            "RSI": round(last['RSI'], 1),
            "Vol": round(last['VolRatio'], 1),
            "Width": round(last['Width'], 1),
            "Status": status,
            "Trend": "UP" if last['Close'] > last['EMA50'] else "DOWN"
        }
    except:
        return None

# ==========================================
# 4. DASHBOARD
# ==========================================
st.markdown("<div class='titan-title'>📡 QUANTUM TITAN V42</div>", unsafe_allow_html=True)

with st.expander("📝 EDIT WATCHLIST", expanded=False):
    tickers_input = st.text_area("DAFTAR SAHAM:", FULL_TITAN_LIST, height=150)

# OPSI BARU: MODE NEKAT
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    risky = st.checkbox("🔥 MODE NEKAT (Abaikan Trend Filter)")
    st.caption("Centang ini jika ingin melihat saham Downtrend yang Squeeze/Rebound.")

if st.button("🚀 SCAN MARKET", type="primary"):
    raw_list = tickers_input.replace("\n", "").split(",")
    stock_list = list(set([t.strip().upper() + ".JK" for t in raw_list if t.strip()]))
    
    st.write(f"🔍 Membedah {len(stock_list)} saham... (Mode Nekat: {'ON' if risky else 'OFF'})")
    
    bar = st.progress(0)
    all_data = []
    
    for i, stock in enumerate(stock_list):
        data = scan_stock(stock, risky_mode=risky)
        if data: all_data.append(data)
        bar.progress((i + 1) / len(stock_list))
        
    bar.empty()
    
    if all_data:
        # 1. FILTER SINYAL UTAMA (SQUEEZE & BREAKOUT)
        sq_list = [r for r in all_data if r['Status'] == "SQUEEZE"]
        bo_list = [r for r in all_data if r['Status'] == "BREAKOUT"]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"##### ⚛️ SQUEEZE ({len(sq_list)})")
            if sq_list:
                for r in sorted(sq_list, key=lambda x: x['Width']):
                    clr = "#00FF00" if r['Change']>=0 else "#FF0000"
                    st.markdown(f"""<div class='signal-card'><span class='ticker-head'>{r['Ticker']}</span> <span class='badge-sq'>SQZ</span>
                    <span class='price-tag' style='color:{clr}'>{r['Price']}</span><br><small>Width: {r['Width']}% | RSI: {r['RSI']}</small></div>""", unsafe_allow_html=True)
            else: st.info("Nihil.")
            
        with c2:
            st.markdown(f"##### 🚀 BREAKOUT ({len(bo_list)})")
            if bo_list:
                for r in sorted(bo_list, key=lambda x: x['Vol'], reverse=True):
                    clr = "#00FF00" if r['Change']>=0 else "#FF0000"
                    st.markdown(f"""<div class='signal-card'><span class='ticker-head'>{r['Ticker']}</span> <span class='badge-bo'>BO</span>
                    <span class='price-tag' style='color:{clr}'>{r['Price']}</span><br><small>Vol: {r['Vol']}x | RSI: {r['RSI']}</small></div>""", unsafe_allow_html=True)
            else: st.info("Nihil.")

        # 2. TABEL PANTAU (DATA MENTAH) - FITUR BARU!
        st.markdown("---")
        st.markdown("### 📊 DATA MONITOR (TOP 20 VOLUME)")
        st.caption("Saham dengan aktivitas volume terbesar hari ini (Walaupun tidak breakout).")
        
        # Urutkan berdasarkan Volume Ratio Tertinggi
        sorted_all = sorted(all_data, key=lambda x: x['Vol'], reverse=True)[:20]
        
        # Tampilkan Tabel Manual (Biar stylenya masuk)
        table_html = "<table class='monitor-table'><tr><th>TICKER</th><th>PRICE</th><th>CHANGE</th><th>VOL (xAvg)</th><th>BB WIDTH</th><th>RSI</th><th>TREND</th></tr>"
        
        for r in sorted_all:
            color_chg = "#00FF00" if r['Change'] >= 0 else "#FF4444"
            trend_icon = "↗️" if r['Trend'] == "UP" else "↘️"
            table_html += f"""
            <tr>
                <td><b>{r['Ticker']}</b></td>
                <td>{r['Price']}</td>
                <td style='color:{color_chg}'>{r['Change']}%</td>
                <td class='val-vol'>{r['Vol']}x</td>
                <td class='val-width'>{r['Width']}%</td>
                <td>{r['RSI']}</td>
                <td>{trend_icon}</td>
            </tr>
            """
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
    else:
        st.error("Gagal mengambil data. Coba refresh atau cek koneksi.")
