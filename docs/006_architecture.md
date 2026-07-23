# アーキテクチャと拡張方針

依存方向は `Presentation / future API / future MCP → Application → Infrastructure`
とする。Domainは他レイヤーへ依存しない。

- `domain/`: 外部境界でも使えるシリアライズ可能なDTO
- `application/`: 公開Serviceファサード、機能別ユースケース、DTO変換、アプリケーション例外
- `infrastructure/`: SQLModelテーブル、Engine／Session、スキーマ作成
  - `repositories/`: Analytics、Occurrence、Meaningなど機能単位の永続化処理
- `presentation/`: 利用者との入出力境界
  - `cli/`: CLI引数、表示、CLI固有型
  - `cli/handlers/`: Capture、Meaning、Metadata、Config、Transfer単位のコマンド処理
  - `csv_io.py`: CSV入出力
- `adapters/`: 外部プロトコルからApplication Serviceへの変換
  - `external/`: HTTP・MCPで共有する外部DTO、ページング、Domain DTOからの変換
  - `http/`: FastAPIアプリケーション構築、リクエストモデル、機能別Route
  - `mcp/`: FastMCPサーバー構築、入力モデル、機能別Tool

各アダプターはレイヤーの公開モジュールを直接使用し、旧構成向けの互換モジュールは持たない。
CRUDと検索はSQLModelを使用し、スキーマ変更はAlembic Revisionで明示する。
Applicationの各更新ユースケースはUnit of Workを使用し、1つのSessionとトランザクションで
完結する。Repositoryはcommitせず、トランザクション境界をApplicationへ集約する。
Repositoryは`infrastructure/repositories/`へ集約し、テーブル・接続・Unit of Workとは
ディレクトリ上でも責務を分ける。
`TermKeeperService` 自体は薄いファサードとし、実装は `use_cases/capture.py`、
`use_cases/meaning.py`、`use_cases/merge.py`、`use_cases/occurrence.py`、
`use_cases/analytics.py`、`use_cases/relation.py`、`use_cases/reference.py`、`use_cases/tag.py`、
`use_cases/config.py` に分割する。
共有するレコード取得とDTO変換だけを`support.py` と `mapping.py` に置き、機能間の
直接呼び出しは避ける。

CLIの`main.py`はパース、Service初期化、エラー処理、JSON出力だけを担当する。
各コマンドの入出力変換は`presentation/cli/handlers/`へユースケース単位で配置し、
`registry.py`だけがコマンド名とHandlerの対応を管理する。
JSONモードは自動化向けの非対話境界とし、標準入力を読まず、標準出力には単一のJSON値だけを
書き出す。不足入力も構造化エラーへ変換する。

CSVファイルの読み取りはPresentationで`ImportRow`へ変換し、検証、Dry Run、既存UUIDの判定、
一括更新は`use_cases/importing.py`で行う。Import中のRepository操作は同じUnit of Workを
共有し、実行時エラーでは全件をロールバックする。
複数値セルはPresentationでJSON文字列配列へencode/decodeし、構文エラーを行番号付きissueへ
変換する。区切り文字による独自エスケープ規則は持たない。

Meaning Repositoryの通常取得は`deleted_at IS NULL`を共通条件とする。Trash操作だけが
削除済みMeaningを明示的に取得する。Meaning統合は参照移動後に統合元を完全削除するが、
利用者による通常削除は必ず論理削除とする。
Tag集計も有効Meaningだけを対象とし、削除・復元に応じて件数へ反映する。
Meaningは`scope_norm`と`full_name_norm`の組を有効行内で一意にし、同一製品・業務領域での
重複概念を防ぐ。同じTermは複数Meaningに属せるため、候補取得は全件を返す。
お気に入りはMeaningの属性として保持し、一覧・検索の絞り込みはRepositoryで行う。
Meaning間の関連は小さいIDを先にした対称ペアとして正規化し、同一ペアを一意に保つ。
参考URLはMeaning配下の独立エンティティとし、同一Meaning内でURLを一意に保つ。

検索はRepositoryで部分一致候補を取得し、Applicationで関連度を計算する。通常ヒットが0件の
場合だけ有効Meaningを読み込み、`SearchSuggestion`を生成する。Presentationは候補ロジックを
持たず、`SearchResult`を表示・JSON化する。

Captureは毎回OccurrenceをPendingで保存し、Term一致は候補として返すだけにする。Inboxは
Pending Occurrenceの読み取りビューであり永続テーブルを持たない。Meaningへの分類・再分類・
解除・破棄・再開はApplicationの明示ユースケースとする。
Capture時のkeyword、memo、sourceはApplication境界で前後空白を除去し、指定された空文字列を
拒否する。

出現分析はOccurrence、Meaningに対する読み取り専用の集約として実装する。集計SQLは
Repositoryへ閉じ込め、Applicationからは`StatsSummary`として返す。

APIやMCPを追加するときは `TermKeeperService` を再利用し、SQLやCLIの標準出力を直接
呼ばない。MCPはCapture、Pending一覧、分類・再分類・解除・破棄・再開、検索、統計、
Tag・Favorite・Related Meaning・Reference操作を型付きツールとして公開する。

MCPアダプターは公式Python SDKのFastMCPを使用し、標準入出力transportで提供する。
`TermKeeperMcpTools`は具体的なDomain DTOを返し、FastMCPが型注釈から構造化出力スキーマを
生成・検証する。検証・トランザクション・検索などの業務ロジックは`TermKeeperService`へ
委譲する。SDKは安定版v1系へ上限を設け、v2の破壊的変更を暗黙に取り込まない。
HTTP APIとMCPがMeaningを入力として受け取る場合は`public_id`（UUID）だけを使用する。
分類・Occurrence編集にはOccurrence自身の`public_id`を使用する。整数IDはローカルDBと
CLIだけで使用する。
Referenceの編集・削除にもReference自身の`public_id`を使用する。HTTP/MCPレスポンスは専用の
外部DTOへ変換し、DB連番や内部ユーザーIDを公開しない。
OccurrenceやReferenceの一覧変換では、関連Meaningの内部IDから`public_id`への対応を一括取得し、
項目ごとのRepository呼び出しを行わない。

外部の一覧応答は`items`、`offset`、`limit`、`has_more`を持つ共通ページ形式とする。
検索応答も同じページ情報を持ち、HTTPとMCPで境界の意味を統一する。
OccurrenceとInboxはApplication層のPageを共有し、Repositoryで`offset`と`limit + 1`を
適用する。全件取得後のsliceは行わない。

HTTPアダプターはFastAPIで`/api/v1`以下へ公開し、PydanticはHTTPリクエストの構文検証だけを
担当する。業務検証はApplicationへ委譲し、`ValidationError`を422、`NotFoundError`を404の
一貫したJSONエラーへ変換する。認証・認可を導入するまではlocalhost専用とする。
FastAPI/Pydanticの入力検証エラーも`ErrorResponse`へ変換し、`details`に入力位置、エラーコード、
メッセージを格納する。Application由来のエラーでは`details`を省略する。
RouteとMCP Toolは機能単位のモジュールへ分割し、アプリケーション／サーバーの構築モジュールは
登録とプロセス起動だけを担当する。

## 時刻

保存値は型付きUTC `datetime` とし、JSON／CSV境界でISO 8601へ変換する。表示側が必要に
応じてローカル時刻へ変換する。`created_at` は生成時刻、`updated_at` は内容または状態の更新時刻、
`occurred_at`は遭遇時刻、`resolved_at`と`discarded_at`は分類状態の変更時刻を表す。

## スキーマ管理

既定DBはOS標準のユーザーデータ領域へ保存し、カレントディレクトリには依存させない。
開発・テスト・外部アダプターでは`TERMKEEPER_DB`による明示パスを優先する。
`tk init` および各CLI起動時にAlembicを実行し、最新Revisionまでupgradeする。
現行モデルを`0001_initial`の初期ベースラインとする。各Revisionは固定DDLとして保持し、
スキーマ変更時は適用済みRevisionを書き換えず、新しいRevisionを追加して順番に適用する。
初期ベースラインは正式リリース前かつ既存DBを引き継がない期間に限りリベースできる。
SQLModel metadataと最新Revisionの差分をテストし、モデルだけを変更してMigrationを追加し忘れる
schema driftを防ぐ。既存データを移行するRevisionは、実際の旧スキーマとデータを模したfixtureで
upgradeを検証する。

Service初期化時のDBエラーは`InitializationError`へ変換する。CLIは通常、パスと復旧導線だけを
表示して終了コード`1`を返し、内部トレースバックは`--debug`指定時だけ表示する。
