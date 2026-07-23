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

    # Plotly 圖表設定，強制顯示工具列並關閉滾動縮放
    PLOTLY_CONFIG = {
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['zoomIn2d', 'zoomOut2d', 'pan2d', 'lasso2d'], # 移除不常用的
        'scrollZoom': False,
        'doubleClick': 'reset',
    }

config = Config()