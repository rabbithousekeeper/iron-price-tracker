# garmin-health-tracker

Garmin Connectから全データを自動取得し、Supabaseに蓄積。Claudeが分析しやすいJSON形式でエクスポートするWebサービス。

## 技術スタック

- バックエンド: Python + FastAPI
- データベース: Supabase (PostgreSQL直接接続)
- Garminデータ取得: garminconnect ライブラリ
- デプロイ: Render (Web Service + Cron Job)

## セットアップ

### 1. 環境変数の設定

```bash
cd backend
cp .env.example .env
# .env を編集して各値を設定
```

### 2. ローカル起動

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. 初回セットアップ（2FA対応）

Garmin Connectで2FAが有効な場合、OTPを使って初回認証が必要です。

```bash
# Garminアプリで表示されるOTPコードを送信
curl -X POST http://localhost:8000/sync/init \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"otp": "123456"}'
```

セッションはDBに保存されるため、以降は自動同期が可能です。

### 4. 手動同期

```bash
curl -X POST http://localhost:8000/sync \
  -H "X-API-Key: YOUR_API_KEY"
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | / | ダッシュボード（HTML） |
| GET | /health | 死活確認 |
| POST | /sync | データ手動同期 |
| POST | /sync/init | 2FA初回セットアップ |
| GET | /export/claude?type={type}&days={N} | Claude用JSONエクスポート |
| GET | /export/prompt?type={type} | 分析依頼プロンプトテンプレート |

### エクスポートタイプ一覧

| type | 説明 | 推奨days |
|---|---|---|
| weekly_training | 週次トレーニング振り返り | 7 |
| monthly_training | 月次トレーニング振り返り | 30 |
| sleep_correlation | 睡眠×トレーニング相関 | 30 |
| overtraining | オーバートレーニング兆候 | 14 |
| peaking | ピーキング分析（race_date必須） | 60 |
| body_composition | 体組成トレンド | 90 |
| health_overview | 総合健康分析 | 30 |
| full | 全データ統合 | 30 |

## 環境変数

| 変数名 | 説明 | 必須 |
|---|---|---|
| GARMIN_EMAIL | Garmin Connectメールアドレス | はい |
| GARMIN_PASSWORD | Garmin Connectパスワード | はい |
| SUPABASE_DB_URL | PostgreSQL接続URL | はい |
| API_KEY | API認証キー | はい |
| FETCH_INTERVAL_HOURS | 同期間隔（時間） | いいえ（デフォルト: 6） |
| ACTIVITY_LIMIT | 取得アクティビティ数上限 | いいえ（デフォルト: 200） |
| SYNC_DAYS_BACK | 遡り日数 | いいえ（デフォルト: 30） |
| TZ | タイムゾーン | いいえ（デフォルト: Asia/Tokyo） |

## Renderデプロイ

`render.yaml` を使用してBlueprint Deployが可能です。

1. GitHubリポジトリをRenderに接続
2. Blueprint Instanceとしてデプロイ
3. ダッシュボードから環境変数を設定
4. POST /sync/init で初回認証を実行
