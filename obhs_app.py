"""
TRENDLINE ENGINE
================================================================
Mesin sistem "Breakout Garis Tren + Trailing Tangga" saham IDX.
Dipakai bersama oleh backtest dan laporan harian, jadi angka live
selalu konsisten dengan backtest yang sudah diaudit.

ATURAN v1.2 (21 Nov 2026) — akun FD (ANALISA FUNDAMENTAL), modal komitmen 100 jt
- Sinyal: garis turun dari pivot ZigZag 3xATR(14), minimal 3 titik sentuh,
  tidak ada CLOSE di atas garis (wick boleh). Sinyal saat close >= garis +
  0,25 ATR dan rata-rata value 20 hari >= Rp1 M.
- Beli: order pre-opening besok, harga batas = close sinyal +10% (dibulatkan
  ke fraksi BEI), lot = 5 jt / close. Kas dikunci sebesar lot x batas.
  Sinyal dilewati kalau kas kurang. Satu saham satu posisi.
- SL (dicek di close, tidak pernah turun) = yang tertinggi dari:
    a. garis sinyal - 1 ATR (dikunci di hari sinyal)
    b. level garis merah tangga (lower high, 4 ukuran swing, skala log)
       yang tembus setelah sinyal, dikunci di hari tembus
    c. high tertinggi sejak beli - 4 ATR
- Jual: besok open setelah close < SL. Kalau volume 0 atau ARB terkunci
  (bar datar turun >= 6,5%), penjualan ditunda.
- Pagar jual (v1.1): kalau dalam satu hari minimal 5 posisi close < SL DAN
  IHSG hari itu turun >= 1%, jual posisi-posisi itu ditunda satu hari
  (sekali per posisi). Besok sore dicek ulang terhadap SL.
- Suspensi (v1.2): posisi yang sudah kena suspensi ke-3 selama dipegang (volume 0)
  dijual di open hari pertama dibuka (antri pre-opening di harga batas ARB).
- Modal komitmen: ukuran posisi & hasil dihitung dari komitmen 100 jt; uang
  disetor bertahap sesuai kebutuhan order (baris "Setor sebelum pre-opening").
- Biaya: beli 0,15%, jual 0,25%, materai Rp10.000 per hari kalau nilai
  transaksi hari itu > Rp10 jt.
- Red-flag & riwayat suspend hanya PERINGATAN, bukan larangan beli.
"""
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

VERSION = "1.2 (21 Nov 2026)"

# ---------------------------------------------------------------- PARAMETER
START_DATA = "2019-01-01"      # WAJIB tetap: pivot & ATR dihitung dari awal data
MULT = 3.0                     # pivot ZigZag garis sinyal (x ATR)
MIN_TOUCH = 3
TOL_PIVOT = 0.5
MAX_ANCHOR = 8
MAX_AGE_LINE = 250
BUF_BREAK = 0.25
VAL_MIN = 1e9
SL_ATR0 = 1.0
CHAND_K = 4.0
LIMIT_PCT = 0.10
ALLOC = 5_000_000
FENCE_N = 5                    # pagar jual: minimal posisi kena SL di hari yang sama
FENCE_IHSG = -0.01             # pagar jual: IHSG hari itu turun >= 1%
IHSG_RET = None                # pd.Series return harian IHSG (diisi run_nightly / backtest)
SUSP_EXIT_N = 3                # v1.2: jual saat dibuka setelah suspensi ke-N selama dipegang (0 = mati)
AKUN = "FD"
AKUN_NAMA = "FUNDAMENTAL"
KOMITMEN = 100_000_000
MODAL_AWAL = 100_000_000
FEE_B, FEE_S = 0.0015, 0.0025
MATERAI, BATAS_MATERAI = 10_000, 10_000_000
ARB_LOCK = -0.065
RED_SCALES = [5.0, 3.0, 1.5, 0.75]
RED_AGE = {5.0: 750, 3.0: 400, 1.5: 200, 0.75: 100}
RED_BUF = 0.25
SUSP_WARN_LB = 120

RED_FLAG = set("AGAR DOOH BIKE AYAM MGLV VISI JARR PGUN TEBE MDIA SINI FORU PIPA JGLE "
               "VKTR SGER IRSX BREN TPIA MMIX PEGE MEJA PACK".split())

IDX_TICKERS_ALL = """AADI, AALI, ABDA, ABMM, ACES, ACRO, ACST, ADCP, ADES, ADHI, ADMF, ADMG,
ADMR, ADRO, AGAR, AGII, AGRO, AGRS, AHAP, AISA, AKKU, AKPI, AKRA, AKSI,
ALDO, ALII, ALKA, ALMI, AMAG, AMAN, AMAR, AMFG, AMIN, AMMN, AMMS, AMOR,
AMRT, ANDI, ANJT, ANTM, APEX, APIC, APII, APLI, APLN, ARCI, AREA, ARGO,
ARII, ARKO, ARNA, ARTA, ARTO, ASDM, ASGR, ASHA, ASII, ASJT, ASLC, ASLI,
ASPI, ASPR, ASRI, ASRM, ASSA, ATAP, ATIC, ATLA, AUTO, AVIA, AWAN, AXIO,
AYAM, BABP, BABY, BACA, BACH, BAIK, BAJA, BALI, BANK, BATR, BAUT, BAYU,
BBCA, BBHI, BBKP, BBLD, BBMD, BBNI, BBRI, BBRM, BBSI, BBSS, BBTN, BBYB,
BCAP, BCIC, BDKR, BDMN, BEBS, BEEF, BEER, BEKS, BELI, BELL, BESS, BEST,
BFIN, BGTG, BHAT, BHIT, BIKE, BINA, BINO, BIPI, BIPP, BIRD, BISI, BJBR,
BJTM, BKDP, BKSL, BKSW, BLES, BLOG, BLTA, BLTZ, BLUE, BMAS, BMHS, BMRI,
BMSR, BMTR, BNBA, BNBR, BNGA, BNII, BNLI, BOAT, BOBA, BOGA, BOLA, BOLT,
BPFI, BPII, BPTR, BRAM, BREN, BRIS, BRMS, BRNA, BRPT, BSBK, BSDE, BSIM,
BSML, BSSR, BSWD, BTEK, BTON, BTPN, BTPS, BUAH, BUDI, BUKA, BUKK, BULL,
BUMI, BUVA, BVIC, BWPT, BYAN, CAKK, CAMP, CARE, CARS, CASA, CASH, CASS,
CBDK, CBPE, CBRE, CBUT, CCSI, CDIA, CEKA, CENT, CFIN, CGAS, CHEK, CHIP,
CINT, CITA, CITY, CLAY, CLEO, CLPI, CMNP, CMNT, CMPP, CMRY, CNKO, CNMA,
COAL, COCO, COIN, CPIN, CPRO, CRAB, CRSN, CSAP, CSIS, CSRA, CTBN, CTRA,
CUAN, CYBR, DAAZ, DADA, DART, DATA, DAYA, DCII, DEPO, DEWA, DEWI, DGIK,
DGNS, DGWG, DILD, DIVA, DKFT, DKHH, DLTA, DMAS, DMMX, DMND, DNAR, DNET,
DOID, DOOH, DOSS, DPUM, DRMA, DSFI, DSNG, DSSA, DUTI, DVLA, DWGL, DYAN,
EAST, ECII, EDGE, EKAD, ELIT, ELPI, ELSA, ELTY, EMAS, EMDE, EMMI, EMTK,
ENAK, ENRG, EPAC, EPMT, ERAA, ERAL, ERTX, ESSA, ESTA, ESTI, EURO, EXCL,
FAPA, FAST, FASW, FILM, FIRE, FISH, FITT, FMII, FOLK, FORE, FORU, FPNI,
FUJI, FUTR, FWCT, GDST, GDYR, GEMS, GGRM, GGRP, GHON, GIAA, GJTL, GLOB,
GLVA, GMFI, GMTD, GOLD, GOLF, GOOD, GOTO, GPRA, GPSO, GRIA, GRPM, GSMF,
GTBO, GTRA, GTSI, GULA, GUNA, GWSA, GZCO, HAIS, HAJJ, HALO, HATM, HBAT,
HDFA, HEAL, HELI, HERO, HEXA, HILL, HITS, HMSP, HOKI, HOMI, HOPE, HRME,
HRTA, HRUM, HUMI, HYGN, IATA, IBOS, IBST, ICBP, IDPR, IFII, IFSH, IGAR,
IKAI, IKBI, IKPM, IMAS, IMJS, IMPC, INAF, INCO, INDF, INDO, INDR, INDS,
INDY, INET, INKP, INOV, INPC, INPP, INPS, INRU, INTA, INTD, INTP, IOTF,
IPAC, IPCC, IPCM, IPOL, IPTV, IRRA, IRSX, ISAT, ISSP, ITIC, ITMA, ITMG,
JARR, JATI, JAWA, JECC, JECX, JELI, JGLE, JIHD, JKON, JMAS, JPFA, JRPT,
JSMR, JSPT, JTPE, KAEF, KAQI, KBAG, KBLI, KBLM, KBLV, KDSI, KDTN, KEEN,
KEJU, KETR, KIAS, KIJA, KING, KINO, KKGI, KLAS, KLBF, KMDS, KMTR, KOBX,
KOCI, KOKA, KONI, KOTA, KPIG, KRAS, KREN, KSIX, LABS, LAND, LAPD, LEAD,
LFLO, LIFE, LINK, LION, LIVE, LMPI, LPCK, LPGI, LPIN, LPKR, LPLI, LPPF,
LPPS, LSIP, LTLS, LUCY, MAHA, MAIN, MAPA, MAPB, MAPI, MARK, MASB, MAXI,
MAYA, MBAP, MBMA, MBSS, MCAS, MCOL, MCOR, MDIA, MDIY, MDKA, MDKI, MDLA,
MDLN, MDRN, MEDC, MEGA, MEJA, MERK, MFMI, MGLV, MGNA, MGRO, MHKI, MICE,
MIDI, MIKA, MINA, MINE, MKAP, MKPI, MKTR, MLBI, MLIA, MLPL, MLPT, MMIX,
MMLP, MNCN, MOLI, MORA, MPIX, MPMX, MPPA, MPRO, MPXL, MRAT, MREI, MSIN,
MSJA, MSKY, MSTI, MTDL, MTEL, MTFN, MTLA, MTMH, MTPS, MTWI, MUTU, MYOH,
MYOR, MYTX, NAIK, NASA, NATO, NAYZ, NCKL, NELY, NEST, NETV, NFCX, NICE,
NICK, NICL, NIKL, NINE, NIRO, NISP, NOBU, NPGF, NRCA, NSSS, NTBK, NZIA,
OASA, OBAT, OBMD, OKAS, OMED, OMRE, PACK, PADA, PADI, PALM, PAMG, PANI,
PANR, PANS, PART, PBID, PBRX, PBSA, PDES, PDPP, PEGE, PEHA, PEVE, PGAS,
PGEO, PGJO, PGUN, PIPA, PJAA, PJHB, PKPK, PLIN, PMJS, PMUI, PNBN, PNBS,
PNGO, PNIN, PNLF, PNSE, POLA, POLI, POLU, PORT, POWR, PPGL, PPRE, PPRO,
PRAY, PRDA, PRDL, PRIM, PSAB, PSAT, PSDN, PSGO, PSKT, PSSI, PTBA, PTMP,
PTMR, PTPP, PTPS, PTPW, PTRO, PTSN, PTSP, PUDP, PURA, PWON, PYFA, PZZA,
RAAM, RAJA, RALS, RANC, RANS, RATU, RBMS, RDTX, REAL, RELF, RELI, RGAS,
RIGS, RISE, RLCO, RMKE, RMKO, ROCK, RODA, RONY, ROTI, RSCH, SAFE, SAGE,
SAME, SAMF, SAPX, SATU, SCCO, SCMA, SCNP, SDMU, SDPC, SDRA, SFAN, SGER,
SGRO, SHID, SHIP, SIDO, SILO, SIMP, SINI, SIPD, SKBM, SKLT, SKRN, SLIS,
SMAR, SMBR, SMCB, SMDM, SMDR, SMGA, SMGR, SMIL, SMKL, SMLE, SMMA, SMMT,
SMRA, SMSM, SOCI, SOFA, SOHO, SOLA, SONA, SOSS, SOTS, SPMA, SPTO, SQMI,
SRAJ, SRSN, SRTG, SSIA, SSMS, SSTM, STAA, STAR, STRK, STTP, SULI, SUNI,
SUPA, SUPR, SURE, SURI, SWID, TALF, TAMA, TAMU, TAPG, TARA, TBIG, TBLA,
TCID, TCPI, TEBE, TFAS, TFCO, TGKA, TGUK, TIFA, TINS, TIRA, TIRT, TKIM,
TLDN, TLKM, TMAS, TMPO, TOBA, TOSK, TOTL, TOTO, TOWR, TPIA, TPMA, TRGU,
TRIM, TRIN, TRIS, TRJA, TRON, TRST, TRUE, TRUK, TRUS, TSPC, TUGU, TYRE,
UANG, UCID, UDNG, UFOE, ULTJ, UNIC, UNIQ, UNSP, UNTD, UNTR, UNVR, URBN,
UVCR, VAST, VERN, VICI, VICO, VINS, VISI, VIVA, VKTR, VOKS, VRNA, VTNY,
WAPO, WBSA, WEGE, WEHA, WGSH, WICO, WIFI, WIIM, WIKA, WINE, WINS, WIRG,
WMPP, WMUU, WOMF, WOOD, WSBP, WTON, XSPI, YELO, YOII, YPAS, YULE, YUPI,
ZATA, ZINC, ZONE, ZYRX"""
TICKERS = sorted(set(t.strip().upper() for t in IDX_TICKERS_ALL.replace("\n", ",").split(",") if t.strip()))


# ---------------------------------------------------------------- UTIL HARGA
def tick(p):
    return 1 if p < 200 else 2 if p < 500 else 5 if p < 2000 else 10 if p < 5000 else 25


def floor_tick(p):
    t = tick(p)
    return np.floor(p / t + 1e-9) * t


def ceil_tick(p):
    """Harga valid terkecil (sesuai fraksi BEI) yang >= p."""
    q = floor_tick(p)
    if q < p - 1e-9:
        q = q + tick(q)
        q = floor_tick(q) if floor_tick(q) >= p - 1e-9 else q
    return float(q)


def trigger_price(sl):
    """Harga close tertinggi (sesuai fraksi BEI) yang sudah memicu jual: close < SL."""
    p = floor_tick(sl)
    if p >= sl - 1e-9:
        p = p - tick(p - 1e-9)
    return float(p)


def ara_lim(p):
    return 0.35 if p < 200 else (0.25 if p <= 5000 else 0.20)


def arb_price(close, tanggal):
    """Harga terendah yang boleh dipasang untuk order jual besok (batas ARB, sesuai fraksi).
    s.d. 31 Des 2026: ARB 7% (Rp11-14: Rp1). Mulai 1 Jan 2027: ARB simetris dengan ARA
    (Rp<=200 35%, >200-5.000 25%, >5.000 20%). Harga <= Rp10: Rp1."""
    c = float(close)
    if c <= 10:
        return max(1.0, c - 1)
    if pd.Timestamp(tanggal) <= pd.Timestamp("2026-12-31"):
        if c <= 14:
            return c - 1
        pct = 0.07
    else:
        pct = 0.35 if c <= 200 else (0.25 if c <= 5000 else 0.20)
    return ceil_tick(c * (1 - pct))


# ---------------------------------------------------------------- DATA
def _download_batch(tickers, start, end, batch=100, pause=3):
    import time
    import yfinance as yf
    out = {}
    for i in range(0, len(tickers), batch):
        grp = [f"{t}.JK" for t in tickers[i:i + batch]]
        d = None
        for _ in range(4):
            try:
                d = yf.download(grp, start=start, end=end, progress=False, auto_adjust=False, group_by="ticker", threads=True)
                break
            except Exception:
                time.sleep(10)
        if d is None or d.empty:
            continue
        lvl0 = d.columns.get_level_values(0) if isinstance(d.columns, pd.MultiIndex) else []
        for g in grp:
            if g in lvl0:
                x = d[g][["Open", "High", "Low", "Close", "Volume"]].dropna()
                x = x[(x.Close > 0) & (x.High > 0)]
                if len(x) > 250:
                    out[g[:-3]] = x
        time.sleep(pause)
    return out


def download_all(tickers=None, start=START_DATA, retries=2):
    """Tarik OHLCV harian semua emiten (.JK). Saham aktif yang bar terakhirnya tertinggal
    (biasanya karena Yahoo membatasi permintaan) diunduh ulang sampai `retries` kali."""
    import time
    tickers = tickers or TICKERS
    end = (pd.Timestamp.now(tz="Asia/Jakarta").normalize() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    data = _download_batch(tickers, start, end)
    for _ in range(retries):
        if not data:
            break
        D = max(df.index[-1] for df in data.values())
        lag = [k for k, df in data.items() if df.index[-1] < D and df.Volume.tail(5).sum() > 0]
        lag += [t for t in tickers if t not in data]
        if not lag:
            break
        time.sleep(20)
        again = _download_batch(lag, start, end, batch=50, pause=5)
        for k, df in again.items():
            if k not in data or df.index[-1] > data[k].index[-1]:
                data[k] = df
    return data


def clean_stock(df):
    """Bersihkan kesalahan Yahoo: bar rusak satu hari diganti bar sebelumnya,
    split/reverse split yang tidak disesuaikan -> harga sebelum split disesuaikan.
    Saham harga < Rp10 tidak disentuh (naik 1 tick bisa > 36%)."""
    df = df.copy().astype(float)
    log = []
    for _ in range(5):
        c = df.Close.values
        changed = False
        for t in range(1, len(c)):
            if c[t - 1] < 10:
                continue
            r = c[t] / c[t - 1] - 1
            if abs(r) <= 0.36:
                continue
            nxt = c[t + 1] / c[t] - 1 if t + 1 < len(c) else 0
            if t + 1 < len(c) and abs(nxt) > 0.36 and np.sign(nxt) != np.sign(r):
                for col in ["Open", "High", "Low", "Close"]:
                    df.iloc[t, df.columns.get_loc(col)] = c[t - 1]
                df.iloc[t, df.columns.get_loc("Volume")] = 0
                log.append((df.index[t], "bar rusak diganti", r))
            else:
                ratio = c[t] / c[t - 1]
                for col in ["Open", "High", "Low", "Close"]:
                    df.iloc[:t, df.columns.get_loc(col)] *= ratio
                df.iloc[:t, df.columns.get_loc("Volume")] /= ratio
                log.append((df.index[t], f"split disesuaikan x{ratio:.4f}", r))
            changed = True
            break
        if not changed:
            break
    return df, log


def clean_all(data):
    out, logs = {}, {}
    for k, df in data.items():
        out[k], lg = clean_stock(df)
        if lg:
            logs[k] = lg
    return out, logs


# ---------------------------------------------------------------- INDIKATOR
def atr_wilder(h, l, c, n=14):
    tr = np.maximum(h - l, np.maximum(abs(h - np.r_[np.nan, c[:-1]]), abs(l - np.r_[np.nan, c[:-1]])))
    tr[0] = h[0] - l[0]
    out = np.full(len(h), np.nan)
    if len(h) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(h)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def zigzag_locks(h, l, atr, mult):
    """Pivot ZigZag ATR + hari pivot itu terkunci (kausal)."""
    n = len(h)
    valid = np.where(~np.isnan(atr))[0]
    if len(valid) == 0:
        return [], []
    s = valid[0]
    piv, lk = [], []
    trend = 0
    hi, hi_i, lo, lo_i = h[s], s, l[s], s
    ext = ext_i = None
    for i in range(s + 1, n):
        th = mult * atr[i]
        if trend == 0:
            if h[i] > hi: hi, hi_i = h[i], i
            if l[i] < lo: lo, lo_i = l[i], i
            if lo_i < i and h[i] - lo >= th:
                piv.append((lo_i, lo, "L")); lk.append(i)
                seg = h[lo_i + 1:i + 1]; k = int(np.argmax(seg)); ext, ext_i, trend = seg[k], lo_i + 1 + k, 1
            elif hi_i < i and hi - l[i] >= th:
                piv.append((hi_i, hi, "H")); lk.append(i)
                seg = l[hi_i + 1:i + 1]; k = int(np.argmin(seg)); ext, ext_i, trend = seg[k], hi_i + 1 + k, -1
        elif trend == 1:
            if h[i] > ext: ext, ext_i = h[i], i
            elif ext - l[i] >= th:
                piv.append((ext_i, ext, "H")); lk.append(i)
                seg = l[ext_i + 1:i + 1]; k = int(np.argmin(seg)); ext, ext_i, trend = seg[k], ext_i + 1 + k, -1
        else:
            if l[i] < ext: ext, ext_i = l[i], i
            elif h[i] - ext >= th:
                piv.append((ext_i, ext, "L")); lk.append(i)
                seg = h[ext_i + 1:i + 1]; k = int(np.argmax(seg)); ext, ext_i, trend = seg[k], ext_i + 1 + k, 1
    return piv, lk


# ---------------------------------------------------------------- GARIS SINYAL
def build_line(highs, b_idx, c, atr, d):
    ib, pb = highs[b_idx]
    best = None
    for j in range(max(0, b_idx - MAX_ANCHOR), b_idx):
        ia, pa = highs[j]
        if pa <= pb or ib - ia < 10:
            continue
        slope = (pb - pa) / (ib - ia)
        touches, ok = 2, True
        for k in range(j + 1, b_idx):
            ik, pk = highs[k]
            Lk = pa + slope * (ik - ia)
            tol = TOL_PIVOT * atr[ik]
            if pk > Lk + tol:
                ok = False; break
            if abs(pk - Lk) <= tol:
                touches += 1
        if not ok or touches < MIN_TOUCH:
            continue
        t = np.arange(ia, d + 1)
        if np.any(c[ia:d + 1] > pa + slope * (t - ia) + 1e-9):
            continue
        if best is None or ia < best[0]:
            best = (ia, pa, slope, touches, ib)
    return best


def signals_for_stock(kode, df, sig_start=None):
    """Semua sinyal break garis turun untuk satu saham (kausal).
    Juga mengembalikan garis yang sedang aktif di bar terakhir (untuk chart)."""
    o, h, l, c, v = [df[x].values.astype(float) for x in ["Open", "High", "Low", "Close", "Volume"]]
    n = len(c)
    atr = atr_wilder(h, l, c)
    val20 = pd.Series(c * v).rolling(20).mean().values
    piv, lk = zigzag_locks(h, l, atr, MULT)
    lock_at = {}
    for (i, p, t), q in zip(piv, lk):
        if t == "H":
            lock_at.setdefault(q, []).append((i, p))
    highs, line, out = [], None, []
    i0 = 0 if sig_start is None else int(np.searchsorted(df.index.values, pd.Timestamp(sig_start).to_datetime64()))
    for d in range(n):
        if d in lock_at:
            for hp in lock_at[d]:
                highs.append(hp)
                nl = build_line(highs, len(highs) - 1, c, atr, d)
                if nl is not None:
                    line = nl
        if line is None:
            continue
        ia, pa, slope, touches, ib = line
        if d - ib > MAX_AGE_LINE:
            line = None; continue
        Ld = pa + slope * (d - ia)
        if c[d] >= Ld + BUF_BREAK * atr[d]:
            if d >= i0 and val20[d] >= VAL_MIN:
                out.append(dict(kode=kode, d=df.index[d], close=c[d], sl0=Ld - SL_ATR0 * atr[d], val=val20[d],
                                line=Ld, atr=atr[d], ia=ia, pa=pa, slope=slope, touches=touches))
            line = None
    active = None
    if line is not None:
        ia, pa, slope, touches, ib = line
        active = dict(ia=ia, pa=pa, slope=slope, touches=touches, ib=ib, now=pa + slope * (n - 1 - ia), atr=atr[-1])
    return out, active


# ---------------------------------------------------------------- TANGGA MERAH
class _Line:
    __slots__ = ("ia", "pa", "slope", "ib", "scale")

    def __init__(s, ia, pa, ib, pb, scale):
        s.ia, s.pa, s.ib, s.scale = ia, pa, ib, scale
        s.slope = (pb - pa) / (ib - ia)

    def at(s, t):
        return s.pa + s.slope * (t - s.ia)


def _make_red(ph, k, C, ATR, d, scale):
    ib, pb = ph[k]
    best = None
    for j in range(max(0, k - 10), k):
        ia, pa = ph[j]
        if pa <= pb or ib - ia < 5:
            continue
        ln = _Line(ia, pa, ib, pb, scale)
        if not all(ph[m][1] <= ln.at(ph[m][0]) + 0.25 * ATR[ph[m][0]] for m in range(j + 1, k)):
            continue
        t = np.arange(ia, d + 1)
        if np.any(C[ia:d + 1] > ln.at(t) + 1e-12):
            continue
        if best is None or ln.at(d) < best.at(d):
            best = ln
    return best


def red_ladder(df):
    """Garis merah (lower high) di 4 ukuran swing, skala log.
    Kembalikan: daftar tembus [(tanggal, level_harga)] dan garis aktif di bar terakhir."""
    h, l, c = [df[x].values.astype(float) for x in ["High", "Low", "Close"]]
    H, L, C = np.log(h), np.log(l), np.log(c)
    n = len(C)
    ATR = atr_wilder(H, L, C)
    ev = {s: {} for s in RED_SCALES}
    for s in RED_SCALES:
        piv, lk = zigzag_locks(H, L, ATR, s)
        for (i, p, t), q in zip(piv, lk):
            if t == "H":
                ev[s].setdefault(q, []).append((i, p))
    ph = {s: [] for s in RED_SCALES}
    reds, breaks = [], []
    for d in range(n):
        if np.isnan(ATR[d]):
            continue
        for s in RED_SCALES:
            for hp in ev[s].get(d, []):
                ph[s].append(hp)
                ln = _make_red(ph[s], len(ph[s]) - 1, C, ATR, d, s)
                if ln is not None and not any(abs(r.at(d) - ln.at(d)) < 0.5 * ATR[d] for r in reds):
                    reds.append(ln)
        alive = []
        for r in reds:
            if d - r.ib > RED_AGE[r.scale]:
                continue
            lv = r.at(d)
            if C[d] >= lv + RED_BUF * ATR[d]:
                breaks.append((df.index[d], float(np.exp(lv))))
                continue
            alive.append(r)
        reds = alive
    active = sorted([dict(scale=r.scale, now=float(np.exp(r.at(n - 1))), ia=r.ia, pa=float(np.exp(r.pa)), slope=r.slope,
                          naik_jika_close=ceil_tick(float(np.exp(r.at(n - 1) + RED_BUF * ATR[n - 1]))))
                     for r in reds], key=lambda z: z["now"])
    return breaks, active


# ---------------------------------------------------------------- PERSIAPAN
def prepare(data, sig_start=None):
    """Hitung semua bahan: sinyal, tembus merah, ATR harian, garis aktif."""
    SIG, RB, ATRS, ACTIVE, REDS = {}, {}, {}, {}, {}
    for k, df in data.items():
        s, act = signals_for_stock(k, df, sig_start)
        SIG[k] = s; ACTIVE[k] = act
        RB[k], REDS[k] = red_ladder(df)
        ATRS[k] = pd.Series(atr_wilder(df.High.values.astype(float), df.Low.values.astype(float), df.Close.values.astype(float)), index=df.index)
    return dict(SIG=SIG, RB=RB, ATRS=ATRS, ACTIVE=ACTIVE, REDS=REDS)


def new_state(modal=MODAL_AWAL, mulai=None):
    return dict(versi=VERSION, modal_awal=modal, modal_masuk=float(modal), deposits=[], pending_dep=0.0,
                cash=float(modal), reserved=0.0, pos={}, pend_buy={}, log=[], skipped=[], events=[],
                materai_total=0.0, last_date=None if mulai is None else str(pd.Timestamp(mulai).date()),
                equity=[], ihsg_start=None, start_date=None, last_report_date=None, last_report_pos={})


def deposit(st, amount, tanggal):
    """Setoran modal baru (bukan untung). Masuk kas, dicatat terpisah, tidak merusak hitungan return."""
    st["cash"] += float(amount)
    st["modal_masuk"] = st.get("modal_masuk", st["modal_awal"]) + float(amount)
    st["pending_dep"] = st.get("pending_dep", 0.0) + float(amount)
    st.setdefault("deposits", []).append(dict(d=str(pd.Timestamp(tanggal).date()), jumlah=float(amount)))
    return st


# ---------------------------------------------------------------- PROSES SATU HARI
def step(st, d, data, P, rb_by, sig_by_day):
    """Proses satu hari bursa d: pagi (eksekusi order semalam), sore (cek SL),
    malam (sinyal baru -> order besok). Logika identik dengan backtest."""
    cash_in_next = 0.0
    trx_val = 0.0
    pos, pend = st["pos"], st["pend_buy"]
    # ---- PAGI: v1.2 suspensi ke-N dibuka hari ini -> jual open
    if SUSP_EXIT_N:
        for k, p in pos.items():
            df = data.get(k)
            if p["sell"] or df is None or d not in df.index or p.get("zrun", 0) < 1 or p.get("neps", 0) < SUSP_EXIT_N:
                continue
            if float(df.at[d, "Volume"]) > 0:
                p["sell"] = True; p["flag_d"] = str(d.date()); p["src"] = "suspensi dibuka"
    # ---- PAGI: jual
    for k in list(pos):
        p = pos[k]
        if not p["sell"]:
            continue
        df = data.get(k)
        if df is None or d not in df.index:
            continue
        i = df.index.get_loc(d)
        b = df.iloc[i]
        pc = df.Close.iloc[i - 1] if i > 0 else b.Close
        if b.Volume <= 0 or (b.High == b.Low and b.Close / pc - 1 <= ARB_LOCK):
            continue
        px = float(b.Open)
        val = p["lot"] * 100 * px
        net = val * (1 - FEE_S)
        trx_val += val
        cash_in_next += net
        st["log"].append(dict(kode=k, beli=p["ed"], jual=str(d.date()), lot=p["lot"], harga_beli=p["ent"], harga_jual=px,
                              modal=p["cost"], hasil=net, pnl=net - p["cost"], ret=net / p["cost"] - 1,
                              sl0=p["sl0"], sl_akhir=p["sl"], naik_merah=p["steps"], flag_d=p.get("flag_d")))
        st.setdefault("events", []).append(dict(d=str(d.date()), jenis="JUAL", kode=k, lot=p["lot"], harga=px, pnl=net - p["cost"], ret=net / p["cost"] - 1))
        del pos[k]
    # ---- PAGI: jual sebagian (penyesuaian manual, mis. FUJI ke jatah 5 jt)
    for k in list(st.get("pend_trim", {})):
        q = int(st["pend_trim"][k]); p = pos.get(k); df = data.get(k)
        if p is None or q <= 0 or q >= p["lot"]:
            st["pend_trim"].pop(k); continue
        if df is None or d not in df.index:
            continue
        i = df.index.get_loc(d); b = df.iloc[i]
        pc = df.Close.iloc[i - 1] if i > 0 else b.Close
        if b.Volume <= 0 or (b.High == b.Low and b.Close / pc - 1 <= ARB_LOCK):
            continue
        px = float(b.Open); val = q * 100 * px; net = val * (1 - FEE_S)
        cpart = p["cost"] * q / p["lot"]
        trx_val += val; cash_in_next += net
        st["log"].append(dict(kode=k, beli=p["ed"], jual=str(d.date()), lot=q, harga_beli=p["ent"], harga_jual=px, modal=cpart,
                              hasil=net, pnl=net - cpart, ret=net / cpart - 1, sl0=p["sl0"], sl_akhir=p["sl"],
                              naik_merah=p["steps"], flag_d=None, sebagian=True))
        st.setdefault("events", []).append(dict(d=str(d.date()), jenis="JUAL SEBAGIAN", kode=k, lot=q, harga=px, pnl=net - cpart, ret=net / cpart - 1))
        p["lot"] -= q; p["cost"] -= cpart
        st["pend_trim"].pop(k)
    # ---- PAGI: beli (urutan = prioritas semalam)
    for k in list(pend):
        o = pend.pop(k)
        df = data.get(k)
        st["reserved"] -= o["reserve"]
        st["cash"] += o["reserve"]
        if df is None or d not in df.index:
            st["skipped"].append((o["d"], k, "tak ada bar")); st.setdefault("events", []).append(dict(d=str(d.date()), jenis="TERLEWAT", kode=k, alasan="tak ada bar")); continue
        b = df.loc[d]
        if b.Volume <= 0:
            st["skipped"].append((o["d"], k, "suspend")); st.setdefault("events", []).append(dict(d=str(d.date()), jenis="TERLEWAT", kode=k, alasan="suspend")); continue
        if b.Open >= b.High and b.Open / o["close"] - 1 >= ara_lim(o["close"]) - 0.01:
            st["skipped"].append((o["d"], k, "ARA terkunci")); st.setdefault("events", []).append(dict(d=str(d.date()), jenis="TERLEWAT", kode=k, alasan="ARA terkunci")); continue
        if b.Open > o["limit"]:
            st["skipped"].append((o["d"], k, "gap > batas")); st.setdefault("events", []).append(dict(d=str(d.date()), jenis="TERLEWAT", kode=k, alasan="gap > batas")); continue
        lot = o["lot"]
        cost = lot * 100 * float(b.Open) * (1 + FEE_B)
        if lot <= 0 or cost > st["cash"]:
            st["skipped"].append((o["d"], k, "kas kurang saat isi")); st.setdefault("events", []).append(dict(d=str(d.date()), jenis="TERLEWAT", kode=k, alasan="kas kurang saat isi")); continue
        st["cash"] -= cost
        trx_val += lot * 100 * float(b.Open)
        pos[k] = dict(ed=str(d.date()), ent=float(b.Open), lot=lot, cost=cost, sl0=o["sl0"], sl=o["sl0"], steps=0,
                      csteps=0, hh=0.0, sig_d=o["d"], sell=False, src="garis-1ATR")
        st.setdefault("events", []).append(dict(d=str(d.date()), jenis="BELI", kode=k, lot=lot, harga=float(b.Open), batas=o["limit"]))
    # ---- SORE: catatan suspensi (v1.2)
    for k, p in pos.items():
        df = data.get(k)
        if df is None or d not in df.index or pd.Timestamp(p["ed"]) >= d:
            continue
        if float(df.at[d, "Volume"]) <= 0:
            if p.get("zrun", 0) == 0:
                p["neps"] = p.get("neps", 0) + 1
            p["zrun"] = p.get("zrun", 0) + 1
        else:
            p["zrun"] = 0
    # ---- SORE: cek SL, lalu naikkan SL
    for k, p in pos.items():
        df = data.get(k)
        if df is None or d not in df.index or p["sell"]:
            continue
        c = float(df.at[d, "Close"])
        if c < p["sl"]:
            p["sell"] = True; p["flag_d"] = str(d.date())
            continue
        rb = rb_by.get(k)
        if rb is not None and d in rb.index and d > pd.Timestamp(p["sig_d"]):
            lv = float(rb.loc[[d]].max())
            if lv > p["sl"]:
                p["sl"] = lv; p["steps"] += 1; p["src"] = "merah tembus"
        p["hh"] = max(p["hh"], float(df.at[d, "High"]))
        ch = p["hh"] - CHAND_K * float(P["ATRS"][k].at[d])
        if ch > p["sl"]:
            p["sl"] = ch; p["csteps"] += 1; p["src"] = "high-4ATR"
    # ---- SORE: pagar jual (v1.1)
    if FENCE_N and IHSG_RET is not None and d in IHSG_RET.index and IHSG_RET.at[d] <= FENCE_IHSG:
        ds = str(d.date())
        baru = [(k, p) for k, p in pos.items() if p["sell"] and p.get("flag_d") == ds and not p.get("delayed")]
        if len(baru) >= FENCE_N:
            for k, p in baru:
                df = data[k]
                p["sell"] = False; p["delayed"] = True; p["delay_d"] = ds
                rb = rb_by.get(k)
                if rb is not None and d in rb.index and d > pd.Timestamp(p["sig_d"]):
                    lv = float(rb.loc[[d]].max())
                    if lv > p["sl"]:
                        p["sl"] = lv; p["steps"] += 1; p["src"] = "merah tembus"
                p["hh"] = max(p["hh"], float(df.at[d, "High"]))
                ch = p["hh"] - CHAND_K * float(P["ATRS"][k].at[d])
                if ch > p["sl"]:
                    p["sl"] = ch; p["csteps"] += 1; p["src"] = "high-4ATR"
                st.setdefault("events", []).append(dict(d=ds, jenis="TUNDA JUAL", kode=k, n=len(baru), ihsg=float(IHSG_RET.at[d])))
    if trx_val > BATAS_MATERAI:
        st["cash"] -= MATERAI; st["materai_total"] += MATERAI
    st["cash"] += cash_in_next
    # ---- MALAM: sinyal baru -> order pre-opening besok
    for s in sorted(sig_by_day.get(d, []), key=lambda z: -z["val"]):
        k = s["kode"]
        if k in pos or k in pend:
            st["skipped"].append((str(d.date()), k, "sudah dipegang")); continue
        lot = int(ALLOC // (s["close"] * 100 * (1 + FEE_B)))
        lim = float(floor_tick(s["close"] * (1 + LIMIT_PCT)))
        reserve = lot * 100 * lim * (1 + FEE_B)
        if lot <= 0 or reserve > st["cash"]:
            st["skipped"].append((str(d.date()), k, "kas kurang")); continue
        st["cash"] -= reserve; st["reserved"] += reserve
        pend[k] = dict(val=s["val"], d=str(d.date()), close=float(s["close"]), lot=lot, limit=lim, reserve=reserve,
                       sl0=float(s["sl0"]), line=float(s["line"]), atr=float(s["atr"]), touches=int(s["touches"]))
    # ---- nilai ekuitas (close terakhir yang diketahui)
    mv = 0.0
    for k, p in pos.items():
        df = data[k]
        last = df.Close[df.index <= d]
        mv += p["lot"] * 100 * float(last.iloc[-1])
    st["equity"].append(dict(d=str(d.date()), cash=st["cash"], reserved=st["reserved"], mv=mv,
                             eq=st["cash"] + st["reserved"] + mv, npos=len(pos), dep=st.get("pending_dep", 0.0)))
    st["pending_dep"] = 0.0
    st["events"] = st.get("events", [])[-300:]
    st["last_date"] = str(d.date())
    if st["cash"] < -1e-6:
        raise RuntimeError(f"Kas negatif di {d}: {st['cash']}")
    return st


def _indexes(P, start=None):
    rb_by = {k: (pd.DataFrame(v, columns=["d", "lv"]).set_index("d")["lv"] if v else pd.Series(dtype=float)) for k, v in P["RB"].items()}
    sig_by_day = {}
    for k, lst in P["SIG"].items():
        for s in lst:
            if start is None or s["d"] >= pd.Timestamp(start):
                sig_by_day.setdefault(s["d"], []).append(s)
    return rb_by, sig_by_day


def set_ihsg(ihsg, data):
    """Return harian IHSG di kalender bursa saham (hari tanpa data IHSG = 0, tidak memicu pagar)."""
    global IHSG_RET
    cal = calendar(data)
    IHSG_RET = ihsg.reindex(cal).ffill().pct_change()
    return IHSG_RET


def calendar(data):
    return sorted(set().union(*[set(df.index) for df in data.values()]))


def run_days(st, data, P, days):
    rb_by, sig_by_day = _indexes(P)
    for d in days:
        step(st, d, data, P, rb_by, sig_by_day)
    return st


def backtest(data, start="2020-01-01", end=None, modal=MODAL_AWAL, P=None):
    P = P or prepare(data)
    st = new_state(modal)
    days = [d for d in calendar(data) if d >= pd.Timestamp(start) and (end is None or d <= pd.Timestamp(end))]
    return run_days(st, data, P, days), P


def nightly(st, data, P):
    """Proses semua hari bursa setelah st['last_date'] sampai data terakhir."""
    last = pd.Timestamp(st["last_date"]) if st["last_date"] else None
    days = [d for d in calendar(data) if last is None or d > last]
    if last is None and days:
        days = days[-1:]          # mulai baru: hanya hari terakhir (cari sinyal untuk besok)
    return run_days(st, data, P, days), days


# ---------------------------------------------------------------- LAPORAN
def warnings_for(k, data, d=None):
    w = []
    if k in RED_FLAG:
        w.append("red-flag")
    df = data.get(k)
    if df is not None:
        v = df.Volume if d is None else df.Volume[df.index <= d]
        if (v.tail(SUSP_WARN_LB) <= 0).any():
            w.append("pernah suspend/tanpa transaksi 120 hari")
    return w


def next_red_above(k, P, price):
    """Harga close (sesuai fraksi) yang membuat SL naik ke garis merah terdekat di atas harga."""
    for r in P["REDS"].get(k, []):
        if r["naik_jika_close"] > price:
            return r["naik_jika_close"]
    return None


def report(st, data, P):
    d = pd.Timestamp(st["last_date"])
    beli = []
    for k, o in st["pend_buy"].items():
        beli.append(dict(kode=k, lot=o["lot"], close_sinyal=o["close"], harga_batas=o["limit"], jual_jika_close_maks=trigger_price(o["sl0"]),
                         modal_maks=round(o["reserve"]), peringatan=", ".join(warnings_for(k, data, d))))
    jual, hold = [], []
    for k, p in st["pos"].items():
        df = data[k]
        c = float(df.Close[df.index <= d].iloc[-1])
        last_bar = df.index[df.index <= d][-1]
        row = dict(kode=k, tgl_beli=p["ed"], harga_beli=p["ent"], lot=p["lot"], close=c,
                   pl_pct=round((c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1) * 100, 2),
                   pl_rp=round(p["lot"] * 100 * c * (1 - FEE_S) - p["cost"]),
                   jual_jika_close_maks=trigger_price(p["sl"]), sumber_sl=p.get("src", ""), sl_naik_jika_close=next_red_above(k, P, c),
                   data_terakhir=str(last_bar.date()), peringatan=", ".join(warnings_for(k, data, d)))
        if p["sell"]:
            row["status"] = "JUAL BESOK OPEN"
            jual.append(row)
        else:
            row["status"] = "HOLD"
            hold.append(row)
    eq = st["equity"][-1] if st["equity"] else dict(eq=st["cash"], cash=st["cash"], reserved=0, mv=0)
    skip_today = [s for s in st["skipped"] if s[0] == st["last_date"]]
    return dict(tanggal=st["last_date"], ekuitas=eq["eq"], kas=eq["cash"], kas_terkunci=eq["reserved"], nilai_saham=eq["mv"],
                beli=beli, jual=jual, hold=hold, terlewat=skip_today,
                realized=sum(x["pnl"] for x in st["log"]), materai=st["materai_total"])


def report_text(R):
    f = lambda x: f"{x:,.0f}".replace(",", ".")
    L = [f"LAPORAN SISTEM TRENDLINE — data close {R['tanggal']}",
         f"Ekuitas {f(R['ekuitas'])} | Kas {f(R['kas'])} | Kas terkunci order {f(R['kas_terkunci'])} | Saham {f(R['nilai_saham'])}", ""]
    L.append(f"BELI BESOK (pre-opening, harga batas): {len(R['beli'])}")
    for b in R["beli"]:
        L.append(f"  {b['kode']:5} {b['lot']} lot  batas {f(b['harga_batas'])}  (close {f(b['close_sinyal'])})  jual jika close <= {f(b['jual_jika_close_maks'])}"
                 + (f"  ⚠ {b['peringatan']}" if b["peringatan"] else ""))
    L.append(f"JUAL BESOK OPEN: {len(R['jual'])}")
    for j in R["jual"]:
        L.append(f"  {j['kode']:5} {j['lot']} lot  close {f(j['close'])} <= {f(j['jual_jika_close_maks'])}  P/L {j['pl_pct']:+.1f}%")
    L.append(f"POSISI HOLD: {len(R['hold'])}")
    for h in R["hold"]:
        nr = f"{f(h['sl_naik_jika_close'])}" if h["sl_naik_jika_close"] else "-"
        L.append(f"  {h['kode']:5} {h['lot']} lot  beli {f(h['harga_beli'])} ({h['tgl_beli']})  close {f(h['close'])}  "
                 f"P/L {h['pl_pct']:+.1f}%  jual jika close <= {f(h['jual_jika_close_maks'])} [{h['sumber_sl']}]  SL naik jika close >= {nr}"
                 + (f"  ⚠ {h['peringatan']}" if h["peringatan"] else ""))
    if R["terlewat"]:
        L.append("TERLEWAT: " + ", ".join(f"{k} ({a})" for _, k, a in R["terlewat"]))
    return "\n".join(L)


# ---------------------------------------------------------------- STATE JSON
def state_to_json(st):
    return json.dumps(st, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else float(o), indent=1)


def state_from_json(s):
    st = json.loads(s)
    st["skipped"] = [tuple(x) for x in st.get("skipped", [])]
    return st


# ---------------------------------------------------------------- LAPORAN MALAM (dipakai jadwal otomatis)
def fetch_ihsg(start=START_DATA):
    import yfinance as yf
    end = (pd.Timestamp.now(tz="Asia/Jakarta").normalize() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    d = yf.download("^JKSE", start=start, end=end, progress=False, auto_adjust=False)
    c = d["Close"]
    if isinstance(c, pd.DataFrame):
        c = c.iloc[:, 0]
    return c.dropna()


def twr(st):
    """Return time-weighted sejak mulai: setoran tidak dihitung sebagai untung."""
    prod, prev = 1.0, None
    start = st.get("start_date")
    for e in st["equity"]:
        if start is not None and e["d"] <= start:
            prev = e["eq"]; continue
        base = prev if prev is not None else st["modal_awal"]
        prod *= (e["eq"] - e.get("dep", 0.0)) / base
        prev = e["eq"]
    return prod - 1


def init_live(data, P, ihsg, modal, tanggal=None):
    """Buat state live baru: proses hari bursa terakhir saja (cari sinyal untuk besok)."""
    st = new_state(modal)
    st, days = nightly(st, data, P)
    D = pd.Timestamp(st["last_date"])
    st["start_date"] = st["last_date"]
    st["ihsg_start"] = float(ihsg[ihsg.index <= D].iloc[-1])
    return st


def _f(x):
    return "-" if x is None else f"{x:,.0f}".replace(",", ".")


def _jt(x):
    return f"{x / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " jt"


def _pct(x):
    return f"{x * 100:+.1f}%".replace(".", ",")


def sisa_komitmen(st):
    """Bagian komitmen yang belum disetor ke akun."""
    return max(0.0, st.get("komitmen", st["modal_masuk"]) - st.get("disetor", st["modal_masuk"]))


def perlu_setor(st):
    """Setoran minimal sebelum pre-opening supaya kas riil di akun cukup untuk order besok."""
    return min(sisa_komitmen(st), max(0.0, sisa_komitmen(st) - st["cash"]))


def kas_riil(st):
    """Kas bebas riil di akun setelah order besok dikunci (sebelum setoran)."""
    return st["cash"] - sisa_komitmen(st)


def catat_setoran(st, jumlah, tanggal):
    """Uang yang benar-benar disetor ke akun FD untuk sistem ini (bukan tambahan modal sistem)."""
    st["disetor"] = st.get("disetor", 0.0) + float(jumlah)
    st.setdefault("setoran", []).append(dict(d=str(pd.Timestamp(tanggal).date()), jumlah=float(jumlah)))
    return st


def _aksi_lines(st, data, D):
    """Bagian AKSI HARI BURSA BERIKUTNYA (dipakai laporan malam dan diulang hari Minggu)."""
    L = []
    jual = [(k, p) for k, p in st["pos"].items() if p["sell"]]
    L.append("JUAL di pre-opening (antri di harga batas ARB, terisi di harga pembukaan):" if jual else "JUAL: -")
    for k, p in jual:
        c = float(data[k].Close[data[k].index <= D].iloc[-1])
        pl = c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1
        why = "suspensi ke-%d dibuka" % p.get("neps", 0) if p.get("src") == "suspensi dibuka" else f"close {_f(c)} ≤ {_f(trigger_price(p['sl']))}"
        L.append(f"  {k} {p['lot']} lot @ {_f(arb_price(c, D + pd.Timedelta(days=1)))} — {why} (P/L {_pct(pl)})"
                 + (f" ⚠ {', '.join(warnings_for(k, data, D))}" if warnings_for(k, data, D) else ""))
    for k, q in st.get("pend_trim", {}).items():
        if k in st["pos"]:
            c = float(data[k].Close[data[k].index <= D].iloc[-1])
            L.append(f"JUAL SEBAGIAN: {k} {q} lot @ {_f(arb_price(c, D + pd.Timedelta(days=1)))} (penyesuaian ke jatah 5 jt, sisa {st['pos'][k]['lot'] - q} lot)")
    for k, p in st["pos"].items():
        if p.get("zrun", 0) > 0 and not p["sell"]:
            msg = f"⏸ {k} sedang suspensi ke-{p.get('neps', 0)} (sudah {p['zrun']} hari bursa)"
            if SUSP_EXIT_N and p.get("neps", 0) >= SUSP_EXIT_N:
                msg += " → begitu BEI umumkan dibuka, antri JUAL semua lot di pre-opening hari itu (harga batas ARB)"
            L.append(msg)
    return L


def _ringkas_rows(st, close, D):
    """Baris tabel ringkas: aksi besok + posisi dipegang. Disimpan juga untuk laporan Minggu."""
    R = [f"{'Aksi':5} {'Kode':5} {'Lot':>6}  {'Harga':<17} Jual jika close ≤"]
    for k, p in st["pos"].items():
        if p["sell"]:
            c = close(k)
            R.append(f"{'JUAL':5} {k:5} {_f(p['lot']):>6}  {'@' + _f(arb_price(c, D + pd.Timedelta(days=1))) + ' (ARB)':<17} -")
    for k, q in st.get("pend_trim", {}).items():
        if k in st["pos"]:
            c = close(k)
            R.append(f"{'JUAL':5} {k:5} {_f(q):>6}  {'@' + _f(arb_price(c, D + pd.Timedelta(days=1))) + ' (sbgn)':<17} -")
    if not any(p["sell"] for p in st["pos"].values()) and not st.get("pend_trim"):
        R.append(f"{'JUAL':5} -")
    for k, o in st["pend_buy"].items():
        R.append(f"{'BELI':5} {k:5} {_f(o['lot']):>6}  {'≤' + _f(o['limit']):<17} {_f(trigger_price(o['sl0']))}")
    if not st["pend_buy"]:
        R.append(f"{'BELI':5} -")
    prev = st.get("last_report_pos", {})
    for k, p in st["pos"].items():
        if p["sell"]:
            continue
        c = close(k)
        pl = c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1
        trig = trigger_price(p["sl"])
        naik = k in prev and trig > prev[k]
        R.append(f"{'POS':5} {k:5} {_f(p['lot']):>6}  {_f(p['ent']) + '→' + _f(c) + ' (' + _pct(pl) + ')':<17} {_f(trig)}" + (" ↑" if naik else ""))
    for k, p in st["pos"].items():
        if p.get("zrun", 0) > 0 and not p["sell"]:
            R.append(f"⏸ {k} suspensi ke-{p.get('neps', 0)} ({p['zrun']} hari bursa)")
    return R


def nightly_report(st, data, P, ihsg, full=None):
    """Teks laporan malam + banner notifikasi. Mengubah st (catatan laporan terakhir)."""
    d = st["last_date"]
    D = pd.Timestamp(d)
    hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"][D.weekday()]
    full = (D.weekday() == 4) if full is None else full
    since = st.get("last_report_date")
    ev = [e for e in st.get("events", []) if since is None or e["d"] > since]
    # kelengkapan data
    aktif = [k for k, df in data.items() if len(df) and df.index[-1] >= D - pd.Timedelta(days=10)
             and df.Volume[df.index <= D].tail(5).sum() > 0]          # saham suspend/tanpa transaksi tidak dihitung
    lengkap = sum(1 for k in aktif if D in data[k].index)
    L = [f"TRENDLINE v{VERSION.split()[0]} • {AKUN} • close {hari} {D.day} {D.strftime('%b %Y')}",
         f"Data: {lengkap}/{len(aktif)} emiten aktif ter-update" + (" ✓" if lengkap >= 0.95 * len(aktif) else " ⚠ banyak yang belum update, cek lagi besok pagi"), ""]
    # ---- aksi besok
    jual = [(k, p) for k, p in st["pos"].items() if p["sell"]]
    L.append("━━ AKSI HARI BURSA BERIKUTNYA ━━")
    a0 = len(L)
    L += _aksi_lines(st, data, D)
    tunda = [e for e in ev if e["jenis"] == "TUNDA JUAL"]
    if tunda:
        L.append(f"PAGAR JUAL AKTIF: {tunda[0]['n']} posisi kena SL dan IHSG {_pct(tunda[0]['ihsg'])} hari ini → jual DITUNDA 1 hari:")
        L.append("  " + ", ".join(e["kode"] for e in tunda) + " (jangan dijual besok; dicek ulang besok sore)")
    L.append("BELI di pre-opening (harga batas; GTC boleh, CANCEL 09.00 kalau belum terisi):" if st["pend_buy"] else "BELI: -")
    siap = 0.0
    for k, o in st["pend_buy"].items():
        siap += o["reserve"]
        w = warnings_for(k, data, D)
        L.append(f"  {k} {o['lot']} lot @ maks {_f(o['limit'])} (close {_f(o['close'])}) → jual jika close ≤ {_f(trigger_price(o['sl0']))}"
                 + (f" ⚠ {', '.join(w)}" if w else ""))
    if st["pend_buy"]:
        L.append(f"Kas yang dikunci order beli: {_jt(siap)}")
    lewat = [s_[1] for s_ in st["skipped"] if s_[0] == d and s_[2] == "kas kurang"]
    if lewat:
        L.append("Sinyal terlewat (kas komitmen 100 jt habis): " + ", ".join(lewat))
    ps = perlu_setor(st)
    L.append(f"💰 SETOR sebelum pre-opening: {_jt(ps)}" if ps > 0 else "💰 Setor: tidak perlu, kas di akun cukup")
    st["last_aksi"] = L[a0:]
    # ---- cek eksekusi
    L += ["", "━━ EKSEKUSI MEKANIS (asumsi ikut penuh) ━━"]
    if not ev:
        L.append("  Tidak ada transaksi.")
    for e in ev:
        if e["jenis"] == "BELI":
            L.append(f"  ✓ Beli {e['kode']} {e['lot']} lot @{_f(e['harga'])} (open {e['d']})")
        elif e["jenis"] == "JUAL":
            L.append(f"  ✓ Jual {e['kode']} {e['lot']} lot @{_f(e['harga'])} (open {e['d']}) → {_pct(e['ret'])} / Rp{_f(e['pnl'])}")
        elif e["jenis"] == "JUAL SEBAGIAN":
            L.append(f"  ✓ Jual sebagian {e['kode']} {e['lot']} lot @{_f(e['harga'])} (open {e['d']}) → {_pct(e['ret'])} / Rp{_f(e['pnl'])}")
        elif e["jenis"] == "TERLEWAT":
            L.append(f"  ✗ {e['kode']} tidak terbeli ({e['d']}): {e['alasan']}")
    # ---- posisi
    baru = {e["kode"] for e in ev if e["jenis"] == "BELI"}
    prev = st.get("last_report_pos", {})
    rows, sama, now_trig = [], 0, {}
    for k, p in st["pos"].items():
        if p["sell"]:
            continue
        c = float(data[k].Close[data[k].index <= D].iloc[-1])
        trig = trigger_price(p["sl"])
        now_trig[k] = trig
        naik = k in prev and trig > prev[k]
        pl = c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1
        nxt = next_red_above(k, P, c)
        w = warnings_for(k, data, D)
        line = (f"  {k:5} {p['lot']} lot  avg {_f(p['ent'])}  close {_f(c)}  {_pct(pl)}  jual≤{_f(trig)}"
                + (" ↑" if naik else "") + (" (baru)" if k in baru else "")
                + f"  SL naik jika ≥{_f(nxt)}" + (f"  ⚠ {', '.join(w)}" if w else ""))
        if full or naik or k in baru:
            rows.append(line)
        else:
            sama += 1
    n_hold = sum(1 for p in st["pos"].values() if not p["sell"])
    L += ["", f"━━ POSISI ({n_hold}) — " + ("LENGKAP (Jumat)" if full else "yang berubah saja") + " ━━"]
    L += rows if rows else ["  Tidak ada perubahan."]
    if not full and sama:
        L.append(f"  {sama} posisi lain tidak berubah.")
    L.append("  ↑ = SL naik hari ini: catat angka jual≤ yang baru. SL dicek dari CLOSE, jangan pasang SL otomatis Stockbit;"
             " jual hanya kalau muncul instruksi JUAL di laporan malam")
    # ---- akun
    eq = st["equity"][-1]
    ih = float(ihsg[ihsg.index <= D].iloc[-1]) if len(ihsg[ihsg.index <= D]) else None
    ih_ret = (ih / st["ihsg_start"] - 1) if (ih and st.get("ihsg_start")) else None
    r = twr(st)
    realized = sum(x["pnl"] for x in st["log"])
    if ih:
        st.setdefault("ihsg_hist", {})[d] = ih
    st["snap"] = {k: float(data[k].Close[data[k].index <= D].iloc[-1]) for k in list(st["pos"]) + list(st["pend_buy"])}
    L += ["", "━━ AKUN (sejak " + str(st.get("start_date")) + ") ━━",
          f"Ekuitas {_jt(eq['eq'])} dari komitmen {_jt(st['modal_masuk'])} | P/L {_jt(eq['eq'] - st['modal_masuk'])}",
          f"Sistem {_pct(r)} vs IHSG {_pct(ih_ret) if ih_ret is not None else '-'}" + (f" (IHSG {_f(ih)})" if ih else ""),
          f"Sudah disetor {_jt(st.get('disetor', st['modal_masuk']))} | sisa komitmen {_jt(sisa_komitmen(st))} | kas riil bebas {_jt(max(0.0, kas_riil(st)))} | realized {_jt(realized)}"]
    aksi = ("Setor " + _jt(perlu_setor(st)) + " · " if perlu_setor(st) > 0 else "") + "Beli " + (", ".join(f"{k} {_f(o['lot'])} lot ≤{_f(o['limit'])}" for k, o in st["pend_buy"].items()) or "-") \
        + " · Jual " + (", ".join([f"{k} {_f(p['lot'])} lot" for k, p in jual] + [f"{k} {_f(q)} lot (sebagian)" for k, q in st.get("pend_trim", {}).items() if k in st["pos"]]) or "-") \
        + " · SL naik " + (", ".join(k for k in now_trig if k in prev and now_trig[k] > prev[k]) or "-")
    banner = f"Trendline – {AKUN_NAMA.title()}: " + aksi
    rows = _ringkas_rows(st, lambda k: float(data[k].Close[data[k].index <= D].iloc[-1]), D)
    foot = (f"Setor {_jt(perlu_setor(st))} sebelum pre-opening | " if perlu_setor(st) > 0 else "") + \
           f"Kas order {_jt(siap)} | Ekuitas {_jt(eq['eq'])} ({_pct(r)} vs IHSG {_pct(ih_ret) if ih_ret is not None else '-'})"
    ringkas = [f"TRENDLINE – {AKUN_NAMA}", f"close {hari} {D.day} {D.strftime('%b %Y')}", ""] + rows + ["", foot]
    st["last_report_date"] = d
    st["last_report_pos"] = now_trig
    return dict(banner=banner, ringkas="\n".join(ringkas), text="\n".join(L), full=full)


# ---------------------------------------------------------------- CLI (dipakai jadwal otomatis)
def run_nightly(state_path, out_path, now=None, raw=None, ihsg=None, wait=300):
    """Satu kali jalan laporan malam. Hasil: file state (diperbarui bila OK) dan file laporan
    berisi baris TANGGAL DATA / STATUS / BANNER lalu teks laporan."""
    import time
    from datetime import timedelta, timezone
    now = now or datetime.now(timezone(timedelta(hours=7)))
    today = pd.Timestamp(now.date())

    def gagal(D, msg):
        open(out_path, "w").write(f"TANGGAL DATA: {D}\nSTATUS: GAGAL - {msg}\nBANNER: Trendline – {AKUN_NAMA.title()}: GAGAL - {msg}\n")
        return dict(status="GAGAL", msg=msg)

    st = state_from_json(open(state_path).read())
    import os
    uji = os.environ.get("TL_UJI_SAMPAI")       # mode uji: potong data sampai tanggal ini, state uji terpisah
    if uji:
        U = pd.Timestamp(uji)
        raw = {k: df[df.index <= U] for k, df in (raw if raw is not None else download_all()).items() if (df.index <= U).sum() > 250}
        ihsg = (ihsg if ihsg is not None else fetch_ihsg())
        ihsg = ihsg[ihsg.index <= U]
        now = datetime(U.year, U.month, U.day, 21, 40, tzinfo=timezone(timedelta(hours=7)))
        today = pd.Timestamp(now.date())
    for attempt in range(3):
        r = raw if raw is not None else download_all()
        D = max(df.index[-1] for df in r.values())
        if raw is not None or D >= today or now.weekday() >= 5:
            break
        time.sleep(wait)
    ih = ihsg if ihsg is not None else fetch_ihsg()
    if D < today and now.weekday() < 5:
        return gagal(D.date(), f"Belum ada data close hari ini ({today.date()}): libur bursa atau Yahoo telat. Data terakhir {D.date()}. Posisi tidak diubah.")
    aktif = [k for k, df in r.items() if df.Volume.tail(5).sum() > 0 and df.index[-1] >= D - pd.Timedelta(days=10)]
    tertinggal = [k for k in aktif if r[k].index[-1] < D]
    if ih.index[-1] > D or len(tertinggal) > 0.10 * len(aktif):
        return gagal(D.date(), f"Data Yahoo belum lengkap (IHSG {ih.index[-1].date()}, {len(tertinggal)}/{len(aktif)} emiten aktif tertinggal). Posisi tidak diubah.")
    if st["last_date"] and pd.Timestamp(st["last_date"]) >= D:
        return gagal(D.date(), f"Data {D.date()} sudah diproses sebelumnya. Posisi tidak diubah.")
    data, clog = clean_all(r)
    P = prepare(data)
    set_ihsg(ih, data)
    st, days = nightly(st, data, P)
    if st.get("start_date") is None:            # laporan pertama: titik awal pembanding IHSG
        st["start_date"] = st["last_date"]
        st["ihsg_start"] = float(ih[ih.index <= pd.Timestamp(st["last_date"])].iloc[-1])
    rep = nightly_report(st, data, P, ih)
    open(state_path, "w").write(state_to_json(st))
    label = "UJI (data lama, bukan sinyal hari ini) — " if os.environ.get("TL_UJI_SAMPAI") else ""
    open(out_path, "w").write(f"TANGGAL DATA: {st['last_date']}\nSTATUS: OK\nBANNER: {label}{rep['banner']}\n\n{label}{rep['ringkas']}"
                              f"\n\n──────── LAPORAN LENGKAP ────────\n\n{label}{rep['text']}\n")
    return dict(status="OK", banner=rep["banner"], text=rep["text"], days=[str(x.date()) for x in days])


def sunday_report(st, today=None):
    """Laporan Minggu malam: ulang aksi Senin dari laporan Jumat + tutup buku mingguan. Tanpa unduh data."""
    from datetime import timedelta, timezone
    today = pd.Timestamp(today) if today is not None else pd.Timestamp(datetime.now(timezone(timedelta(hours=7))).date())
    D = pd.Timestamp(st["last_date"])
    mon = D - pd.Timedelta(days=D.weekday())                       # Senin minggu data terakhir
    eqs = st["equity"]
    prev = [e for e in eqs if pd.Timestamp(e["d"]) < mon]
    wk = [e for e in eqs if pd.Timestamp(e["d"]) >= mon]
    e0 = prev[-1]["eq"] if prev else st["modal_masuk"]
    e1 = eqs[-1]["eq"]
    r_w = 1.0
    base = e0
    for e in wk:
        r_w *= (e["eq"] - e.get("dep", 0.0)) / base
        base = e["eq"]
    r_w -= 1
    tr = [x for x in st["log"] if pd.Timestamp(x["jual"]) >= mon]
    rz_w = sum(x["pnl"] for x in tr)
    rz_all = sum(x["pnl"] for x in st["log"])
    ih = st.get("ihsg_hist", {})
    ihk = sorted(ih)
    ih0 = [ih[k] for k in ihk if pd.Timestamp(k) < mon]
    ih1 = ih[ihk[-1]] if ihk else None
    ih_w = (ih1 / ih0[-1] - 1) if (ih0 and ih1) else None
    ih_all = (ih1 / st["ihsg_start"] - 1) if (ih1 and st.get("ihsg_start")) else None
    L = [f"TRENDLINE v{VERSION.split()[0]} • {AKUN} • MINGGU {today.day} {today.strftime('%b %Y')}",
         f"Ulangan rekomendasi dari data close {['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'][D.weekday()]} {D.day} {D.strftime('%b %Y')} + tutup buku mingguan", "",
         "━━ AKSI SENIN (sama dengan laporan Jumat) ━━"]
    L += st.get("last_aksi", ["(laporan Jumat belum ada)"])
    L += ["", f"━━ TUTUP BUKU MINGGU {mon.strftime('%d %b')}–{D.strftime('%d %b %Y')} ━━",
          f"Ekuitas {_jt(e0)} → {_jt(e1)} | minggu ini {_pct(r_w)} vs IHSG {_pct(ih_w) if ih_w is not None else '-'}",
          f"Transaksi ditutup minggu ini: {len(tr)} (untung {sum(1 for x in tr if x['pnl'] > 0)}, rugi {sum(1 for x in tr if x['pnl'] <= 0)}) | realized {_jt(rz_w)}"]
    for x in tr:
        L.append(f"  {x['kode']} {x['lot']} lot  {_f(x['harga_beli'])} → {_f(x['harga_jual'])}  {_pct(x['ret'])} / Rp{_f(x['pnl'])}")
    L += ["", f"━━ POSISI ({len(st['pos'])}) ━━"]
    snap = st.get("snap", {})
    for k, p in st["pos"].items():
        c = snap.get(k)
        pl = (c * (1 - FEE_S) / (p["ent"] * (1 + FEE_B)) - 1) if c else None
        L.append(f"  {k:5} {p['lot']} lot  avg {_f(p['ent'])}  close {_f(c)}  {_pct(pl) if pl is not None else '-'}  jual≤{_f(trigger_price(p['sl']))}"
                 + ("  (JUAL Senin)" if p["sell"] else "")
                 + (f"  ({st['pend_trim'][k]} lot dijual Senin, sisa {p['lot'] - st['pend_trim'][k]} lot)" if k in st.get("pend_trim", {}) else ""))
    L += ["", f"━━ KUMULATIF sejak {st.get('start_date')} ━━",
          f"Sistem {_pct(twr(st))} vs IHSG {_pct(ih_all) if ih_all is not None else '-'} | realized {_jt(rz_all)}",
          f"Sudah disetor {_jt(st.get('disetor', st['modal_masuk']))} dari komitmen {_jt(st['modal_masuk'])} | sisa {_jt(sisa_komitmen(st))}"]
    ps = perlu_setor(st)
    aksi = (f"Setor {_jt(ps)} · " if ps > 0 else "") + "Beli " + (", ".join(f"{k} {_f(o['lot'])} lot ≤{_f(o['limit'])}" for k, o in st["pend_buy"].items()) or "-") \
        + " · Jual " + (", ".join([f"{k} {_f(p['lot'])} lot" for k, p in st["pos"].items() if p["sell"]] + [f"{k} {_f(q)} lot (sebagian)" for k, q in st.get("pend_trim", {}).items() if k in st["pos"]]) or "-")
    banner = f"Trendline – {AKUN_NAMA.title()}: Senin " + aksi + f" · minggu ini {_pct(r_w)} vs IHSG {_pct(ih_w) if ih_w is not None else '-'}"
    ringkas = [f"TRENDLINE – {AKUN_NAMA}", f"Min {today.day} {today.strftime('%b %Y')} · aksi Senin (data close {D.day} {D.strftime('%b')})", ""] \
        + _ringkas_rows(dict(st, last_report_pos={}), lambda k: snap.get(k) or st["pos"][k]["ent"], D) + ["",
          (f"Setor {_jt(ps)} sebelum Senin pre-opening | " if ps > 0 else "Tidak perlu setor | ")
          + f"Minggu ini {_pct(r_w)} vs IHSG {_pct(ih_w) if ih_w is not None else '-'} | Ekuitas {_jt(e1)}"]
    st["last_week_close"] = str(today.date())
    return dict(banner=banner, ringkas="\n".join(ringkas), text="\n".join(L))


def run_sunday(state_path, out_path, today=None):
    st = state_from_json(open(state_path).read())
    rep = sunday_report(st, today)
    open(state_path, "w").write(state_to_json(st))
    open(out_path, "w").write(f"TANGGAL DATA: {st['last_date']}\nSTATUS: OK\nBANNER: {rep['banner']}\n\n{rep['ringkas']}"
                              f"\n\n──────── LAPORAN LENGKAP ────────\n\n{rep['text']}\n")
    return rep


if __name__ == "__main__":
    import os
    import streamlit as st

    st.set_page_config(page_title=f"Trendline Engine — {AKUN}", layout="wide")
    st.title(f"TRENDLINE ENGINE — {AKUN} ({AKUN_NAMA})")
    st.caption(f"Versi: {VERSION}")

    sp = "trendline_state.json"
    op = "trendline_laporan.md"

    with st.sidebar:
        st.header("Pengaturan & Eksekusi")
        modal_init = st.number_input(
            "Modal Awal / Komitmen (Rp)",
            min_value=1_000_000,
            value=int(MODAL_AWAL),
            step=5_000_000,
        )
        tunggu_detik = st.number_input(
            "Jeda retry Yahoo Finance (detik)",
            min_value=5,
            max_value=300,
            value=30,
            step=5,
        )
        reset_state = st.checkbox("Buat / reset state baru saat inisialisasi", value=False)

    if not os.path.exists(sp) or reset_state:
        st.warning(f"File `{sp}` belum tersedia atau mode reset aktif. Silakan inisialisasi state terlebih dahulu.")
        if st.button("Inisialisasi State Baru (Init Live)", type="primary"):
            with st.spinner("Mengunduh data OHLCV & IHSG, menghitung indikator, dan membuat state awal..."):
                raw_init = download_all()
                ihsg_init = fetch_ihsg()
                data_init, _ = clean_all(raw_init)
                P_init = prepare(data_init)
                set_ihsg(ihsg_init, data_init)
                st_init = init_live(data_init, P_init, ihsg_init, float(modal_init))
                open(sp, "w").write(state_to_json(st_init))
                rep_init = nightly_report(st_init, data_init, P_init, ihsg_init)
                open(sp, "w").write(state_to_json(st_init))
                open(op, "w").write(
                    f"TANGGAL DATA: {st_init['last_date']}\nSTATUS: OK\nBANNER: {rep_init['banner']}\n\n"
                    f"{rep_init['ringkas']}\n\n──────── LAPORAN LENGKAP ────────\n\n{rep_init['text']}\n"
                )
            st.success("State awal berhasil dibuat!")
            st.rerun()
        st.stop()

    st_curr = state_from_json(open(sp).read())
    eq_last = st_curr["equity"][-1]["eq"] if st_curr.get("equity") else st_curr.get("cash", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data Terakhir", st_curr.get("last_date") or "-")
    c2.metric("Ekuitas", rp(eq_last) if "rp" in globals() else _jt(eq_last))
    c3.metric("Kas Sistem", _jt(st_curr.get("cash", 0.0)))
    c4.metric("Posisi Aktif", f"{len(st_curr.get('pos', {}))} saham")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Jalankan Update Malam (Nightly)", type="primary", use_container_width=True):
            with st.spinner("Mengunduh data terbaru & memproses laporan malam..."):
                res = run_nightly(sp, op, wait=int(tunggu_detik))
            if res["status"] == "OK":
                st.success(f"Selesai! {res['banner']}")
                st.rerun()
            else:
                st.warning(res["msg"])

    with col2:
        if st.button("Jalankan Laporan Minggu (--minggu)", use_container_width=True):
            with st.spinner("Menyusun laporan Minggu & tutup buku mingguan..."):
                res_w = run_sunday(sp, op)
            st.success(f"Selesai! {res_w['banner']}")
            st.rerun()

    if os.path.exists(op):
        raw_rep = open(op).read()
        tab_ringkas, tab_lengkap, tab_raw, tab_backup = st.tabs([
            "Laporan Ringkas",
            "Laporan Lengkap",
            "Teks Mentah (.md)",
            "Backup State (.json)"
        ])

        ringkas_txt, lengkap_txt = raw_rep, raw_rep
        marker = "──────── LAPORAN LENGKAP ────────"
        if marker in raw_rep:
            parts = raw_rep.split(marker, 1)
            ringkas_txt = parts[0].strip()
            lengkap_txt = parts[1].strip()

        with tab_ringkas:
            st.code(ringkas_txt, language="text")

        with tab_lengkap:
            st.code(lengkap_txt, language="text")

        with tab_raw:
            st.text_area("Salin seluruh teks laporan:", raw_rep, height=450)

        with tab_backup:
            st.info("Unduh `trendline_state.json` setelah update berhasil jika ingin menyimpannya sebagai backup atau meng-commit ke GitHub.")
            st.download_button(
                label="Unduh trendline_state.json",
                data=open(sp).read(),
                file_name="trendline_state.json",
                mime="application/json",
            )
    else:
        st.info("Belum ada file laporan (`trendline_laporan.md`). Klik **Jalankan Update Malam** untuk menghasilkan laporan.")
