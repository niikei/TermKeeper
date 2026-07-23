# ユースケース

## 1. 新しい用語を捕捉する

```bash
tk add ICMR --memo "月次決算会議" --source Teams
```

新しいInboxを `New` 状態で作成し、作成日時・更新日時・最終確認日時を記録する。

## 2. 未解決語に再遭遇する

```bash
tk add ICMR --source Slack
```

正規化した検索語が同じ未解決Inboxを新規作成せず、以下を更新する。

- `occurrence_count` を1増やす
- `last_seen_at` と `updated_at` を更新する
- 指定されたmemoまたはsourceを更新する

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
遷移し、解決先Meaningと終了日時を記録する。

## 5. 登録済み用語に再遭遇する

```bash
tk add ICMR
```

一致するTermが既に存在する場合はInboxを作成せず、登録済みMeaningを表示する。

## 6. 用語を検索・参照する

```bash
tk search ICMR
tk show 1
tk meanings
```

検索はTerm、正式名称、説明の部分一致で行う。詳細表示では別名と作成・更新日時も表示する。

## 7. Meaningを整理する

```bash
tk alias 1 ICMR
tk edit 1 --name "Intercompany Matching and Reconciliation"
```

Meaningへ別名を追加し、正式名称や説明を更新する。対話形式の編集も利用できる。

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
