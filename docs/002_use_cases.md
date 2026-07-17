# ユースケース

## ケース1: 新しい用語を登録する

ユーザー:

```text
tk add ICMR
```

結果:

```text
INBOX登録完了
InboxID: 1
Keyword: ICMR
```

## ケース2: 未処理一覧を確認する

ユーザー:

```text
tk inbox
```

結果:

```text
1 ICMR New
2 TCR Pending
3 BOM New
```

## ケース3: 用語を解決する

ユーザー:

```text
tk resolve 1
```

入力:

```text
正式名称:
Intercompany Matching and Reconciliation

説明:
グループ間取引照合機能
```

結果:

```text
Meaning作成

MeaningID: 100
```

## ケース4: 用語を検索する

ユーザー:

```text
tk search ICMR
```

結果:

```text
Intercompany Matching and Reconciliation

グループ間取引照合機能
```

## ケース5: 登録済み用語を再度追加する

ユーザー:

```text
tk add ICMR
```

結果:

```text
既に登録済みです

MeaningID: 100
Intercompany Matching and Reconciliation
```

INBOXには追加しない。

## ケース6: 未解決用語を再度追加する

状態:

```text
InboxID: 1
Keyword: ICMR
Status: Pending
```

ユーザー:

```text
tk add ICMR
```

結果:

```text
未解決の登録があります

InboxID: 1
Status: Pending
```
