# アーキテクチャと拡張方針

依存方向は `Presentation / future API / future MCP → Application → Infrastructure`
とする。Domainは他レイヤーへ依存しない。

- `domain/`: 外部境界でも使えるシリアライズ可能なDTO
- `application/`: 公開Serviceファサード、機能別ユースケース、DTO変換、アプリケーション例外
- `infrastructure/`: SQLModelテーブル、Engine／Session、スキーマ作成、リポジトリ
- `presentation/`: CLI引数、コマンド処理、表示、CSV入出力

各アダプターはレイヤーの公開モジュールを直接使用し、旧構成向けの互換モジュールは持たない。
CRUD、検索、スキーマ作成はSQLModelを使用する。旧SQLiteスキーマとの自動互換性や移行処理は
持たないため、本版は新規データベースを前提とする。
Applicationの各更新ユースケースはUnit of Workを使用し、1つのSessionとトランザクションで
完結する。Repositoryはcommitせず、トランザクション境界をApplicationへ集約する。
`TermKeeperService` 自体は薄いファサードとし、実装は `use_cases/inbox.py`、
`use_cases/meaning.py`、`use_cases/merge.py`、`use_cases/occurrence.py`、
`use_cases/tag.py`、`use_cases/config.py` に分割する。
共有するレコード取得とDTO変換だけを`support.py` と `mapping.py` に置き、機能間の
直接呼び出しは避ける。

CSVファイルの読み取りはPresentationで`ImportRow`へ変換し、検証、Dry Run、既存UUIDの判定、
一括更新は`use_cases/importing.py`で行う。Import中のRepository操作は同じUnit of Workを
共有し、実行時エラーでは全件をロールバックする。

APIやMCPを追加するときは `TermKeeperService` を再利用し、SQLやCLIの標準出力を直接
呼ばない。MCPツールはまず `add`, `inbox`, `occurrences`, `resolve`, `search`, `show`,
`merge`, `tag`, `untag`, `tags` を1対1で公開する。

## 時刻

保存値は型付きUTC `datetime` とし、JSON／CSV境界でISO 8601へ変換する。表示側が必要に
応じてローカル時刻へ変換する。`created_at` は生成時刻、`updated_at` は内容または状態の更新時刻、
`last_seen_at` は同じ未解決語を最後に目にした時刻を表す。

## スキーマ管理

`tk init` および各CLI起動時に、SQLModelで新規テーブルを作成する。スキーマ変更が必要に
なった段階でAlembicなどの専用マイグレーション管理を導入する。
