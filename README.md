# TermKeeper

知らない言葉をその場で捕捉し、後から意味を整理するためのCLIツールです。

```text
会議中は登録だけ → 後で調査・整理 → 必要なときに検索
```

完璧な用語集を作ることではなく、知らない言葉を取りこぼさないことを重視します。

## 必要環境

- Python 3.12以上
- SQLite（SQLModel経由で利用）

## セットアップ

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
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

同じ未解決語を再度登録した場合、重複行は作成せず、出現回数と最終確認日時を更新します。
既にMeaningへ解決済みの場合は、登録済みのMeaningを表示します。

### 未処理項目の確認

```bash
tk inbox
```

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
tk show 1
tk meanings
```

### 整理

```bash
tk alias 1 ICMR
tk unalias 1 ICMR
tk edit 1 --name "Intercompany Matching and Reconciliation"
tk delete 1
tk discard 2
tk history
```

### CSV入出力

```bash
tk export terms.csv
tk import terms.csv
```

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

## Python APIと将来のMCP連携

CLIを介さず、Application層のサービスを利用できます。

```python
from termkeeper import TermKeeperService

service = TermKeeperService()
service.initialize()
result = service.add("BTP", source="Slack")
```

将来のHTTP APIやMCPサーバーも、このサービスをアダプターから呼び出します。

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
│   ├── infrastructure/  # SQLModel tables・Session・repository
│   ├── presentation/    # CLI・表示・CSV
│   └── config.py        # 実行時設定
├── tests/
├── data/
└── pyproject.toml
```

## 開発

```bash
pytest
ruff check .
ruff format --check .
```

`pytest` はカバレッジも計測し、90%を下回ると失敗します。

アーキテクチャの詳細は [アーキテクチャと拡張方針](docs/006_architecture.md) を参照してください。
