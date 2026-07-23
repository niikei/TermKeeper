# 現在のスコープ

## 実装済み

- SQLModelとSQLiteによるローカル永続化
- Inboxの捕捉、一覧、履歴、破棄
- memoとsourceによる遭遇コンテキスト
- 同一未解決語の出現回数と最終確認日時
- 遭遇ごとのsource・memo・時刻を保持するOccurrence履歴
- Meaning・Inbox・keyword・source・期間によるOccurrence履歴の絞り込み
- 未解決Inboxと個別Occurrenceの編集、更新監査
- Meaningの作成、編集、一覧、詳細表示
- Termと別名の管理
- Meaning統合のDry Run、Term・Occurrence・Inbox移動
- Meaningの論理削除、Trash一覧、復元、完全削除
- Meaningへの複数Tag付与、一覧・検索のTag絞り込み
- Term・正式名称・説明の複数語検索、対象指定、関連度順、一致理由
- 検索0件時の類似候補、候補数指定、候補無効化
- 対話／非対話での解決と編集
- CSV Import／Export
- CSV ImportのDry Run、strict検証、行番号issue、全件トランザクション
- JSON出力
- `user.name` と `user.email` の設定管理
- UTCの作成・更新・最終確認・終了日時
- Meaning外部識別用UUIDとユーザー監査列
- Unit of Workによるユースケース単位のトランザクション
- Applicationサービスを介した外部アダプター向け境界

## 未実装

- AIによる意味候補生成
- HTTP API / FastAPI
- MCPサーバー
- Web UI
- Teams、Slack、メールなどからの自動捕捉
- Power Automate、SharePoint、Dataverse連携
- カテゴリ、関連用語
- URL、添付ファイル
- お気に入り
- 出現回数を利用した分析・ランキング・ダッシュボード
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
