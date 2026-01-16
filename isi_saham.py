import pandas as pd
import requests
from io import StringIO

def get_real_idx_stocks():
    print("🚀 MEMULAI PROSES SCRAPING DATA SAHAM IDX...")
    
    # 1. Gunakan URL Wikipedia (Sumber Publik Paling Stabil untuk Ticker)
    url = "https://en.wikipedia.org/wiki/List_of_companies_listed_on_the_Indonesia_Stock_Exchange"
    
    # 2. TEKNIK ANTI-BLOKIR: Menyamar sebagai Browser Chrome
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Request halaman dengan header
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Cek jika ada error koneksi
        
        # Baca tabel dari konten HTML
        # Kita mencari tabel yang punya kolom 'Stock Code' atau 'Ticker Symbol'
        dfs = pd.read_html(StringIO(response.text))
        
        target_df = None
        for df in dfs:
            # Cek kolom untuk memastikan ini tabel saham
            # Wikipedia sering mengubah nama header, kita cek beberapa kemungkinan
            cols = [c.lower() for c in df.columns]
            if any("code" in c for c in cols) and any("company" in c for c in cols):
                target_df = df
                break
        
        if target_df is None:
            print("❌ Gagal menemukan tabel saham di halaman tersebut.")
            return []

        # 3. BERSIHKAN DATA
        # Ambil kolom pertama (biasanya Code)
        target_df = target_df.rename(columns={target_df.columns[0]: 'Ticker'})
        
        # Pastikan Ticker adalah string 4 karakter
        valid_stocks = []
        for code in target_df['Ticker']:
            clean_code = str(code).strip()[:4] # Ambil 4 huruf pertama
            if clean_code.isalpha() and len(clean_code) == 4:
                valid_stocks.append(clean_code)
        
        print(f"✅ BERHASIL: Ditemukan {len(valid_stocks)} saham aktif.")
        return valid_stocks

    except Exception as e:
        print(f"❌ TERJADI ERROR: {e}")
        return []

# --- EKSEKUSI ---
all_tickers = get_real_idx_stocks()

if all_tickers:
    # Simpan ke CSV agar bisa dipakai Dashboard
    df_save = pd.DataFrame(all_tickers, columns=["Ticker"])
    df_save.to_csv("daftar_saham_idx_fixed.csv", index=False)
    print("📁 Data tersimpan di: daftar_saham_idx_fixed.csv")
    
    # Preview 10 saham pertama
    print(f"Contoh Saham: {all_tickers[:10]}")
else:
    # FALLBACK JIKA SCRAPING MACET TOTAL (Agar Anda tetap punya data)
    print("⚠️ Menggunakan Data Fallback (Top 50 Liquid)...")
    fallback_list = [
        "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "GOTO",
        "BUKA", "EMTK", "ARTO", "BRPT", "TPIA", "BREN", "CUAN", "PTRO", "ADRO", "PTBA",
        "ITMG", "PGAS", "MEDC", "ANTM", "MDKA", "INCO", "MBMA", "BRMS", "AMMN", "PSAB",
        "BUMI", "DEWA", "ENRG", "BSDE", "CTRA", "SMRA", "PANI", "ASRI", "MNCN", "SCMA",
        "KLBF", "SILO", "HEAL", "MIKA", "CPIN", "JPFA", "MYOR", "UNVR", "ACES", "MAPI"
    ]
    df_save = pd.DataFrame(fallback_list, columns=["Ticker"])
    df_save.to_csv("daftar_saham_idx_fixed.csv", index=False)
