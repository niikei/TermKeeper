# CLI仕様

## 共通

```text
tk [--json] [--debug] [--color auto|always|never] COMMAND ...
tk --version
```

引数なしの`tk`はバージョン、Pending件数、Meaning件数、Scope件数と次の操作を表示する。
`--json`と`--debug`はトップレベル、コマンドグループ直後、最終サブコマンド直後の
いずれにも置ける。Applicationエラー時は終了コード`2`、
DB初期化エラー時は終了コード`1`を返す。内部トレースバックは通常表示せず、
`--debug`指定時だけ標準エラーへ出力する。

初期化後はSQLModel metadataが要求するテーブル・列を検査する。Revisionが同じでも構造が
一致しなければSchema不一致として起動を拒否し、Tracebackではなく`tk init --reset`を案内する。
`--reset`はSQLite DBをtimestamp付きbackupへ退避してから再作成する破壊的操作であり、確認または
`--yes`を必須とする。

### 色と視覚表現

色は装飾ではなく、意味と視線誘導のために限定して使用する。色だけに依存せず、`#1`、
`[General]`、`Pending`、`[error]`などの文字と記号を常に残す。

| 意味 | 表現 | 主な適用先 |
| --- | --- | --- |
| 選択・参照可能なID | シアン＋太字 | Meaning、Occurrence、Scope、Reference |
| コマンド、設定キー、パス、Tag | シアン | dashboard、config、data、Tag |
| Scope | マゼンタ | 候補、検索、Meaning詳細 |
| 成功、Resolved、正常診断 | 緑 | 作成・更新・分類、履歴、doctor |
| Pending、警告、dry-run、favorite | 黄 | dashboard、履歴、import、favorite |
| エラー、Discarded、削除・破壊操作 | 赤＋太字 | stderr、履歴、purge、reset確認 |
| 見出し、Meaning名、検索一致 | 太字 | 一覧、検索、統計 |
| 日時、source、補助説明 | 薄い表示 | inbox、history、show、stats |

`--color`の値は次のとおり。

- `auto`: TTYの場合だけ色を使う。デフォルト。
- `always`: パイプやCIを含め、強制的に色を使う。
- `never`: 常に色を使わない。

`auto`では非TTY、空でない`NO_COLOR`、`TERM=dumb`で色を無効化し、空でない
`FORCE_COLOR`で強制できる。コマンドラインの`always`/`never`は環境変数より優先する。
stdoutとstderrは個別にTTY判定する。JSON出力は`--color=always`が併用されても色を使わず、
ANSI制御文字を含めない。`completion`と`--version`もプレーンテキストのままとする。

### Help

`tk --help`のusageはコマンド名をすべて展開せず、`tk [OPTIONS] COMMAND ...`として表示する。
コマンド一覧に加え、`Everyday workflow`、`Management`、`System and data`の用途別ガイドと
`tk COMMAND --help`への案内を表示する。

管理グループのhelpは`tk meaning ACTION ...`のように表現し、有効なAction一覧と
`tk GROUP ACTION --help`への案内を表示する。末端コマンドでは位置引数、オプション、
具体例を表示する。Helpは`--color=always`が指定されてもANSIカラーを使用しない。

## コマンド一覧

| コマンド | 用途 | 主な引数 |
| --- | --- | --- |
| `init` | DBを最新Alembic Revisionへ更新・再作成 | `--reset`, `--yes` |
| `add` | 遭遇を捕捉 | `keyword`, `--memo`, `--source`, `--meaning`, `--no-prompt` |
| `add-many` | 複数の遭遇を原子的に捕捉 | `--term`, `--file`, `--memo`, `--source`, `--yes` |
| `inbox` | Pending Occurrence一覧 | `--offset`, `--limit` |
| `list` | Active Meaningのコンパクト一覧 | `--tag`, `--scope`, `--favorite` |
| `resolve` | 新規・既存Meaningへ分類 | `occurrence_id`, `--meaning`または`--name`, `--scope`, `--description` |
| `search` / `meaning search` | Meaning検索 | text、field、tag、scope、favorite、suggestion |
| `inbox search` | Pending Occurrence検索 | text、source、since、ページング |
| `show` | Meaning詳細 | Meaning ID |
| `history` | 全Occurrence履歴 | `--offset`, `--limit` |
| `stats` | 遭遇統計 | `--limit` |
| `occurrence search/list/edit/unresolve/discard/reopen` | Occurrence管理 | text、filter、ID、ページング |
| `meaning search/list/edit/alias-*/favorite/unfavorite` | Meaning管理 | text、Meaning ID、更新値 |
| `meaning relate/unrelate/related` | Meaning関連 | Meaning ID |
| `meaning merge/delete/trash/restore/purge` | Meaning lifecycle | Meaning ID、`--dry-run`, `--yes` |
| `scope search/add/list/edit/delete` | Scope管理 | text、name、description、Scope ID |
| `tag add/remove/list` | Tag管理 | Meaning ID、name |
| `reference add/edit/remove/list` | 参考URL管理 | Meaning・Reference ID |
| `data export/import` | CSV入出力 | path、dry-run、strict |
| `config` | user.name / user.email | key、value、list、unset |
| `doctor` | DB・Schema・設定診断 | なし |
| `completion` | bash/zsh/fish補完生成 | shell |

## `tk list`

Active Meaningを更新日時の新しい順に、`ID / Meaning / Scope / Aliases`の表で表示する。
favoriteは名称の前に`★`を表示する。`--scope`、`--tag`、`--favorite`は組み合わせ可能。
人間向けの空一覧は`No meanings found.`を表示し、JSONではMeaningオブジェクトの配列を返す。

`tk meaning list`は説明、Tag、作成・更新日時を含む詳細・管理用表示として維持する。

## `tk add`

1. 入力を検証する。
2. 必ず新しいOccurrenceを保存する。
3. `--meaning`があれば明示されたMeaningへResolvedとして保存する。
4. 指定がなければPendingとして保存し、一致Termを持つ全Meaningをscope付き候補として表示する。
5. 対話端末で候補があればMeaningを選択できる。EnterはPendingを維持する。

候補が1件でも自動分類しない。JSON、非TTY、`--no-prompt`では選択を求めない。

## `tk add-many`

位置引数は受け取らない。引数なしのTTYでは1行1用語を入力し、一覧をプレビューしてから確認する。
少量の明示入力は反復可能な`--term`、ファイルまたは標準入力は`--file PATH|-`を使用する。
`--term`と`--file`は排他的で、`--memo`と`--source`は全項目に共通適用する。

空入力、ファイル内の空行、正規化後の重複、100件超を拒否する。Applicationの
`capture_many`が全件を事前検証し、1つのUnit of Workで登録するため、途中失敗時も一部登録を
残さない。複数登録中はMeaning選択を求めず、候補数を表示してPendingの整理を利用者に委ねる。
JSONまたは非TTYで入力元がない場合は、標準入力を暗黙に読まず構造化エラーを返す。

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

通常モードで一致Meaningがある場合は、新規Meaning入力より先に候補選択を提示する。候補が1件なら
Enterで選択し、複数件ならMeaning IDを入力する。`n`は新規Meaning作成、`q`は副作用なしの
キャンセルとする。候補がない場合だけ新規Meaningの入力へ進む。

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

## Search

```bash
tk search TEXT
tk meaning search TEXT
tk occurrence search TEXT
tk inbox search TEXT
tk scope search TEXT
```

`tk search`と`tk meaning search`は同じMeaning検索ユースケースを呼ぶ。

完全一致、前方一致、部分一致の順で採点する。複数語は標準でAND、`--match-any`でOR。
`--field term|name|description|all`、`--tag`、`--scope`、`--favorite`で絞り込む。
通常ヒットがない場合だけ類似候補を返す。
Term、正式名称、説明はNFKC＋casefoldで比較し、全角／半角や`Straße`／`STRASSE`の差を
吸収する。レスポンスの一致文字列は正規化前の原文を返す。人間向け出力はID、正式名称、
Scope、一致箇所、スコアに絞り、詳細は`tk show`で確認する。

Occurrence検索はkeyword、memo、sourceを横断し、`--meaning`、`--status`、`--source`、
`--since`の構造化条件を先に適用する。結果は`occurred_at`降順、Occurrence ID降順。
Inbox検索はstatusを常にPendingへ固定し、source、since、ページングを受け付ける。

Scope検索はnameとdescriptionを対象にし、正規化name、Scope IDの順で安定して返す。
Occurrence、Inbox、Scope検索のJSONは`items`、`offset`、`limit`、`has_more`を持つ。

## Meaning lifecycle

Meaningは`full_name`、Scope参照、説明、Term、Tagを持つ。有効MeaningのScope・正規化正式名称の組は
一意。`meaning merge`はTerm、Tag、Occurrence、Reference、Relationを移動する。同一URLと同一関連先は
統合先を優先して重複排除し、統合元と統合先の直接Relationは畳み込む。

`meaning delete`は論理削除し、Occurrence参照を維持する。`meaning restore`はPending Occurrenceを
自動分類しない。`meaning purge`は参照OccurrenceがないTrash内Meaningだけを完全削除できる。

`meaning purge`、実更新する`meaning merge`、`scope delete`は人間向け実行で確認を求める。
自動化とJSONモードでは`--yes`を必須とし、入力待ちを行わない。

## 診断と補完

`tk doctor`はTermKeeperのバージョン、資格情報を伏せたDB接続先、DB backend、現在と期待する
Alembic Revision、利用者設定の有無を表示する。DB初期化自体に失敗した場合は通常の初期化エラーと
`tk --debug doctor`による技術情報を返す。
DB接続またはスキーマ診断が異常なら終了コード`1`、正常なら`0`を返す。

`tk completion bash|zsh|fish`は標準出力へ補完スクリプトを生成する。JSONモードではshell名と
スクリプトをJSONオブジェクトとして返す。

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
