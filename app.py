import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from huggingface_hub import list_repo_files

# =========================================================
# CONFIG & 完美還原 F1 官方視覺與無邊框 CSS
# =========================================================
st.set_page_config(
    page_title="F1 Telemetry Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

custom_css = """
<style>
/* 隱藏預設元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 強制滿版、無邊框、黑色背景 */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
    background-color: #000000 !important;
}
.stApp {
    background-color: #000000 !important;
    color: #ffffff !important;
}

/* 頂部 F1 紅色警示邊條 */
header::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 4px;
    background-color: #e10600;
    z-index: 99999;
}

/* 隱藏標題連結圖標 */
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
    display: none !important;
}

/* 無邊框下劃線選單外觀 */
div[data-testid="stSelectbox"] > div {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    padding-left: 0px !important;
}
div[data-testid="stSelectbox"] > div:hover {
    border-bottom: 1px solid rgba(255, 255, 255, 0.4) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
    color: #FFFFFF !important;
    font-size: 14px !important;
}
div[data-testid="stSelectbox"] label p {
    color: #6b7280 !important;
    font-size: 10px !important;
    letter-spacing: 0.2em !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =========================================================
# F1 官方頂部列 (Logo + 導覽連結 + Sign In / Subscribe)
# =========================================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; background-color: #15151e; padding: 12px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); margin: -2rem -2rem 1.5rem -2rem;">
    <div style="display: flex; align-items: center; gap: 35px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" alt="F1 Logo" style="height: 24px; width: auto;" />
        <div style="display: flex; gap: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #fff; letter-spacing: 0.1em;">
            <a href="https://www.formula1.com/en/racing/2024.html" target="_blank" style="color: white; text-decoration: none;">Schedule</a>
            <a href="https://www.formula1.com/en/results.html" target="_blank" style="color: white; text-decoration: none;">Results</a>
            <a href="https://www.formula1.com/en/results.html/team.html" target="_blank" style="color: white; text-decoration: none;">Standings</a>
            <a href="https://www.formula1.com/en/drivers.html" target="_blank" style="color: white; text-decoration: none;">Drivers</a>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
        <a href="https://account.formula1.com" target="_blank" style="color: #d1d5db; text-decoration: none;">Sign In</a>
        <a href="https://f1tv.formula1.com/" target="_blank" style="background-color: #e10600; color: white; padding: 6px 14px; border-radius: 2px; text-decoration: none;">Subscribe</a>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 標題與即時同步燈號列
# =========================================================
col_title, col_live = st.columns([4, 1])
with col_title:
    st.markdown('<h1 style="font-size: 16px; font-weight: 300; letter-spacing: 0.2em; margin: 0;">TELEMETRY STUDIO <span style="background-color: #e10600; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 10px;">PRO v2</span></h1>', unsafe_allow_html=True)
with col_live:
    st.markdown('<div style="text-align: right; font-size: 10px; font-family: monospace; color: #9ca3af; padding-top: 3px;">LIVE SYNC <span style="display: inline-block; width: 8px; height: 8px; background-color: #e10600; border-radius: 50%; margin-left: 5px;"></span></div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 12px 0;'>", unsafe_allow_html=True)

# =========================================================
# DATA & FILE INDEX
# =========================================================
TEAM_COLORS = {
    "red bull": "#3671C6", "ferrari": "#F91536", "mercedes": "#6CD3BF", "mclaren": "#F58020",
    "aston martin": "#229971", "alpine": '#2293D1', "williams": "#37BEDD", "alphatauri": "#5E8FAA",
    "alfa romeo": "#C92D4B", "haas": "#B6BABD", "rb": "#6692FF", "racing bulls": "#6692FF",
    "sauber": "#52E252", "kick sauber": "#52E252"
}

SESSION_NAMES = {
    "R": "Race", "Q": "Qualifying", "S": "Sprint", "SQ": "Sprint Shootout",
    "FP1": "Free Practice 1", "FP2": "Free Practice 2", "FP3": "Free Practice 3"
}

def get_team_color(team: str) -> str:
    team = str(team).lower()
    return next((v for k, v in TEAM_COLORS.items() if k in team), "#FFFFFF")

@st.cache_data(ttl=3600, show_spinner=False)
def get_file_index() -> pd.DataFrame:
    try:
        files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")
    except:
        return pd.DataFrame(columns=["year", "event", "session", "filename"])
    rows = []
    for f in files:
        if not f.endswith(".parquet"): continue
        parts = f[:-8].split("_")
        if len(parts) < 3: continue
        rows.append({"year": int(parts[0]), "event": "_".join(parts[1:-1]), "session": parts[-1], "filename": f})
    return pd.DataFrame(rows)

df_files = get_file_index()

@st.cache_data(show_spinner=False)
def load_telemetry(filename: str) -> pd.DataFrame:
    path = f"hf://datasets/{REPO_ID}/{filename}"
    try:
        df_loaded = pd.read_parquet(path)
        # 強制將所有欄位名稱標準化為首字母大寫，確保 Distance、Speed 等欄位100%抓得到
        df_loaded.columns = [
            col.strip().capitalize() if col.strip().lower() in ['distance', 'speed', 'throttle', 'brake', 'rpm', 'driver', 'team', 'x', 'y', 'drs', 'sector'] else col 
            for col in df_loaded.columns
        ]
        return df_loaded
    except:
        return pd.DataFrame()

# =========================================================
# 三欄式排版：左側選單 | 中間遙測圖表 | 右側賽道圖
# =========================================================
sidebar_col, main_col, map_col = st.columns([1, 2.3, 1.7], gap="medium")

with sidebar_col:
    if not df_files.empty:
        years = sorted(df_files.year.unique(), reverse=True)
        year = st.selectbox("Year", years, index=0 if 2024 in years else 0)

        events = sorted(df_files[df_files.year == year].event.unique())
        event = st.selectbox("Grand Prix", events, index=0)

        sessions = df_files[(df_files.year == year) & (df_files.event == event)].session.unique()
        session = st.selectbox("Session", sessions, format_func=lambda x: SESSION_NAMES.get(x, x), index=0)

        file_row = df_files[(df_files.year == year) & (df_files.event == event) & (df_files.session == session)]
        filename = file_row.iloc[0].filename if not file_row.empty else None
        
        df = load_telemetry(filename) if filename else pd.DataFrame()
        drivers = sorted(df.Driver.unique()) if "Driver" in df.columns else []

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
        driver1 = st.selectbox("Driver 1", drivers, index=drivers.index("VER") if "VER" in drivers else (0 if drivers else 0))
        driver2 = st.selectbox("Driver 2", drivers, index=drivers.index("LEC") if "LEC" in drivers else (1 if len(drivers) > 1 else 0))
    else:
        st.selectbox("Year", [2024])
        st.selectbox("Grand Prix", ["Bahrain Grand Prix"])
        st.selectbox("Session", ["Qualifying"])
        driver1, driver2 = "VER", "LEC"
        df = pd.DataFrame()

with main_col:
    if df.empty or "Driver" not in df.columns:
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 500px; color: #4b5563; font-size: 13px; font-weight: 500; letter-spacing: 0.2em;">
            NO DATA AVAILABLE
        </div>
        """, unsafe_allow_html=True)
    else:
        selected = [driver1] if driver1 == driver2 else [driver1, driver2]
        driver_groups = {k: v for k, v in df.groupby("Driver")}

        fig = make_subplots(
            rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
            subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake", "RPM")
        )
        metrics = [("Speed", 1, "solid"), ("Throttle", 2, "solid"), ("Brake", 3, "dot"), ("RPM", 4, "solid")]

        for drv in selected:
            d = driver_groups.get(drv)
            if d is None: continue
            color = get_team_color(d.Team.iloc[0] if "Team" in d.columns else "")
            for metric, row, dash in metrics:
                if metric not in d.columns: continue
                y = d[metric].astype("int8") if metric == "Brake" else d[metric]
                fig.add_trace(go.Scattergl(
                    x=d["Distance"], y=y, mode="lines",
                    name=drv if row == 1 else None, showlegend=row == 1,
                    line=dict(color=color, width=1.5, dash=dash),
                    hovertemplate=f"{drv} : %{{y}}<extra></extra>"
                ), row=row, col=1)

        fig.update_layout(
            height=720, margin=dict(l=35, r=10, t=10, b=10),
            paper_bgcolor='transparent', plot_bgcolor='transparent',
            showlegend=False, hovermode='x unified'
        )

        for i in range(1, 5):
            fig.update_xaxes(showgrid=True, gridcolor='#121212', row=i, col=1, tickfont=dict(size=9, color='#666'))
            fig.update_yaxes(showgrid=True, gridcolor='#121212', row=i, col=1, tickfont=dict(size=9, color='#666'))

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with map_col:
    if not df.empty and {"X", "Y"}.issubset(df.columns):
        st.markdown('<p style="font-size: 10px; color: #6b7280; letter-spacing: 0.15em; font-weight: 600; margin-bottom: 5px;">TRACK MAP (SECTOR 1 / 2 / 3)</p>', unsafe_allow_html=True)
        track = df[df.Driver == driver1] if "Driver" in df.columns else df
        
        if not track.empty:
            max_d = track["Distance"].max() if "Distance" in track.columns else 1
            s1_lim, s2_lim = max_d * 0.32, max_d * 0.70
            
            s1_x, s1_y, s2_x, s2_y, s3_x, s3_y = [], [], [], [], [], []
            for i in range(len(track)):
                d = track["Distance"].iloc[i]
                px, py = track["X"].iloc[i], track["Y"].iloc[i]
                if d <= s1_lim: s1_x.append(px); s1_y.append(py)
                elif d <= s2_lim: s2_x.append(px); s2_y.append(py)
                else: s3_x.append(px); s3_y.append(py)

            map_fig = go.Figure()
            map_fig.add_trace(go.Scattergl(x=s1_x, y=s1_y, mode='lines', line=dict(color='#E10600', width=4), hoverinfo='skip'))
            map_fig.add_trace(go.Scattergl(x=s2_x, y=s2_y, mode='lines', line=dict(color='#00A0E9', width=4), hoverinfo='skip'))
            map_fig.add_trace(go.Scattergl(x=s3_x, y=s3_y, mode='lines', line=dict(color='#FFD500', width=4), hoverinfo='skip'))

            map_fig.update_layout(
                height=520, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='transparent', plot_bgcolor='transparent',
                xaxis=dict(visible=False, scaleanchor='y', scaleratio=1, fixedrange=True),
                yaxis=dict(visible=False, fixedrange=True), showlegend=False
            )
            st.plotly_chart(map_fig, use_container_width=True, config={'displayModeBar': False})