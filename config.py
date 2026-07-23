import os

class Config:
    DEBUG_MODE = False
    HOST = "0.0.0.0"
    PORT = int(os.environ.get("PORT", 10000))
    
    # 補上這行：支援的 F1 年份清單
    SUPPORTED_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    # 預設選項
    DEFAULT_TRACK = "Monza"
    DEFAULT_SESSION = "Q"

    # Plotly 圖表設定，關閉上方工具列並保留 hover 功能
    PLOTLY_CONFIG = {
        'responsive': True,
        'displayModeBar': False,
        'hoverdistance': 20,
    }

    # Plotly layout 設定，讓圖表自動填滿容器並鎖定軸線縮放
    PLOTLY_LAYOUT = {
        'autosize': True,
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'margin': { 't': 10, 'b': 10, 'l': 10, 'r': 10 },
        'xaxis': {
            'visible': False,
            'fixedrange': True,
        },
        'yaxis': {
            'visible': False,
            'fixedrange': True,
            'scaleanchor': 'x',
        },
        'hovermode': 'closest',
    }

config = Config()