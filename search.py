"""Модуль поиска подстрок в строке.

Реализованы алгоритмы:
- Кнута-Морриса-Пратта (KMP)
- Бойера-Мура (BM)
- Ахо-Корасик (AC)
- Рабина-Карпа (RK) с кольцевым хешем
- Бойера-Мура-Хорспула (BMH)

Основная функция search() возвращает индексы начала всех вхождений
одной или нескольких подстрок.
"""

from typing import Optional, Union

__all__ = ['search']

ALGORITHMS = ('kmp', 'bm', 'ac', 'rk', 'bmh')


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
# 1. Кнута-Морриса-Пратта
# ---------------------------------------------------------------------------

def _kmp_prefix(pattern: str) -> list:
    """Вычисляет префикс-функцию для алгоритма KMP."""
    n = len(pattern)
    prefix = [0] * n
    j = 0
    for i in range(1, n):
        while j > 0 and pattern[i] != pattern[j]:
            j = prefix[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        prefix[i] = j
    return prefix


def kmp_search(string: str, pattern: str) -> list:
    """Алгоритм Кнута-Морриса-Пратта.

    Возвращает список индексов начала всех вхождений pattern в string.
    """
    if not pattern or not string or len(pattern) > len(string):
        return []

    prefix = _kmp_prefix(pattern)
    result = []
    j = 0
    for i, ch in enumerate(string):
        while j > 0 and ch != pattern[j]:
            j = prefix[j - 1]
        if ch == pattern[j]:
            j += 1
        if j == len(pattern):
            result.append(i - len(pattern) + 1)
            j = prefix[j - 1]
    return result


# ---------------------------------------------------------------------------
# 2. Бойера-Мура
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
    """Алгоритм Бойера-Мура (bad character + good suffix)."""
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
# 3. Ахо-Корасик
# ---------------------------------------------------------------------------

class _AhoCorasickNode:
    """Узел бора для алгоритма Ахо-Корасик."""

    __slots__ = ('children', 'fail', 'output')

    def __init__(self):
        self.children = {}
        self.fail = None
        self.output = []


def _build_aho_corasick(patterns: list):
    """Строит бор и суффиксные ссылки для алгоритма Ахо-Корасик."""
    root = _AhoCorasickNode()
    root.fail = root

    for pat in patterns:
        node = root
        for ch in pat:
            if ch not in node.children:
                node.children[ch] = _AhoCorasickNode()
            node = node.children[ch]
        node.output.append(pat)

    queue = []
    for child in root.children.values():
        child.fail = root
        queue.append(child)

    while queue:
        node = queue.pop(0)
        for ch, child in node.children.items():
            queue.append(child)
            fail = node.fail
            while fail is not root and ch not in fail.children:
                fail = fail.fail
            if ch in fail.children:
                child.fail = fail.children[ch]
            else:
                child.fail = root
            child.output.extend(child.fail.output)

    return root


def aho_corasick_search(string: str, patterns: list) -> dict:
    """Алгоритм Ахо-Корасик для поиска нескольких подстрок."""
    result = {p: [] for p in patterns}
    if not string or not patterns:
        return result

    root = _build_aho_corasick(patterns)
    node = root
    for i, ch in enumerate(string):
        while node is not root and ch not in node.children:
            node = node.fail
        if ch in node.children:
            node = node.children[ch]
        else:
            node = root
        for pat in node.output:
            result[pat].append(i - len(pat) + 1)
    return result


# ---------------------------------------------------------------------------
# 4. Рабина-Карпа (кольцевой хеш)
# ---------------------------------------------------------------------------

class RingHash:
    """Кольцевой хеш для алгоритма Рабина-Карпа.

    Поддерживает добавление символа в конец и удаление символа из начала
    за O(1), что позволяет вычислять хеш каждой подстроки длины m
    за O(1) при скольжении окна.
    """

    __slots__ = ('_base', '_mod', '_hash', '_power', '_length', '_chars')

    def __init__(self, length: int, base: int = 257, mod: int = 2 ** 61 - 1):
        self._base = base
        self._mod = mod
        self._hash = 0
        self._power = 1
        self._length = length
        self._chars = []

    def append(self, ch: str) -> None:
        """Добавляет символ в конец окна."""
        self._hash = (self._hash * self._base + ord(ch)) % self._mod
        # base^(m-1) — только пока окно не заполнилось до длины m-1
        if len(self._chars) < self._length - 1:
            self._power = (self._power * self._base) % self._mod
        self._chars.append(ch)

    def slide(self, new_ch: str) -> None:
        """Сдвигает окно: удаляет первый символ, добавляет новый в конец."""
        old_ch = self._chars.pop(0)
        self._hash = (self._hash - ord(old_ch) * self._power) % self._mod
        self._hash = (self._hash * self._base + ord(new_ch)) % self._mod
        self._chars.append(new_ch)

    @property
    def value(self) -> int:
        """Текущее значение хеша."""
        return self._hash

    @property
    def length(self) -> int:
        """Текущая длина окна."""
        return len(self._chars)


def _hash_string(s: str, base: int = 257, mod: int = 2 ** 61 - 1) -> int:
    """Вычисляет хеш строки."""
    h = 0
    for ch in s:
        h = (h * base + ord(ch)) % mod
    return h


def rabin_karp_search(string: str, pattern: str) -> list:
    """Алгоритм Рабина-Карпа с самостоятельно реализованным кольцевым хешем."""
    if not pattern or not string or len(pattern) > len(string):
        return []

    m = len(pattern)
    n = len(string)
    pattern_hash = _hash_string(pattern)
    result = []

    window = RingHash(m)
    for i in range(m):
        window.append(string[i])

    if window.value == pattern_hash and string[:m] == pattern:
        result.append(0)

    for i in range(m, n):
        window.slide(string[i])
        if window.value == pattern_hash:
            start = i - m + 1
            if string[start:start + m] == pattern:
                result.append(start)
    return result


# ---------------------------------------------------------------------------
# 5. Бойера-Мура-Хорспула
# ---------------------------------------------------------------------------

def bmh_search(string: str, pattern: str) -> list:
    """Алгоритм Бойера-Мура-Хорспула."""
    if not pattern or not string or len(pattern) > len(string):
        return []

    m = len(pattern)
    n = len(string)
    shift = {}
    for i in range(m - 1):
        shift[pattern[i]] = m - 1 - i
    result = []
    i = 0
    while i <= n - m:
        j = m - 1
        while j >= 0 and pattern[j] == string[i + j]:
            j -= 1
        if j < 0:
            result.append(i)
            i += 1
        else:
            i += shift.get(string[i + m - 1], m)
    return result


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

_ALGO_MAP = {
    'kmp': kmp_search,
    'bm': bm_search,
    'bmh': bmh_search,
    'rk': rabin_karp_search,
}


def _search_one(string: str, pattern: str, method: str,
                algorithm: str,
                count: Optional[int]) -> Optional[tuple]:
    """Поиск одной подстроки выбранным алгоритмом."""
    if not pattern:
        return None

    if algorithm == 'ac':
        all_matches = aho_corasick_search(string, [pattern])[pattern]
    else:
        all_matches = _ALGO_MAP[algorithm](string, pattern)

    if method == 'last':
        all_matches = all_matches[::-1]

    if count is not None:
        all_matches = all_matches[:count]

    return _to_tuple_or_none(all_matches)


def _search_many(string: str, patterns: list, method: str,
                 algorithm: str,
                 count: Optional[int]) -> Optional[dict]:
    """Поиск нескольких подстрок.

    Лимит count распределяется между подстроками так:

    1. Сначала каждой подстроке (в порядке перечисления) гарантируется
       минимум одно совпадение, если оно у неё есть, пока не исчерпается count.
    2. Затем оставшийся лимит жадно раздаётся по порядку подстрокам,
       у которых ещё остались невыбранные совпадения.

    Возвращает None, если ни для одной подстроки совпадений не найдено.
    """
    # 1. Собираем все совпадения для каждой подстроки
    raw = {}
    for p in patterns:
        if algorithm == 'ac':
            matches = aho_corasick_search(string, [p])[p]
        else:
            matches = _ALGO_MAP[algorithm](string, p)
        if method == 'last':
            matches = matches[::-1]
        raw[p] = list(matches)

    # 2. Фаза 1: гарантируем по одному совпадению каждой подстроке
    taken = {p: [] for p in patterns}
    remaining = count

    if remaining is not None:
        for p in patterns:
            if remaining <= 0:
                break
            if raw[p]:
                taken[p].append(raw[p].pop(0))
                remaining -= 1

        # 3. Фаза 2: жадно добавляем остаток
        for p in patterns:
            if remaining <= 0:
                break
            extra = raw[p][:remaining]
            taken[p].extend(extra)
            remaining -= len(extra)
    else:
        for p in patterns:
            taken[p] = raw[p]

    # 4. Формируем результат; None, если ничего не нашли
    any_found = any(taken[p] for p in patterns)
    if not any_found:
        return None

    return {p: _to_tuple_or_none(taken[p]) for p in patterns}


def search(string: str,
           sub_string: Union[str, list],
           case_sensitivity: bool = False,
           method: str = 'first',
           count: Optional[int] = None,
           algorithm: str = 'kmp') -> Optional[Union[tuple, dict]]:
    """Поиск всех вхождений подстроки (подстрок) в строке.

    :param string: исходная строка
    :param sub_string: одна подстрока или список подстрок
    :param case_sensitivity: True — учитывать регистр, False — нет
    :param method: 'first' — прямой порядок, 'last' — обратный
    :param count: максимальное количество вхождений (None — все)
    :param algorithm: 'kmp' | 'bm' | 'ac' | 'rk' | 'bmh'
    :return: кортеж индексов для одной подстроки,
             словарь {подстрока: кортеж индексов | None} для нескольких,
             None если совпадений нет.
    """
    if method not in ('first', 'last'):
        raise ValueError("method должен быть 'first' или 'last'")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm должен быть одним из {ALGORITHMS}")

    norm_string = _normalize(string, case_sensitivity)

    if isinstance(sub_string, str):
        norm_pattern = _normalize(sub_string, case_sensitivity)
        return _search_one(norm_string, norm_pattern, method, algorithm, count)

    if isinstance(sub_string, (list, tuple)):
        patterns = list(sub_string)
        norm_patterns = [_normalize(p, case_sensitivity) for p in patterns]
        return _search_many(norm_string, norm_patterns, method, algorithm, count)

    raise TypeError('sub_string должен быть str или list[str]')