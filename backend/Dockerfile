FROM python:3.12-slim

WORKDIR /app

# 依存パッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ポートを公開（Renderが$PORTを注入）
EXPOSE 10000

# uvicornで起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
