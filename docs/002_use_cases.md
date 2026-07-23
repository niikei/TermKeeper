# ユースケース

## 1. 新しい用語を捕捉する

```bash
tk add ICMR --memo "月次決算会議" --source Teams
```

新しいInboxを `New` 状態で作成し、同時に遭遇時刻・memo・sourceをOccurrenceへ記録する。

## 2. 未解決語に再遭遇する

```bash
tk add ICMR --source Slack
```

正規化した検索語が同じ未解決Inboxを新規作成せず、新しいOccurrenceを追加する。

過去のmemo・source・遭遇時刻は上書きしない。表示時の出現回数と最終確認日時は、
Occurrence履歴から算出する。

## 3. 未処理一覧を確認する

```bash
tk inbox
```

未解決のInboxを最終確認日時の新しい順で表示する。ID、用語、状態、出現回数、更新日時に
加えて、登録されていればmemoとsourceも表示する。

## 4. 用語を解決する

対話形式:

```bash
tk resolve 1
```

非対話形式:

```bash
tk resolve 1 --name "Intercompany Matching and Reconciliation" \
  --description "グループ間取引照合機能"
```

Meaningを作成し、Inboxのkeywordと正式名称をTermとして関連付ける。Inboxは `Closed` に
遷移し、解決先Meaningと終了日時を記録する。Meaning作成・Term追加・Inbox更新・Occurrence
関連付けは1トランザクションで実行し、途中で失敗した場合はすべて取り消す。

## 5. 登録済み用語に再遭遇する

```bash
tk add ICMR
```

一致するTermが既に存在する場合はInboxを作成せず、登録済みMeaningを表示する。この遭遇も
Meaningへ直接関連付けたOccurrenceとして保存する。

## 6. 用語を検索・参照する

```bash
tk search ICMR
tk search "enterprise planning" --all
tk search "planning document" --any --in description --limit 10
tk show 1
tk meanings
```

検索はTerm、正式名称、説明を対象に、完全一致、前方一致、部分一致の順で関連度を付ける。
複数語は標準ですべての語に一致する結果を返し、`--any`でいずれかの語に切り替える。
結果にはスコア、一致フィールド、一致文字列を含む。詳細表示では別名と作成・更新日時も表示する。

## 7. Meaningを整理する

```bash
tk alias 1 ICMR
tk unalias 1 ICMR
tk edit 1 --name "Intercompany Matching and Reconciliation"
tk delete 1
```

Meaningへ別名を追加・削除し、正式名称や説明を更新する。不要になったMeaningは削除できる。
対話形式の編集も利用できる。

## 8. Inboxを破棄する

```bash
tk discard 2
```

未解決Inboxを `Discarded` に遷移し、更新日時と終了日時を記録する。

## 9. 外部ツールと連携する

```bash
tk --json search ICMR
tk export terms.csv
tk import terms.csv
```

JSONはスクリプトや将来のアダプター、CSVはバックアップや一括編集に利用する。
CSVではDB内部IDではなく、外部連携向けのUUID `public_id` を使用する。

## 10. 利用者情報を管理する

```bash
tk config user.name "Taro Yamada"
tk config user.email taro@example.com
tk config --unset user.email
```

利用者情報は型付きUserProfileへ保存し、Meaning・Inbox・Occurrenceの作成者や更新者として
記録する。
