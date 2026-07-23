"""Relevance scoring for Meaning search results."""

from difflib import SequenceMatcher
from typing import cast

from termkeeper.domain import (
    Meaning,
    SearchField,
    SearchHit,
    SearchQuery,
    SearchSuggestion,
)
from termkeeper.infrastructure.normalization import normalize_keyword

_MIN_SUGGESTION_RATIO = 0.6
type _Match = tuple[int, SearchField, str]


def rank_search(meanings: list[Meaning], query: SearchQuery) -> list[SearchHit]:
    tokens = _tokens(query.text)
    hits = [
        hit
        for meaning in meanings
        if (
            hit := _score_meaning(
                meaning,
                tokens,
                query.field,
                match_all=query.match_all,
            )
        )
        is not None
    ]
    hits.sort(
        key=lambda hit: (
            -hit.score,
            normalize_keyword(hit.meaning.full_name),
            hit.meaning.meaning_id,
        ),
    )
    return hits[: query.limit]


def search_tokens(text: str) -> tuple[str, ...]:
    return _tokens(text)


def rank_suggestions(meanings: list[Meaning], query: SearchQuery) -> list[SearchSuggestion]:
    query_text = normalize_keyword(query.text)
    suggestions = [
        suggestion
        for meaning in meanings
        if (suggestion := _suggestion(meaning, query_text, query.field)) is not None
    ]
    suggestions.sort(
        key=lambda item: (
            -item.similarity,
            normalize_keyword(item.meaning.full_name),
            item.meaning.meaning_id,
        ),
    )
    return suggestions[: query.suggestion_limit]


def _score_meaning(
    meaning: Meaning,
    tokens: tuple[str, ...],
    field: SearchField,
    *,
    match_all: bool,
) -> SearchHit | None:
    token_matches = [_best_match(meaning, token, field) for token in tokens]
    matched: list[_Match] = [
        cast("_Match", candidate) for candidate in token_matches if candidate is not None
    ]
    if not matched or (match_all and len(matched) != len(tokens)):
        return None
    best = max(matched, key=_match_score)
    _, matched_field, matched_text = best
    return SearchHit(
        meaning=meaning,
        score=sum(score for score, _, _ in matched),
        matched_field=matched_field,
        matched_text=matched_text,
    )


def _match_score(candidate: _Match) -> int:
    score, _, _ = candidate
    return score


def _best_match(
    meaning: Meaning,
    token: str,
    field: SearchField,
) -> _Match | None:
    candidates: list[_Match] = []
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
    matches = [candidate for candidate in candidates if _match_score(candidate) > 0]
    if not matches:
        return None
    return max(matches, key=_match_score)


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


def _suggestion(
    meaning: Meaning,
    query_text: str,
    field: SearchField,
) -> SearchSuggestion | None:
    candidates: list[tuple[float, SearchField, str]] = []
    if field in {SearchField.ALL, SearchField.TERM}:
        candidates.extend(
            (
                SequenceMatcher(None, query_text, normalize_keyword(term)).ratio(),
                SearchField.TERM,
                term,
            )
            for term in meaning.terms
        )
    if field in {SearchField.ALL, SearchField.NAME}:
        candidates.append(
            (
                SequenceMatcher(
                    None,
                    query_text,
                    normalize_keyword(meaning.full_name),
                ).ratio(),
                SearchField.NAME,
                meaning.full_name,
            ),
        )
    if field in {SearchField.ALL, SearchField.DESCRIPTION} and meaning.description:
        candidates.append(
            (
                SequenceMatcher(
                    None,
                    query_text,
                    normalize_keyword(meaning.description),
                ).ratio(),
                SearchField.DESCRIPTION,
                meaning.description,
            ),
        )
    if not candidates:
        return None
    ratio, matched_field, matched_text = max(candidates, key=lambda candidate: candidate[0])
    if ratio < _MIN_SUGGESTION_RATIO:
        return None
    return SearchSuggestion(
        meaning=meaning,
        similarity=round(ratio * 100),
        matched_field=matched_field,
        matched_text=matched_text,
    )


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(normalize_keyword(part) for part in text.split() if part.strip()))
