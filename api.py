from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import unicodedata
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
_CACHE_MAPPING = None
_CACHE_OPTIONS = None

def _normalize_str(s: str) -> str:
    """強制消除重音符號並轉為小寫"""
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower()

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
        try:
            files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
            norm_event = _normalize_str(event_name).replace("grand", "").replace("prix", "").strip()
            event_keyword = norm_event.split()[0] if norm_event else ""
            
            for f in files:
                norm_f = _normalize_str(f)
                if str(year) in norm_f and event_keyword in norm_f:
                    clean_session = session_type.replace(" ", "").lower()
                    if clean_session in norm_f.replace("_", ""):
                        filename = f
                        break
            if not filename:
                for f in files:
                    norm_f = _normalize_str(f)
                    if str(year) in norm_f and event_keyword in norm_f:
                        filename = f
                        break
        except Exception:
            pass

    if not filename:
        raise FileNotFoundError(f"找不到對應資料檔案: {year} {event_name} {session_type}")
        
    try:
        local_path = hf_hub_download(repo_id=REPO_ID, filename=filename, repo_type="dataset")
        df = pd.read_parquet(local_path)
        return df.fillna(0)
    except Exception as e:
        raise FileNotFoundError(f"無法從 Hugging Face 下載 {filename}: {e}")

def _filter_driver_data(df, driver_name: str):
    driver_col = None
    for col in ['Driver', 'Abbreviation', 'DriverNumber', 'name', 'Car']:
        if col in df.columns:
            driver_col = col
            break
            
    if not driver_col:
        driver_col = df.columns[0]
    
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
    mask = (driver_series == driver_upper) | (driver_series == abbr) | (driver_series.str.contains(last_name))
    filtered_df = df[mask]
    return filtered_df

def _get_col(df, possible_names):
    """無差別搜尋欄位名稱（無視大小寫）"""
    for col in df.columns:
        if col.upper() in [n.upper() for n in possible_names]:
            return col
    return None

@app.get("/api/options")
def get_options():
    _, options = _get_file_mapping()
    if not options:
        options = {"2024": {"Bahrain Grand Prix": ["Free Practice 1", "Race"]}}
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
        driver_df = _filter_driver_data(df, driver)

        if len(driver_df) == 0:
            return {"error": f"找不到車手 {driver} 的數據。該資料集包含的欄位有：{list(df.columns)}"}

        # 動態抓取欄位名稱，無視大小寫
        team_col = _get_col(driver_df, ['Team'])
        dist_col = _get_col(driver_df, ['Distance'])
        speed_col = _get_col(driver_df, ['Speed'])
        throttle_col = _get_col(driver_df, ['Throttle'])
        brake_col = _get_col(driver_df, ['Brake'])
        rpm_col = _get_col(driver_df, ['RPM'])
        gear_col = _get_col(driver_df, ['nGear', 'Gear'])
        drs_col = _get_col(driver_df, ['DRS'])
        x_col = _get_col(driver_df, ['X'])
        y_col = _get_col(driver_df, ['Y'])
        sector_col = _get_col(driver_df, ['Sector'])

        # 防呆檢查：如果連 Speed 欄位都找不到，直接報錯，讓你知道是不是上傳錯了！
        if not speed_col:
            return {"error": f"這份檔案不是遙測資料！它包含的欄位有: {list(df.columns)}。請確認上傳到 Hugging Face 的是 telemetry 檔案，而不是 laps 檔案。"}

        team_name = str(driver_df[team_col].iloc[0]) if team_col else "Unknown"

        return {
            "Driver": str(driver).upper(),
            "Team": team_name,
            "Distance": driver_df[dist_col].tolist() if dist_col else [],
            "Speed": driver_df[speed_col].tolist() if speed_col else [],
            "Throttle": driver_df[throttle_col].tolist() if throttle_col else [],
            "Brake": driver_df[brake_col].astype(int).tolist() if brake_col else [],
            "RPM": driver_df[rpm_col].tolist() if rpm_col else [],
            "nGear": driver_df[gear_col].astype(int).tolist() if gear_col else [],
            "DRS": driver_df[drs_col].tolist() if drs_col else [0]*len(driver_df),
            "X": driver_df[x_col].tolist() if x_col else [],
            "Y": driver_df[y_col].tolist() if y_col else [],
            "Sector": driver_df[sector_col].astype(int).tolist() if sector_col else [1]*len(driver_df)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ai_analysis")
def ai_analysis(year: int, event_name: str, session_type: str, driver1: str, driver2: str):
    return {"error": "暫時停用以專注修復圖表"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port)