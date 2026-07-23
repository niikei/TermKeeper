# ユースケース

## 1. 用語へ遭遇する

```bash
tk add ICMR --memo "月次決算会議" --source Teams
```

遭遇ごとに独立したOccurrenceを`Pending`状態で作成する。登録済みTermと一致してもMeaningへ
自動分類しない。一致するすべてのMeaningをscope付き候補として返す。

分類先が確定している場合だけ明示できる。

```bash
tk add ERP --meaning 12
```

## 2. 未分類Occurrenceを確認する

```bash
tk inbox
```

Inboxは永続エンティティではなく、`Pending`状態のOccurrenceを新しい順で表示する作業ビュー。
同じkeywordの遭遇もまとめず、個別に表示する。

## 3. 遭遇履歴を確認・修正する

```bash
tk occurrences
tk occurrences --meaning 1
tk occurrences --status Pending
tk occurrences --keyword MDM --source Slack
tk occurrences --since 2026-07-01 --limit 20
tk occurrences --offset 20 --limit 20
tk occurrence-edit 3 --keyword ERP --memo "訂正" --source Teams
tk occurrence-edit 3 --clear-memo --clear-source
```

Occurrenceのraw keyword、memo、source、日時、分類状態、Meaningを表示する。編集は対象Occurrence
だけに作用し、他の遭遇やMeaningのTermは暗黙に変更しない。
`inbox`、`history`、`occurrences`はDB側でページングし、500件を超える履歴も取得できる。

## 4. 新しいMeaningとして解決する

```bash
tk resolve 1 \
  --name "Enterprise Resource Planning" \
  --scope SAP \
  --description "SAPにおける基幹業務統合の概念"
```

Meaning、正式名称と遭遇語のTermを作成し、対象Occurrenceだけを`Resolved`へ遷移する。
同じ正規化正式名称とscopeを持つ有効Meaningが存在する場合は拒否する。

## 5. 既存Meaningへ分類・再分類する

```bash
tk resolve 1 --meaning 12
tk unresolve 1
```

既存Meaningへの分類はIDを明示する。分類済みOccurrenceへ別Meaningを指定した場合は再分類する。
`unresolve`はMeaning参照を外して`Pending`へ戻す。

## 6. 不要な遭遇を破棄・再開する

```bash
tk discard 1
tk reopen 1
```

`discard`はPendingからDiscarded、`reopen`はDiscardedからPendingへ遷移する。Discardedを直接
Meaningへ分類することはできない。

## 7. scopeで概念を区別する

Scopeは独立して管理し、Meaning作成前に登録する。`General`だけはDB初期化時に用意される。

```bash
tk scope-add SAP
tk scope-add Radio
tk scopes
```

同じ表記でも、製品や業務領域が異なれば別Meaningとして管理する。

```text
ERP [SAP]   → Enterprise Resource Planning
ERP [Radio] → Effective Radiated Power
```

```bash
tk search ERP --scope SAP
tk meanings --scope SAP
```

scopeはMeaningの識別境界であり、Tagとは異なる。同じ正式名称は別scopeなら許可し、同一scope
内では重複を防ぐ。

## 8. Meaningを検索・整理する

```bash
tk search "enterprise planning" --all
tk search ERP --tag Core --scope SAP
tk show 1
tk edit 1 --name "Enterprise Resource Planning" --scope "SAP S/4HANA"
tk alias 1 ERP
tk tag 1 Core
tk favorite 1
```

検索はTerm、正式名称、説明を関連度順に返す。Tag、scope、お気に入りで絞り込める。

## 9. Meaningを統合する

```bash
tk merge 2 1 --dry-run
tk merge 2 1
```

統合元のTerm、Tag、Occurrence、Reference、Relationを統合先へ移し、統合元を削除する。
同一URLのReferenceと同一関連先のRelationは統合先を優先して重複排除する。統合元と統合先の
直接Relationは自己Relationになるため畳み込む。Dry Runは移動・重複排除・畳み込み件数を返す。

## 10. Meaningを削除・復元する

```bash
tk delete 1
tk trash
tk restore 1
tk purge 1
```

通常削除は論理削除。Occurrenceの分類履歴は維持する。Occurrenceから参照されるMeaningの
完全削除は拒否し、再分類または`unresolve`を先に要求する。復元時に同じTermのPending
Occurrenceを自動分類しない。

## 11. CSVで一括入出力する

```bash
tk export terms.csv
tk import terms.csv --dry-run
tk import terms.csv --strict
```

CSVは`scope`列を含む。Scope名は事前登録が必要で、未知のScope、同一scope内の重複正式名称、
不正UUID、空の必須項目をissueとして扱う。
Importは1つのUnit of Workで実行し、実行時エラーでは全件をロールバックする。
`terms`と`tags`はJSON文字列配列としてセルに格納し、セミコロン、カンマ、引用符、Unicodeを
含む値を可逆に扱う。空セルは空配列として扱い、不正なJSON配列は行単位のissueにする。

## 12. 利用者情報を記録する

```bash
tk config user.name "Taro Yamada"
tk config user.email taro@example.com
```

利用者情報はUserProfileへ保存し、Meaning・Occurrenceなどの作成者、更新者、分類者として
監査列へ記録する。
