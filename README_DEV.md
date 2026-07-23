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
export TERMKEEPER_DB="$PWD/data/development.db"
uv run tk init
```

現在のスキーマは旧DBとの互換性や自動マイグレーションを持ちません。スキーマ変更を試す際は、
使い捨ての新規DBを使用してください。

## ディレクトリ構成

```text
src/termkeeper/
├── domain/                 # DTO、Enum
├── application/
│   ├── service.py          # 公開ファサード
│   ├── use_cases/          # inbox、meaning、merge、occurrence、tag、configのユースケース
│   ├── mapping.py          # SQLModelレコードからDTOへの変換
│   ├── support.py          # Application層の共有処理
│   └── errors.py           # Application層の例外
├── infrastructure/
│   ├── repositories/       # 機能別Repository
│   └── ...                 # SQLModelテーブル、接続、Unit of Work
├── presentation/
│   ├── cli/
│   │   └── handlers/       # 機能別CLI Handler
│   └── csv_io.py           # CSV境界
├── adapters/
│   ├── external/           # HTTP・MCP共通の外部DTOと変換
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
uv run pytest tests/presentation/test_cli.py::test_json_workflow
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

Ruffの警告は原則としてコード側で解消します。ルール除外は、フレームワークの制約やテストで
一般的な記法など、理由を説明できる場合に限定します。

## 実装方針

- 1つの更新ユースケースを1つのUnit of Workで完結させる
- Meaning統合はTerm行の監査情報を保持し、参照付け替えと削除を同一トランザクションで行う
- Tagは正規化名を一意にし、MeaningTagで多対多の関連を管理する
- CSV ImportはApplication層で全行を検証し、1つのUnit of Workで一括反映する
- Meaningの通常取得は論理削除済みを除外し、完全削除はTrash経由に限定する
- Inbox・Occurrence更新では正規化列と更新者・更新日時を同じUnit of Workで更新する
- Repository内では`commit()`しない
- 遭遇は毎回Occurrenceとして保存し、memoやsourceを上書きしない
- Occurrence一覧の入力は`OccurrenceQuery`、出力は`OccurrenceItem`で表現する
- DB内部IDを外部連携の識別子にせず、Meaningの`public_id`を使用する
- Inbox、Occurrence、Referenceも外部境界では`public_id`を使用する
- HTTP/MCPの一覧は共通ページ形式とし、DB連番や内部ユーザーIDを返さない
- 検索条件と結果は`SearchQuery`／`SearchHit`で表現し、CLI固有の型を持ち込まない
- 検索応答は`SearchResult`で通常ヒットと類似候補を分離し、候補は0件時だけ計算する
- CLI固有の処理をApplication層へ持ち込まない
- APIやMCPを追加するときも既存のApplicationユースケースを再利用する
- `service.py`を肥大化させず、機能別の`use_cases/`へ実装する
- 互換レイヤーは追加せず、必要になった時点で明示的なマイグレーションを設計する
- スキーマ変更はAlembic Revisionとして追加し、`tk init`で最新状態へupgradeする

## テスト方針

変更内容に応じて、適切な境界でテストします。

- Application: ユースケース、入力検証、トランザクションのロールバック
- Infrastructure: DB制約、Repository固有の契約
- Presentation: CLI終了コード、通常表示、JSON、CSV

CSVの構文解析はPresentation、行検証・Dry Run・一括更新はApplicationの責務とする。

単に100%へ近づけるためのテストではなく、利用者に影響する分岐、外部連携境界、データ整合性を
優先します。

テストは一時DBを使用します。ローカルの`data/termkeeper.db`は変更しません。

## 新しい機能を追加するとき

1. DTOや状態が必要なら`domain/`へ追加する
2. 永続化が必要ならSQLModelテーブルとRepositoryを更新する
3. トランザクションを含む操作を`application/use_cases/`へ追加する
4. CLIはApplicationのメソッドを呼ぶ薄いHandlerとして実装する
5. Applicationと外部境界のテストを追加する
6. ER図、CLI仕様、ユースケース文書を更新する

DBスキーマを変更した場合は、少なくとも
[ドメインモデル](docs/003_domain_model.md)のER図も更新してください。

## 関連ドキュメント

- [概要](docs/001_overview.md)
- [ユースケース](docs/002_use_cases.md)
- [ドメインモデル・ER図](docs/003_domain_model.md)
- [CLI仕様](docs/004_cli_spec.md)
- [MVPスコープ](docs/005_mvp_scope.md)
- [アーキテクチャと拡張方針](docs/006_architecture.md)
