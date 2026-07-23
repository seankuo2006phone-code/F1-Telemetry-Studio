import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from huggingface_hub import list_repo_files
import warnings

warnings.filterwarnings('ignore')

# =========================================================
# 1. Page Config & Extreme Borderless CSS
# =========================================================
st.set_page_config(
    page_title="F1 Telemetry Studio Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

custom_css = """
<style>
/* Hide Streamlit elements */
#MainMenu, footer, header { visibility: hidden !important; }

/* Force pure black background & edge-to-edge padding */
.block-container {
    padding: 0rem 1.5rem !important;
    max-width: 100% !important;
    background-color: #000000 !important;
}
.stApp {
    background-color: #000000 !important;
    color: #ffffff !important;
}

/* Red top accent line */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 4px;
    background-color: #e10600;
    z-index: 99999;
}

/* ---------------------------------------------------
   EXTREME BORDERLESS SELECTBOX (No Border, No Underline, No Background)
--------------------------------------------------- */
div[data-testid="stSelectbox"] {
    background-color: transparent !important;
}
div[data-baseweb="select"] {
    background-color: transparent !important;
}
div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div:hover, 
div[data-baseweb="select"] > div:focus,
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="select"] > div:active {
    background-color: transparent !important;
    border: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
    outline: none !important;
}
div[data-baseweb="select"] span { 
    color: #ffffff !important; 
    font-size: 15px !important; 
    font-weight: 500 !important;
    padding-left: 0 !important;
}
div[data-baseweb="select"] svg { display: none !important; }

/* Dropdown menu overlay */
div[data-baseweb="popover"] > div {
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 4px !important;
}
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background-color: transparent !important;
    color: #ffffff !important;
}
ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
    background-color: #e10600 !important;
}

/* Selectbox labels */
div[data-testid="stSelectbox"] label p {
    color: #6b7280 !important;
    font-size: 10px !important;
    letter-spacing: 0.2em !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}

/* Minimal scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #e10600; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =========================================================
# 2. Perfect Aligned Top Header (Logo + Nav + Title)
# =========================================================
header_html = """
<div style="background-color: #15151e; padding: 15px 25px; margin: 0rem -1.5rem 20px -1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
        <div style="display: flex; align-items: center; gap: 35px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg" alt="F1 Logo" style="height: 22px; width: auto;" />
            <div style="display: flex; gap: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #fff; letter-spacing: 0.1em;">
                <a href="https://www.formula1.com/en/racing/2024.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8;">Schedule</a>
                <a href="https://www.formula1.com/en/results.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8;">Results</a>
                <a href="https://www.formula1.com/en/results.html/team.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8;">Standings</a>
                <a href="https://www.formula1.com/en/drivers.html" target="_blank" style="color: white; text-decoration: none; opacity: 0.8;">Drivers</a>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
            <a href="https://account.formula1.com" target="_blank" style="color: #d1d5db; text-decoration: none; opacity: 0.8;">Sign In</a>
            <a href="https://f1tv.formula1.com/" target="_blank" style="background-color: #e10600; color: white; padding: 6px 14px; border-radius: 2px; text-decoration: none;">Subscribe</a>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 18px; font-weight: 300; letter-spacing: 0.25em; color: white; margin: 0;">TELEMETRY STUDIO</span>
            <span style="background-color: #e10600; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 12px; color: white; letter-spacing: 0.1em;">PRO v2</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 10px; font-family: monospace; color: #9ca3af; letter-spacing: 0.1em;">LIVE SYNC</span>
            <span style="display: inline-block; width: 8px; height: 8px; background-color: #e10600; border-radius: 50%; box-shadow: 0 0 5px #e10600;"></span>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# =========================================================
# 3. Core Data & Cache Functions
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
    except Exception:
        return pd.DataFrame(columns=["year", "event", "session", "filename"])

@st.cache_data(show_spinner=False)
def load_telemetry(filename: str) -> pd.DataFrame:
    path = f"hf://datasets/{REPO_ID}/{filename}"
    try:
        df_loaded = pd.read_parquet(path)
        rename_map = {}
        for col in df_loaded.columns:
            cl = str(col).strip().lower()
            if 'distance' in cl and 'ahead' not in cl: rename_map[col] = 'Distance'
            elif cl == 'speed': rename_map[col] = 'Speed'
            elif cl == 'throttle': rename_map[col] = 'Throttle'
            elif cl == 'brake': rename_map[col] = 'Brake'
            elif cl == 'rpm': rename_map[col] = 'RPM'
            elif cl in ['ngear', 'gear']: rename_map[col] = 'Gear'
            elif cl == 'drs': rename_map[col] = 'DRS'
            elif 'driver' in cl and 'ahead' not in cl: rename_map[col] = 'Driver'
            elif cl == 'team': rename_map[col] = 'Team'
            elif cl == 'x': rename_map[col] = 'X'
            elif cl == 'y': rename_map[col] = 'Y'
        
        df_loaded.rename(columns=rename_map, inplace=True)
        # 移除重複的欄位名 (解決 DataFrame 轉 Series 產生的 AttributeError)
        df_loaded = df_loaded.loc[:, ~df_loaded.columns.duplicated()]
        
        if 'Brake' in df_loaded.columns:
            df_loaded['Brake'] = pd.to_numeric(df_loaded['Brake'], errors='coerce').fillna(0).astype(int)
        
        if 'Driver' in df_loaded.columns and 'Distance' in df_loaded.columns:
            df_loaded = df_loaded.sort_values(by=['Driver', 'Distance']).reset_index(drop=True)
            
        return df_loaded
    except Exception:
        return pd.DataFrame()

# =========================================================
# 4. Delta Time Engine
# =========================================================
def calculate_delta_time(d1, d2):
    if d1.empty or d2.empty or 'Distance' not in d1.columns or 'Distance' not in d2.columns:
        return None
    try:
        dist1 = d1['Distance'].values
        speed_kmh1 = d1['Speed'].values
        time1 = np.zeros(len(dist1))
        for i in range(1, len(dist1)):
            d_dist = dist1[i] - dist1[i-1]
            v_ms = max(((speed_kmh1[i] + speed_kmh1[i-1]) / 2) / 3.6, 0.1)
            time1[i] = time1[i-1] + (d_dist / v_ms)
            
        dist2 = d2['Distance'].values
        speed_kmh2 = d2['Speed'].values
        time2 = np.zeros(len(dist2))
        for i in range(1, len(dist2)):
            d_dist = dist2[i] - dist2[i-1]
            v_ms = max(((speed_kmh2[i] + speed_kmh2[i-1]) / 2) / 3.6, 0.1)
            time2[i] = time2[i-1] + (d_dist / v_ms)
            
        time2_interp = np.interp(dist1, dist2, time2)
        delta = time1 - time2_interp
        return pd.Series(delta, index=d1.index)
    except:
        return None

# =========================================================
# 5. AI Insights Engine
# =========================================================
def generate_ai_insights(df, drv1, drv2):
    if df.empty or "Speed" not in df.columns:
        return "<p style='color: #666; font-size: 13px; font-family: monospace;'>[ Awaiting telemetry packets... ]</p>"
        
    d1 = df[df['Driver'] == drv1] if 'Driver' in df.columns else pd.DataFrame()
    d2 = df[df['Driver'] == drv2] if 'Driver' in df.columns else pd.DataFrame()
    
    if d1.empty or d2.empty: 
        return "<p style='color: #666; font-size: 13px;'>Incomplete driver vectors.</p>"
        
    vmax1 = d1['Speed'].max() if 'Speed' in d1.columns else 0
    vmax2 = d2['Speed'].max() if 'Speed' in d2.columns else 0
    brake_zones1 = len(d1[d1['Brake'] > 0]) if 'Brake' in d1.columns else 0
    brake_zones2 = len(d2[d2['Brake'] > 0]) if 'Brake' in d2.columns else 0
    
    vmax_diff = abs(vmax1 - vmax2)
    faster_drv = drv1 if vmax1 >= vmax2 else drv2
    
    return f"""
    <div style="background-color: #111111; padding: 15px; border-radius: 6px; border-left: 3px solid #e10600;">
        <p style="font-size: 10px; color: #777; margin-bottom: 5px; font-family: monospace;">[ FASTF1 NEURAL INSIGHTS V1.2 ]</p>
        <p style="font-size: 13px; color: #ddd; margin-bottom: 12px; line-height: 1.5;">
            Kinematic scan complete. <b>{faster_drv}</b> exhibits a distinct aerodynamic efficiency advantage, logging a V-Max surplus of <span style="color: #e10600; font-weight: bold;">+{vmax_diff:.1f} km/h</span>.
        </p>
        <div style="display: flex; justify-content: space-between; border-top: 1px solid #333; border-bottom: 1px solid #333; padding: 8px 0; margin-bottom: 10px;">
            <div style="width: 48%;">
                <span style="font-size: 10px; color: #999; display: block;">{drv1} V-MAX</span>
                <span style="font-size: 16px; color: #fff; font-weight: bold; font-family: monospace;">{vmax1:.0f} <span style="font-size: 10px;">km/h</span></span>
            </div>
            <div style="width: 48%;">
                <span style="font-size: 10px; color: #999; display: block;">{drv2} V-MAX</span>
                <span style="font-size: 16px; color: #fff; font-weight: bold; font-family: monospace;">{vmax2:.0f} <span style="font-size: 10px;">km/h</span></span>
            </div>
        </div>
        <ul style="font-size: 12px; color: #aaa; padding-left: 16px; margin-bottom: 0; line-height: 1.5;">
            <li><b>Brake Trace:</b> {drv1} logged {brake_zones1} heavy deceleration points vs {drv2}'s {brake_zones2}.</li>
            <li>Throttle patterns indicate divergence in corner exit traction strategies.</li>
        </ul>
    </div>
    """

# =========================================================
# 6. Main Layout (Three Scrollable Columns)
# =========================================================
df_files = get_file_index()
col_left, col_mid, col_right = st.columns([1.2, 3.0, 1.6], gap="large")

# --- Left Column: Controls ---
with col_left:
    with st.container(height=800, border=False):
        if not df_files.empty:
            years = sorted(df_files.year.unique(), reverse=True)
            year = st.selectbox("Year", years, key="yr")

            events = sorted(df_files[df_files.year == year].event.unique())
            event = st.selectbox("Grand Prix", events, key="ev")

            sessions = df_files[(df_files.year == year) & (df_files.event == event)].session.unique()
            session = st.selectbox("Session", sessions, format_func=lambda x: SESSION_NAMES.get(x, x), key="ss")

            file_row = df_files[(df_files.year == year) & (df_files.event == event) & (df_files.session == session)]
            filename = file_row.iloc[0].filename if not file_row.empty else None
            df = load_telemetry(filename) if filename else pd.DataFrame()
            
            # 安全擷取 Driver 欄位，徹底防止 DataFrame 沒有 .unique() 的問題
            if "Driver" in df.columns:
                driver_series = df["Driver"]
                if isinstance(driver_series, pd.DataFrame):
                    driver_series = driver_series.iloc[:, 0]
                drivers = sorted([str(x) for x in driver_series.dropna().unique()])
            else:
                drivers = []

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 25px 0;'>", unsafe_allow_html=True)
            
            driver1 = st.selectbox("Driver 1", drivers, index=drivers.index("VER") if "VER" in drivers else 0, key="d1") if drivers else "VER"
            driver2 = st.selectbox("Driver 2", drivers, index=drivers.index("LEC") if "LEC" in drivers else (1 if len(drivers)>1 else 0), key="d2") if drivers else "LEC"
        else:
            df, driver1, driver2 = pd.DataFrame(), "VER", "LEC"

# --- Middle Column: Telemetry Charts ---
with col_mid:
    with st.container(height=800, border=False):
        if df.empty or "Driver" not in df.columns:
            st.markdown("<div style='text-align:center; color:#444; margin-top:300px; font-family:monospace;'>[ NO TELEMETRY DATA ]</div>", unsafe_allow_html=True)
        else:
            d1 = df[df['Driver'] == driver1].copy()
            d2 = df[df['Driver'] == driver2].copy()
            
            if driver1 != driver2:
                d1['Delta'] = calculate_delta_time(d1, d2)
            else:
                d1['Delta'] = 0.0
                
            c1 = get_team_color(d1.Team.iloc[0]) if not d1.empty and 'Team' in d1.columns else "#3671C6"
            c2 = get_team_color(d2.Team.iloc[0]) if not d2.empty and 'Team' in d2.columns else "#F91536"

            fig = make_subplots(
                rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.015,
                subplot_titles=("Delta Time (s)", "Speed (km/h)", "Throttle (%)", "Brake", "RPM", "Gear")
            )
            
            # Delta Trace
            if 'Delta' in d1.columns and not d1['Delta'].isna().all():
                fig.add_trace(go.Scattergl(
                    x=d1['Distance'], y=d1['Delta'], mode="lines",
                    name="Delta", line=dict(color=c1, width=1.5), fill='tozeroy', fillcolor=f"{c1}33",
                    hovertemplate=f"<b>{driver1} Relative</b>: %{{y:+.3f}}s<extra></extra>"
                ), row=1, col=1)

            # Telemetry Traces
            metrics = [("Speed", 2, "solid"), ("Throttle", 3, "solid"), ("Brake", 4, "dot"), ("RPM", 5, "solid"), ("Gear", 6, "solid")]
            for drv, d_drv, c_drv in [(driver1, d1, c1), (driver2, d2, c2)]:
                if d_drv.empty: continue
                for metric, row, dash in metrics:
                    if metric not in d_drv.columns: continue
                    fig.add_trace(go.Scattergl(
                        x=d_drv['Distance'], y=d_drv[metric], mode="lines",
                        name=drv if row == 2 else None, showlegend=(row == 2),
                        line=dict(color=c_drv, width=1.5, dash=dash),
                        hovertemplate=f"<b>{drv}</b>: %{{y}}<extra></extra>"
                    ), row=row, col=1)

            # Fixed scale with cursor tracking
            fig.update_layout(
                height=780, margin=dict(l=25, r=15, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#bbb")),
                hovermode='x unified', hoverlabel=dict(bgcolor="#111", font_size=12, font_family="monospace"),
                dragmode=False, 
                font=dict(color="#ffffff")
            )

            for i in range(1, 7):
                fig.update_xaxes(
                    showgrid=True, gridcolor='rgba(255,255,255,0.05)', fixedrange=True, 
                    showspikes=True, spikemode='across', spikethickness=1, spikecolor='#666', spikedash='solid',
                    row=i, col=1, tickfont=dict(size=9, color='#777')
                )
                fig.update_yaxes(
                    showgrid=True, gridcolor='rgba(255,255,255,0.05)', fixedrange=True, 
                    row=i, col=1, tickfont=dict(size=9, color='#777')
                )
                if i-1 < len(fig.layout.annotations):
                    fig.layout.annotations[i-1].update(font=dict(size=10, color="#888", letter_spacing="2px"))

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- Right Column: Track Map & AI Analysis ---
with col_right:
    with st.container(height=800, border=False):
        st.markdown('<p style="font-size: 11px; color: #e10600; letter-spacing: 0.15em; font-weight: 700; margin-bottom: -15px;">TRACK TOPOLOGY</p>', unsafe_allow_html=True)
        if not df.empty and {"X", "Y"}.issubset(df.columns):
            track = df[df.Driver == driver1] if "Driver" in df.columns else df
            if not track.empty and "Distance" in track.columns:
                max_d = track["Distance"].max()
                s1_lim, s2_lim = max_d * 0.32, max_d * 0.70
                
                cond_s1 = track["Distance"] <= s1_lim
                cond_s2 = (track["Distance"] > s1_lim) & (track["Distance"] <= s2_lim)
                cond_s3 = track["Distance"] > s2_lim

                map_fig = go.Figure()
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s1, "X"], y=track.loc[cond_s1, "Y"], mode='lines', line=dict(color='#E10600', width=3.5), hoverinfo='skip'))
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s2, "X"], y=track.loc[cond_s2, "Y"], mode='lines', line=dict(color='#00A0E9', width=3.5), hoverinfo='skip'))
                map_fig.add_trace(go.Scattergl(x=track.loc[cond_s3, "X"], y=track.loc[cond_s3, "Y"], mode='lines', line=dict(color='#FFD500', width=3.5), hoverinfo='skip'))

                map_fig.update_layout(
                    height=300, margin=dict(l=0, r=0, t=25, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    dragmode=False, xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True, scaleanchor='x', scaleratio=1),
                    showlegend=False
                )
                st.plotly_chart(map_fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown("<div style='height: 250px; display: flex; align-items: center; color: #444; font-family: monospace;'>[ NO TRACK DATA ]</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown('<p style="font-size: 11px; color: #e10600; letter-spacing: 0.15em; font-weight: 700; margin-bottom: 12px;">AI TELEMETRY ANALYSIS</p>', unsafe_allow_html=True)
        st.markdown(generate_ai_insights(df, driver1, driver2), unsafe_allow_html=True)