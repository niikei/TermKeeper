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
| `inbox-edit` | 未解決Inboxのkeyword修正 | `inbox_id`, `--keyword` |
| `history` | 全Inbox履歴 | なし |
| `occurrences` | 遭遇履歴を表示・絞り込み | `--meaning`, `--inbox`, `--keyword`, `--source`, `--since`, `--limit` |
| `occurrence-edit` | 個別Occurrenceを修正 | `occurrence_id`, `--keyword`, `--memo`, `--source`, `--clear-memo`, `--clear-source` |
| `resolve` | InboxをMeaningへ解決 | `inbox_id`, `--name`, `--description` |
| `search` | 関連度検索と類似候補 | `keyword`, `--all`, `--any`, `--in`, `--limit`, `--tag`, `--suggestions`, `--no-suggestions` |
| `show` | Meaning詳細 | `meaning_id` |
| `meanings` | Meaning一覧 | `--tag` |
| `alias` | Meaningへ別名を追加 | `meaning_id`, `keyword` |
| `unalias` | Meaningから別名を削除 | `meaning_id`, `keyword` |
| `delete` | MeaningをTrashへ移動 | `meaning_id` |
| `trash` | 論理削除済みMeaning一覧 | なし |
| `restore` | TrashからMeaningを復元 | `meaning_id` |
| `purge` | Trash内Meaningを完全削除 | `meaning_id` |
| `merge` | Meaningを別のMeaningへ統合 | `source_id`, `target_id`, `--dry-run` |
| `tag` | Meaningへタグを追加 | `meaning_id`, `name` |
| `untag` | Meaningからタグを削除 | `meaning_id`, `name` |
| `tags` | タグとMeaning件数を一覧表示 | なし |
| `edit` | Meaningを編集 | `meaning_id`, `--name`, `--description` |
| `discard` | 未解決Inboxを破棄 | `inbox_id` |
| `config` | ユーザー設定を取得・更新 | `[key]`, `[value]`, `--list`, `--unset` |
| `export` | MeaningをCSV出力 | `[path]` |
| `import` | MeaningをCSV取込 | `path`, `--dry-run`, `--strict` |

## 主要な処理規則

### `tk add`

1. 入力をNFKC正規化し、大文字・小文字を統一する。
2. 登録済みTermがあればMeaningを返す。
3. 同じ未解決Inboxがあれば出現回数と最終確認日時を更新する。
4. どちらもなければ新しいInboxを作成する。

### `tk resolve`

`--name` を省略すると正式名称と説明を対話入力する。解決時にMeaningを作成し、Inboxの
keywordと正式名称をTermとして登録する。

### `tk occurrences`

Occurrenceを`occurred_at`の新しい順で表示する。

- `--meaning ID`: Meaning IDで絞り込み
- `--inbox ID`: Inbox IDで絞り込み
- `--keyword TEXT`: NFKC・大文字小文字を正規化した部分一致
- `--source TEXT`: 大文字小文字を区別しない完全一致
- `--since DATE_OR_DATETIME`: ISO 8601形式の日時以降
- `--limit N`: 最大件数。標準50、指定可能範囲は1〜500

複数の条件を指定した場合はすべてを満たすOccurrenceを返す。JSON結果は
`occurrence_id`、`keyword`、`memo`、`source`、`occurred_at`、`inbox_id`、
`meaning_id`、`created_by_id`、`updated_at`、`updated_by_id`を含む。

### `tk inbox-edit` / `tk occurrence-edit`

`inbox-edit`は`New`状態のInboxだけを編集し、keywordとkeyword_norm、更新日時、更新者を更新する。
別の未解決Inboxと正規化keywordが重複する変更、Closed・Discardedの編集は拒否する。Inboxの
修正では、遭遇時のrawデータであるOccurrence keywordは変更しない。

`occurrence-edit`は指定Occurrenceのkeyword・memo・sourceを個別に編集する。keyword変更時は
keyword_normも更新する。`--clear-memo`と`--clear-source`は値をNULLへ戻す。同じフィールドへの
値指定とclear指定の併用、変更項目なし、空文字の値は拒否する。Inboxや他のOccurrenceは
変更しない。

### `tk edit`

`--name` を省略すると対話形式になる。空入力は現在値を維持する。新しい正式名称は検索用
Termにも追加する。

### `tk merge`

```bash
tk merge SOURCE_ID TARGET_ID [--dry-run]
```

統合元MeaningのTerm、Tag、Occurrence、解決済みInboxを統合先Meaningへ移動する。
同じ正規化TermまたはTagが統合先に存在する場合は重複を削除し、それ以外の関連行は
作成日時・作成者を保持したまま移動する。統合先の更新日時と更新者を記録し、最後に
統合元Meaningを削除する。

すべての変更は1トランザクションで実行し、途中で失敗した場合はロールバックする。
`--dry-run`は`terms_moved`、`tags_moved`、`occurrences_moved`、`inboxes_moved`を返すが
変更を保存しない。
統合元と統合先に同じIDは指定できない。

### `tk delete` / `tk trash` / `tk restore` / `tk purge`

`delete`は`deleted_at`と`deleted_by_id`を記録する論理削除で、Term・Tag・Occurrence・Inboxとの
関連は保持する。削除済みMeaningは通常の取得、一覧、検索、Term照合、CSV Exportから除外する。

`restore`はMeaningを再び有効にする。削除中に同じTermがInboxへ再捕捉されていた場合、その
InboxをClosedへ遷移し、Occurrenceを復元Meaningへ関連付ける。`purge`はTrash内のMeaningだけを
完全削除し、TermとMeaningTagはCASCADE、OccurrenceとInboxのMeaning参照はSET NULLとする。

### `tk tag` / `tk untag` / `tk tags`

Tag名はNFKC正規化と大文字小文字の統一により一意に管理する。同じTagの追加は冪等で、
最後のMeaningからTagを外すと未使用Tagも削除する。`tk meanings --tag NAME`と
`tk search QUERY --tag NAME`で絞り込める。Meaning統合時はTagリンクも移動し、重複を除去する。

### `tk search`

空白区切りの複数語に対応し、標準ではすべての語に一致するMeaningを返す。

- `--all`: すべての検索語に一致（標準）
- `--any`: いずれかの検索語に一致
- `--in all|term|name|description`: 検索対象。標準は`all`
- `--limit N`: 最大件数。標準20、指定可能範囲は1〜100
- `--tag NAME`: 指定タグを持つMeaningだけに絞り込み
- `--suggestions N`: 0件時の候補数。標準3、指定可能範囲は0〜10
- `--no-suggestions`: 候補計算を無効化

Term完全一致、正式名称完全一致、前方一致、部分一致、説明一致の順に重み付けし、合計スコアの
降順で返す。同点では正式名称、Meaning IDの順に並べる。結果はMeaningに加えて`score`、
`matched_field`、`matched_text`を含む。SQLの`%`と`_`はワイルドカードではなく文字として扱う。

通常ヒットが0件の場合のみ、`difflib.SequenceMatcher`で検索対象のTerm・正式名称・説明との
類似度を計算する。類似度60%以上を降順で返し、削除済みMeaningとタグ条件外Meaningは除外する。
JSONは`hits`と`suggestions`を持ち、候補には`meaning`、`similarity`、`matched_field`、
`matched_text`を含む。

### `tk export` / `tk import`

CSV列は以下の通り。

```text
public_id,full_name,description,terms,tags,created_at,updated_at
```

`terms` と `tags` はセミコロン区切り。Import時、存在するUUID `public_id` は更新し、
それ以外は新規作成する。

- `--dry-run`: 作成・更新・スキップ予定と行番号付きissueを返し、DBを変更しない
- `--strict`: issueが1件でもあればApplicationエラーとして全件拒否する
- 標準: issueのある行をスキップし、有効行を1トランザクションで反映する

空の`full_name`、不正UUID、ファイル内の重複UUIDをissueとして扱う。DB更新中の例外は
全件ロールバックする。結果は`created`、`updated`、`skipped`、`dry_run`、`issues`を含む。
論理削除済みMeaningのUUIDはissueとし、明示的な`restore`を要求する。

### `tk config`

対応キーは `user.name` と `user.email`。値を指定すると更新、値を省略すると取得、
`--list` または引数なしでは全設定を表示する。`--unset` で値を解除する。設定は
データベース単位で型付きUserProfileとして保存する。
