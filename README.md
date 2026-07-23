# TermKeeper

知らない言葉を捨てないためのCLIツール。会議中は一瞬で捕捉し、後から意味を整理できます。

## セットアップ

Python 3.12以降を使用します。

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
tk init
```

データベースの保存先は `TERMKEEPER_DB` で変更できます。

```bash
TERMKEEPER_DB=~/Documents/terms.db tk inbox
```

## 基本操作

```bash
tk add ICMR --memo "月次決算会議" --source "Teams"
tk inbox
tk resolve 1 --name "Intercompany Matching and Reconciliation" \
  --description "グループ間取引の照合"
tk search ICMR
tk show 1
```

同じ未解決語を再登録すると重複行は作らず、出現回数と最終確認日時を更新します。

## API / MCP連携

CLIの全主要コマンドは `--json` に対応しています。

```bash
tk --json search MDM
```

PythonからはCLIを介さず、安定したユースケース層を利用できます。将来のFastAPIやMCP
サーバーはこの層をアダプターから呼び出します。

```python
from termkeeper import TermKeeperService

service = TermKeeperService()
service.initialize()
result = service.add("BTP", source="Slack")
```

## 開発

```bash
pytest
ruff check .
```

構成は責務ごとに分離しています。

```text
src/termkeeper/
├── models.py   # API/MCPでも共有するドメインDTO
├── service.py  # ユースケース
├── db.py       # SQLiteアダプターとマイグレーション
├── config.py   # 実行時設定
└── cli.py      # CLIアダプター
```

## コンセプト

会議やチャットで知らない言葉に遭遇したとき、

```text
調べる時間がない
↓
メモしない
↓
忘れる
```

を防ぐ。

TermKeeper は、

```text
会議中は登録だけ
整理は後で
```

を実現するための個人用ナレッジ収集ツールである。

## 目的

業務中に出てきた未知の用語を蓄積し、

- 後で調べる
- 意味を整理する
- 再利用する

ことを支援する。

## 非目的

TermKeeper の目的は、

```text
完璧な用語集を作ること
```

ではない。

目的は、

```text
知らない言葉を取りこぼさないこと
```

である。

## 設計思想

### 会議中の操作を最小化する

会議中に入力するのは単語だけ。

例:

```text
tk add ICMR
tk add BOM
tk add BTP
```

### 整理は後で行う

正式名称や説明は後で登録できればよい。

登録時に入力を強制しない。

### 意味中心で管理する

このシステムは略語管理ではなく意味管理を行う。

例:

```text
MDM
Master Data Management
マスタ管理
```

は同じ意味を表す。

また、

```text
MDM
↓
Master Data Management

MDM
↓
Mobile Device Management
```

のように、

同じ単語が複数の意味を持つことも許可する。

## MVP機能

### 用語登録

```text
tk add ICMR
```

未整理用語として登録する。

### 未処理一覧

```text
tk inbox
```

未整理用語を確認する。

### 用語解決

```text
tk resolve 1
```

未整理用語に正式名称・説明を付与する。

### 用語検索

```text
tk search MDM
```

登録済みの意味を検索する。

### 破棄

```text
tk discard 1
```

不要な登録を破棄する。

## データモデル

システムは以下の構造で管理する。

```text
INBOX
↓
TERM
↓
MEANING
```

### INBOX

未整理用語。

会議中に発見した言葉を保存する。

### TERM

検索語。

略語・正式名称・別名などを管理する。

### MEANING

意味そのもの。

利用者が最終的に理解したい対象。

## ディレクトリ構成

```text
TermKeeper/
├─ docs/
├─ src/
├─ tests/
├─ data/
├─ pyproject.toml
└─ README.md
```

## MVP対象

- Python
- SQLite
- CLI
- INBOX管理
- TERM管理
- MEANING管理
- 検索
- 解決
- 破棄

## MVP対象外

- AI候補生成
- Teams連携
- Power Automate連携
- SharePoint連携
- Web UI
- タグ
- カテゴリ
- 添付ファイル
- URL管理
- 利用分析

## 成功条件

成功条件は、

```text
正しい用語集が完成すること
```

ではない。

成功条件は、

```text
知らない言葉を捨てなくなること
```

である。

例えば、

```text
ICMR
BTP
MDM
BOM
TCR
```

のような言葉を会議中に気軽に保存し、

必要なときに後から整理・参照できる状態になれば成功とする。
