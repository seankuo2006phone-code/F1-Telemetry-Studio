import fastf1
import pandas as pd
import os

fastf1.Cache.enable_cache('fastf1_cache')

def generate_all_sessions(year=2024, event="Bahrain Grand Prix"):
    sessions = ['FP1', 'FP2', 'FP3', 'Q', 'R']
    
    for session_type in sessions:
        try:
            print(f"正在從 FastF1 載入 {year} {event} ({session_type})...")
            session = fastf1.get_session(year, event, session_type)
            session.load(telemetry=True, weather=False, messages=False)
            
            records = []
            for driver in session.drivers:
                try:
                    laps = session.laps.pick_driver(driver)
                    if laps.empty: continue
                    
                    valid_laps = laps.pick_accurate()
                    if valid_laps.empty:
                        valid_laps = laps
                    
                    fastest_lap = valid_laps.pick_fastest()
                    if fastest_lap is None or pd.isna(fastest_lap['LapTime']): continue
                    
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry.empty: continue
                    
                    driver_info = session.get_driver(driver)
                    driver_code = driver_info.get('Abbreviation', str(driver))
                    team_name = driver_info.get('TeamName', 'Unknown')
                    
                    # 確保寫入的是 3 字母縮寫 (VER, LEC 等)
                    telemetry['Driver'] = driver_code
                    telemetry['Team'] = team_name
                    records.append(telemetry)
                except Exception:
                    pass
                    
            if not records:
                print(f"-> {session_type} 無有效資料，跳過。")
                continue
                
            df = pd.concat(records, ignore_index=True)
            raw_event = event.replace(" ", "_")
            filename = f"{year}_{raw_event}_{session_type}.parquet"
            os.makedirs("parquet_cache", exist_ok=True)
            local_path = os.path.join("parquet_cache", filename)
            
            df.to_parquet(local_path)
            print(f"-> 成功生成：{filename}")
        except Exception as e:
            print(f"-> 該站無此賽程 ({session_type}) 或載入失敗: {e}")

if __name__ == "__main__":
    generate_all_sessions(year=2024, event="Bahrain Grand Prix")