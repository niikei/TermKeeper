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
- SQLite（SQLModel経由で利用）

## セットアップ

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
tk init
```

データベースは標準で `data/termkeeper.db` に保存されます。保存先は環境変数で変更できます。

```bash
TERMKEEPER_DB=~/Documents/terms.db tk inbox
```

## 基本的な使い方

### 捕捉

```bash
tk add ICMR --memo "月次決算会議" --source "Teams"
```

同じ未解決語を再度登録した場合、Inboxの重複行は作成せず、新しい遭遇履歴を記録します。
既にMeaningへ解決済みの場合は、登録済みのMeaningを表示します。

### 未処理項目の確認

```bash
tk inbox
tk inbox-edit 1 --keyword ERP
```

### 遭遇履歴

```bash
tk occurrences
tk occurrences --meaning 1
tk occurrences --inbox 2
tk occurrences --keyword MDM --source Slack
tk occurrences --since 2026-07-01 --limit 20
tk occurrence-edit 3 --memo "訂正後のメモ" --source Teams
tk occurrence-edit 3 --clear-memo
tk stats --limit 10
```

遭遇ごとの用語、memo、source、日時、Inbox／Meaningとの関連を確認できます。
未解決Inboxのkeywordと、個別Occurrenceのkeyword・memo・sourceを修正できます。
`stats`では総遭遇数、未解決数、Meaning数と、頻出語・出典を確認できます。

### 解決

対話形式:

```bash
tk resolve 1
```

非対話形式:

```bash
tk resolve 1 \
  --name "Intercompany Matching and Reconciliation" \
  --description "グループ間取引の照合"
```

### 検索と詳細表示

```bash
tk search ICMR
tk search "enterprise planning" --all
tk search "planning document" --any --in description --limit 10
tk search ERP --tag SAP
tk search ERPP --suggestions 3
tk search ERPP --no-suggestions
tk search ERP --favorite
tk show 1
tk meanings --tag SAP
tk meanings --favorite
```

検索は完全一致、前方一致、部分一致の順に関連度を付け、一致理由とともに表示します。
複数語は標準ですべての語に一致するMeaningを探します。`--any`でいずれかの語、
`--in term|name|description|all`で検索対象、`--limit`で最大件数を指定できます。
`--tag`を指定すると、そのタグを持つMeaningだけに絞り込みます。
`--favorite`を指定すると、お気に入りのMeaningだけに絞り込みます。
検索結果がない場合は、Term・正式名称などの類似度から候補を表示します。候補数は
`--suggestions`、無効化は`--no-suggestions`で指定できます。

### 整理

```bash
tk alias 1 ICMR
tk unalias 1 ICMR
tk edit 1 --name "Intercompany Matching and Reconciliation"
tk tag 1 SAP
tk untag 1 SAP
tk tags
tk favorite 1
tk unfavorite 1
tk relate 1 2
tk related 1
tk unrelate 1 2
tk reference-add 1 https://example.com/erp --title "ERP guide"
tk references 1
tk reference-edit 1 --title "Official ERP guide"
tk reference-remove 1
tk merge 2 1 --dry-run
tk merge 2 1
tk delete 1
tk trash
tk restore 1
tk purge 1
tk discard 2
tk history
```

`merge SOURCE TARGET`は、統合元のTerm、Tag、Occurrence、解決済みInboxを統合先へ移動し、
統合元Meaningを削除します。`--dry-run`では変更せず、移動件数だけを確認できます。

`relate A B`は2つのMeaningを双方向に関連付けます。`related ID`で関連Meaningを一覧表示し、
`unrelate A B`で関連を解除できます。

`reference-add`は調査資料などのHTTP/HTTPS URLをMeaningへ保存します。同じMeaningへの同一URLは
重複登録されません。`reference-edit`でURL・タイトルを修正し、`--clear-title`でタイトルを
消去できます。

`delete`はMeaningをTrashへ移す論理削除です。通常の一覧・検索・Term照合・CSV Exportから
除外されます。`restore`で復元し、`purge`でTrash内のMeaningを完全削除できます。

### CSV入出力

```bash
tk export terms.csv
tk import terms.csv --dry-run
tk import terms.csv
tk import terms.csv --strict
```

Importは全有効行を1トランザクションで反映します。`--dry-run`は作成・更新・スキップ件数と
行番号付き問題を表示するだけでDBを変更しません。`--strict`は問題が1行でもあれば全件を
拒否します。標準モードでは問題行をスキップし、有効行だけを一括反映します。

### ユーザー設定

```bash
tk config user.name "Taro Yamada"
tk config user.email taro@example.com
tk config user.name
tk config --list
tk config --unset user.email
```

設定はTermKeeperのデータベース単位で保存されます。

## JSON出力

主要コマンドは機械可読なJSONを出力できます。`--json` はサブコマンドより前に指定します。

```bash
tk --json search MDM
tk --json add BTP --source Slack
```

エラー時もJSON形式でエラー種別とメッセージを返し、終了コードは `2` になります。
検索JSONは`hits`と`suggestions`を持つオブジェクトです。

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

`TERMKEEPER_DB`でCLIと同じデータベースを指定できます。MCPクライアントには、サーバー起動
コマンドとして`tk-mcp`を登録してください。Capture、Inbox、Resolve、Search、Occurrence、
Stats、Tag、Favorite、Related Meaning、Referenceの20ツールを公開します。各ツールは具体的な
Domain DTOに基づく構造化出力スキーマを持ちます。

### HTTP API

```bash
uv sync --extra api
uv run tk-api
```

標準では`http://127.0.0.1:8000`で待ち受けます。OpenAPI仕様は`/openapi.json`、
対話的なAPIドキュメントは`/docs`で確認できます。現在はローカル利用向けで認証を持たないため、
外部ネットワークへ直接公開しないでください。
Inboxの捕捉・一覧・解決、Meaningの一覧・取得・更新・論理削除・Trash・復元、検索、統計を
`/api/v1`以下から利用できます。Meaningを指定するパスでは、DB内部の連番ではなくレスポンスの
`public_id`（UUID）を使用します。
Inboxを解決するパスでも、捕捉レスポンスに含まれるInboxの`public_id`を使用します。
Occurrence、Tag、Favorite、関連Meaning、Referenceの操作にも対応しています。外部レスポンスは
DB連番を含まず、一覧は`items`、`offset`、`limit`、`has_more`のページ形式です。

## データモデル

```text
INBOX ── resolves to ──> MEANING <── belongs to ── TERM
```

- Inbox: まだ整理していない用語と状態
- Occurrence: 用語へ遭遇した時刻、出典、メモの履歴
- Meaning: 利用者が理解したい意味
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
│   ├── adapters/        # MCPなどの外部プロトコル
│   ├── presentation/
│   │   ├── cli/         # CLI構築・表示・機能別Handler
│   │   └── csv_io.py    # CSV境界
│   └── config.py        # 実行時設定
├── tests/
├── data/
└── pyproject.toml
```

## 開発

セットアップ、テスト、Lint、型検査、実装方針は
[開発者ガイド](README_DEV.md)を参照してください。アーキテクチャの詳細は
[アーキテクチャと拡張方針](docs/006_architecture.md)に記載しています。
