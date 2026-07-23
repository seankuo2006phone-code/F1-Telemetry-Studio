from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from huggingface_hub import list_repo_files

app = FastAPI(title="F1 Telemetry Studio PRO API (Bulletproof Engine)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"
DATASET_DIR = "parquet_cache"
os.makedirs(DATASET_DIR, exist_ok=True)

def _get_file_mapping():
    """自動掃描 Hugging Face 雲端檔案，精準分離 Grand Prix 與 Session"""
    mapping = {}
    try:
        files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        for f in files:
            if not f.endswith(".parquet"): continue
            name_part = f[:-8] # 移除 .parquet
            parts = name_part.split("_")
            if len(parts) < 2: continue
            
            year = str(parts[0])
            rest = parts[1:]
            rest_upper = [p.upper() for p in rest]
            
            # 從尾端精準判斷 Session 並從 rest 中剝離，確保 Grand Prix 名稱絕對純淨
            if len(rest_upper) >= 2 and rest_upper[-2] == "SPRINT" and rest_upper[-1] in ["QUALIFYING", "Q"]:
                session = "Sprint Qualifying"
                rest = rest[:-2]
            elif rest_upper[-1] in ["SQ"]:
                session = "Sprint Qualifying"
                rest = rest[:-1]
            elif rest_upper[-1] in ["SPRINT"]:
                session = "Sprint"
                rest = rest[:-1]
            elif rest_upper[-1] in ["Q", "QUALIFYING"]:
                session = "Qualifying"
                rest = rest[:-1]
            elif rest_upper[-1] in ["R", "RACE"]:
                session = "Race"
                rest = rest[:-1]
            elif rest_upper[-1] in ["1", "FP1", "P1"]:
                session = "Free Practice 1"
                rest = rest[:-1]
                if rest and rest[-1].upper() in ["FREE", "FP", "PRACTICE"]: rest = rest[:-1]
            elif rest_upper[-1] in ["2", "FP2", "P2"]:
                session = "Free Practice 2"
                rest = rest[:-1]
                if rest and rest[-1].upper() in ["FREE", "FP", "PRACTICE"]: rest = rest[:-1]
            elif rest_upper[-1] in ["3", "FP3", "P3"]:
                session = "Free Practice 3"
                rest = rest[:-1]
                if rest and rest[-1].upper() in ["FREE", "FP", "PRACTICE"]: rest = rest[:-1]
            else:
                session = rest[-1]
                rest = rest[:-1]
            
            # 清理殘留的字眼
            while rest and rest[-1].upper() in ["FREE", "PRACTICE", "FP"]:
                rest = rest[:-1]
                
            event_name = " ".join(rest).title()
            mapping[(year, event_name, session)] = f
            mapping[(year, event_name, rest_upper[-1] if rest_upper else session)] = f
    except Exception as e:
        print("解析 Hugging Face 檔案對應錯誤:", e)
    return mapping


def _load_session_df(year: int, event_name: str, session_type: str):
    raw_event = event_name.replace(" ", "_")
    
    # 建立多種可能的檔名組合直接去 Hugging Face 嘗試下載，不依賴 scan
    session_variants = {
        "Free Practice 1": ["FP1", "1", "Practice_1", "Free_Practice_1"],
        "Free Practice 2": ["FP2", "2", "Practice_2", "Free_Practice_2"],
        "Free Practice 3": ["FP3", "3", "Practice_3", "Free_Practice_3"],
        "Qualifying": ["Qualifying", "Q"],
        "Race": ["Race", "R"],
        "Sprint": ["Sprint"],
        "Sprint Qualifying": ["Sprint_Qualifying", "SQ"]
    }
    
    variants = session_variants.get(session_type, [session_type])
    
    # 依次嘗試所有可能的檔名格式
    for var in variants:
        filename = f"{year}_{raw_event}_{var}.parquet"
        local_path = os.path.join(DATASET_DIR, filename)

        if os.path.exists(local_path):
            return pd.read_parquet(local_path)
            
        hf_url = f"hf://datasets/{REPO_ID}/{filename}"
        try:
            print(f"嘗試從 Hugging Face 下載: {hf_url}")
            df_temp = pd.read_parquet(hf_url)
            df_temp.to_parquet(local_path)
            return df_temp
        except Exception as e:
            print(f"嘗試下載 {filename} 失敗: {e}")
            continue
            
    raise FileNotFoundError(f"找不到對應資料檔案: {year} {event_name} {session_type}")


@app.get("/api/options")
def get_options():
    options = {}
    mapping = _get_file_mapping()
    
    for (year, event_name, session), filename in mapping.items():
        norm_session = session
        if session.upper() in ["Q", "QUALIFYING"]: norm_session = "Qualifying"
        elif session.upper() in ["R", "RACE"]: norm_session = "Race"
        elif session.upper() in ["SPRINT"]: norm_session = "Sprint"
        elif session.upper() in ["FP1", "1"] and "Practice" not in session: norm_session = "Free Practice 1"
        elif session.upper() in ["FP2", "2"] and "Practice" not in session: norm_session = "Free Practice 2"
        elif session.upper() in ["FP3", "3"] and "Practice" not in session: norm_session = "Free Practice 3"
        
        if year not in options: options[year] = {}
        if event_name not in options[year]: options[year][event_name] = []
        if norm_session not in options[year][event_name]: 
            options[year][event_name].append(norm_session)
            
    if not options:
        options = {
            "2024": {
                "Bahrain Grand Prix": ["Free Practice 1", "Free Practice 2", "Free Practice 3", "Qualifying", "Sprint", "Race"]
            }
        }
    return options


@app.get("/api/telemetry")
def get_telemetry(
    year: int = Query(...),
    event_name: str = Query(...),
    session_type: str = Query(...),
    driver: str = Query(...)
):
    try:
        df = _load_session_df(year, event_name, session_type)
        driver_col = 'Driver' if 'Driver' in df.columns else df.columns[0]
        driver_df = df[df[driver_col].astype(str).str.upper() == driver.upper()]

        if len(driver_df) == 0:
            return {"error": f"找不到車手 {driver}"}

        team_col = 'Team' if 'Team' in df.columns else 'team'
        team_name = str(driver_df[team_col].iloc[0]) if team_col in df.columns else "Unknown"

        return {
            "Driver": str(driver).upper(),
            "Team": team_name,
            "Distance": driver_df['Distance'].tolist() if 'Distance' in driver_df.columns else [],
            "Speed": driver_df['Speed'].tolist() if 'Speed' in driver_df.columns else [],
            "Throttle": driver_df['Throttle'].tolist() if 'Throttle' in driver_df.columns else [],
            "Brake": driver_df['Brake'].astype(int).tolist() if 'Brake' in driver_df.columns else [],
            "RPM": driver_df['RPM'].tolist() if 'RPM' in driver_df.columns else [],
            "nGear": driver_df['nGear'].astype(int).tolist() if 'nGear' in driver_df.columns else [],
            "DRS": driver_df['DRS'].tolist() if 'DRS' in driver_df.columns else [0]*len(driver_df),
            "X": driver_df['X'].tolist() if 'X' in driver_df.columns else [],
            "Y": driver_df['Y'].tolist() if 'Y' in driver_df.columns else [],
            "Sector": driver_df['Sector'].astype(int).tolist() if 'Sector' in driver_df.columns else [1]*len(driver_df)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ai_analysis")
def ai_analysis(
    year: int = Query(...),
    event_name: str = Query(...),
    session_type: str = Query(...),
    driver1: str = Query(...),
    driver2: str = Query(...)
):
    try:
        df = _load_session_df(year, event_name, session_type)
        if df.empty:
            return {"error": "找不到指定 session 的資料"}

        driver_col = 'Driver' if 'Driver' in df.columns else df.columns[0]
        driver1_df = df[df[driver_col].astype(str).str.upper() == driver1.upper()]
        driver2_df = df[df[driver_col].astype(str).str.upper() == driver2.upper()]

        if len(driver1_df) == 0 or len(driver2_df) == 0:
            return {"error": "找不到指定車手資料，請確認 driver 名稱與 session 是否一致"}

        def summarize(target_df):
            speed = target_df['Speed'].astype(float) if 'Speed' in target_df.columns else pd.Series([0.0] * len(target_df))
            throttle = target_df['Throttle'].astype(float) if 'Throttle' in target_df.columns else pd.Series([0.0] * len(target_df))
            brake = target_df['Brake'].astype(float) if 'Brake' in target_df.columns else pd.Series([0.0] * len(target_df))
            rpm = target_df['RPM'].astype(float) if 'RPM' in target_df.columns else pd.Series([0.0] * len(target_df))
            sector = target_df['Sector'].astype(int) if 'Sector' in target_df.columns else pd.Series([1] * len(target_df))

            return {
                "avg_speed": round(float(speed.mean()), 2),
                "top_speed": round(float(speed.max()), 2),
                "avg_throttle": round(float(throttle.mean()), 2),
                "avg_brake": round(float(brake.mean()), 2),
                "avg_rpm": round(float(rpm.mean()), 2),
                "dominant_sector": int(sector.mode().iloc[0]) if not sector.mode().empty else 1
            }

        stats1 = summarize(driver1_df)
        stats2 = summarize(driver2_df)

        winner = driver1 if stats1['avg_speed'] >= stats2['avg_speed'] else driver2
        leader_text = (
            f"{winner} 在平均速度上稍占優勢"
            if abs(stats1['avg_speed'] - stats2['avg_speed']) > 2
            else "兩位車手在平均速度上相當接近"
        )

        analysis = (
            f"AI 賽道戰報：在 {year} {event_name} ({session_type}) 中，"
            f"{driver1} 與 {driver2} 的表現比較如下。"
            f"{driver1} 平均速度 {stats1['avg_speed']} km/h，最高速度 {stats1['top_speed']} km/h，"
            f"平均油門 {stats1['avg_throttle']}、平均剎車 {stats1['avg_brake']}、平均轉速 {stats1['avg_rpm']}。"
            f"{driver2} 平均速度 {stats2['avg_speed']} km/h，最高速度 {stats2['top_speed']} km/h，"
            f"平均油門 {stats2['avg_throttle']}、平均剎車 {stats2['avg_brake']}、平均轉速 {stats2['avg_rpm']}。"
            f"{leader_text}，並且 {driver1} 的主要節奏集中在 Sector {stats1['dominant_sector']}，"
            f"而 {driver2} 則以 Sector {stats2['dominant_sector']} 為主。"
        )

        return {
            "analysis": analysis,
            "driver1": {"name": driver1, "stats": stats1},
            "driver2": {"name": driver2, "stats": stats2},
            "winner": winner
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port)