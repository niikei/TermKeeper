# アーキテクチャと拡張方針

依存方向は `Presentation / future API / future MCP → Application → Infrastructure`
とする。Domainは他レイヤーへ依存しない。

- `domain/`: 外部境界でも使えるシリアライズ可能なDTO
- `application/`: 公開Serviceファサード、機能別ユースケース、DTO変換、アプリケーション例外
- `infrastructure/`: SQLModelテーブル、Engine／Session、スキーマ作成
  - `repositories/`: Analytics、Inbox、Meaningなど機能単位の永続化処理
- `presentation/`: 利用者との入出力境界
  - `cli/`: CLI引数、表示、CLI固有型
  - `cli/handlers/`: Capture、Meaning、Metadata、Config、Transfer単位のコマンド処理
  - `csv_io.py`: CSV入出力
- `adapters/`: MCPなど外部プロトコルからApplication Serviceへの変換

各アダプターはレイヤーの公開モジュールを直接使用し、旧構成向けの互換モジュールは持たない。
CRUD、検索、スキーマ作成はSQLModelを使用する。旧SQLiteスキーマとの自動互換性や移行処理は
持たないため、本版は新規データベースを前提とする。
Applicationの各更新ユースケースはUnit of Workを使用し、1つのSessionとトランザクションで
完結する。Repositoryはcommitせず、トランザクション境界をApplicationへ集約する。
Repositoryは`infrastructure/repositories/`へ集約し、テーブル・接続・Unit of Workとは
ディレクトリ上でも責務を分ける。
`TermKeeperService` 自体は薄いファサードとし、実装は `use_cases/inbox.py`、
`use_cases/meaning.py`、`use_cases/merge.py`、`use_cases/occurrence.py`、
`use_cases/analytics.py`、`use_cases/relation.py`、`use_cases/reference.py`、`use_cases/tag.py`、
`use_cases/config.py` に分割する。
共有するレコード取得とDTO変換だけを`support.py` と `mapping.py` に置き、機能間の
直接呼び出しは避ける。

CLIの`main.py`はパース、Service初期化、エラー処理、JSON出力だけを担当する。
各コマンドの入出力変換は`presentation/cli/handlers/`へユースケース単位で配置し、
`registry.py`だけがコマンド名とHandlerの対応を管理する。

CSVファイルの読み取りはPresentationで`ImportRow`へ変換し、検証、Dry Run、既存UUIDの判定、
一括更新は`use_cases/importing.py`で行う。Import中のRepository操作は同じUnit of Workを
共有し、実行時エラーでは全件をロールバックする。

Meaning Repositoryの通常取得は`deleted_at IS NULL`を共通条件とする。Trash操作だけが
削除済みMeaningを明示的に取得する。Meaning統合は参照移動後に統合元を完全削除するが、
利用者による通常削除は必ず論理削除とする。
お気に入りはMeaningの属性として保持し、一覧・検索の絞り込みはRepositoryで行う。
Meaning間の関連は小さいIDを先にした対称ペアとして正規化し、同一ペアを一意に保つ。
参考URLはMeaning配下の独立エンティティとし、同一Meaning内でURLを一意に保つ。

検索はRepositoryで部分一致候補を取得し、Applicationで関連度を計算する。通常ヒットが0件の
場合だけ有効Meaningを読み込み、`SearchSuggestion`を生成する。Presentationは候補ロジックを
持たず、`SearchResult`を表示・JSON化する。

InboxとOccurrenceの編集はApplicationで状態・重複・入力競合を検証し、Repositoryで正規化列と
更新監査列を同時に変更する。InboxとOccurrenceは別の履歴境界として扱い、一方の編集を他方へ
暗黙に波及させない。

出現分析はOccurrence、Inbox、Meaningに対する読み取り専用の集約として実装する。集計SQLは
Repositoryへ閉じ込め、Applicationからは`StatsSummary`として返す。

APIやMCPを追加するときは `TermKeeperService` を再利用し、SQLやCLIの標準出力を直接
呼ばない。MCPは`capture_term`, `list_inbox`, `resolve_inbox`, `search_meanings`,
`get_meaning`, `list_occurrences`, `get_stats`, Tag・Favorite・Related Meaning・Reference
操作の計17ツールを公開する。

MCPアダプターは公式Python SDKのFastMCPを使用し、標準入出力transportで提供する。
`TermKeeperMcpTools`は具体的なDomain DTOを返し、FastMCPが型注釈から構造化出力スキーマを
生成・検証する。検証・トランザクション・検索などの業務ロジックは`TermKeeperService`へ
委譲する。SDKは安定版v1系へ上限を設け、v2の破壊的変更を暗黙に取り込まない。
HTTP APIとMCPがMeaningを入力として受け取る場合は`public_id`（UUID）だけを使用する。
整数の`meaning_id`はローカルDBとCLI向けの識別子とし、外部クライアントの参照には使用しない。

HTTPアダプターはFastAPIで`/api/v1`以下へ公開し、PydanticはHTTPリクエストの構文検証だけを
担当する。業務検証はApplicationへ委譲し、`ValidationError`を422、`NotFoundError`を404の
一貫したJSONエラーへ変換する。認証・認可を導入するまではlocalhost専用とする。

## 時刻

保存値は型付きUTC `datetime` とし、JSON／CSV境界でISO 8601へ変換する。表示側が必要に
応じてローカル時刻へ変換する。`created_at` は生成時刻、`updated_at` は内容または状態の更新時刻、
`last_seen_at` は同じ未解決語を最後に目にした時刻を表す。

## スキーマ管理

`tk init` および各CLI起動時に、SQLModelで新規テーブルを作成する。スキーマ変更が必要に
なった段階でAlembicなどの専用マイグレーション管理を導入する。
