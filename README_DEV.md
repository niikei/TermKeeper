# TermKeeper Development Guide

TermKeeperを開発・保守する人向けのガイドです。利用方法は
[README.md](README.md)、設計の詳細は
[アーキテクチャと拡張方針](docs/006_architecture.md)を参照してください。

## 必要環境

- Python 3.12以上
- [uv](https://docs.astral.sh/uv/)
- Git

## 開発環境の構築

```bash
git clone <repository-url>
cd TermKeeper
uv sync --extra dev
uv run tk init
```

`--extra dev`は実行時依存に加え、pytest、Ruff、Mypy、Pyright、MCP SDKをインストールします。
MCPサーバーだけを利用する場合は`uv sync --extra mcp`を使用できます。
HTTP APIだけを利用する場合は`uv sync --extra api`を使用できます。
TermKeeperを利用するだけなら`uv sync`で十分です。

作業用DBを明示すると、通常利用するDBとの混在を避けられます。

```bash
export TERMKEEPER_DATABASE_URL="sqlite:///$PWD/data/development.db"
uv run tk init
```

`tk init`はAlembicでDBを最新Revisionへ更新します。初期化に失敗した場合は
`uv run tk --debug init`で原因トレースを確認できます。
baselineをrebaseして既存開発DBを引き継がない場合は`uv run tk init --reset`を使用します。
SQLite DBは削除せずtimestamp付きbackupへ退避されます。

## ディレクトリ構成

```text
src/termkeeper/
├── domain/                 # DTO、Enum
├── application/
│   ├── service.py          # 公開ファサード
│   ├── use_cases/          # 照会・更新・状態遷移など責務別のユースケース
│   ├── mapping.py          # SQLModelレコードからDTOへの変換
│   ├── support.py          # Application層の共有処理
│   └── errors.py           # Application層の例外
├── infrastructure/
│   ├── repositories/       # 機能別Repository
│   └── ...                 # SQLModelテーブル、接続、Unit of Work
├── adapters/
│   ├── cli/
│   │   └── handlers/       # 人間向けの機能別CLI Handler
│   ├── external/           # HTTP・MCP共通の外部DTOとQuery変換
│   ├── http/
│   │   └── routes/         # FastAPIの機能別Route
│   └── mcp/
│       └── tools/          # MCPの機能別Tool
└── config.py               # 実行時設定
```

依存方向は次のとおりです。

```text
Presentation / API / MCP → Application → Infrastructure
                  Domain ← Application
```

外部アダプターはRepositoryやSQLModelテーブルを直接操作せず、`TermKeeperService`を呼び出します。

## 開発コマンド

### テスト

```bash
uv run pytest
```

pytestはカバレッジも計測します。全体カバレッジが90%未満になると失敗します。

特定のテストだけを実行する場合:

```bash
uv run pytest tests/application/test_search.py
uv run pytest tests/adapters/cli/test_cli.py::test_json_workflow
```

### フォーマットとLint

```bash
uv run ruff format .
uv run ruff check .
```

変更せずにフォーマット差分だけ確認する場合:

```bash
uv run ruff format --check .
```

### 型検査

```bash
uv run pyright
uv run mypy src
```

### パッケージビルド

```bash
uv build
```

プロジェクトのバージョンは`src/termkeeper/_version.py`で一元管理します。
Hatch、CLIの`tk --version`、Python APIの`termkeeper.__version__`はすべてこの値を参照します。
CLI起動時にパッケージメタデータを検索しないため、バージョン変更時はこのファイルだけを
更新してください。

## 変更時の推奨チェック

コミット前に次を実行します。

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run mypy src
uv run pytest
uv build
git diff --check
```

GitHub Actionsでも同じ品質検査をPython 3.12で実行し、pytestはPython 3.13・3.14でも
実行します。`develop`・`main`へのpushとPull Requestが対象です。

Ruffの警告は原則としてコード側で解消します。ルール除外は、フレームワークの制約やテストで
一般的な記法など、理由を説明できる場合に限定します。

## 実装方針

- 1つの更新ユースケースを1つのUnit of Workで完結させる
- Meaning統合はTerm行の監査情報を保持し、参照付け替えと削除を同一トランザクションで行う
- Tagは正規化名を一意にし、MeaningTagで多対多の関連を管理する
- CSV ImportはApplication層で全行を検証し、1つのUnit of Workで一括反映する
- Meaningの通常取得は論理削除済みを除外し、完全削除はTrash経由に限定する
- Captureは分類を行わず、OccurrenceをPendingとして保存する
- 単件・一括Captureは`CaptureUseCases.capture_many`を共有し、Adapterで`add`をループしない
- Meaningへの分類・再分類は利用者が明示し、候補検索には副作用を持たせない
- Scopeは独立エンティティとし、Meaningは`scope_id`で参照する
- Meaningは`scope_id`と正規化正式名称の組を有効データ内で一意にする
- Occurrence更新では正規化列と更新者・更新日時を同じUnit of Workで更新する
- Repository内では`commit()`しない
- 遭遇は毎回Occurrenceとして保存し、memoやsourceを上書きしない
- Occurrence一覧・検索の入力は`OccurrenceQuery`、出力は`Page[OccurrenceItem]`で表現する
- DB内部IDを外部連携の識別子にせず、Meaningの`public_id`を使用する
- Occurrence、Referenceも外部境界では`public_id`を使用する
- Occurrence／InboxはApplication層から共通ページ形式とし、DBでページングする
- HTTP/MCPの一覧はDB連番や内部ユーザーIDを返さない
- Meaning検索条件と結果は`SearchQuery`／`SearchHit`、Occurrence検索条件は
  `OccurrenceQuery`で表現し、CLI固有の型を持ち込まない
- Meaning検索のフィールドOR、smart modeの語ALL/ANY、exact／prefix／contains／glob／regexは
  `SearchUseCases`で一度だけ実装し、CLI・HTTP・MCPで同じ意味にする
- 正規表現検索はDB方言へ委譲せず、文字数・候補件数・照合時間に上限を設ける
- Meaningの一覧変換は`to_meanings`でScope・Term・Tagを一括取得し、ループ内で
  `to_meaning`を呼ばない
- 検索は軽量Documentを採点してから返却ページだけを完全DTOへhydrateする
- 一括CaptureはOccurrence単件処理をループせず、Meaning参照・候補検索・候補hydrateを一括する
- 検索応答は`SearchResult`で通常ヒットと類似候補を分離し、候補は0件時だけ計算する
- CLI固有の処理をApplication層へ持ち込まない
- APIやMCPを追加するときも既存のApplicationユースケースを再利用する
- `service.py`を肥大化させず、機能別の`use_cases/`へ実装する
- Meaningの照会・更新・Trash lifecycle、OccurrenceのCapture・分類状態遷移を混在させない
- 互換レイヤーは追加せず、必要になった時点で明示的なマイグレーションを設計する
- スキーマ変更はAlembic Revisionとして追加し、`tk init`で最新状態へupgradeする
- 適用済みRevisionは書き換えず、次のRevisionにforward migrationを追加する
- SQLModelを変更したら、初期Revisionとの一致テストまたは新しいRevisionの移行テストを追加する

## テスト方針

変更内容に応じて、適切な境界でテストします。

- Application: ユースケース、入力検証、トランザクションのロールバック
- Infrastructure: DB制約、Repository固有の契約
- Presentation: CLI終了コード、通常表示、JSON、CSV
- Performance: SQLクエリ数が入力件数に比例しないことをQuery Counterで検証

CSVの構文解析はPresentation、行検証・Dry Run・一括更新はApplicationの責務とする。
`terms`／`tags`セルはJSON文字列配列とし、Presentationで構文エラーを行issueへ変換する。

単に100%へ近づけるためのテストではなく、利用者に影響する分岐、外部連携境界、データ整合性を
優先します。

テストは一時DBを使用します。通常利用するユーザーデータ領域のDBは変更しません。

## 新しい機能を追加するとき

1. DTOや状態が必要なら`domain/`へ追加する
2. 永続化が必要ならSQLModelテーブルとRepositoryを更新する
3. トランザクションを含む操作を`application/use_cases/`へ追加する
4. CLIはApplicationのメソッドを呼ぶ薄いHandlerとして実装する
5. Applicationと外部境界のテストを追加する
6. ER図、CLI仕様、ユースケース文書を更新する

DBスキーマを変更した場合は、少なくとも
[ドメインモデル](docs/003_domain_model.md)のER図も更新してください。
既存データがあるRevisionを変更するときはDBを事前にバックアップし、実データを模したfixtureで
upgradeを検証してください。

## 関連ドキュメント

- [概要](docs/001_overview.md)
- [ユースケース](docs/002_use_cases.md)
- [ドメインモデル・ER図](docs/003_domain_model.md)
- [CLI仕様](docs/004_cli_spec.md)
- [MVPスコープ](docs/005_mvp_scope.md)
- [アーキテクチャと拡張方針](docs/006_architecture.md)
- [Windowsへのオフライン配布](docs/007_windows_distribution.md)
