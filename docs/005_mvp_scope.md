# 現在のスコープ

## 実装済み

- SQLModelとSQLiteによるローカル永続化
- Inboxの捕捉、一覧、履歴、破棄
- memoとsourceによる遭遇コンテキスト
- 同一未解決語の出現回数と最終確認日時
- Meaningの作成、編集、一覧、詳細表示
- Termと別名の管理
- Term・正式名称・説明の検索
- 対話／非対話での解決と編集
- CSV Import／Export
- JSON出力
- `user.name` と `user.email` の設定管理
- UTCの作成・更新・最終確認・終了日時
- Applicationサービスを介した外部アダプター向け境界

## 未実装

- AIによる意味候補生成
- HTTP API / FastAPI
- MCPサーバー
- Web UI
- Teams、Slack、メールなどからの自動捕捉
- Power Automate、SharePoint、Dataverse連携
- タグ、カテゴリ、関連用語
- URL、添付ファイル
- お気に入り
- 出現回数を利用した分析・ランキング・ダッシュボード
- Meaningの統合・削除
- 同期、複数ユーザー、認証・認可

## 拡張順序

```text
Application Service
├── CLI（実装済み）
├── MCP adapter
├── HTTP API
└── Web / collaboration adapters
```

外部連携ではCLI出力やSQLiteを直接操作せず、`TermKeeperService` を利用する。
