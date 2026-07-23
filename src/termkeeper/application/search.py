"""Relevance scoring for Meaning search results."""

from termkeeper.domain import Meaning, SearchField, SearchHit, SearchQuery
from termkeeper.infrastructure.sqlite_utils import normalize_keyword


def rank_search(meanings: list[Meaning], query: SearchQuery) -> list[SearchHit]:
    tokens = _tokens(query.text)
    hits = [
        hit
        for meaning in meanings
        if (hit := _score_meaning(meaning, tokens, query.field, query.match_all)) is not None
    ]
    hits.sort(
        key=lambda hit: (-hit.score, hit.meaning.full_name.casefold(), hit.meaning.meaning_id)
    )
    return hits[: query.limit]


def search_tokens(text: str) -> tuple[str, ...]:
    return _tokens(text)


def _score_meaning(
    meaning: Meaning,
    tokens: tuple[str, ...],
    field: SearchField,
    match_all: bool,
) -> SearchHit | None:
    token_matches = [_best_match(meaning, token, field) for token in tokens]
    matched = [candidate for candidate in token_matches if candidate is not None]
    if not matched or (match_all and len(matched) != len(tokens)):
        return None
    best = max(matched, key=lambda candidate: candidate[0])
    return SearchHit(
        meaning=meaning,
        score=sum(candidate[0] for candidate in matched),
        matched_field=best[1],
        matched_text=best[2],
    )


def _best_match(
    meaning: Meaning,
    token: str,
    field: SearchField,
) -> tuple[int, SearchField, str] | None:
    candidates: list[tuple[int, SearchField, str]] = []
    if field in {SearchField.ALL, SearchField.TERM}:
        candidates.extend(
            _match_text(term, token, SearchField.TERM, (100, 80, 60)) for term in meaning.terms
        )
    if field in {SearchField.ALL, SearchField.NAME}:
        candidates.append(
            _match_text(meaning.full_name, token, SearchField.NAME, (90, 70, 50)),
        )
    if field in {SearchField.ALL, SearchField.DESCRIPTION} and meaning.description:
        candidates.append(
            _match_text(meaning.description, token, SearchField.DESCRIPTION, (40, 30, 20)),
        )
    matches = [candidate for candidate in candidates if candidate[0] > 0]
    return max(matches, default=None, key=lambda candidate: candidate[0])


def _match_text(
    text: str,
    token: str,
    field: SearchField,
    weights: tuple[int, int, int],
) -> tuple[int, SearchField, str]:
    exact, prefix, contains = weights
    normalized = normalize_keyword(text)
    if normalized == token:
        score = exact
    elif normalized.startswith(token):
        score = prefix
    elif token in normalized:
        score = contains
    else:
        score = 0
    return score, field, text


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(normalize_keyword(part) for part in text.split() if part.strip()))
