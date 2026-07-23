import os
import fastf1
import logging

logger = logging.getLogger(__name__)

def initialize_cache():
    """
    初始化 FastF1 的快取資料夾。
    如果在本地端、Render 或 Hugging Face 部署，這能避免重複下載龐大的原始遙測資料。
    """
    # 定義快取資料夾名稱 (與我們剛剛在 build_cache.py 設定的一致)
    cache_dir = 'fastf1_cache'
    
    try:
        # 確保資料夾存在，如果沒有就建立一個
        os.makedirs(cache_dir, exist_ok=True)
        
        # 正式啟用 FastF1 快取
        fastf1.Cache.enable_cache(cache_dir)
        logger.info(f"✅ FastF1 快取已成功啟用於 '{cache_dir}' 資料夾。")
        
    except Exception as e:
        logger.error(f"❌ 無法啟用 FastF1 快取: {e}")