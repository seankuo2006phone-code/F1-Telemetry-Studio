import os
import pandas as pd
import fastf1
from huggingface_hub import hf_hub_download

def load_telemetry_data(filename):
    """Load telemetry data from Hugging Face Hub"""
    file_path = hf_hub_download(
        repo_id="SeanKuo2006/F1-Telemetry-Data",
        filename=filename,
        repo_type="dataset"
    )
    return pd.read_parquet(file_path)

def load_fastest_lap_telemetry(year, track, session_id, driver_abbr):
    cache_file = f"data_cache/{year}_{track}_{session_id}.parquet"
    if os.path.exists(cache_file):
        try:
            df = pd.read_parquet(cache_file)
            if driver_abbr == "FASTEST OVERALL":
                fastest_driver = df.loc[df['LapTime'].idxmin()]['Driver']
                tel = df[df['Driver'] == fastest_driver]
            else:
                tel = df[df['Driver'] == driver_abbr]
            
            if tel.empty:
                return {}, None
                
            lap_info = {'Team': tel['Team'].iloc[0], 'LapTime': tel['LapTime'].iloc[0]}
            return lap_info, tel
        except Exception as e:
            print(f"❌ 讀取快取發生錯誤: {e}")

    # 如果沒快取，直接回傳空值，嚴禁連線上網！
    print(f"⚠️ 找不到 {cache_file}，請先執行 build_cache.py 建立資料！")
    return {}, None


def get_session_drivers(year, track, session_id):
    """直接從 Parquet 檔案中提取有參賽的車手名單"""
    cache_file = f"data_cache/{year}_{track}_{session_id}.parquet"
    if os.path.exists(cache_file):
        df = pd.read_parquet(cache_file)
        return df['Driver'].unique().tolist()
    
    return []


def fetch_full_historical_trend(track, session_id):
    """直接讀取 2018-2025 的 Parquet 檔案來繪製歷史趨勢，斷絕網路連線"""
    trend_data = []
    for y in range(2018, 2026):
        cache_file = f"data_cache/{y}_{track}_{session_id}.parquet"
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
            fastest_lap = df['LapTime'].min()
            
            # 將時間轉換為秒數供圖表顯示
            total_s = fastest_lap.total_seconds() if hasattr(fastest_lap, 'total_seconds') else float(fastest_lap)
            trend_data.append({'Year': y, 'LapTime_s': total_s})
            
    return pd.DataFrame(trend_data)