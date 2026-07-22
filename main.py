import os
import pandas as pd
import numpy as np
from functools import lru_cache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download

try:
    import fastf1
except ImportError:
    fastf1 = None

app = FastAPI()

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

# 官方週末排序權重
SESSION_ORDER = [
    "Free Practice 1",
    "Free Practice 2",
    "Free Practice 3",
    "Sprint Shootout",
    "Sprint",
    "Qualifying",
    "Race",
]

# 🌟 雙向對應字典：精準處理前後端縮寫與完整名稱
SESSION_NAME_MAP = {
    "Q": "Qualifying", "Qualifying": "Qualifying",
    "R": "Race", "Race": "Race",
    "S": "Sprint", "Sprint": "Sprint",
    "SQ": "Sprint Shootout", "Sprint Shootout": "Sprint Shootout", "Sprint_Shootout": "Sprint Shootout",
    "FP1": "Free Practice 1", "Free Practice 1": "Free Practice 1", "Free_Practice_1": "Free Practice 1",
    "FP2": "Free Practice 2", "Free Practice 2": "Free Practice 2", "Free_Practice_2": "Free Practice 2",
    "FP3": "Free Practice 3", "Free Practice 3": "Free Practice 3", "Free_Practice_3": "Free Practice 3",
}

REVERSE_SESSION_MAP = {
    "Free Practice 1": "FP1",
    "Free Practice 2": "FP2",
    "Free Practice 3": "FP3",
    "Sprint Shootout": "SQ",
    "Sprint": "S",
    "Qualifying": "Q",
    "Race": "R"
}

# ==========================================
# 核心資料處理模組 (Core Data Loader)
# ==========================================
def _safe_numeric_list(series):
    """將任何欄位安全轉成可供前端直接繪圖的數字 list"""
    if series is None:
        return []
    try:
        return pd.to_numeric(series, errors="coerce").fillna(0).astype(float).tolist()
    except Exception:
        return []


@lru_cache(maxsize=128)
def get_telemetry_data(year: str, event_name: str, session_type: str, driver: str):
    """使用 FastF1 結合本地快取，並具備完整欄位防呆機制"""
    try:
        if fastf1 is None:
            return {"error": "fastf1 is not installed in this environment"}

        DRIVER_MAP = {
            "Max Verstappen": "VER", "Sergio Perez": "PER",
            "Lewis Hamilton": "HAM", "George Russell": "RUS",
            "Charles Leclerc": "LEC", "Carlos Sainz": "SAI",
            "Lando Norris": "NOR", "Oscar Piastri": "PIA",
            "Fernando Alonso": "ALO", "Lance Stroll": "STR",
            "Pierre Gasly": "GAS", "Esteban Ocon": "OCO",
            "Alexander Albon": "ALB", "Logan Sargeant": "SAR",
            "Yuki Tsunoda": "TSU", "Daniel Ricciardo": "RIC",
            "Valtteri Bottas": "BOT", "Zhou Guanyu": "ZHO",
            "Kevin Magnussen": "MAG", "Nico Hulkenberg": "HUL",
            "Sebastian Vettel": "VET", "Kimi Raikkonen": "RAI",
            "Mick Schumacher": "MSC", "Nicholas Latifi": "LAT",
            "Nikita Mazepin": "MAZ", "Antonio Giovinazzi": "GIO",
            "Daniil Kvyat": "KVY", "Romain Grosjean": "GRO",
            "Robert Kubica": "KUB", "Marcus Ericsson": "ERI"
        }
        driver_code = DRIVER_MAP.get(driver, driver[:3].upper())

        session_map_short = {
            "Free Practice 1": "FP1", "Free Practice 2": "FP2", "Free Practice 3": "FP3",
            "Sprint Shootout": "SQ", "Sprint": "S", "Qualifying": "Q", "Race": "R"
        }
        short_session = session_map_short.get(session_type, session_type)

        session = fastf1.get_session(int(year), event_name, short_session)
        session.load(telemetry=True, weather=False, messages=False)

        laps = session.laps.pick_driver(driver_code)
        if laps.empty:
            laps = session.laps.pick_driver(driver)
        if laps.empty:
            return {"error": f"Driver {driver_code} not found in this session"}

        fastest_lap = laps.pick_fastest()
        if fastest_lap is None or pd.isna(fastest_lap['LapTime']):
            fastest_lap = laps.iloc[0]

        tel = fastest_lap.get_telemetry()
        if tel is None or tel.empty:
            return {"error": "No telemetry telemetry found for the selected lap"}

        if 'Distance' in tel.columns:
            tel = tel.sort_values('Distance', kind='mergesort').reset_index(drop=True)

        return {
            "Driver": driver,
            "Team": str(fastest_lap.get('Team', 'Unknown')),
            "Distance": _safe_numeric_list(tel['Distance']) if 'Distance' in tel.columns else [],
            "Speed": _safe_numeric_list(tel['Speed']) if 'Speed' in tel.columns else [],
            "Throttle": _safe_numeric_list(tel['Throttle']) if 'Throttle' in tel.columns else [],
            "Brake": _safe_numeric_list(tel['Brake']) if 'Brake' in tel.columns else [],
            "RPM": _safe_numeric_list(tel['RPM']) if 'RPM' in tel.columns else [],
            "nGear": _safe_numeric_list(tel['nGear']) if 'nGear' in tel.columns else [],
            "DRS": _safe_numeric_list(tel['DRS']) if 'DRS' in tel.columns else [],
            "X": _safe_numeric_list(tel['X']) if 'X' in tel.columns else [],
            "Y": _safe_numeric_list(tel['Y']) if 'Y' in tel.columns else [],
            **({"Sector": _safe_numeric_list(tel['Sector'])} if 'Sector' in tel.columns else {})
        }
    except Exception as e:
        print(f"Error loading telemetry data: {e}")
        return {"error": str(e)}

# ==========================================
# API 端點 (API Endpoints)
# ==========================================

@app.get("/api/options")
def get_options():
    """取得所有可用的年份、賽事與階段選單，並轉換為前端相容格式"""
    try:
        index_file_path = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename="index.parquet")
        df_files = pd.read_parquet(index_file_path)
        
        event_col = "event_name" if "event_name" in df_files.columns else "event"
        session_col = "session_type" if "session_type" in df_files.columns else "session"
        
        menu_options = {}
        for year in sorted(df_files["year"].unique(), reverse=True):
            year_str = str(year)
            menu_options[year_str] = {}
            year_df = df_files[df_files["year"] == year]
            
            for event in sorted(year_df[event_col].unique()):
                raw_sessions = year_df[year_df[event_col] == event][session_col].drop_duplicates().tolist()
                
                # 轉成前端偏好的縮寫格式 (FP1, FP2, Q, R...)
                short_sessions = [REVERSE_SESSION_MAP.get(s, s) for s in raw_sessions]
                
                # 依照賽事週末順序排序
                short_sessions.sort(
                    key=lambda x: SESSION_ORDER.index(SESSION_NAME_MAP.get(x, x)) 
                    if SESSION_NAME_MAP.get(x, x) in SESSION_ORDER else 99
                )
                menu_options[year_str][event] = short_sessions
                
        return menu_options
    except Exception as e:
        print(f"讀取 Index 失敗: {e}")
        return {
            "2024": {
                "Bahrain Grand Prix": ["FP1", "FP2", "FP3", "Q", "R"]
            }
        }

@app.get("/api/telemetry")
async def get_telemetry(year: str, event_name: str, session_type: str, driver: str):
    """提供給前端圖表渲染用的原始遙測資料"""
    return get_telemetry_data(year, event_name, session_type, driver)

@app.get("/api/ai_analysis")
async def get_ai_analysis(year: str, event_name: str, session_type: str, driver1: str, driver2: str):
    """
    🏎️ AI Race Engineer Core Module
    """
    try:
        d1_data = get_telemetry_data(year, event_name, session_type, driver1)
        d2_data = get_telemetry_data(year, event_name, session_type, driver2)
        
        if "error" in d1_data or "error" in d2_data:
            return {"insights": ["⚠️ Insufficient telemetry data to generate AI insights."]}

        speed1, speed2 = np.array(d1_data["Speed"]), np.array(d2_data["Speed"])
        throttle1, throttle2 = np.array(d1_data["Throttle"]), np.array(d2_data["Throttle"])
        brake1, brake2 = np.array(d1_data["Brake"]), np.array(d2_data["Brake"])
        
        max_speed1, max_speed2 = np.max(speed1), np.max(speed2)
        avg_speed1, avg_speed2 = np.mean(speed1), np.mean(speed2)
        full_throttle1 = np.sum(throttle1 >= 99) / len(throttle1) * 100
        full_throttle2 = np.sum(throttle2 >= 99) / len(throttle2) * 100
        
        insights = []
        
        coasting1 = np.sum((throttle1 < 5) & (brake1 < 5)) / len(throttle1) * 100
        coasting2 = np.sum((throttle2 < 5) & (brake2 < 5)) / len(throttle2) * 100
        
        if coasting1 > coasting2 + 1:
            insights.append(f"🔋 {driver1} spends more time coasting ({coasting1:.1f}% vs {coasting2:.1f}%), indicating potential fuel saving (lift-and-coast) or instability on corner entry.")
        elif coasting2 > coasting1 + 1:
            insights.append(f"🔋 {driver2} exhibits a higher lift-and-coast ratio ({coasting2:.1f}% vs {coasting1:.1f}%), losing momentum before initial brake application.")
            
        brake_pct1 = np.sum(brake1 > 0) / len(brake1) * 100
        brake_pct2 = np.sum(brake2 > 0) / len(brake2) * 100
        
        if brake_pct1 < brake_pct2 - 1 and avg_speed1 >= avg_speed2 - 0.5:
            insights.append(f"🛑 {driver1} is deeper and harder on the brakes. They achieve their deceleration phase in less time ({brake_pct1:.1f}% vs {brake_pct2:.1f}% of lap distance).")
        elif brake_pct2 < brake_pct1 - 1 and avg_speed2 >= avg_speed1 - 0.5:
            insights.append(f"🛑 {driver2} demonstrates superior braking efficiency, spending less total time on the brake pedal ({brake_pct2:.1f}% vs {brake_pct1:.1f}%) while maintaining pace.")
        
        if max_speed1 > max_speed2 + 2:
            insights.append(f"🚀 {driver1} holds a clear top speed advantage ({max_speed1:.1f} km/h vs {max_speed2:.1f} km/h), indicating a lower drag setup or later braking phases.")
        elif max_speed2 > max_speed1 + 2:
            insights.append(f"🚀 {driver2} dominates the straights with a top speed advantage of +{(max_speed2 - max_speed1):.1f} km/h.")
            
        if full_throttle1 > full_throttle2 + 2:
            insights.append(f"⏱️ {driver1} spends more time at wide-open throttle ({full_throttle1:.1f}% vs {full_throttle2:.1f}%), suggesting earlier and more aggressive throttle pickup on corner exits.")
        elif full_throttle2 > full_throttle1 + 2:
            insights.append(f"⏱️ {driver2} demonstrates better traction confidence, spending +{(full_throttle2 - full_throttle1):.1f}% more time at 100% throttle compared to {driver1}.")
            
        speed_diff = avg_speed1 - avg_speed2
        if speed_diff > 0.5:
            insights.append(f"🔥 {driver1} carries superior overall momentum, maintaining an average speed delta of +{speed_diff:.1f} km/h over the lap.")
        elif speed_diff < -0.5:
            insights.append(f"🔥 {driver2} exhibits better overall track flow, carrying an average speed advantage of +{abs(speed_diff):.1f} km/h.")
        
        low_speed_mask1 = speed1 < 150
        low_speed_mask2 = speed2 < 150
        if np.any(low_speed_mask1) and np.any(low_speed_mask2):
            avg_ls1 = np.mean(speed1[low_speed_mask1])
            avg_ls2 = np.mean(speed2[low_speed_mask2])
            if avg_ls1 > avg_ls2 + 1.5:
                insights.append(f"⚙️ {driver1} displays superior mechanical grip in low-speed zones (<150 km/h), averaging +{(avg_ls1 - avg_ls2):.1f} km/h over {driver2}.")
            elif avg_ls2 > avg_ls1 + 1.5:
                insights.append(f"⚙️ {driver2} finds better traction out of slow corners (<150 km/h), indicating a more compliant suspension setup or optimal tyre temperature.")

        high_speed_mask1 = speed1 > 250
        high_speed_mask2 = speed2 > 250
        if np.any(high_speed_mask1) and np.any(high_speed_mask2):
            avg_hs1 = np.mean(speed1[high_speed_mask1])
            avg_hs2 = np.mean(speed2[high_speed_mask2])
            if avg_hs1 > avg_hs2 + 1.5:
                insights.append(f"🌪️ {driver1} is visibly stronger in high-speed sections (>250 km/h), carrying +{(avg_hs1 - avg_hs2):.1f} km/h, demonstrating higher aerodynamic downforce and driver commitment.")
            elif avg_hs2 > avg_hs1 + 1.5:
                insights.append(f"🌪️ {driver2} carries significant momentum through high-speed aero zones (>250 km/h), maintaining a +{(avg_hs2 - avg_hs1):.1f} km/h advantage.")

        partial_throttle1 = np.sum((throttle1 > 10) & (throttle1 < 90)) / len(throttle1) * 100
        partial_throttle2 = np.sum((throttle2 > 10) & (throttle2 < 90)) / len(throttle2) * 100
        
        if partial_throttle1 > partial_throttle2 + 2:
            insights.append(f"⚠️ {driver1} makes more mid-corner throttle corrections ({partial_throttle1:.1f}% partial throttle), hinting at rear-end instability or struggling with traction limit.")
        elif partial_throttle2 > partial_throttle1 + 2:
            insights.append(f"⚠️ {driver2} applies the throttle more tentatively ({partial_throttle2:.1f}% partial throttle phase), spending less time at full commitment compared to {driver1}.")

        if len(insights) == 0:
            insights.append(f"⚖️ Telemetry profiles for {driver1} and {driver2} are nearly identical. Lap time deltas are likely down to micro-corrections in steering or subtle tyre degradation.")

        return {"insights": insights}

    except Exception as e:
        return {"insights": [f"⚠️ AI Computation Error: {str(e)}"]}