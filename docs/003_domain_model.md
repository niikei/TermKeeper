# ドメインモデル

## 概念

TermKeeperは、遭遇をOccurrenceとして記録し、未整理のInboxをMeaningへ解決する。

```text
USERPROFILE ──> INBOX ──> OCCURRENCE
                    └── resolves to ──> MEANING <── TERM
```

## ER図

```mermaid
erDiagram

    MEANING ||--o{ TERM : "has aliases"
    MEANING o|--o{ INBOX : "resolves captures"
    INBOX o|--o{ OCCURRENCE : "records encounters"
    MEANING o|--o{ OCCURRENCE : "classifies encounters"
    USERPROFILE o|--o{ INBOX : "creates"
    USERPROFILE o|--o{ MEANING : "creates and updates"

    USERPROFILE {
        integer user_id PK
        text name "nullable"
        text email "nullable"
        datetime created_at "UTC"
        datetime updated_at "UTC"
    }

    MEANING {
        integer meaning_id PK
        uuid public_id UK
        text full_name
        text description "nullable"
        datetime created_at "UTC"
        datetime updated_at "UTC"
        integer created_by_id FK "nullable"
        integer updated_by_id FK "nullable"
    }

    TERM {
        integer term_id PK
        integer meaning_id FK
        text keyword
        text keyword_norm
        datetime created_at "UTC"
        datetime updated_at "UTC"
        integer created_by_id FK "nullable"
    }

    INBOX {
        integer inbox_id PK
        text keyword
        text keyword_norm
        text status "New Closed Discarded"
        integer resolved_meaning_id FK "nullable"
        datetime created_at "UTC"
        datetime updated_at "UTC"
        datetime closed_at "nullable"
        integer created_by_id FK "nullable"
    }

    OCCURRENCE {
        integer occurrence_id PK
        text keyword
        integer inbox_id FK "nullable"
        integer meaning_id FK "nullable"
        text memo "nullable"
        text source "nullable"
        datetime occurred_at "UTC"
        integer created_by_id FK "nullable"
    }
```

### リレーションと制約

- 1つのMeaningは0個以上のTermを持つ。
- Termは必ず1つのMeaningに属し、Meaning削除時に連動して削除される。
- Inboxは未解決・破棄状態ではMeaningを持たず、解決後に1つのMeaningを参照する。
- 用語への遭遇は毎回Occurrenceとして保存し、sourceやmemoを上書きしない。
- Meaningは外部連携用の安定したUUID `public_id` を持つ。
- 開いているInboxの `keyword_norm` は部分一意制約で重複を防ぐ。
- Termの `(keyword_norm, meaning_id)` は一意で、同じMeaningへの別表記の重複を防ぐ。
- `keyword_norm` はNFKC正規化と大文字・小文字の統一後の検索値を保持する。

### インデックス

| インデックス | 対象列 | 用途 |
| --- | --- | --- |
| `uq_inbox_open_keyword` | `inbox.keyword_norm WHERE status = NEW` | 未解決Inboxの重複防止 |
| `idx_term_keyword` | `term.keyword_norm` | 用語検索 |
| `idx_term_meaning` | `term.meaning_id` | Meaningから別名を取得 |

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

    New --> Closed
    New --> Discarded
```
