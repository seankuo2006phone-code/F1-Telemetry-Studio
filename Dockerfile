# 使用輕量級的 Python 3.10 作為基礎
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 將專案中所有檔案（包含 data_cache 快取資料夾）複製進伺服器
COPY . .

# Hugging Face 要求必須有一個權限為 1000 的使用者
RUN useradd -m -u 1000 user
USER user

# 開放 Hugging Face 預設的 7860 端口
EXPOSE 7860

# 啟動正式環境用的 Gunicorn 伺服器
CMD ["gunicorn", "-b", "0.0.0.0:7860", "main:server"]