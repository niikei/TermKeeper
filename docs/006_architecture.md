# アーキテクチャと拡張方針

依存方向は `Presentation / future API / future MCP → Application → Infrastructure`
とする。Domainは他レイヤーへ依存しない。

- `domain/`: 外部境界でも使えるシリアライズ可能なDTO
- `application/`: 用語捕捉、解決、検索などのユースケース
- `infrastructure/`: SQLModelテーブル、Engine／Session、スキーマ作成、リポジトリ
- `presentation/`: CLI引数、コマンド処理、表示、CSV入出力

各アダプターはレイヤーの公開モジュールを直接使用し、旧構成向けの互換モジュールは持たない。
CRUD、検索、スキーマ作成はSQLModelを使用する。旧SQLiteスキーマとの自動互換性は持たない。

APIやMCPを追加するときは `TermKeeperService` を再利用し、SQLやCLIの標準出力を直接
呼ばない。MCPツールはまず `add`, `inbox`, `resolve`, `search`, `show` を1対1で公開する。

## 時刻

保存値はタイムゾーン付きUTCのISO 8601形式とする。表示側が必要に応じてローカル時刻へ
変換する。`created_at` は生成時刻、`updated_at` は内容または状態の更新時刻、
`last_seen_at` は同じ未解決語を最後に目にした時刻を表す。

## スキーマ管理

`tk init` および各CLI起動時に、SQLModelで新規テーブルを作成する。スキーマ変更が必要に
なった段階でAlembicなどの専用マイグレーション管理を導入する。
