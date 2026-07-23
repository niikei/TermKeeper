# CLI仕様

## 共通

```text
tk [--json] [--debug] COMMAND ...
tk --version
```

共通オプションはサブコマンドより前に置く。Applicationエラー時は終了コード`2`、
DB初期化エラー時は終了コード`1`を返す。内部トレースバックは通常表示せず、
`--debug`指定時だけ標準エラーへ出力する。

## コマンド一覧

| コマンド | 用途 | 主な引数 |
| --- | --- | --- |
| `init` | DBを最新Alembic Revisionへ更新 | なし |
| `add` | 遭遇を捕捉 | `keyword`, `--memo`, `--source`, `--meaning` |
| `inbox` | Pending Occurrence一覧 | なし |
| `history` | 全Occurrence履歴 | なし |
| `occurrences` | 遭遇履歴を絞り込み | `--meaning`, `--status`, `--keyword`, `--source`, `--since`, `--limit` |
| `occurrence-edit` | 遭遇情報を修正 | `occurrence_id`, keyword/memo/source更新・clear |
| `resolve` | 新規・既存Meaningへ分類 | `occurrence_id`, `--meaning`または`--name`, `--scope`, `--description` |
| `unresolve` | 分類をPendingへ戻す | `occurrence_id` |
| `discard` | Pendingを破棄 | `occurrence_id` |
| `reopen` | DiscardedをPendingへ戻す | `occurrence_id` |
| `search` | Meaning検索 | query、field、tag、scope、favorite、suggestion |
| `show` / `meanings` | Meaning表示・一覧 | ID、`--tag`, `--scope`, `--favorite` |
| `edit` | Meaning更新 | ID、`--name`, `--scope`, `--description` |
| `alias` / `unalias` | Term追加・削除 | Meaning ID、keyword |
| `tag` / `untag` / `tags` | Tag管理 | Meaning ID、name |
| `favorite` / `unfavorite` | お気に入り | Meaning ID |
| `relate` / `unrelate` / `related` | Meaning関連 | Meaning ID |
| `reference-*` / `references` | 参考URL管理 | Meaning・Reference ID |
| `merge` | Meaning統合 | source、target、`--dry-run` |
| `delete` / `trash` / `restore` / `purge` | Meaning lifecycle | Meaning ID |
| `export` / `import` | CSV入出力 | path、dry-run、strict |
| `config` | user.name / user.email | key、value、list、unset |

## `tk add`

1. 入力を検証する。
2. 必ず新しいOccurrenceを保存する。
3. `--meaning`があれば明示されたMeaningへResolvedとして保存する。
4. 指定がなければPendingとして保存し、一致Termを持つ全Meaningをscope付き候補として表示する。

候補が1件でも自動分類しない。

## `tk resolve`

新規Meaning:

```bash
tk resolve OCCURRENCE_ID --name NAME --scope SCOPE --description TEXT
```

既存Meaning:

```bash
tk resolve OCCURRENCE_ID --meaning MEANING_ID
```

`--name`省略時は対話入力する。新規作成では同じ`scope_norm`と`full_name_norm`を持つ有効Meaningを
拒否する。既存Meaning指定はResolvedの再分類にも利用できる。

## 分類状態

- `unresolve`: Resolved → Pending
- `discard`: Pending → Discarded
- `reopen`: Discarded → Pending
- Discardedはreopenするまで分類不可

## `tk occurrences`

Occurrenceを`occurred_at`の新しい順で表示する。

- `--meaning ID`
- `--status Pending|Resolved|Discarded`
- `--keyword TEXT`
- `--source TEXT`
- `--since ISO-8601`
- `--limit N`

JSONにはID、public_id、keyword、memo、source、status、meaning_id、各日時・監査列を含む。

## `tk search`

完全一致、前方一致、部分一致の順で採点する。複数語は標準でAND、`--any`でOR。
`--in term|name|description|all`、`--tag`、`--scope`、`--favorite`で絞り込む。
通常ヒットがない場合だけ類似候補を返す。

## Meaning lifecycle

Meaningは`full_name`、`scope`、説明、Term、Tagを持つ。有効Meaningの正規化scope・正式名称の組は
一意。`merge`はTerm、Tag、Occurrence、Reference、Relationを移動する。同一URLと同一関連先は
統合先を優先して重複排除し、統合元と統合先の直接Relationは畳み込む。

`delete`は論理削除し、Occurrence参照を維持する。`restore`はPending Occurrenceを自動分類しない。
`purge`は参照OccurrenceがないTrash内Meaningだけを完全削除できる。

## CSV

```text
public_id,full_name,scope,description,terms,tags,created_at,updated_at
```

`scope`省略時は`General`。空の正式名称・scope、不正UUID、ファイル内重複UUID、同一scope内の
重複正式名称をissueとする。`--strict`はissueが1件でもあれば更新しない。

## 外部識別子

CLIはローカル整数IDを使用する。HTTPとMCPはMeaning、Occurrence、Referenceの`public_id` UUIDを
使用し、DB連番や内部UserProfile IDを公開しない。
