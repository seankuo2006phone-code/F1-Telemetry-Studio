import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from huggingface_hub import list_repo_files

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="F1 Telemetry Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

REPO_ID = "SeanKuo2006/F1-Telemetry-Data"

# 終極無邊框 CSS 注入：強制抹除所有輸入框邊界、背景，並隱藏連結圖標 (🔗)
custom_css = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 隱藏標題旁的 🔗 圖標 */
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
    display: none !important;
}

/* 徹底透明化所有 Selectbox 的背景與邊框 */
div[data-testid="stSelectbox"] * {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 確保下拉選單文字顏色 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
    color: #FFFFFF !important;
    font-size: 1rem !important;
}
div[data-testid="stSelectbox"] label p {
    color: #888888 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =========================================================
# TEAM COLORS
# =========================================================
TEAM_COLORS = {
    "red bull": "#3671C6",
    "ferrari": "#F91536",
    "mercedes": "#6CD3BF",
    "mclaren": "#F58020",
    "aston martin": "#229971",
    "alpine": '#2293D1',
    "williams": "#37BEDD",
    "alphatauri": "#5E8FAA",
    "alfa romeo": "#C92D4B",
    "haas": "#B6BABD",
    "rb": "#6692FF",
    "racing bulls": "#6692FF",
    "sauber": "#52E252",
    "kick sauber": "#52E252"
}

SESSION_NAMES = {
    "R": "Race",
    "Q": "Qualifying",
    "S": "Sprint",
    "SQ": "Sprint Shootout",
    "FP1": "Free Practice 1",
    "FP2": "Free Practice 2",
    "FP3": "Free Practice 3"
}

def get_team_color(team: str) -> str:
    team = str(team).lower()
    return next(
        (v for k, v in TEAM_COLORS.items() if k in team),
        "#FFFFFF"
    )

# =========================================================
# FILE LIST CACHE
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_file_index() -> pd.DataFrame:
    files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")

    rows = []
    for f in files:
        if not f.endswith(".parquet"):
            continue

        parts = f[:-8].split("_")
        if len(parts) < 3:
            continue

        rows.append({
            "year": int(parts[0]),
            "event": "_".join(parts[1:-1]),
            "session": parts[-1],
            "filename": f
        })

    return pd.DataFrame(rows)

df_files = get_file_index()

# =========================================================
# TELEMETRY LOADER
# =========================================================
@st.cache_data(show_spinner="Loading telemetry data...")
def load_telemetry(filename: str) -> pd.DataFrame:
    path = f"hf://datasets/{REPO_ID}/{filename}"

    cols = [
        "Driver", "Team", "Distance", "Speed",
        "Throttle", "Brake", "RPM",
        "X", "Y", "DRS", "Sector"
    ]

    try:
        return pd.read_parquet(path, columns=cols)
    except Exception:
        return pd.read_parquet(path)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div style="text-align:center;padding:10px 0 30px 0;">
        <h1 style="font-size:3rem;font-weight:900;letter-spacing:2px;margin:0;">
            F1 Telemetry Studio
        </h1>
        <p style="color:#888;font-size:1rem;">
            Professional Formula One Telemetry Analysis Platform
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TOP CONTROLS
# =========================================================
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    year = st.selectbox(
        "YEAR",
        sorted(df_files.year.unique(), reverse=True)
    )

events = sorted(df_files[df_files.year == year].event.unique())

with c2:
    event = st.selectbox("CIRCUIT", events)

sessions = df_files[
    (df_files.year == year) &
    (df_files.event == event)
].session.unique()

with c3:
    session = st.selectbox(
        "SESSION",
        sessions,
        format_func=lambda x: SESSION_NAMES.get(x, x)
    )

filename = df_files[
    (df_files.year == year) &
    (df_files.event == event) &
    (df_files.session == session)
].iloc[0].filename

df = load_telemetry(filename)

drivers = sorted(df.Driver.unique())

with c4:
    driver1 = st.selectbox(
        "DRIVER 1",
        drivers,
        index=drivers.index("VER") if "VER" in drivers else 0
    )

with c5:
    driver2 = st.selectbox(
        "DRIVER 2",
        drivers,
        index=drivers.index("ALO") if "ALO" in drivers else (1 if len(drivers) > 1 else 0)
    )

selected = [driver1] if driver1 == driver2 else [driver1, driver2]
driver_groups = {k: v for k, v in df.groupby("Driver")}

# =========================================================
# LAYOUT
# =========================================================
has_xy = {"X", "Y"}.issubset(df.columns)

if has_xy:
    col_chart, col_map = st.columns([3.3, 1.2])
else:
    col_chart = st.container()
    col_map = None

# =========================================================
# TELEMETRY FIGURE
# =========================================================
def build_telemetry_figure(selected_drivers: list[str]) -> go.Figure:

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            "Speed (km/h)",
            "Throttle (%)",
            "Brake",
            "RPM"
        )
    )

    metrics = [
        ("Speed", 1, "solid"),
        ("Throttle", 2, "solid"),
        ("Brake", 3, "dot"),
        ("RPM", 4, "solid")
    ]

    for drv in selected_drivers:
        d = driver_groups.get(drv)
        if d is None:
            continue

        color = get_team_color(d.Team.iloc[0])
        x = d.Distance

        for metric, row, dash in metrics:
            if metric not in d.columns:
                continue

            y = d[metric]
            if metric == "Brake":
                y = y.astype("int8")

            fig.add_trace(
                go.Scattergl(
                    x=x,
                    y=y,
                    mode="lines",
                    name=drv if row == 1 else None,
                    showlegend=row == 1,
                    line=dict(color=color, width=2, dash=dash),
                    legendgroup=drv,
                    # 強制指定懸浮格式：只顯示 車手簡寫: 數據，徹底過濾掉多餘的 X 軸座標
                    hovertemplate=f"{drv} : %{{y}}<extra></extra>"
                ),
                row=row,
                col=1
            )

    fig.update_layout(
        height=860,
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=40, b=10),
        # 數據懸浮標籤：全透明背景、無邊框、字體全部強制改為 F1 紅色 (#E10600)
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=14, color="#E10600")
        ),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.02,
            yanchor="bottom"
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    # 垂直對齊參考線：紅色、虛線、貫穿子圖
    fig.update_xaxes(
        showspikes=True,
        spikecolor="#E10600",
        spikethickness=1,
        spikedash="dash",
        spikemode="across"
    )
    fig.update_xaxes(title_text="Distance (m)", row=4, col=1)

    return fig

with col_chart:
    st.plotly_chart(
        build_telemetry_figure(selected),
        use_container_width=True,
        config={"displayModeBar": False}
    )

# =========================================================
# TRACK MAP (右側無邊框小視窗)
# =========================================================
if has_xy and col_map is not None:
    with col_map:
        st.markdown(
            "<h4 style='text-align:center;color:#CCCCCC;font-weight:600;'>Track Map</h4>",
            unsafe_allow_html=True
        )

        track = driver_groups[driver1]
        fig_track = go.Figure()

        if "Sector" not in track.columns:
            dist = track.Distance / track.Distance.max()
            sectors = pd.cut(
                dist,
                bins=[0, 1/3, 2/3, 1],
                labels=[1, 2, 3]
            )
            track = track.assign(Sector=sectors)

        sector_colors = {
            1: "#E10600",
            2: "#FFD700",
            3: "#00D2BE"
        }

        for sec, color in sector_colors.items():
            sec_df = track[track.Sector.astype(str) == str(sec)]
            fig_track.add_trace(
                go.Scattergl(
                    x=sec_df.X,
                    y=sec_df.Y,
                    mode="lines",
                    line=dict(color=color, width=4),
                    name=f"Sector {sec}",
                    hoverinfo="skip"
                )
            )

        if "DRS" in track.columns:
            drs = track[track.DRS >= 10]
            fig_track.add_trace(
                go.Scattergl(
                    x=drs.X,
                    y=drs.Y,
                    mode="markers",
                    marker=dict(color="#00FF7F", size=5),
                    name="DRS Active",
                    hoverinfo="skip"
                )
            )

        fig_track.update_layout(
            height=500,
            template="plotly_dark",
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=True,
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1.02,
                yanchor="bottom"
            ),
            # fixedrange=True 鎖定 X/Y 軸範圍，使地圖無法被滑鼠滾輪縮放
            xaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                fixedrange=True
            ),
            yaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                scaleanchor="x",
                fixedrange=True
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            dragmode="pan" # 開啟滑鼠點擊抓取平移
        )

        # F1 TELEMETRY STUDIO FINAL HOVER CONFIG
        fig_track.update_layout(
            hovermode="x",
            hoverlabel=dict(
                bgcolor="rgba(0,0,0,0)",
                bordercolor="rgba(0,0,0,0)",
                font=dict(size=14, color="#FF0000")
            )
        )

        fig_track.update_xaxes(showspikes=False)
        fig_track.update_yaxes(showspikes=False)

        # 顯示 X 軸的 spike（時間游標）
        try:
            fig_track.update_xaxes(
                showspikes=True,
                spikecolor="#E10600",
                spikedash="dash",
                spikemode="across"
            )
        except NameError:
            pass

        # 這是確保工具列在手機上也會出現的設定
        config = {
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'pan2d', 'lasso2d'], # 移除不常用的
            'scrollZoom': False,
            'doubleClick': 'reset',
        }

        # 在圖上繪製紅色虛線（時間軸標記）
        # 確保 target_time_x_value 已在其他地方設定為你想要標記的 X 軸時間值
        try:
            fig_track.add_shape(
                type="line",
                x0=target_time_x_value,
                y0=0,
                x1=target_time_x_value,
                y1=350,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash"
                )
            )
        except NameError:
            # 如果 target_time_x_value 未定義則跳過，不影響其他功能
            pass

        # 繪製圖表
        st.plotly_chart(fig_track, config=config, use_container_width=True)

# =========================================================
# RAW DATA
# =========================================================
st.divider()

with st.expander("Raw Telemetry Data"):
    st.dataframe(
        df[df.Driver.isin(selected)],
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# DATASET FILES
# =========================================================
# ---------- Load dataset ----------
try:
    all_files = get_file_list()
except NameError:
    # Fallback to repository listing if get_file_list is unavailable
    all_files = list_repo_files(repo_id=REPO_ID, repo_type="dataset")

# Debug
st.write("Number of parquet files:", len(all_files))
st.write(all_files)

options = []
for f in all_files:
    options.append(f)

selected_files = st.multiselect("Select dataset files to load:", options, default=options[:1])