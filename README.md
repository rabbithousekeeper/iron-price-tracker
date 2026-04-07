# iron-price-tracker

鉄価格トラッカーWebアプリ

## 技術スタック

- フロントエンド: React 18 + TypeScript + Vite
- スタイリング: Tailwind CSS
- グラフ: Recharts

## セットアップ

```bash
npm install
npm run dev
```

## 環境変数

| 変数名 | 説明 | 必須 |
|---|---|---|
| `VITE_API_URL` | バックエンドAPIのURL | いいえ（未設定時はモックデータを使用） |

### ローカル開発

`.env.example` をコピーして `.env` を作成し、バックエンドURLを設定します。

```bash
cp .env.example .env
```

`.env` ファイル:

```
VITE_API_URL=https://price-tracker-backend-0dai.onrender.com
```

`VITE_API_URL` を設定するとバックエンドAPIから実データを取得します。未設定の場合はモックデータで動作します。

### Render へのデプロイ時の設定

Render でフロントエンドをデプロイする場合、以下の手順で `VITE_API_URL` を設定してください。

1. [Render ダッシュボード](https://dashboard.render.com/) にログイン
2. 対象の Web Service（フロントエンド）を選択
3. **Environment** タブを開く
4. **Add Environment Variable** をクリック
5. 以下を入力:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://price-tracker-backend-0dai.onrender.com`
6. **Save Changes** をクリック
7. サービスを再デプロイ（Manual Deploy > Deploy latest commit）

> **注意**: `VITE_` プレフィックスが付いた環境変数は Vite のビルド時にバンドルに埋め込まれます。環境変数を変更した場合は必ず再デプロイが必要です。

## 機能

- 37品目の価格データをリアルタイム表示（カード・グラフ・テーブル）
- 日別・月別・年別・年度別の期間切り替え
- 複数品目の比較チャート
- CSVダウンロード
- 「データを更新」ボタンによる手動スクレイピング実行（API接続時）
