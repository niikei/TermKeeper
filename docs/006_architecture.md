# アーキテクチャと拡張方針

依存方向は `Presentation / future API / future MCP → Application → Infrastructure`
とする。Domainは他レイヤーへ依存しない。

- `domain/`: 外部境界でも使えるシリアライズ可能なDTO
- `application/`: 用語捕捉、解決、検索などのユースケース
- `infrastructure/`: SQLite接続、スキーマ更新、Inbox・Meaning別リポジトリ
- `presentation/`: CLI引数、コマンド処理、表示、CSV入出力

トップレベルの `cli.py`, `db.py`, `models.py`, `service.py` は既存利用者のimportを壊さない
ための互換モジュールであり、新規コードは各レイヤーのパッケージを直接使用する。

APIやMCPを追加するときは `TermKeeperService` を再利用し、SQLやCLIの標準出力を直接
呼ばない。MCPツールはまず `add`, `inbox`, `resolve`, `search`, `show` を1対1で公開する。

## 時刻

保存値はタイムゾーン付きUTCのISO 8601形式とする。表示側が必要に応じてローカル時刻へ
変換する。`created_at` は生成時刻、`updated_at` は内容または状態の更新時刻、
`last_seen_at` は同じ未解決語を最後に目にした時刻を表す。

## マイグレーション

`tk init` および各CLI起動時に、既存データを保持したまま追加可能な変更を適用する。
複雑な変更が必要になった段階で、連番付きマイグレーションテーブルへ移行する。
