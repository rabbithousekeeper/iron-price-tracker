# CLAUDE.md - プロジェクトルール（必ず守ること）

## PR作成ルール（変更禁止）
- PRのタイトル・説明文は必ず英語と日本語を併記すること
- 形式：英語タイトル / 日本語タイトル
- 説明文も英語セクションの直後に日本語訳を記載すること

### PRテンプレート例
```
タイトル：Add feature X / 機能Xを追加

## Summary / 概要
[English description]

## 概要（日本語）
[日本語での説明]

## Key Changes / 主な変更点
- Change A / 変更A
- Change B / 変更B
```

## 技術スタック
- バックエンド：Python + FastAPI
- データベース：Supabase（PostgreSQL直接接続）
- Garminデータ取得：garminconnect ライブラリ
- デプロイ：Render（Web Service + Cron Job）

## コーディングルール
- コメントは日本語で記載すること
- コミットメッセージは英語（GitHubの標準に従う）
