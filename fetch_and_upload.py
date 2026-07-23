import os
import time
import ctypes
import fastf1
import pandas as pd
from huggingface_hub import HfApi, list_repo_files

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"
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

def prevent_computer_sleep():
    """🛡️ 告訴 Windows 保持清醒（防止系統進入睡眠與關閉電源）"""
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

def rebuild_f1_dataset():
    api = HfApi()
    token = os.environ.get("HF_TOKEN")
    
    print("🚀 啟動無情抓取程式（已移除所有冷卻限制，暴力連線版）...")

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
                if "Testing" in event_name or "Pre-Season" in event_name:
                    continue
                
                safe_event_name = event_name.replace(" ", "_")
                round_number = event['RoundNumber']
                
                for code, full_name in SESSION_MAPPING.items():
                    safe_session_name = full_name.replace(" ", "_")
                    filename = f"{year}_{safe_event_name}_{safe_session_name}.parquet"
                    filepath = os.path.join(LOCAL_DATA_DIR, filename)
                    
                    if filename in existing_files:
                        print(f"[已存在雲端，自動跳過] {filename}")
                        continue

                    try:
                        session = fastf1.get_session(year, round_number, code)
                        session.load(telemetry=True, weather=False, messages=False)
                        
                        df_to_save = session.laps
                        if df_to_save is None or df_to_save.empty:
                            continue
                            
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
                            
                        time.sleep(0.3)
                            
                    except Exception as e:
                        # 💥 遇到任何錯誤 (包含 API 限制) 都只印出警告，直接硬幹下一個檔案
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