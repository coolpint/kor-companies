from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .models import CompanyConfig
from .utils import normalize_whitespace

LATIN_PATTERN = re.compile(r"[A-Za-z]")
HIRAGANA_PATTERN = re.compile(r"[\u3040-\u309f]")
KATAKANA_PATTERN = re.compile(r"[\u30a0-\u30ff\uff66-\uff9f]")
HAN_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
HANGUL_PATTERN = re.compile(r"[\uac00-\ud7a3]")


@dataclass
class MatchResult:
    company: CompanyConfig
    aliases: List[str]


@dataclass
class _AliasRule:
    alias: str
    pattern: re.Pattern | None
    use_substring: bool


class CompanyMatcher:
    def __init__(self, companies: List[CompanyConfig]):
        self._companies = companies
        self._rules = {
            company.canonical_name_en: [_compile_alias(alias) for alias in company.all_aliases()]
            for company in companies
        }

    def match(self, text: str) -> List[MatchResult]:
        haystack = normalize_whitespace(text)
        lowered = haystack.casefold()
        matches: List[MatchResult] = []

        for company in self._companies:
            hit_aliases: List[str] = []
            for rule in self._rules[company.canonical_name_en]:
                if rule.use_substring:
                    if rule.alias.casefold() in lowered:
                        hit_aliases.append(rule.alias)
                elif rule.pattern and rule.pattern.search(haystack):
                    hit_aliases.append(rule.alias)

            if hit_aliases:
                deduped = []
                seen = set()
                for alias in hit_aliases:
                    key = alias.casefold()
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(alias)
                matches.append(MatchResult(company=company, aliases=deduped))

        return matches


def _compile_alias(alias: str) -> _AliasRule:
    value = alias.strip()
    if not value:
        return _AliasRule(alias=value, pattern=None, use_substring=True)
    escaped = re.escape(value)
    escaped = escaped.replace(r"\ ", r"\s+")
    if LATIN_PATTERN.search(value):
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
        return _AliasRule(alias=value, pattern=pattern, use_substring=False)
    boundary_chars = _build_non_latin_boundary_chars(value)
    pattern = re.compile(rf"(?<![{boundary_chars}]){escaped}(?![{boundary_chars}])")
    return _AliasRule(alias=value, pattern=pattern, use_substring=False)


def find_matching_aliases(text: str, aliases: List[str]) -> List[str]:
    haystack = normalize_whitespace(text)
    lowered = haystack.casefold()
    hits: List[str] = []
    for alias in aliases:
        rule = _compile_alias(alias)
        if rule.use_substring:
            if rule.alias.casefold() in lowered:
                hits.append(rule.alias)
        elif rule.pattern and rule.pattern.search(haystack):
            hits.append(rule.alias)

    deduped = []
    seen = set()
    for alias in hits:
        key = alias.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(alias)
    return deduped


def is_short_latin_alias(alias: str) -> bool:
    value = alias.strip()
    if not value:
        return False
    compact = re.sub(r"[^A-Za-z0-9]", "", value)
    return bool(compact) and compact.isascii() and compact.isalpha() and len(compact) <= 4


def _build_non_latin_boundary_chars(alias: str) -> str:
    chunks = ["A-Za-z0-9_"]
    if HIRAGANA_PATTERN.search(alias):
        chunks.append(r"\u3040-\u309f")
    if KATAKANA_PATTERN.search(alias):
        chunks.append(r"\u30a0-\u30ff\uff66-\uff9f")
    if HAN_PATTERN.search(alias):
        chunks.append(r"\u3400-\u4dbf\u4e00-\u9fff")
    if HANGUL_PATTERN.search(alias):
        chunks.append(r"\uac00-\ud7a3")
    return "".join(chunks)
