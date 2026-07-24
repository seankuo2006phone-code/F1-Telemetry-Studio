import os
import time
import ctypes
import logging
import fastf1
import pandas as pd
from huggingface_hub import HfApi, list_repo_files

# ==========================================
# 1. 核心參數設定區
# ==========================================
REPO_ID = "SeanKuo2006/F1-Telemetry-Data-V2" 
LOCAL_CACHE_DIR = "./f1_cache"
LOCAL_DATA_DIR = "./F1_data_temp"
YEARS = range(2018, 2026)
MAX_LOOPS = 5  # 最多重複掃描 5 輪

# 前端絕對不可或缺的遙測欄位
COLS_TO_KEEP = ["Driver", "Team", "Distance", "Speed", "Throttle", "Brake", "RPM", "X", "Y", "DRS", "Sector"]

SESSION_MAPPING = {
    "FP1": "Free Practice 1", "FP2": "Free Practice 2", "FP3": "Free Practice 3",
    "SQ": "Sprint Shootout", "S": "Sprint", "Q": "Qualifying", "R": "Race"
}

# 建立必要的資料夾
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
fastf1.Cache.enable_cache(LOCAL_CACHE_DIR)

# 設定日誌
logging.basicConfig(filename='f1_upload_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# ==========================================
# 2. 系統與網路防禦機制
# ==========================================
def prevent_computer_sleep():
    """強制 Windows 保持清醒"""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except Exception:
        pass

def get_uploaded_files_with_retry(api):
    """取得雲端檔案清單（含斷線無限重試機制）"""
    while True:
        try:
            return set(list_repo_files(repo_id=REPO_ID, repo_type="dataset"))
        except Exception as e:
            print(f"⚠️ 取得雲端檔案清單失敗，重試中... ({e})")
            time.sleep(3)

# ==========================================
# 3. 主程序 (加入自動重複檢查與無間斷機制)
# ==========================================
def main():
    api = HfApi()
    token = os.environ.get("HF_TOKEN")
    
    print("🚀 [全速衝刺版] 啟動！程式將不斷掃描，抓過的會印出提示，且中途不休息。")
    
    current_loop = 1
    
    while current_loop <= MAX_LOOPS:
        print(f"\n🔄 ===== 第 {current_loop} 輪全面掃描開始 =====")
        new_uploads_count = 0
        existing_files = get_uploaded_files_with_retry(api)
        
        for year in YEARS:
            prevent_computer_sleep()
            print(f"\n👉 正在檢查 {year} 年賽季...")
            
            try:
                schedule = fastf1.get_event_schedule(year)
            except Exception as e:
                logging.error(f"無法取得 {year} 年行事曆: {e}")
                continue

            for _, event in schedule.iterrows():
                event_name = event['EventName']
                if "Testing" in event_name or "Pre-Season" in event_name or event['RoundNumber'] == 0:
                    continue
                
                safe_event_name = str(event_name).replace(" ", "_").replace("/", "_")
                round_number = event['RoundNumber']
                
                for code, full_name in SESSION_MAPPING.items():
                    safe_session_name = full_name.replace(" ", "_")
                    filename = f"{year}_{safe_event_name}_{safe_session_name}.parquet"
                    filepath = os.path.join(LOCAL_DATA_DIR, filename)
                    
                    if filename in existing_files:
                        print(f"⏩ {filename} 已經上傳hugging face")
                        continue
                        
                    print(f"⏳ 發現缺漏，正在補抓: {filename}")
                    
                    try:
                        session = fastf1.get_session(year, round_number, code)
                        try:
                            session.load(telemetry=True, weather=False, messages=False)
                        except Exception as load_e:
                            logging.warning(f"略過 {filename}: 官方資料庫缺漏 ({load_e})")
                            continue

                        all_telemetry = []
                        
                        # 單一車手防呆
                        for driver in session.drivers:
                            try:
                                laps = session.laps.pick_driver(driver)
                                if len(laps) == 0: continue
                                
                                fastest_lap = laps.pick_fastest()
                                if pd.isna(fastest_lap.get('LapTime')): continue
                                
                                telemetry = fastest_lap.get_telemetry()
                                if telemetry.empty: continue
                                
                                dr_info = session.get_driver(driver)
                                telemetry['Driver'] = dr_info.get('Abbreviation', driver)
                                telemetry['Team'] = fastest_lap['Team']
                                
                                max_dist = telemetry['Distance'].max()
                                if max_dist > 0:
                                    norm_dist = telemetry['Distance'] / max_dist
                                    telemetry['Sector'] = pd.cut(norm_dist, bins=[0, 1/3, 2/3, 1], labels=[1, 2, 3])
                                else:
                                    telemetry['Sector'] = 1
                                    
                                all_telemetry.append(telemetry)
                            except Exception as driver_e:
                                continue 
                        
                        if not all_telemetry:
                            continue
                            
                        df_to_save = pd.concat(all_telemetry, ignore_index=True)
                        existing_cols = [c for c in COLS_TO_KEEP if c in df_to_save.columns]
                        df_to_save = df_to_save[existing_cols]
                        
                        df_to_save.to_parquet(filepath, index=False)
                        
                        for attempt in range(3):
                            try:
                                api.upload_file(
                                    path_or_fileobj=filepath,
                                    path_in_repo=filename,
                                    repo_id=REPO_ID,
                                    repo_type="dataset",
                                    token=token
                                )
                                existing_files.add(filename)
                                print(f"✅ 成功補齊並上傳: {filename}")
                                new_uploads_count += 1
                                break
                            except Exception as upload_e:
                                if attempt == 2:
                                    logging.error(f"上傳失敗 {filename}: {upload_e}")
                                time.sleep(3)
                                
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            
                    except Exception as global_e:
                        logging.error(f"徹底崩潰 {filename}: {global_e}")
                        continue
        
        # 檢查這一輪有沒有抓到新東西
        if new_uploads_count == 0:
            print("\n🎉 [任務徹底完成] 連續一整輪都沒有新檔案可抓，所有資料都已 100% 補齊！")
            break
        else:
            print(f"\n⚠️ 第 {current_loop} 輪結束，總共補齊了 {new_uploads_count} 份缺失資料。")
            print("⚡ 立即展開下一輪掃描...")
            current_loop += 1

if __name__ == "__main__":
    main()