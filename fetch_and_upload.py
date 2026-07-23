import os
import time
import ctypes
import fastf1
import pandas as pd
from huggingface_hub import HfApi, list_repo_files

# ⚠️ 注意：如果你剛才有新建一個 Repository (例如結尾加了 -V2)，請記得改這裡！
REPO_ID = "SeanKuo2006/F1-Telemetry-Data-V2" 
LOCAL_CACHE_DIR = "./f1_cache"
LOCAL_DATA_DIR = "./F1 data"

os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
fastf1.Cache.enable_cache(LOCAL_CACHE_DIR)

SESSION_MAPPING = {
    "FP1": "Free Practice 1",
    "FP2": "Free Practice 2",
    "FP3": "Free Practice 3",
    "SQ": "Sprint Shootout",
    "S": "Sprint",
    "Q": "Qualifying",
    "R": "Race"
}

YEARS = range(2018, 2026)

# 確保只保留能畫出遙測圖表的關鍵欄位
cols_to_keep = [
    "Driver", "Team", "Distance", "Speed",
    "Throttle", "Brake", "RPM",
    "X", "Y", "DRS", "Sector"
]

def prevent_computer_sleep():
    """🛡️ 告訴 Windows 保持清醒（防止系統進入睡眠與關閉電源）"""
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

def rebuild_f1_dataset():
    api = HfApi()
    token = os.environ.get("HF_TOKEN")
    
    print("🚀 啟動無情抓取程式（防睡眠 + 真正遙測數據極速版）...")

    while True:
        # 🛡️ 每次大迴圈開始時，強制重新整理防睡眠狀態，確保筆電不待機
        prevent_computer_sleep()
        
        print("\n🔄 [開始新一輪巡邏] 正在取得雲端現有檔案清單以供自動略過...")
        try:
            existing_files = set(list_repo_files(repo_id=REPO_ID, repo_type="dataset"))
        except Exception as e:
            print(f"⚠️ 取得雲端檔案清單失敗: {e}，5秒後自動重試...")
            time.sleep(5)
            continue

        uploaded_in_this_pass = 0

        for year in YEARS:
            print(f"\n================ 正在處理 {year} 年賽季 ================")
            time.sleep(1)
            
            try:
                schedule = fastf1.get_event_schedule(year)
            except Exception as e:
                print(f"⚠️ 無法取得 {year} 年行事曆: {e}，略過此年份。")
                continue

            for _, event in schedule.iterrows():
                event_name = event['EventName']
                # 排除測試賽季或無效賽事
                if "Testing" in event_name or "Pre-Season" in event_name or event['RoundNumber'] == 0:
                    continue
                
                safe_event_name = event_name.replace(" ", "_")
                round_number = event['RoundNumber']
                
                for code, full_name in SESSION_MAPPING.items():
                    safe_session_name = full_name.replace(" ", "_")
                    filename = f"{year}_{safe_event_name}_{safe_session_name}.parquet"
                    filepath = os.path.join(LOCAL_DATA_DIR, filename)
                    
                    if filename in existing_files:
                        # 已經有了就無情跳過，不印廢話浪費效能
                        continue

                    try:
                        session = fastf1.get_session(year, round_number, code)
                        session.load(telemetry=True, weather=False, messages=False)
                        
                        # ==========================================
                        # 核心修復區：抓取真正的遙測數據，而不是 Laps！
                        # ==========================================
                        all_telemetry = []
                        for driver in session.drivers:
                            try:
                                laps = session.laps.pick_driver(driver)
                                if len(laps) == 0: continue
                                fastest_lap = laps.pick_fastest()
                                telemetry = fastest_lap.get_telemetry()
                                
                                # 轉換車手代號為 3 字母縮寫
                                telemetry['Driver'] = session.get_driver(driver)['Abbreviation']
                                telemetry['Team'] = fastest_lap['Team']
                                
                                # 計算賽道區段
                                max_dist = telemetry['Distance'].max()
                                if max_dist > 0:
                                    norm_dist = telemetry['Distance'] / max_dist
                                    telemetry['Sector'] = pd.cut(norm_dist, bins=[0, 1/3, 2/3, 1], labels=[1, 2, 3])
                                else:
                                    telemetry['Sector'] = 1
                                    
                                all_telemetry.append(telemetry)
                            except Exception:
                                pass
                        
                        if len(all_telemetry) == 0:
                            continue
                            
                        # 合併所有車手資料並篩選欄位
                        df_to_save = pd.concat(all_telemetry, ignore_index=True)
                        existing_cols = [c for c in cols_to_keep if c in df_to_save.columns]
                        df_to_save = df_to_save[existing_cols]
                        # ==========================================
                        
                        # 存檔並上傳
                        df_to_save.to_parquet(filepath, index=False)
                        
                        api.upload_file(
                            path_or_fileobj=filepath,
                            path_in_repo=filename,
                            repo_id=REPO_ID,
                            repo_type="dataset",
                            token=token
                        )
                        print(f"✅ [成功上傳] {filename}")
                        
                        existing_files.add(filename)
                        uploaded_in_this_pass += 1
                        
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            
                    except Exception as e:
                        # 💥 遇到任何錯誤都只印出警告，直接硬幹下一個檔案
                        print(f"⚠️ 傳輸 {filename} 時發生錯誤: {e}，無視警告直接進入下一個！")
                        continue

        # 如果真的完全沒有任何新檔案要上傳，才代表 100% 完工
        if uploaded_in_this_pass == 0:
            print("\n🎉 太棒了！所有年份與賽事皆已 100% 確認上傳完畢，自動結束程式！")
            break
        else:
            print(f"\n🔄 本輪共補充上傳了 {uploaded_in_this_pass} 個檔案，繼續進行下一輪巡邏...")
            time.sleep(3)

if __name__ == "__main__":
    rebuild_f1_dataset()