from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from huggingface_hub import list_repo_files, hf_hub_download

app = FastAPI(title="F1 Telemetry Studio PRO API (Bulletproof Engine)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

# 加入全域快取，避免 Hugging Face API 頻繁請求導致被 Ban
_CACHE_MAPPING = None
_CACHE_OPTIONS = None

def _get_file_mapping():
    global _CACHE_MAPPING, _CACHE_OPTIONS
    if _CACHE_MAPPING is not None and _CACHE_OPTIONS is not None:
        return _CACHE_MAPPING, _CACHE_OPTIONS
        
    mapping = {}
    options = {}
    try:
        files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        for f in files:
            if not f.endswith(".parquet"): continue
            name_part = f[:-8] 
            parts = name_part.split("_")
            if len(parts) < 3: continue
            
            year = parts[0]
            rest = parts[1:]
            
            gp_index = -1
            for i in range(len(rest) - 1):
                if rest[i].lower() == "grand" and rest[i+1].lower() == "prix":
                    gp_index = i + 1
                    break
            
            if gp_index != -1:
                event_parts = rest[:gp_index+1]
                session_parts = rest[gp_index+1:]
                event_name = " ".join(event_parts).title()
            else:
                event_parts = []
                session_parts = []
                for i, p in enumerate(rest):
                    if p.upper() in ["FP1", "FP2", "FP3", "P1", "P2", "P3", "Q", "QUALIFYING", "R", "RACE", "SPRINT", "SQ"]:
                        event_parts = rest[:i]
                        session_parts = rest[i:]
                        break
                if not event_parts:
                    event_parts = rest[:-1]
                    session_parts = [rest[-1]] if rest else []
                event_name = " ".join(event_parts).title()
                
            session_str = "".join(session_parts).upper()
            if any(k in session_str for k in ["FP1", "P1", "FREE1", "PRACTICE1"]) or session_parts == ["1"]:
                session = "Free Practice 1"
            elif any(k in session_str for k in ["FP2", "P2", "FREE2", "PRACTICE2"]) or session_parts == ["2"]:
                session = "Free Practice 2"
            elif any(k in session_str for k in ["FP3", "P3", "FREE3", "PRACTICE3"]) or session_parts == ["3"]:
                session = "Free Practice 3"
            elif "SPRINT" in session_str and ("QUALIFYING" in session_str or "Q" in session_str or "SQ" in session_str):
                session = "Sprint Qualifying"
            elif "SPRINT" in session_str:
                session = "Sprint"
            elif "QUALIFYING" in session_str or session_str == "Q":
                session = "Qualifying"
            elif "RACE" in session_str or session_str == "R" or not session_parts:
                session = "Race"
            else:
                session = " ".join(session_parts).title()
                if not session: session = "Race"
                
            mapping[(str(year), event_name, session)] = f
            
            if year not in options: options[year] = {}
            if event_name not in options[year]: options[year][event_name] = []
            if session not in options[year][event_name]: 
                options[year][event_name].append(session)
    except Exception as e:
        print("檔案掃描錯誤:", e)
        
    _CACHE_MAPPING = mapping
    _CACHE_OPTIONS = options
    return mapping, options


def _load_session_df(year: int, event_name: str, session_type: str):
    mapping, _ = _get_file_mapping()
    filename = mapping.get((str(year), event_name, session_type))
            
    if not filename:
        raise FileNotFoundError(f"找不到對應資料檔案: {year} {event_name} {session_type}")
        
    try:
        local_path = hf_hub_download(repo_id=REPO_ID, filename=filename, repo_type="dataset")
        return pd.read_parquet(local_path)
    except Exception as e:
        raise FileNotFoundError(f"無法從 Hugging Face 下載 {filename}: {e}")

# 新增的智慧車手過濾器：解決全名(Max Verstappen)與縮寫(VER)無法匹配的問題
def _filter_driver_data(df, driver_name: str):
    possible_cols = ['Driver', 'Abbreviation', 'DriverNumber', 'name']
    driver_col = next((col for col in possible_cols if col in df.columns), df.columns[0])
    
    abbr_map = {
        "MAX VERSTAPPEN": "VER", "CHARLES LECLERC": "LEC", "SERGIO PEREZ": "PER",
        "CARLOS SAINZ": "SAI", "LANDO NORRIS": "NOR", "OSCAR PIASTRI": "PIA",
        "GEORGE RUSSELL": "RUS", "LEWIS HAMILTON": "HAM", "FERNANDO ALONSO": "ALO",
        "LANCE STROLL": "STR", "YUKI TSUNODA": "TSU", "DANIEL RICCIARDO": "RIC",
        "NICO HULKENBERG": "HUL", "KEVIN MAGNUSSEN": "MAG", "ALEXANDER ALBON": "ALB",
        "LOGAN SARGEANT": "SAR", "ESTEBAN OCON": "OCO", "PIERRE GASLY": "GAS",
        "VALTTERI BOTTAS": "BOT", "ZHOU GUANYU": "ZHO", "GUANYU ZHOU": "ZHO",
        "LIAM LAWSON": "LAW", "OLIVER BEARMAN": "BEA", "FRANCO COLAPINTO": "COL"
    }
    
    driver_upper = driver_name.upper()
    abbr = abbr_map.get(driver_upper, driver_name.split()[-1][:3].upper())
    last_name = driver_name.split()[-1].upper()
    
    driver_series = df[driver_col].astype(str).str.upper()
    # 只要符合全名、縮寫，或包含姓氏，全部都能正確抓到
    mask = (driver_series == driver_upper) | (driver_series == abbr) | (driver_series.str.contains(last_name))
    return df[mask]


@app.get("/api/options")
def get_options():
    _, options = _get_file_mapping()
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
        
        # 使用智慧過濾器取代原本必定失敗的嚴格字串比對
        driver_df = _filter_driver_data(df, driver)

        if len(driver_df) == 0:
            return {"error": f"找到賽事資料，但裡面沒有車手 {driver} 的數據。"}

        team_col = 'Team' if 'Team' in df.columns else 'team'
        team_name = str(driver_df[team_col].iloc[0]) if team_col in driver_df.columns else "Unknown"

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

        # 使用智慧過濾器
        driver1_df = _filter_driver_data(df, driver1)
        driver2_df = _filter_driver_data(df, driver2)

        if len(driver1_df) == 0 or len(driver2_df) == 0:
            return {"error": "找不到指定車手資料，請確認車手是否參與了該場 Session"}

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