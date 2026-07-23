# 現在のスコープ

## 実装済み

- SQLModelとSQLiteによる既定のローカル永続化、DB URLによる接続切り替え
- Occurrenceの捕捉、Pending Inboxビュー、分類、再分類、破棄、再開
- memoとsourceによる遭遇コンテキスト
- 遭遇ごとのsource・memo・時刻を保持するOccurrence履歴
- Meaning・状態・keyword・source・期間によるOccurrence履歴の絞り込み
- 個別Occurrenceの編集、分類監査
- 総遭遇数と頻出語・出典の分析、ランキング
- Meaningの作成、編集、一覧、詳細表示
- Termと別名の管理
- Meaning統合のDry Run、Term・Occurrence移動
- Meaning scopeとscope内の重複防止・検索絞り込み
- Meaningの論理削除、Trash一覧、復元、完全削除
- Meaningへの複数Tag付与、一覧・検索のTag絞り込み
- Meaningのお気に入り登録、一覧・検索の絞り込み
- Meaning同士の双方向関連付け、解除、一覧
- Meaningの参考URL追加、編集、一覧、削除
- Term・正式名称・説明の複数語検索、対象指定、関連度順、一致理由
- 検索0件時の類似候補、候補数指定、候補無効化
- 対話／非対話での解決と編集
- CSV Import／Export
- CSV ImportのDry Run、strict検証、行番号issue、全件トランザクション
- JSON出力
- `user.name` と `user.email` の設定管理
- UTCの作成・更新・遭遇・分類・破棄日時
- Meaning外部識別用UUIDとユーザー監査列
- Unit of Workによるユースケース単位のトランザクション
- Applicationサービスを介した外部アダプター向け境界
- 公式Python SDKによる標準入出力MCPサーバー、24ツール
- FastAPIによるローカルHTTP API、OpenAPI仕様、統一エラー応答
- Meaning、Occurrence、Referenceの外部UUID
- HTTP／MCPの内部IDを含まない構造化応答と共通ページネーション
- AlembicによるスキーマRevision管理

## 未実装

- AIによる意味候補生成
- Web UI
- Teams、Slack、メールなどからの自動捕捉
- Power Automate、SharePoint、Dataverse連携
- カテゴリ
- 添付ファイル
- Webダッシュボード
- 同期、複数ユーザー、認証・認可

## 拡張順序

```text
Application Service
├── CLI（実装済み）
├── MCP adapter（実装済み）
├── HTTP API（実装済み）
└── Web / collaboration adapters
```

外部連携ではCLI出力やデータベースを直接操作せず、`TermKeeperService` を利用する。
