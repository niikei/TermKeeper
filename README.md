# TermKeeper

知らない言葉をその場で捕捉し、後から意味を整理するためのCLIツールです。

```text
会議中は登録だけ → 後で調査・整理 → 必要なときに検索
```

完璧な用語集を作ることではなく、知らない言葉を取りこぼさないことを重視します。

開発環境の構築や品質チェックについては
[開発者ガイド](README_DEV.md)を参照してください。

## 必要環境

- Python 3.12以上
- SQLite（既定）またはSQLAlchemy URLで指定したデータベース

## セットアップ

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
tk init
```

GitHubへ接続できないWindows環境へwheel、完全オフライン一式、またはソースZIPで
配布する場合は、[Windowsへのオフライン配布](docs/007_windows_distribution.md)を
参照してください。ソースディレクトリを直接`PATH`へ追加する運用は推奨しません。

データベースはOS標準のユーザーデータ領域に保存されます。macOSでは通常
`~/Library/Application Support/TermKeeper/termkeeper.db`です。保存先は環境変数で変更できます。
旧既定値の`data/termkeeper.db`は自動移行しません。継続利用する場合は
`TERMKEEPER_DATABASE_URL`で明示してください。

```bash
TERMKEEPER_DATABASE_URL=sqlite:////absolute/path/terms.db tk inbox
```

PostgreSQLを使用する場合は任意依存と接続URLを指定します。

```bash
uv sync --extra postgres
TERMKEEPER_DATABASE_URL=postgresql+psycopg://user:password@localhost/termkeeper tk init
```

### DBの初期化

`tk init`は現行スキーマの新しいDBを作成します。各コマンドも起動時に同じ初期化を行うため、
通常は最初のコマンド実行時に自動作成されます。初期化に失敗した場合、技術的な原因は
`tk --debug init`で確認できます。

開発中にAlembic baselineを作り直したDBなど、Revision記録と実際のテーブル構造が一致しない
場合は、通常起動時に不一致を検出して復旧方法を表示します。既存データを引き継がずSQLite DBを
作り直す場合は次を実行します。

```bash
tk init --reset
```

確認後、既存DBを同じディレクトリの`*.backup-<timestamp>.db`へ退避してから新規作成します。
自動化では`tk init --reset --yes`を使用します。PostgreSQLの自動resetには対応しません。

## 基本的な使い方

引数なしでバージョン、現在の状態、次の操作を確認できます。

```bash
tk
```

インストールされているTermKeeperのバージョンを確認できます。

```bash
tk --version
```

コマンドを日常操作・管理・システムに分けたガイドと、個別のオプション・実行例を確認できます。

```bash
tk --help
tk meaning --help
tk add --help
```

### 捕捉

```bash
tk add ICMR --memo "月次決算会議" --source "Teams"
```

`add`は毎回独立したOccurrenceを未分類状態で保存します。同じ表記のMeaningが存在しても
自動では紐付けず、分類候補として表示します。対話端末では候補をその場で選択でき、Enterなら
PendingのままInboxへ残します。JSON、パイプ入力、`--no-prompt`では入力待ちしません。
分類先が事前に明らかな場合は`--meaning ID`で明示できます。
対話端末ではID、Scope、状態、成功・警告・エラーなどを意味に応じて色分けします。
`--color=auto|always|never`で制御でき、`auto`がデフォルトです。常に無効にする場合は
`NO_COLOR=1 tk add TERM`のようにも指定できます。JSONと非TTY出力は通常プレーンテキストです。

複数の遭遇をまとめて捕捉するときは、位置引数を並べず`add-many`を使用します。

```bash
tk add-many
tk add-many --term ERP --term CRM
tk add-many --file terms.txt
pbpaste | tk add-many --file - --yes
```

引数なしでは1行1用語の対話入力と登録前確認を行います。`--file`も1行1用語のUTF-8形式です。
`--term`と`--file`は排他的で、`--memo`と`--source`は全件へ適用されます。空入力、空行、
正規化後の重複、100件超を拒否し、1件でも不正なら何も登録しません。JSONモードは対話入力を
行わないため、`--term`または`--file`が必要です。

### 登録済み用語の一覧

```bash
tk list
tk list --scope SAP
tk list --tag Core
tk list --tag Core --tag SAP --tag-match all
tk list --favorite
tk list --has-description --has-alias --sort name --order asc
tk list --updated-since 2026-07-01T00:00:00Z
```

`list`はActive Meaningを`ID / Meaning / Scope / Aliases`のコンパクトな表で表示する日常用ビュー
です。繰り返した`--tag`は`--tag-match all|any`で結合します。説明・Aliasの有無、作成・更新日時、
並び順、ページ位置でも絞り込めます。`tk meaning list`は同じ絞り込みで詳細を表示し、
`tk show ID`は1件を表示します。

### 未処理項目の確認

```bash
tk inbox
```

Inboxは独立したテーブルではなく、未分類（Pending）のOccurrence一覧です。

### 遭遇履歴

```bash
tk history
tk occurrence list
tk occurrence list --meaning 1
tk occurrence list --status Pending
tk occurrence list --keyword MDM --source Slack
tk occurrence list --since 2026-07-01 --limit 20
tk occurrence list --offset 20 --limit 20
tk occurrence edit 3 --memo "訂正後のメモ" --source Teams
tk occurrence edit 3 --clear-memo
tk stats --limit 10
```

遭遇ごとの用語、memo、source、状態、日時、Meaningとの関連を確認できます。
個別Occurrenceのkeyword・memo・sourceを修正できます。
`inbox`、`history`、`occurrence list`は`--offset`と`--limit`に対応します。
一覧はDBでページングされ、
JSON出力は`items`、`offset`、`limit`、`has_more`を返します。
`stats`では総遭遇数、未解決数、Meaning数と、頻出語・出典を確認できます。

### 解決

Meaningを製品・組織・業務領域で分離する場合は、先にScopeを登録します。

```bash
tk scope add Finance --description "財務・連結領域"
tk scope list
```

対話形式:

```bash
tk resolve 1
```

遭遇語に一致するMeaningがある場合は候補を表示します。候補が1件ならEnterでそのMeaningへ
分類でき、`n`で別概念として新しいMeaningを作成、`q`でキャンセルできます。候補が複数ある場合は
表示されたMeaning IDを選択します。候補がない場合だけ正式名称と説明を入力します。

非対話形式:

```bash
tk resolve 1 \
  --name "Intercompany Matching and Reconciliation" \
  --scope "Finance" \
  --description "グループ間取引の照合"
```

既存Meaningへ分類する場合:

```bash
tk resolve 1 --meaning 12
```

`--json`では入力待ちを行いません。新しいMeaningを作る場合は`--name`を必ず指定してください。
`--scope`は登録済みのScope名を指定します。省略時は初期登録される`General`です。

分類は後から安全に修正できます。

```bash
tk occurrence unresolve 1
tk occurrence discard 1
tk occurrence reopen 1
```

### 検索と詳細表示

```bash
tk search ICMR
tk meaning search ICMR
tk search "enterprise planning"
tk search "planning document" --word-match any --field description --limit 10
tk search ERP --field term --field name
tk search "ERP*" --mode glob --field term
tk search '^ERP-[0-9]+$' --mode regex --field term
tk search ERP --tag SAP
tk search ERP --scope SAP
tk search ERPP --suggestions 3
tk search ERPP --no-suggestions
tk search ERP --favorite
tk occurrence search planning --status Pending --source Teams
tk inbox search planning --source Teams
tk scope search platform
tk show 1
tk meaning list --tag SAP
tk meaning list --scope SAP
tk meaning list --favorite
```

`tk search`は`tk meaning search`の短縮形です。標準の`--mode smart`は完全一致、前方一致、
部分一致の順に関連度を付け、一致理由とともに表示します。複数語は標準ですべての語を必要とし、
`--word-match any`ならいずれかの語を探します。
`--field term|name|description`は繰り返し指定でき、指定フィールド間はORです。たとえば
`--field term --field description --word-match all`では、各検索語がTermまたは説明の
どちらかにあれば一致します。
`--mode exact|prefix|contains|glob|regex`では検索文字列を分割せず、各フィールド全体に対して
指定方式で照合します。globや正規表現はシェル展開を避けるため引用符で囲んでください。
`--limit`で最大件数を指定できます。
`--tag`を指定すると、そのタグを持つMeaningだけに絞り込みます。
`--scope`を指定すると、SAP、Oracle、Generalなどの概念境界で絞り込みます。
`--favorite`を指定すると、お気に入りのMeaningだけに絞り込みます。
smart検索で結果がない場合は、Term・正式名称などの類似度から候補を表示します。候補数は
`--suggestions`、無効化は`--no-suggestions`で指定できます。
Occurrence検索はkeyword、memo、sourceを横断し、status、source、since、Meaningで先に
絞り込めます。`tk inbox search`は同じ検索をPendingだけに限定します。Scope検索は名前と説明を
対象にします。

### 整理

```bash
tk meaning alias-add 1 ICMR
tk meaning alias-remove 1 ICMR
tk meaning edit 1 --name "Intercompany Matching and Reconciliation" --scope Finance
tk meaning edit 1 --clear-description
tk tag add 1 SAP
tk tag remove 1 SAP
tk tag list
tk meaning favorite 1
tk meaning unfavorite 1
tk meaning relate 1 2
tk meaning related 1
tk meaning unrelate 1 2
tk reference add 1 https://example.com/erp --title "ERP guide"
tk reference list 1
tk reference edit 1 --title "Official ERP guide"
tk reference remove 1
tk meaning merge 2 1 --dry-run
tk meaning merge 2 1 --yes
tk meaning delete 1
tk meaning trash
tk meaning restore 1
tk meaning purge 1 --yes
tk occurrence discard 2
tk history
```

`meaning edit`は指定した項目だけを更新し、省略した項目は現在値を維持します。
引数なしの通常実行では対話入力に切り替わりますが、JSONモードでは更新項目を1つ以上
指定してください。説明の削除には`--clear-description`を使います。

`meaning merge SOURCE TARGET`は、統合元のTerm、Tag、Occurrence、Reference、Relationを統合先へ移動し、
統合元Meaningを削除します。同一URLのReferenceと同一関連先のRelationは重複排除され、
sourceとtargetの直接Relationは自己Relationになるため畳み込まれます。`--dry-run`では変更せず、
移動・重複排除・畳み込み件数を確認できます。実行時は確認に応答するか`--yes`を指定します。

`meaning relate A B`は2つのMeaningを双方向に関連付けます。`meaning related ID`で
関連Meaningを一覧表示し、`meaning unrelate A B`で関連を解除できます。

`reference add`は調査資料などのHTTP/HTTPS URLをMeaningへ保存します。同じMeaningへの同一URLは
重複登録されません。`reference edit`でURL・タイトルを修正し、`--clear-title`でタイトルを消去できます。

`meaning delete`はMeaningをTrashへ移す論理削除です。通常の一覧・検索・Term照合・CSV Exportから
除外されます。`meaning restore`で復元できます。分類履歴を保護するため、Occurrenceから参照される
Meaningは`meaning purge`できません。先に該当Occurrenceを`occurrence unresolve`または
再分類してください。完全削除には確認または`--yes`が必要です。

### CSV入出力

```bash
tk data export terms.csv
tk data import terms.csv --dry-run
tk data import terms.csv
tk data import terms.csv --strict
```

Importは全有効行を1トランザクションで反映します。`--dry-run`は作成・更新・スキップ件数と
行番号付き問題を表示するだけでDBを変更しません。`--strict`は問題が1行でもあれば全件を
拒否します。標準モードでは問題行をスキップし、有効行だけを一括反映します。
`terms`と`tags`のセルはJSON文字列配列です（例: `["ERP","SAP;Legacy"]`）。これにより、
セミコロン、カンマ、引用符、Unicodeを含むalias／tagも欠損なく往復できます。

### ユーザー設定

```bash
tk config user.name "Taro Yamada"
tk config user.email taro@example.com
tk config user.name
tk config --list
tk config --unset user.email
```

設定はTermKeeperのデータベース単位で保存されます。

### 診断とシェル補完

```bash
tk doctor
source <(tk completion zsh)
source <(tk completion bash)
tk completion fish | source
```

`doctor`はバージョン、資格情報を隠したDB接続先、backend、Alembic Revision、
`user.name`・`user.email`の設定有無を確認します。
DB接続またはスキーマに問題がある場合は終了コード`1`を返すため、監視にも利用できます。

## JSON出力

主要コマンドは機械可読なJSONを出力できます。`--json`はコマンドの前後どちらにも指定できます。

```bash
tk --json search MDM
tk add BTP --source Slack --json
```

JSONモードは完全に非対話で、標準入力を要求せず、標準出力にはJSONだけを出力します。
必須の入力が不足した場合もJSON形式でエラー種別とメッセージを返し、終了コードは `2` になります。
Meaning検索JSONは`hits`と`suggestions`を持つオブジェクトです。Occurrence、Inbox、Scopeの
検索JSONは`items`、`offset`、`limit`、`has_more`を持つページ形式です。

## Python APIとMCP連携

CLIを介さず、Application層のサービスを利用できます。

```python
from termkeeper import TermKeeperService

service = TermKeeperService()
service.initialize()
result = service.add("BTP", source="Slack")
```

HTTP APIなどの外部アダプターも、このサービスを直接呼び出します。

### MCPサーバー

MCP用依存を追加してインストールします。

```bash
pip install -e ".[mcp]"
```

ローカルの標準入出力サーバーを起動するコマンドは次のとおりです。

```bash
tk-mcp
```

`TERMKEEPER_DATABASE_URL`でCLIと同じデータベースを指定できます。MCPクライアントには、
サーバー起動コマンドとして`tk-mcp`を登録してください。単件`capture_term`と原子的な
1〜100件の`capture_terms`、分類・再分類、Meaning・
Occurrence・Inbox・Scope検索、Stats、Tag、Favorite、Related Meaning、Referenceなどの
型付きツールを公開します。
各ツールは具体的なDomain DTOに基づく構造化出力スキーマを持ちます。

### HTTP API

```bash
uv sync --extra api
uv run tk init
uv run tk-api
```

標準では`http://127.0.0.1:8000`で待ち受けます。OpenAPI仕様は`/openapi.json`、
対話的なAPIドキュメントは`/docs`で確認できます。現在はローカル利用向けで認証を持たないため、
外部ネットワークへ直接公開しないでください。
APIプロセスは起動時にMigrationを実行しません。デプロイ時は`tk init`を先に実行し、
`/ready`が成功してからトラフィックを流してください。
`/health`はプロセスの生存確認、`/ready`はDB接続とスキーマを含む受付可能性の確認に使用します。
`POST /api/v1/occurrences`の単件捕捉と`POST /api/v1/occurrences/batch`の原子的な一括捕捉、
未分類一覧・分類・再分類、Meaningの一覧・取得・更新・論理削除・Trash・復元、
Meaning・Occurrence・Inbox・Scope検索、統計を`/api/v1`以下から利用できます。Meaningを
指定するパスでは、DB内部の連番ではなく
レスポンスの
`public_id`（UUID）を使用します。
分類パスでは、捕捉レスポンスに含まれるOccurrenceの`public_id`を使用します。
Tag、Favorite、関連Meaning、Referenceの操作にも対応しています。外部レスポンスは
DB連番を含まず、一覧は`items`、`offset`、`limit`、`has_more`のページ形式です。
Scopeは`/api/v1/scopes`で管理し、HTTP/MCPからMeaningのScopeを指定するときはScopeの
`public_id`（UUID）を使用します。
MCPでは`list_meanings`で検索語なしのMeaning巡回、`search_meanings`で関連度付き検索を
使い分けます。どちらも`has_more`が真なら、現在の`offset`に返却件数を足して次ページを
取得します。
Meaningの作成・編集・Alias追加削除・論理削除・Trash確認・復元も型付きMCPツールで行えます。
不可逆なpurgeはAI向けツールとして公開せず、人間がCLIで明示確認して実行します。

検索エンドポイントは`/api/v1/meanings/search`、`/api/v1/occurrences/search`、
`/api/v1/inbox/search`、`/api/v1/scopes/search`です。

## データモデル

```text
SCOPE ──> MEANING <── TERM
           ↑
OCCURRENCE
```

- Inbox: Pending状態のOccurrenceを表示する作業ビュー
- Occurrence: 用語へ遭遇した時刻、出典、メモ、分類状態の履歴
- Scope: SAPや業務領域など、Meaningを区別する管理対象の名前空間
- Meaning: 利用者が理解したい概念。必ず1つのScopeに属する
- Term: 略語、正式名称、別名などMeaningを検索するための語

詳細は [ドメインモデル](docs/003_domain_model.md) を参照してください。

## プロジェクト構成

```text
TermKeeper/
├── docs/
├── src/termkeeper/
│   ├── domain/          # DTOとドメインモデル
│   ├── application/     # ユースケース
│   ├── infrastructure/  # SQLModel tables・Session
│   │   └── repositories/ # 機能別Repository
│   ├── adapters/
│   │   ├── cli/         # CLI構築・表示・CSV・機能別Handler
│   │   ├── external/    # HTTP・MCP共通の外部DTOとQuery変換
│   │   ├── http/        # FastAPI app・機能別Route
│   │   └── mcp/         # MCP server・機能別Tool
│   └── config.py        # 実行時設定
├── tests/
├── data/
└── pyproject.toml
```

## 開発

セットアップ、テスト、Lint、型検査、実装方針は
[開発者ガイド](README_DEV.md)を参照してください。アーキテクチャの詳細は
[アーキテクチャと拡張方針](docs/006_architecture.md)に記載しています。
