"""Garmin Health Tracker バックエンドAPI

FastAPIアプリケーションのエントリーポイント
Supabase PostgreSQL + Render Web Serviceとしてデプロイ可能な構成
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db, GarminSyncLog, SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    logger.info("Garmin Health Tracker API 起動中（Supabase PostgreSQL接続）...")
    init_db()
    logger.info("APIサーバー起動完了")
    yield
    logger.info("APIサーバー終了")


app = FastAPI(
    title="Garmin Health Tracker API",
    description="Garmin Connectデータ取得・分析ミドルウェア",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録（遅延インポートで循環参照回避）
from app.routers import sync, export  # noqa: E402
app.include_router(sync.router)
app.include_router(export.router)


# ── ダッシュボード用HTMLテンプレート ──

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Garmin Health Tracker</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
    h1 { font-size: 1.5rem; margin-bottom: 1.5rem; color: #38bdf8; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #94a3b8; }
    .btn { background: #2563eb; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; margin-right: 0.5rem; margin-bottom: 0.5rem; }
    .btn:hover { background: #1d4ed8; }
    .btn:disabled { background: #475569; cursor: not-allowed; }
    .btn-init { background: #7c3aed; }
    .btn-init:hover { background: #6d28d9; }
    .status { margin-top: 1rem; padding: 1rem; background: #0f172a; border-radius: 8px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
    .log-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .log-table th, .log-table td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #334155; }
    .log-table th { color: #94a3b8; }
    .ok { color: #4ade80; }
    .error { color: #f87171; }
    input { background: #0f172a; border: 1px solid #334155; color: #e2e8f0; padding: 0.5rem; border-radius: 6px; margin-right: 0.5rem; font-size: 0.9rem; }
    .api-key-section { margin-bottom: 1rem; }
    .flex { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
  </style>
</head>
<body>
  <h1>Garmin Health Tracker</h1>

  <div class="card">
    <h2>API Key</h2>
    <div class="api-key-section">
      <input type="password" id="apiKey" placeholder="API Key を入力" style="width: 300px;" />
    </div>
  </div>

  <div class="card">
    <h2>データ同期</h2>
    <div class="flex">
      <button class="btn" onclick="doSync()">同期実行</button>
      <div>
        <input type="text" id="otp" placeholder="OTPコード（6桁）" style="width: 160px;" />
        <button class="btn btn-init" onclick="doInit()">2FA初回セットアップ</button>
      </div>
    </div>
    <div class="status" id="syncResult">結果がここに表示されます</div>
  </div>

  <div class="card">
    <h2>同期ログ（直近10件）</h2>
    <table class="log-table" id="logTable">
      <thead><tr><th>日時</th><th>状態</th><th>Activities</th><th>Sleep</th><th>Health</th><th>Body</th><th>メッセージ</th></tr></thead>
      <tbody id="logBody"><tr><td colspan="7">読み込み中...</td></tr></tbody>
    </table>
  </div>

  <script>
    function getKey() { return document.getElementById('apiKey').value; }

    async function doSync() {
      const key = getKey();
      if (!key) { alert('API Keyを入力してください'); return; }
      const el = document.getElementById('syncResult');
      el.textContent = '同期中...';
      try {
        const res = await fetch('/sync', { method: 'POST', headers: { 'X-API-Key': key } });
        const data = await res.json();
        el.textContent = JSON.stringify(data, null, 2);
        loadLogs();
      } catch (e) { el.textContent = 'エラー: ' + e.message; }
    }

    async function doInit() {
      const key = getKey();
      const otp = document.getElementById('otp').value;
      if (!key) { alert('API Keyを入力してください'); return; }
      if (!otp) { alert('OTPコードを入力してください'); return; }
      const el = document.getElementById('syncResult');
      el.textContent = 'セットアップ中...';
      try {
        const res = await fetch('/sync/init', {
          method: 'POST',
          headers: { 'X-API-Key': key, 'Content-Type': 'application/json' },
          body: JSON.stringify({ otp: otp })
        });
        const data = await res.json();
        el.textContent = JSON.stringify(data, null, 2);
      } catch (e) { el.textContent = 'エラー: ' + e.message; }
    }

    async function loadLogs() {
      // ログは認証不要で表示（ダッシュボード用）
      try {
        const res = await fetch('/logs');
        const data = await res.json();
        const tbody = document.getElementById('logBody');
        if (!data.logs || data.logs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7">ログがありません</td></tr>';
          return;
        }
        tbody.innerHTML = data.logs.map(l => `<tr>
          <td>${l.synced_at || ''}</td>
          <td class="${l.status === 'ok' ? 'ok' : 'error'}">${l.status}</td>
          <td>${l.activities ?? ''}</td>
          <td>${l.sleep_days ?? ''}</td>
          <td>${l.health_days ?? ''}</td>
          <td>${l.body_days ?? ''}</td>
          <td>${l.message || ''}</td>
        </tr>`).join('');
      } catch (e) {
        document.getElementById('logBody').innerHTML = '<tr><td colspan="7">ログ取得エラー</td></tr>';
      }
    }

    loadLogs();
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """シンプルHTMLダッシュボード"""
    return DASHBOARD_HTML


@app.get("/health")
def health():
    """サービス死活確認"""
    return {"status": "ok"}


@app.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    """同期ログ一覧（ダッシュボード表示用・認証不要）"""
    logs = db.query(GarminSyncLog).order_by(desc(GarminSyncLog.synced_at)).limit(10).all()
    return {
        "logs": [
            {
                "synced_at": log.synced_at.isoformat() if log.synced_at else None,
                "status": log.status,
                "activities": log.activities,
                "sleep_days": log.sleep_days,
                "health_days": log.health_days,
                "body_days": log.body_days,
                "message": log.message,
            }
            for log in logs
        ]
    }
