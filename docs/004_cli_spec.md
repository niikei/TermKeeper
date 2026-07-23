# CLI仕様

## 共通

```text
tk [--json] [--debug] COMMAND ...
tk --version
```

`--json`と`--debug`はトップレベル、コマンドグループ直後、最終サブコマンド直後の
いずれにも置ける。Applicationエラー時は終了コード`2`、
DB初期化エラー時は終了コード`1`を返す。内部トレースバックは通常表示せず、
`--debug`指定時だけ標準エラーへ出力する。

## コマンド一覧

| コマンド | 用途 | 主な引数 |
| --- | --- | --- |
| `init` | DBを最新Alembic Revisionへ更新 | なし |
| `add` | 遭遇を捕捉 | `keyword`, `--memo`, `--source`, `--meaning` |
| `inbox` | Pending Occurrence一覧 | `--offset`, `--limit` |
| `resolve` | 新規・既存Meaningへ分類 | `occurrence_id`, `--meaning`または`--name`, `--scope`, `--description` |
| `search` | Meaning検索 | query、field、tag、scope、favorite、suggestion |
| `show` | Meaning詳細 | Meaning ID |
| `stats` | 遭遇統計 | `--limit` |
| `occurrence list/history/edit/unresolve/discard/reopen` | Occurrence管理 | filter、ID、ページング |
| `meaning list/edit/alias-*/favorite/unfavorite` | Meaning管理 | Meaning ID、更新値 |
| `meaning relate/unrelate/related` | Meaning関連 | Meaning ID |
| `meaning merge/delete/trash/restore/purge` | Meaning lifecycle | Meaning ID、`--dry-run`, `--yes` |
| `scope add/list/edit/delete` | Scope管理 | name、description、Scope ID |
| `tag add/remove/list` | Tag管理 | Meaning ID、name |
| `reference add/edit/remove/list` | 参考URL管理 | Meaning・Reference ID |
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

通常モードでは`--name`省略時に対話入力する。JSONモードは入力待ちを行わないため、新規作成時の
`--name`を必須とし、不足時はJSONエラーと終了コード`2`を返す。`--scope`は登録済みScope名を
指定し、省略時は`General`を使う。新規作成では同じ`scope_id`と
`full_name_norm`を持つ有効Meaningを拒否する。既存Meaning指定はResolvedの再分類にも利用できる。

`--meaning`と`--name`は排他的である。`--meaning`指定時に`--scope`または`--description`を
併用した場合も、曖昧な入力として拒否する。

## `tk meaning edit`

`--name`、`--scope`、`--description`のうち指定した項目だけを更新し、省略した項目は現在値を
維持する。通常モードで更新項目を1つも指定しない場合だけ対話入力する。JSONモードでは入力待ちを
行わず、更新項目を1つ以上必須とする。説明を削除する場合は`--clear-description`を使う。

## 分類状態

- `occurrence unresolve`: Resolved → Pending
- `occurrence discard`: Pending → Discarded
- `occurrence reopen`: Discarded → Pending
- Discardedはreopenするまで分類不可

## `tk occurrence list`

Occurrenceを`occurred_at`の新しい順で表示する。

- `--meaning ID`
- `--status Pending|Resolved|Discarded`
- `--keyword TEXT`
- `--source TEXT`
- `--since ISO-8601`
- `--offset N`
- `--limit N`

DB側で`offset`と`limit + 1`を適用し、500件を超える履歴も取得できる。JSONは`items`、
`offset`、`limit`、`has_more`を持つページ形式で、各itemにID、public_id、keyword、memo、
source、status、meaning_id、各日時・監査列を含む。

## `tk search`

完全一致、前方一致、部分一致の順で採点する。複数語は標準でAND、`--match-any`でOR。
`--field term|name|description|all`、`--tag`、`--scope`、`--favorite`で絞り込む。
通常ヒットがない場合だけ類似候補を返す。
Term、正式名称、説明はNFKC＋casefoldで比較し、全角／半角や`Straße`／`STRASSE`の差を
吸収する。レスポンスの一致文字列は正規化前の原文を返す。人間向け出力はID、正式名称、
Scope、一致箇所、スコアに絞り、詳細は`tk show`で確認する。

## Meaning lifecycle

Meaningは`full_name`、Scope参照、説明、Term、Tagを持つ。有効MeaningのScope・正規化正式名称の組は
一意。`meaning merge`はTerm、Tag、Occurrence、Reference、Relationを移動する。同一URLと同一関連先は
統合先を優先して重複排除し、統合元と統合先の直接Relationは畳み込む。

`meaning delete`は論理削除し、Occurrence参照を維持する。`meaning restore`はPending Occurrenceを
自動分類しない。`meaning purge`は参照OccurrenceがないTrash内Meaningだけを完全削除できる。

`meaning purge`、実更新する`meaning merge`、`scope delete`は人間向け実行で確認を求める。
自動化とJSONモードでは`--yes`を必須とし、入力待ちを行わない。

## CSV

```text
public_id,full_name,scope,description,terms,tags,created_at,updated_at
```

`scope`省略時は`General`。CSV内のScope名は事前登録が必要。空の正式名称・scope、不正UUID、
ファイル内重複UUID、同一scope内の
重複正式名称をissueとする。`terms`と`tags`はJSON文字列配列（例:
`["ERP","SAP;Legacy"]`）として格納する。空セルは空配列として許容し、非空セルの旧区切り文字
形式、非文字列要素、空文字要素はissueとする。`--strict`はissueが1件でもあれば更新しない。

## 外部識別子

CLIはローカル整数IDを使用する。HTTPとMCPはMeaning、Scope、Occurrence、Referenceの`public_id` UUIDを
使用し、DB連番や内部UserProfile IDを公開しない。
