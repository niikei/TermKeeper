# CLI仕様

## 共通仕様

```text
tk [--json] <command> [options]
```

- `--json`: 結果をUTF-8のJSONで標準出力へ出力する。サブコマンドより前に指定する。
- 成功時の終了コードは `0`、入力・未検出・ファイル操作エラーは `2`。
- CLI起動時にSQLModelでデータベーステーブルを初期化する。

## コマンド一覧

| コマンド | 用途 | 主な引数・オプション |
|---|---|---|
| `init` | DBを初期化・更新 | なし |
| `add` | Inboxへ捕捉 | `keyword`, `--memo`, `--source` |
| `inbox` | 未解決Inbox一覧 | なし |
| `history` | 全Inbox履歴 | なし |
| `resolve` | InboxをMeaningへ解決 | `inbox_id`, `--name`, `--description` |
| `search` | Term・正式名称・説明を検索 | `keyword` |
| `show` | Meaning詳細 | `meaning_id` |
| `meanings` | Meaning一覧 | なし |
| `alias` | Meaningへ別名を追加 | `meaning_id`, `keyword` |
| `edit` | Meaningを編集 | `meaning_id`, `--name`, `--description` |
| `discard` | 未解決Inboxを破棄 | `inbox_id` |
| `config` | ユーザー設定を取得・更新 | `[key]`, `[value]`, `--list` |
| `export` | MeaningをCSV出力 | `[path]` |
| `import` | MeaningをCSV取込 | `path` |

## 主要な処理規則

### `tk add`

1. 入力をNFKC正規化し、大文字・小文字を統一する。
2. 登録済みTermがあればMeaningを返す。
3. 同じ未解決Inboxがあれば出現回数と最終確認日時を更新する。
4. どちらもなければ新しいInboxを作成する。

### `tk resolve`

`--name` を省略すると正式名称と説明を対話入力する。解決時にMeaningを作成し、Inboxの
keywordと正式名称をTermとして登録する。

### `tk edit`

`--name` を省略すると対話形式になる。空入力は現在値を維持する。新しい正式名称は検索用
Termにも追加する。

### `tk export` / `tk import`

CSV列は以下の通り。

```text
meaning_id,full_name,description,terms,created_at,updated_at
```

`terms` はセミコロン区切り。Import時、存在する `meaning_id` は更新し、それ以外は新規作成する。

### `tk config`

対応キーは `user.name` と `user.email`。値を指定すると更新、値を省略すると取得、
`--list` または引数なしでは全設定を表示する。設定はデータベース単位で保存する。
