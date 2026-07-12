# ... (bagian penarikan data) ...

            # ---------------------------------------------------------
            # NEW STRICT FILTERS (MENGGANTIKAN PARAMETER DEFAULT)
            # ---------------------------------------------------------
            
            # 1. Parameter Utama: Lonjakan Volume Ekstrem ( > 4x MA20)
            is_volume_explosion = last['Volume'] > (last['vol_ma20'] * 4)
            
            # 2. Parameter Momentum Harga (Bullish Marubozu & Naik > 10%)
            is_strong_bull = (last['Close'] > last['Open']) and (last['chg_pct'] >= 0.10)
            
            # 3. SMMA 200 Crossover (Kemarin di bawah/sama dengan SMMA, hari ini di atas SMMA)
            is_smma_cross = (last['Close'] > last['SMMA_200']) and (prev['Close'] <= prev['SMMA_200'])
            
            # 4. Stochastic Momentum (%K di atas %D)
            is_stoch_momentum = last['Stoch_K'] > last['Stoch_D']
            
            # STRICT GATEKEEPER: HANYA lolos jika KEEMPAT syarat terpenuhi
            if not (is_volume_explosion and is_strong_bull and is_smma_cross and is_stoch_momentum): 
                continue
                
            # ---------------------------------------------------------
            
            score = 100 # Konfirmasi maksimal karena parameter sangat ketat
            strategy_tag = "VOL BREAKOUT"
            thesis_points = []
            
            thesis_points.append(f"🔥 <b>EXPLOSIVE BREAKOUT:</b> Volume meledak {last['vol_power']:.1f}x dari rata-rata dengan kenaikan +{last['chg_pct']*100:.1f}%.")
            thesis_points.append("🎯 <b>SMMA 200 CROSSOVER:</b> Validasi penembusan resisten SMMA 200 dari bawah, indikasi reversal kuat.")
            thesis_points.append("⚡ <b>MOMENTUM UP:</b> Stochastic %K memotong ke atas %D menegaskan momentum terakselerasi.")
            
            # ... (eksekusi rencana trading dan rendering UI) ...
