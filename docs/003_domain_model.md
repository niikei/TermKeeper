# ドメインモデル

## 概念

TermKeeperは以下の流れで情報を管理する。

```text
INBOX
↓
TERM
↓
MEANING
```

## ER図

```mermaid
erDiagram

    MEANING ||--o{ TERM : has

    MEANING ||--o{ INBOX : resolved_to

    MEANING {
        int MeaningID

    string FullName
        string Description

    datetime CreatedAt
        datetime UpdatedAt
    }

    TERM {
        int TermID

    int MeaningID

    string Keyword
        string KeywordNorm

    datetime CreatedAt
        datetime UpdatedAt
    }

    INBOX {
        int InboxID

    string Keyword
        string KeywordNorm

    string Memo

    string Status

    int ResolvedMeaningID

    datetime CreatedAt
        datetime UpdatedAt
        datetime ClosedAt
    }
```

## TERM

検索に利用する単語。

例:

```text
MDM
Master Data Management
マスタ管理
```

## MEANING

利用者が理解したい対象。

例:

```text
Master Data Management

顧客・商品・取引先などの
マスタデータを統合管理する仕組み
```

## INBOX

未整理用語の保管場所。

会議中はまずここへ登録する。

## 状態遷移

```mermaid
stateDiagram-v2

    [*] --> New

    New --> Pending
    New --> Closed
    New --> Discarded

    Pending --> Closed
    Pending --> Discarded
```
