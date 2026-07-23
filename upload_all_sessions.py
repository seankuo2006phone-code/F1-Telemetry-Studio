import fastf1
import pandas as pd
from huggingface_hub import HfApi
import os

fastf1.Cache.enable_cache('fastf1_cache')

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"
api = HfApi()

# 設定你要下載的年份（可自行增減，例如 [2023, 2024]）
YEARS = [2024]
SESSIONS = ['FP1', 'FP2', 'FP3', 'Q', 'R']

cols_to_keep = [
    "Driver", "Team", "Distance", "Speed",
    "Throttle", "Brake", "RPM",
    "X", "Y", "DRS", "Sector"
]

for year in YEARS:
    print(f"正在獲取 {year} 年官方賽事排程...")
    schedule = fastf1.get_event_schedule(year)
    
    for _, event in schedule.iterrows():
        # 排除測試賽 (Round 0)
        if event['RoundNumber'] == 0:
            continue
            
        event_name = event['EventName'].replace(" Grand Prix", "").replace(" ", "_")
        
        for sess_type in SESSIONS:
            filename = f"{year}_{event_name}_{sess_type}.parquet"
            
            try:
                # 載入指定的賽程
                session = fastf1.get_session(year, event['EventName'], sess_type)
                session.load(telemetry=True, weather=False, messages=False)
                
                all_telemetry = []
                for driver in session.drivers:
                    try:
                        laps = session.laps.pick_driver(driver)
                        if len(laps) == 0: continue
                        fastest_lap = laps.pick_fastest()
                        telemetry = fastest_lap.get_telemetry()
                        
                        telemetry['Driver'] = driver
                        telemetry['Team'] = fastest_lap['Team']
                        
                        max_dist = telemetry['Distance'].max()
                        if max_dist > 0:
                            norm_dist = telemetry['Distance'] / max_dist
                            telemetry['Sector'] = pd.cut(norm_dist, bins=[0, 1/3, 2/3, 1], labels=[1, 2, 3])
                        else:
                            telemetry['Sector'] = 1
                            
                        all_telemetry.append(telemetry)
                    except Exception:
                        pass
                
                if len(all_telemetry) > 0:
                    df_combined = pd.concat(all_telemetry, ignore_index=True)
                    existing_cols = [c for c in cols_to_keep if c in df_combined.columns]
                    df_combined = df_combined[existing_cols]
                    
                    df_combined.to_parquet(filename)
                    
                    print(f"正在上傳: {filename} ...")
                    api.upload_file(
                        path_or_fileobj=filename,
                        path_in_repo=filename,
                        repo_id=REPO_ID,
                        repo_type="dataset"
                    )
                    
                    os.remove(filename)
                    print(f"✔ {filename} 上傳成功！")
                else:
                    print(f"✖ {filename} 無有效資料，跳過。")
                    
            except Exception as e:
                # 某些站點可能沒有 Sprint 或是還沒開賽，直接略過錯誤
                print(f"ℹ 略過 {filename} (可能無此賽程)")

print("全賽季所有賽程與數據同步作業已全面完成！")