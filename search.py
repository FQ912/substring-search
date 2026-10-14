"""Модуль поиска подстрок в строке.

Реализован алгоритм Бойера-Мура (bad character + good suffix).
Основная функция search() возвращает индексы начала всех вхождений
одной или нескольких подстрок.
"""

from typing import Optional, Union

__all__ = ['search']


# ---------------------------------------------------------------------------
# Вспомогательные утилиты
# ---------------------------------------------------------------------------

def _normalize(string: str, case_sensitivity: bool) -> str:
    """Приводит строку к нужному регистру."""
    return string if case_sensitivity else string.lower()


def _to_tuple_or_none(items):
    """Преобразует список в кортеж, пустой список -> None."""
    return tuple(items) if items else None


# ---------------------------------------------------------------------------
# Алгоритм Бойера-Мура
# ---------------------------------------------------------------------------

def _bm_bad_character(pattern: str) -> dict:
    """Таблица «плохого символа» для алгоритма Бойера-Мура."""
    table = {}
    for i, ch in enumerate(pattern):
        table[ch] = i
    return table


def _bm_good_suffix(pattern: str) -> list:
    """Таблица «хорошего суффикса» для алгоритма Бойера-Мура."""
    m = len(pattern)
    shift = [m] * (m + 1)
    border = [0] * (m + 1)
    i = m
    j = m + 1
    border[i] = j
    while i > 0:
        while j <= m and pattern[i - 1] != pattern[j - 1]:
            if shift[j] == m:
                shift[j] = j - i
            j = border[j]
        i -= 1
        j -= 1
        border[i] = j
    j = border[0]
    for i in range(m + 1):
        if shift[i] == m:
            shift[i] = j
        if i == j:
            j = border[j]
    return shift


def bm_search(string: str, pattern: str) -> list:
    """Алгоритм Бойера-Мура (bad character + good suffix).

    Возвращает список индексов начала всех вхождений pattern в string.
    """
    if not pattern or not string or len(pattern) > len(string):
        return []

    m = len(pattern)
    n = len(string)
    bad = _bm_bad_character(pattern)
    good = _bm_good_suffix(pattern)
    result = []
    i = 0
    while i <= n - m:
        j = m - 1
        while j >= 0 and pattern[j] == string[i + j]:
            j -= 1
        if j < 0:
            result.append(i)
            i += good[0]
        else:
            bad_shift = j - bad.get(string[i + j], -1)
            good_shift = good[j + 1]
            i += max(bad_shift, good_shift, 1)
    return result


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def _search_one(string: str, pattern: str, method: str,
                count: Optional[int]) -> Optional[tuple]:
    """Поиск одной подстроки."""
    if not pattern:
        return None

    all_matches = bm_search(string, pattern)

    if method == 'last':
        all_matches = all_matches[::-1]

    if count is not None:
        all_matches = all_matches[:count]

    return _to_tuple_or_none(all_matches)


def _search_many(string: str, patterns: list, method: str,
                 count: Optional[int]) -> Optional[dict]:
    """Поиск нескольких подстрок.

    Лимит count распределяется между подстроками так:

    1. Сначала каждой подстроке (в порядке перечисления) гарантируется
       минимум одно совпадение, если оно у неё есть, пока не исчерпается count.
    2. Затем оставшийся лимит жадно раздаётся по порядку подстрокам,
       у которых ещё остались невыбранные совпадения.

    Возвращает None, если ни для одной подстроки совпадений не найдено.
    """
    raw = {}
    for p in patterns:
        matches = bm_search(string, p)
        if method == 'last':
            matches = matches[::-1]
        raw[p] = list(matches)

    taken = {p: [] for p in patterns}
    remaining = count

    if remaining is not None:
        for p in patterns:
            if remaining <= 0:
                break
            if raw[p]:
                taken[p].append(raw[p].pop(0))
                remaining -= 1

        for p in patterns:
            if remaining <= 0:
                break
            extra = raw[p][:remaining]
            taken[p].extend(extra)
            remaining -= len(extra)
    else:
        for p in patterns:
            taken[p] = raw[p]

    any_found = any(taken[p] for p in patterns)
    if not any_found:
        return None

    return {p: _to_tuple_or_none(taken[p]) for p in patterns}


def search(string: str,
           sub_string: Union[str, list],
           case_sensitivity: bool = False,
           method: str = 'first',
           count: Optional[int] = None) -> Optional[Union[tuple, dict]]:
    """Поиск всех вхождений подстроки (подстрок) в строке.

    :param string: исходная строка
    :param sub_string: одна подстрока или список подстрок
    :param case_sensitivity: True — учитывать регистр, False — нет
    :param method: 'first' — прямой порядок, 'last' — обратный
    :param count: максимальное количество вхождений (None — все)
    :return: кортеж индексов для одной подстроки,
             словарь {подстрока: кортеж индексов | None} для нескольких,
             None если совпадений нет.
    """
    if method not in ('first', 'last'):
        raise ValueError("method должен быть 'first' или 'last'")

    norm_string = _normalize(string, case_sensitivity)

    if isinstance(sub_string, str):
        norm_pattern = _normalize(sub_string, case_sensitivity)
        return _search_one(norm_string, norm_pattern, method, count)

    if isinstance(sub_string, (list, tuple)):
        patterns = list(sub_string)
        norm_patterns = [_normalize(p, case_sensitivity) for p in patterns]
        return _search_many(norm_string, norm_patterns, method, count)

    raise TypeError('sub_string должен быть str или list[str]')