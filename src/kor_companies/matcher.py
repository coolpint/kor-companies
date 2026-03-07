from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .models import CompanyConfig
from .utils import normalize_whitespace

LATIN_PATTERN = re.compile(r"[A-Za-z]")


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
    if LATIN_PATTERN.search(value):
        escaped = re.escape(value)
        escaped = escaped.replace(r"\ ", r"\s+")
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
        return _AliasRule(alias=value, pattern=pattern, use_substring=False)
    return _AliasRule(alias=value, pattern=None, use_substring=True)

