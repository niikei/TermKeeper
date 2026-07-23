# ドメインモデル

## 概念

TermKeeperは遭遇をOccurrenceとして保存し、Meaningへの分類を別操作として扱う。

```text
Occurrence(Pending) ── explicit classification ──> Meaning <── Term
```

文字列の一致は分類候補を生成するだけで、分類の根拠にはしない。Inboxは`Pending`の
Occurrence一覧であり、DBテーブルではない。

## ER図

```mermaid
erDiagram

    MEANING ||--o{ TERM : "has aliases"
    MEANING ||--o{ MEANINGTAG : "classified by"
    MEANING ||--o{ MEANINGRELATION : "related as low id"
    MEANING ||--o{ MEANINGRELATION : "related as high id"
    MEANING ||--o{ MEANINGREFERENCE : "has sources"
    MEANING o|--o{ OCCURRENCE : "classifies"
    TAG ||--o{ MEANINGTAG : "assigned through"
    USERPROFILE o|--o{ MEANING : "creates and updates"
    USERPROFILE o|--o{ OCCURRENCE : "captures and classifies"

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
        text full_name_norm
        text scope
        text scope_norm
        text description "nullable"
        boolean is_favorite
        datetime created_at "UTC"
        datetime updated_at "UTC"
        datetime deleted_at "nullable"
        integer created_by_id FK "nullable"
        integer updated_by_id FK "nullable"
        integer deleted_by_id FK "nullable"
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

    OCCURRENCE {
        integer occurrence_id PK
        uuid public_id UK
        text keyword
        text keyword_norm
        text status "Pending Resolved Discarded"
        integer meaning_id FK "nullable"
        text memo "nullable"
        text source "nullable"
        datetime occurred_at "UTC"
        datetime updated_at "UTC"
        datetime resolved_at "nullable"
        datetime discarded_at "nullable"
        integer created_by_id FK "nullable"
        integer updated_by_id FK "nullable"
        integer resolved_by_id FK "nullable"
        integer discarded_by_id FK "nullable"
    }

    TAG {
        integer tag_id PK
        text name
        text name_norm UK
        datetime created_at "UTC"
        integer created_by_id FK "nullable"
    }

    MEANINGTAG {
        integer meaning_id PK, FK
        integer tag_id PK, FK
        datetime created_at "UTC"
        integer created_by_id FK "nullable"
    }

    MEANINGRELATION {
        integer meaning_id_low PK, FK
        integer meaning_id_high PK, FK
        datetime created_at "UTC"
        integer created_by_id FK "nullable"
    }

    MEANINGREFERENCE {
        integer reference_id PK
        uuid public_id UK
        integer meaning_id FK
        text url
        text title "nullable"
        datetime created_at "UTC"
        datetime updated_at "UTC"
        integer created_by_id FK "nullable"
        integer updated_by_id FK "nullable"
    }
```

## 状態遷移

```mermaid
stateDiagram-v2

    [*] --> Pending
    Pending --> Resolved : create or assign Meaning
    Resolved --> Pending : unresolve
    Resolved --> Resolved : reassign
    Pending --> Discarded : discard
    Discarded --> Pending : reopen
```

DBのCHECK制約は次を保証する。

- `Pending`: `meaning_id IS NULL`
- `Resolved`: `meaning_id IS NOT NULL`
- `Discarded`: `meaning_id IS NULL`

## Meaningとscope

Meaningは文字列ではなく概念を表す。`scope`はSAP、Oracle、Radio、Generalなど、概念が成立する
製品・組織・業務領域を表す。

```text
ERP [SAP]   → Enterprise Resource Planning
ERP [Radio] → Effective Radiated Power
```

有効Meaningの`(scope_norm, full_name_norm)`は一意。同じ正式名称でもscopeが異なれば別概念として
登録できる。Termの`keyword_norm`はMeaningをまたいで一意にしないため、同じ略語を複数概念が
持てる。

## リレーションと制約

- 遭遇は毎回独立したOccurrenceとして保存する。
- Occurrenceのkeyword、memo、sourceは遭遇時点の履歴であり、Meaning編集で変更しない。
- Term一致は候補検索にだけ使用し、Meaningへ自動分類しない。
- Termの`(keyword_norm, meaning_id)`は一意。
- Meaningの論理削除後もOccurrenceの分類参照は保持する。
- 参照中Meaningの物理削除は`RESTRICT`し、分類履歴を暗黙に失わない。
- MeaningRelationは小さいMeaning IDを先にした対称ペア。
- MeaningReferenceの`(meaning_id, url)`は一意。
- `keyword_norm`、`scope_norm`、`full_name_norm`はNFKCとcasefold相当の正規化検索値。
- 外部境界ではMeaning、Occurrence、MeaningReferenceのUUID `public_id`を使用する。

## インデックス

| インデックス | 対象 | 用途 |
| --- | --- | --- |
| `uq_meaning_active_scope_name` | `scope_norm, full_name_norm WHERE deleted_at IS NULL` | scope内の重複Meaning防止 |
| `idx_term_keyword` | `term.keyword_norm` | 候補・用語検索 |
| `idx_term_meaning` | `term.meaning_id` | Meaningの別名取得 |
| `ix_occurrence_keyword_norm` | `occurrence.keyword_norm` | 遭遇語検索 |
| `ix_occurrence_status` | `occurrence.status` | Inboxと状態絞り込み |
| `ix_occurrence_occurred_at` | `occurrence.occurred_at` | 期間・新しい順 |
| `ix_meaning_deleted_at` | `meaning.deleted_at` | 通常一覧とTrashの分離 |
| `ix_meaning_is_favorite` | `meaning.is_favorite` | お気に入り絞り込み |
| `ix_occurrence_public_id` | `occurrence.public_id` | 外部UUID解決 |
| `ix_meaningreference_public_id` | `meaningreference.public_id` | 外部UUID解決 |
