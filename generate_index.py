import os
import pandas as pd
from huggingface_hub import HfApi, list_repo_files

# 你的 Hugging Face 倉庫 ID
REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

def create_index():
    print("🔍 正在掃描雲端檔案，準備建立總目錄...")
    api = HfApi()
    token = os.environ.get("HF_TOKEN")
    
    try:
        files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
    except Exception as e:
        print(f"⚠️ 無法取得檔案清單: {e}")
        return
        
    records = []
    for f in files:
        if not f.endswith(".parquet") or f == "index.parquet":
            continue
            
        name_no_ext = f.replace(".parquet", "")
        
        session_map = {
            "Free_Practice_1": "Free Practice 1",
            "Free_Practice_2": "Free Practice 2",
            "Free_Practice_3": "Free Practice 3",
            "Sprint_Shootout": "Sprint Shootout",
            "Sprint": "Sprint",
            "Qualifying": "Qualifying",
            "Race": "Race"
        }
        
        for suffix, session_name in session_map.items():
            if name_no_ext.endswith(suffix):
                year = int(name_no_ext[:4])
                event_raw = name_no_ext[5:-(len(suffix)+1)]
                event_name = event_raw.replace("_", " ")
                
                # 💡 終極防呆：同時把 key 命名為 event 與 event_name，滿足後端所有需求！
                records.append({
                    "year": year,
                    "event": event_name,
                    "event_name": event_name,
                    "session": session_name,
                    "session_type": session_name,
                    "filename": f
                })
                break

    if not records:
        print("⚠️ 找不到任何有效的賽事檔案！")
        return
        
    df = pd.DataFrame(records)
    df.to_parquet("index.parquet", index=False)
    print(f"✅ 目錄建立完成！共收錄了 {len(df)} 場賽事檔案。")
    
    print("🚀 正在上傳目錄 (index.parquet) 到 Hugging Face...")
    try:
        api.upload_file(
            path_or_fileobj="index.parquet",
            path_in_repo="index.parquet",
            repo_id=REPO_ID,
            repo_type="dataset",
            token=token
        )
        print("🎉 上傳成功！圖書館員終於拿到目錄了！")
    except Exception as e:
        print(f"⚠️ 上傳失敗: {e}")

if __name__ == "__main__":
    create_index()