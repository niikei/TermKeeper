"""Relevance scoring for Meaning search results."""

from collections.abc import Callable
from difflib import SequenceMatcher
from fnmatch import fnmatchcase
from time import monotonic
from typing import cast
from unicodedata import normalize

import regex

from termkeeper.domain import (
    LogicalOperator,
    Meaning,
    SearchField,
    SearchHit,
    SearchMode,
    SearchQuery,
    SearchSuggestion,
)
from termkeeper.infrastructure.normalization import normalize_keyword

_MIN_SUGGESTION_RATIO = 0.6
_REGEX_TIMEOUT_SECONDS = 0.02
_REGEX_TOTAL_TIMEOUT_SECONDS = 1.0
type _Match = tuple[int, SearchField, str]


def rank_search(meanings: list[Meaning], query: SearchQuery) -> list[SearchHit]:
    if query.mode == SearchMode.SMART:
        hits = _rank_smart(meanings, query)
    else:
        hits = _rank_pattern(meanings, query)
    hits.sort(
        key=lambda hit: (
            -hit.score,
            normalize_keyword(hit.meaning.full_name),
            hit.meaning.meaning_id,
        ),
    )
    return hits


def _rank_smart(meanings: list[Meaning], query: SearchQuery) -> list[SearchHit]:
    tokens = _tokens(query.text)
    match_all = query.word_match == LogicalOperator.ALL
    fields = frozenset(query.fields)
    return [
        hit
        for meaning in meanings
        if (
            hit := _score_meaning(
                meaning,
                tokens,
                fields,
                match_all=match_all,
            )
        )
        is not None
    ]


def _rank_pattern(meanings: list[Meaning], query: SearchQuery) -> list[SearchHit]:
    matches = _pattern_matcher(query)
    hits = [
        hit
        for meaning in meanings
        if (hit := _pattern_hit(meaning, frozenset(query.fields), matches, query.mode)) is not None
    ]
    return hits


def search_tokens(text: str) -> tuple[str, ...]:
    return _tokens(text)


def rank_suggestions(meanings: list[Meaning], query: SearchQuery) -> list[SearchSuggestion]:
    query_text = normalize_keyword(query.text)
    suggestions = [
        suggestion
        for meaning in meanings
        if (suggestion := _suggestion(meaning, query_text, frozenset(query.fields))) is not None
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
    fields: frozenset[SearchField],
    *,
    match_all: bool,
) -> SearchHit | None:
    token_matches = [_best_match(meaning, token, fields) for token in tokens]
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
    fields: frozenset[SearchField],
) -> _Match | None:
    candidates: list[_Match] = []
    if SearchField.TERM in fields:
        candidates.extend(
            _match_text(term, token, SearchField.TERM, (100, 80, 60)) for term in meaning.terms
        )
    if SearchField.NAME in fields:
        candidates.append(
            _match_text(meaning.full_name, token, SearchField.NAME, (90, 70, 50)),
        )
    if SearchField.DESCRIPTION in fields and meaning.description:
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


def _pattern_hit(
    meaning: Meaning,
    fields: frozenset[SearchField],
    matches: Callable[[str], bool],
    mode: SearchMode,
) -> SearchHit | None:
    candidates = [
        (field, text) for field, text in _searchable_texts(meaning, fields) if matches(text)
    ]
    if not candidates:
        return None
    matched_field, matched_text = max(
        candidates,
        key=lambda item: _field_weight(item[0]),
    )
    mode_bonus = {
        SearchMode.EXACT: 30,
        SearchMode.PREFIX: 20,
        SearchMode.CONTAINS: 10,
        SearchMode.GLOB: 5,
        SearchMode.REGEX: 5,
    }[mode]
    return SearchHit(
        meaning=meaning,
        score=_field_weight(matched_field) + mode_bonus,
        matched_field=matched_field,
        matched_text=matched_text,
    )


def _searchable_texts(
    meaning: Meaning,
    fields: frozenset[SearchField],
) -> list[tuple[SearchField, str]]:
    values: list[tuple[SearchField, str]] = []
    if SearchField.TERM in fields:
        values.extend((SearchField.TERM, term) for term in meaning.terms)
    if SearchField.NAME in fields:
        values.append((SearchField.NAME, meaning.full_name))
    if SearchField.DESCRIPTION in fields and meaning.description:
        values.append((SearchField.DESCRIPTION, meaning.description))
    return values


def _field_weight(field: SearchField) -> int:
    return {
        SearchField.TERM: 100,
        SearchField.NAME: 90,
        SearchField.DESCRIPTION: 40,
    }[field]


def _pattern_matcher(query: SearchQuery) -> Callable[[str], bool]:
    if query.mode == SearchMode.REGEX:
        regex_pattern = regex.compile(
            normalize("NFKC", query.text),
            regex.IGNORECASE | regex.VERSION1,
        )
        deadline = monotonic() + _REGEX_TOTAL_TIMEOUT_SECONDS

        def regex_matches(text: str) -> bool:
            remaining = deadline - monotonic()
            if remaining <= 0:
                message = "Regular expression evaluation exceeded its total time limit."
                raise TimeoutError(message)
            return (
                regex_pattern.search(
                    normalize("NFKC", text),
                    timeout=min(_REGEX_TIMEOUT_SECONDS, remaining),
                )
                is not None
            )

        return regex_matches

    normalized_pattern = normalize_keyword(query.text)
    if query.mode == SearchMode.EXACT:
        return lambda text: normalize_keyword(text) == normalized_pattern
    if query.mode == SearchMode.PREFIX:
        return lambda text: normalize_keyword(text).startswith(normalized_pattern)
    if query.mode == SearchMode.CONTAINS:
        return lambda text: normalized_pattern in normalize_keyword(text)
    if query.mode == SearchMode.GLOB:
        return lambda text: fnmatchcase(normalize_keyword(text), normalized_pattern)
    message = f"Unsupported search mode: {query.mode}."
    raise ValueError(message)


def _suggestion(
    meaning: Meaning,
    query_text: str,
    fields: frozenset[SearchField],
) -> SearchSuggestion | None:
    candidates: list[tuple[float, SearchField, str]] = []
    if SearchField.TERM in fields:
        candidates.extend(
            (
                SequenceMatcher(None, query_text, normalize_keyword(term)).ratio(),
                SearchField.TERM,
                term,
            )
            for term in meaning.terms
        )
    if SearchField.NAME in fields:
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
    if SearchField.DESCRIPTION in fields and meaning.description:
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
