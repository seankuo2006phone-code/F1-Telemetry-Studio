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


def _load_session_df(year: int, event_name: str, session_type: str):
    raw_event = event_name.replace(" ", "_")
    filename = f"{year}_{raw_event}_{session_type}.parquet"
    local_path = os.path.join(DATASET_DIR, filename)

    if not os.path.exists(local_path):
        hf_url = f"hf://datasets/{REPO_ID}/{filename}"
        try:
            df_temp = pd.read_parquet(hf_url)
            df_temp.to_parquet(local_path)
        except Exception:
            raise FileNotFoundError(f"找不到資料: {filename}")

    return pd.read_parquet(local_path)


@app.get("/api/options")
def get_options():
    options = {}
    try:
        if os.path.exists(DATASET_DIR):
            for f in os.listdir(DATASET_DIR):
                if not f.endswith(".parquet"): continue
                name_part = f[:-8] # 移除 .parquet
                parts = name_part.split("_")
                if len(parts) < 3: continue
                
                year = str(parts[0])
                event_name = "_".join(parts[1:-1]).replace("_", " ").title()
                session = parts[-1]
                
                if year not in options: options[year] = {}
                if event_name not in options[year]: options[year][event_name] = []
                if session not in options[year][event_name]: 
                    options[year][event_name].append(session)
    except Exception as e:
        print("掃描本地快取錯誤:", e)

    # 保底機制：如果本機完全沒有掃描到檔案，提供預設選項讓前端正常運作
    if not options:
        options = {
            "2024": {
                "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"]
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