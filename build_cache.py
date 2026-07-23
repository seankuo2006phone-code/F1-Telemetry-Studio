import fastf1
import pandas as pd
import os
import time
from fastf1.exceptions import RateLimitExceededError

# --- 設定 ---
CACHE_DIR = "data_cache"
FASTF1_CACHE = "fastf1_cache"
SESSION_TYPE = 'Q'
YEARS = range(2022, 2026)

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FASTF1_CACHE, exist_ok=True)
fastf1.Cache.enable_cache(FASTF1_CACHE)

def get_missing_list():
    """掃描目前缺漏的比賽"""
    missing = []
    for year in YEARS:
        schedule = fastf1.get_event_schedule(year)
        for _, event in schedule.iterrows():
            if event['RoundNumber'] == 0: continue
            file_name = f"{year}_{event['EventName'].replace(' ', '_')}_{SESSION_TYPE}.parquet"
            if not os.path.exists(os.path.join(CACHE_DIR, file_name)):
                missing.append((year, event))
    return missing

def main():
    while True:
        print("\n🔍 [系統檢查] 正在掃描缺失檔案...")
        missing_races = get_missing_list()
        
        if not missing_races:
            print("\n" + "="*50)
            print("✅ 下載完畢！所有場次已 100% 補齊。")
            print("="*50)
            break
        
        print(f"⚠️ 發現 {len(missing_races)} 場比賽缺漏，開始補齊...")
        
        # 開始自動下載任務
        for year, event in missing_races:
            event_name = event['EventName'].replace(' ', '_')
            file_name = f"{year}_{event_name}_{SESSION_TYPE}.parquet"
            file_path = os.path.join(CACHE_DIR, file_name)
            
            # 再做一次 double check，避免中間被手動下載補齊
            if os.path.exists(file_path): continue

            try:
                print(f"📥 正在抓取: {year} {event_name}")
                session = event.get_session(SESSION_TYPE)
                session.load(telemetry=True, weather=False, messages=False)
                
                if session.results.empty:
                    print(f"⚠️ {year} {event_name} 數據異常，跳過")
                    continue

                laps = session.laps
                telemetry_list = []
                for driver in session.results['Abbreviation']:
                    driver_fastest = laps.pick_drivers(driver).pick_fastest()
                    # 嚴格的防錯檢查 (解決 NoneType 問題)
                    if driver_fastest is not None and not driver_fastest.empty:
                        tel = driver_fastest.get_telemetry()
                        tel['Driver'] = driver 
                        tel['Team'] = driver_fastest['Team']
                        tel['LapTime'] = driver_fastest['LapTime']
                        telemetry_list.append(tel)
                
                if telemetry_list:
                    pd.concat(telemetry_list).to_parquet(file_path, engine='pyarrow')
                    print(f"✅ 完成: {file_name}")
                
            except RateLimitExceededError:
                print("\n🛑 觸發 API 流量限制！系統將自動暫停並等待下一次重試...")
                time.sleep(60)
                break # 跳出當前迴圈，觸發外層 while 重新執行掃描
            except Exception as e:
                print(f"❌ 錯誤 {event_name}: {e}")
                continue # 遇到錯誤就跳過這場，繼續下一場

if __name__ == "__main__":
    main()