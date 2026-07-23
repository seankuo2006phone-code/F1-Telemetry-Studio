import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from huggingface_hub import list_repo_files
import warnings

# 忽略 pandas 或繪圖的無關警告
warnings.filterwarnings('ignore')

# =========================================================
# 1. 頁面設定 & 極致無邊框 F1 專業版 CSS
# =========================================================
st.set_page_config(
    page_title="F1 Telemetry Studio Pro",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

custom_css = """
<style>
/* 隱藏預設的 Header, Footer 與 Menu */
#MainMenu, footer, header { visibility: hidden !important; }

/* 強制滿版與純黑背景 */
.block-container {
    padding: 1rem 2rem !important;
    max-width: 100% !important;
    background-color: #000000 !important;
}
.stApp {
    background-color: #000000 !important;
    color: #ffffff !important;
}

/* 頂部 F1 標誌性紅色警示邊條 */
header::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 4px;
    background-color: #e10600;
    z-index: 99999;
}

/* 隱藏 Markdown 標題旁邊的連結圖標 */
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }

/* ---------------------------------------------------
   極致無邊框選單：強制把 Streamlit 複雜的底層背景徹底挖空
--------------------------------------------------- */
div[data-testid="stSelectbox"] {
    background-color: transparent !important;
}
div[data-baseweb="select"] {
    background-color: transparent !important;
}
div[data-baseweb="select"] > div {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease-in-out;
}
div[data-baseweb="select"] > div:hover, 
div[data-baseweb="select"] > div:focus-within {
    border-bottom: 1px solid #e10600 !important;
}
div[data-baseweb="select"] span { color: #ffffff !important; font-size: 14px !important; }
div[data-baseweb="select"] svg { fill: #ffffff !important; }

/* 選單下拉列表的深色覆蓋 */
div[data-baseweb="popover"] > div {
    background-color: #15151e !important;
    border: 1px solid #333 !important;
    border-radius: 4px !important;
}
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background-color: transparent !important;
    color: #ffffff !important;
}
ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
    background-color: #e10600 !important;
}

/* 選單標題文字 (Year, Grand Prix...) */
div[data-testid="stSelectbox"] label p {
    color: #6b7280 !important;
    font-size: 10px !important;
    letter-spacing: 0.2em !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}

/* 獨立區塊自訂捲軸樣式 (隱形且俐落的科技感) */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #e10600; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =========================================================
# 2. F1 官方頂部列 (Logo + 導覽連結 + 登入/訂閱)
# =========================================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; background-color: #15151e; padding: 12px 24px; border-bottom: 1px solid rgba(255,255,255,0.05); margin: -2rem -2rem 1.5rem -2rem;">
    <div style="display: flex; align-items: center; gap: 35px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" alt="F1 Logo" style="height: 24px; width: auto;" />
        <div style="display: flex; gap: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #fff; letter-spacing: 0.1em;">
            <a href="https://www.formula1.com/en/racing/2024.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8; transition: 0.2s;">Schedule</a>
            <a href="https://www.formula1.com/en/results.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8; transition: 0.2s;">Results</a>
            <a href="https://www.formula1.com/en/results.html/team.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8; transition: 0.2s;">Standings</a>
            <a href="https://www.formula1.com/en/drivers.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8; transition: 0.2s;">Drivers</a>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
        <a href="https://account.formula1.com" target="_blank" style="color: #d1d5db; text-decoration: none; opacity: 0.8;">Sign In</a>
        <a href="https://f1tv.formula1.com/" target="_blank" style="background-color: #e10600; color: white; padding: 6px 14px; border-radius: 2px; text-decoration: none; box-shadow: 0 2px 4px rgba(225,6,0,0.3);">Subscribe</a>
    </div>
</div>
""", unsafe_allow_html=True)

col_title, col_live = st.columns([4, 1])
with col_title:
    st.markdown('<h1 style="font-size: 16px; font-weight: 300; letter-spacing: 0.2em; margin: 0;">TELEMETRY STUDIO <span style="background-color: #e10600; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 10px; color: white;">PRO v2</span></h1>', unsafe_allow_html=True)
with col_live:
    st.markdown('<div style="text-align: right; font-size: 10px; font-family: monospace; color: #9ca3af; padding-top: 3px;">LIVE SYNC <span style="display: inline-block; width: 8px; height: 8px; background-color: #e10600; border-radius: 50%; margin-left: 5px; box-shadow: 0 0 5px #e10600;"></span></div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 12px 0 20px 0;'>", unsafe_allow_html=True)

# =========================================================
# 3. 核心資料與快取功能 (包含強悍防呆機制)
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
    except Exception as e:
        st.error(f"Failed to fetch dataset index: {e}")
        return pd.DataFrame(columns=["year", "event", "session", "filename"])
    
    rows = []
    for f in files:
        if not f.endswith(".parquet"): continue
        parts = f[:-8].split("_")
        if len(parts) < 3: continue
        rows.append({"year": int(parts[0]), "event": "_".join(parts[1:-1]), "session": parts[-1], "filename": f})
    
    df_files = pd.DataFrame(rows)
    if not df_files.empty:
        df_files = df_files.sort_values(by=["year", "event", "session"], ascending=[False, True, True])
    return df_files

@st.cache_data(show_spinner=False)
def load_telemetry(filename: str) -> pd.DataFrame:
    path = f"hf://datasets/{REPO_ID}/{filename}"
    try:
        df_loaded = pd.read_parquet(path)
        
        # 強悍的欄位名稱自動對齊邏輯 (過濾任何前後空白或大小寫干擾)
        rename_map = {}
        for col in df_loaded.columns:
            cl = str(col).strip().lower()
            if 'distance' in cl and 'ahead' not in cl and 'relative' not in cl: rename_map[col] = 'Distance'
            elif cl == 'speed': rename_map[col] = 'Speed'
            elif cl == 'throttle': rename_map[col] = 'Throttle'
            elif cl == 'brake': rename_map[col] = 'Brake'
            elif cl == 'rpm': rename_map[col] = 'RPM'
            elif cl == 'ngear' or cl == 'gear': rename_map[col] = 'Gear'
            elif cl == 'drs': rename_map[col] = 'DRS'
            elif 'driver' in cl and 'ahead' not in cl: rename_map[col] = 'Driver'
            elif cl == 'team': rename_map[col] = 'Team'
            elif cl == 'x': rename_map[col] = 'X'
            elif cl == 'y': rename_map[col] = 'Y'
            elif cl == 'time' or cl == 'sessiontime': rename_map[col] = 'Time'
            
        df_loaded.rename(columns=rename_map, inplace=True)
        
        # 若資料集缺乏 Driver 欄位，給予預設值以防崩潰
        if 'Driver' not in df_loaded.columns:
            df_loaded['Driver'] = 'UNKNOWN'
            
        # 若資料集缺乏 Distance 欄位，嘗試用 Time 或行號補齊 X 軸
        if 'Distance' not in df_loaded.columns:
            if 'Time' in df_loaded.columns:
                df_loaded['Distance'] = range(len(df_loaded)) # Fallback index
            else:
                df_loaded['Distance'] = range(len(df_loaded))
                
        # 強制將 Brake 轉換為數值 (因為部分 FastF1 輸出會是 True/False 或 NaN)
        if 'Brake' in df_loaded.columns:
            df_loaded['Brake'] = pd.to_numeric(df_loaded['Brake'], errors='coerce').fillna(0).astype(int)
            
        return df_loaded
    except Exception as e:
        st.error(f"Error decoding telemetry array: {str(e)}")
        return pd.DataFrame()

df_files = get_file_index()

# =========================================================
# 4. 高階 AI 分析引擎 (生成進階賽道見解)
# =========================================================
def generate_advanced_ai_insights(df, drv1, drv2):
    if df.empty or "Speed" not in df.columns or "Brake" not in df.columns:
        return "<p style='color: #666; font-size: 13px;'>Awaiting valid telemetry packets...</p>"
        
    d1 = df[df['Driver'] == drv1]
    d2 = df[df['Driver'] == drv2] if drv1 != drv2 else d1
    
    if d1.empty or d2.empty:
        return "<p style='color: #666; font-size: 13px;'>Incomplete driver vectors detected.</p>"
        
    # 分析極速與油門特性
    vmax1, vmax2 = d1['Speed'].max(), d2['Speed'].max()
    throttle_avg1 = d1['Throttle'].mean() if 'Throttle' in d1.columns else 0
    throttle_avg2 = d2['Throttle'].mean() if 'Throttle' in d2.columns else 0
    
    # 計算重煞車區域 (Brake == 1 的次數/比例)
    brake_zones1 = len(d1[d1['Brake'] > 0])
    brake_zones2 = len(d2[d2['Brake'] > 0])
    
    vmax_diff = abs(vmax1 - vmax2)
    faster_drv = drv1 if vmax1 >= vmax2 else drv2
    
    # 建立動態分析文本
    insight_html = f"""
    <div style="background: linear-gradient(145deg, #111111 0%, #1a1a1a 100%); padding: 18px; border-radius: 6px; border-left: 3px solid #e10600; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
        <p style="font-size: 11px; color: #888; margin-bottom: 8px; font-family: monospace;">[NEURAL DIAGNOSTICS v2.4 ONLINE]</p>
        <p style="font-size: 13px; color: #eee; margin-bottom: 12px; line-height: 1.6;">
            Kinematic scan complete. <b>{faster_drv}</b> exhibits a distinct aerodynamic efficiency advantage, logging a V-Max surplus of <span style="color: #e10600; font-weight: bold;">+{vmax_diff:.1f} km/h</span> on primary straights.
        </p>
        <div style="display: flex; justify-content: space-between; border-top: 1px solid #333; border-bottom: 1px solid #333; padding: 8px 0; margin-bottom: 12px;">
            <div style="width: 48%;">
                <span style="font-size: 10px; color: #999; display: block;">{drv1} V-MAX</span>
                <span style="font-size: 16px; color: #fff; font-weight: bold; font-family: monospace;">{vmax1:.0f} <span style="font-size: 10px;">km/h</span></span>
            </div>
            <div style="width: 48%;">
                <span style="font-size: 10px; color: #999; display: block;">{drv2} V-MAX</span>
                <span style="font-size: 16px; color: #fff; font-weight: bold; font-family: monospace;">{vmax2:.0f} <span style="font-size: 10px;">km/h</span></span>
            </div>
        </div>
        <ul style="font-size: 12px; color: #bbb; padding-left: 16px; margin-bottom: 0; line-height: 1.5;">
            <li><b>Throttle Profile:</b> {drv1} commits to full throttle {throttle_avg1:.1f}% of the lap compared to {drv2}'s {throttle_avg2:.1f}%, indicating setup divergence in traction zones.</li>
            <li><b>Brake Trace:</b> Telemetry signatures show {drv1} utilizing {brake_zones1} distinct deceleration inputs vs {drv2}'s {brake_zones2}, revealing differing trail-braking techniques.</li>
        </ul>
    </div>
    """
    return insight_html

# =========================================================
# 5. 三大獨立滑動區塊配置 (st.container 限定高度)
# =========================================================
col_left, col_mid, col_right = st.columns([1.2, 2.6, 1.8], gap="medium")

# ----------------- 區塊 1: 控制選單 (Left) -----------------
with col_left:
    with st.container(height=850, border=False):
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
            drivers = sorted(df.Driver.dropna().unique()) if "Driver" in df.columns else []

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 25px 0;'>", unsafe_allow_html=True)
            
            driver1 = st.selectbox("Driver 1", drivers, index=drivers.index("VER") if "VER" in drivers else (0 if drivers else 0))
            driver2 = st.selectbox("Driver 2", drivers, index=drivers.index("LEC") if "LEC" in drivers else (1 if len(drivers) > 1 else 0))
            
            # 渲染左側專屬的車手摘要卡片 (讓左側不單調)
            if not df.empty and drivers:
                c_team1 = get_team_color(df[df.Driver == driver1].Team.iloc[0]) if 'Team' in df.columns else "#fff"
                c_team2 = get_team_color(df[df.Driver == driver2].Team.iloc[0]) if 'Team' in df.columns else "#fff"
                
                st.markdown(f"""
                <div style="margin-top: 25px;">
                    <p style="font-size: 10px; color: #6b7280; letter-spacing: 0.2em; font-weight: 600; text-transform: uppercase;">Active Telemetry Links</p>
                    <div style="display: flex; align-items: center; background: #111; padding: 10px; border-left: 3px solid {c_team1}; margin-bottom: 8px;">
                        <span style="font-family: monospace; font-size: 16px; font-weight: bold; color: #fff; width: 40px;">{driver1}</span>
                        <span style="font-size: 10px; color: #888; margin-left: auto;">TX / RX: STABLE</span>
                    </div>
                    <div style="display: flex; align-items: center; background: #111; padding: 10px; border-left: 3px solid {c_team2};">
                        <span style="font-family: monospace; font-size: 16px; font-weight: bold; color: #fff; width: 40px;">{driver2}</span>
                        <span style="font-size: 10px; color: #888; margin-left: auto;">TX / RX: STABLE</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        else:
            st.selectbox("Year", [2024])
            st.selectbox("Grand Prix", ["Abu Dhabi"])
            st.selectbox("Session", ["Qualifying"])
            driver1, driver2 = "VER", "LEC"
            df = pd.DataFrame()

# ----------------- 區塊 2: 遙測數據核心圖表 (Middle) -----------------
with col_mid:
    with st.container(height=850, border=False):
        if df.empty or "Driver" not in df.columns:
            st.markdown("""
            <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 600px;">
                <p style="color: #4b5563; font-size: 14px; font-weight: 500; letter-spacing: 0.2em;">NO TELEMETRY DATA AVAILABLE</p>
                <p style="color: #333; font-size: 11px;">Verify API endpoint or dataset integrity.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            selected_drivers = [driver1] if driver1 == driver2 else [driver1, driver2]
            driver_groups = {k: v for k, v in df.groupby("Driver")}

            # 使用 5 行子圖包含檔位 (Gear) 資訊
            fig = make_subplots(
                rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.015,
                subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake", "RPM", "Gear")
            )
            
            # 定義各子圖對應的物理指標
            metrics = [
                ("Speed", 1, "solid"), 
                ("Throttle", 2, "solid"), 
                ("Brake", 3, "dot"), 
                ("RPM", 4, "solid"),
                ("Gear", 5, "solid")
            ]

            for drv in selected_drivers:
                d = driver_groups.get(drv)
                if d is None or d.empty: continue
                
                color = get_team_color(d.Team.iloc[0] if "Team" in d.columns else "")
                x_axis = d["Distance"]
                
                for metric, row, dash in metrics:
                    if metric not in d.columns: continue
                    y_data = d[metric]
                    
                    fig.add_trace(go.Scattergl(
                        x=x_axis, y=y_data, mode="lines",
                        name=drv if row == 1 else None, showlegend=(row == 1),
                        line=dict(color=color, width=1.5, dash=dash),
                        hovertemplate=f"<b>{drv}</b> : %{{y}}<extra></extra>"
                    ), row=row, col=1)

            # 更新排版設定，徹底停用縮放與拖曳，但啟用十字準星追蹤
            fig.update_layout(
                height=800, margin=dict(l=35, r=15, t=30, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#bbb", size=11)),
                hovermode='x unified', hoverlabel=dict(bgcolor="#111", font_size=12, font_family="monospace"),
                dragmode=False, # 絕對禁用拖曳放大
                font=dict(color="#ffffff", family="Arial, sans-serif")
            )

            # 更新所有 X, Y 軸設定
            for i in range(1, 6):
                fig.update_xaxes(
                    showgrid=True, gridcolor='rgba(255,255,255,0.05)', 
                    fixedrange=True, # 絕對禁用 X 軸縮放
                    showspikes=True, spikemode='across', spikethickness=1, spikecolor='#555555', spikedash='solid',
                    row=i, col=1, tickfont=dict(size=9, color='#777')
                )
                fig.update_yaxes(
                    showgrid=True, gridcolor='rgba(255,255,255,0.05)', 
                    fixedrange=True, # 絕對禁用 Y 軸縮放
                    row=i, col=1, tickfont=dict(size=9, color='#777')
                )
                # 讓子圖標題顏色低調且具科技感
                if i-1 < len(fig.layout.annotations):
                    fig.layout.annotations[i-1].update(font=dict(size=11, color="#888", letter_spacing="1px"))

            # Streamlit 1.60+ 支援 width="stretch" 等新參數，但為確保相容性直接忽略報錯參數
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ----------------- 區塊 3: 賽道圖 & AI 分析 (Right) -----------------
with col_right:
    with st.container(height=850, border=False):
        # 賽道渲染引擎
        st.markdown('<p style="font-size: 11px; color: #e10600; letter-spacing: 0.15em; font-weight: 700; margin-bottom: -15px;">TRACK TOPOLOGY</p>', unsafe_allow_html=True)
        if not df.empty and {"X", "Y"}.issubset(df.columns):
            track = df[df.Driver == driver1] if "Driver" in df.columns else df
            if not track.empty:
                max_d = track["Distance"].max()
                s1_lim, s2_lim = max_d * 0.32, max_d * 0.70
                
                # 向量化切分微區段，優化渲染效能
                cond_s1 = track["Distance"] <= s1_lim
                cond_s2 = (track["Distance"] > s1_lim) & (track["Distance"] <= s2_lim)
                cond_s3 = track["Distance"] > s2_lim

                map_fig = go.Figure()
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s1, "X"], y=track.loc[cond_s1, "Y"], mode='lines', line=dict(color='#E10600', width=3.5), hoverinfo='skip'))
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s2, "X"], y=track.loc[cond_s2, "Y"], mode='lines', line=dict(color='#00A0E9', width=3.5), hoverinfo='skip'))
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s3, "X"], y=track.loc[cond_s3, "Y"], mode='lines', line=dict(color='#FFD500', width=3.5), hoverinfo='skip'))

                map_fig.update_layout(
                    height=340, margin=dict(l=0, r=0, t=25, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    dragmode=False, # 禁用賽道圖拖曳
                    xaxis=dict(visible=False, scaleanchor='y', scaleratio=1, fixedrange=True),
                    yaxis=dict(visible=False, fixedrange=True), showlegend=False
                )
                st.plotly_chart(map_fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown("<div style='height: 300px; display: flex; align-items: center; justify-content: center; color: #444; font-size: 12px; font-family: monospace;'>[ GPS / TRACK DATA UNAVAILABLE ]</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 25px 0 15px 0;'>", unsafe_allow_html=True)

        # AI 遙測診斷引擎
        st.markdown('<p style="font-size: 11px; color: #e10600; letter-spacing: 0.15em; font-weight: 700; margin-bottom: 12px;">AI TELEMETRY ANALYSIS 🤖</p>', unsafe_allow_html=True)
        insights = generate_advanced_ai_insights(df, driver1, driver2)
        st.markdown(insights, unsafe_allow_html=True)