"""Консольная утилита поиска подстрок в строке или файле.

Примеры запуска:
    python cli.py --string "ababbababa" --sub "aba"
    python cli.py --string "ababbababa" --sub "aba" "bba" --color
    python cli.py --file input.txt --sub "aba" --count 5
    python cli.py --string "abcabc" --sub "abc" --method last --limit 3
"""

import argparse
import sys
from typing import Optional

from colorama import Fore, Style, init as colorama_init

from search import search
from logger import log_execution_time

colorama_init(autoreset=True)

COLORS = [
    Fore.RED,
    Fore.GREEN,
    Fore.YELLOW,
    Fore.BLUE,
    Fore.MAGENTA,
    Fore.CYAN,
    Fore.LIGHTRED_EX,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTYELLOW_EX,
    Fore.LIGHTBLUE_EX,
]

MAX_LINES = 10


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog='substring-search',
        description='Поиск подстрок в строке или файле с цветовым выделением.',
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        '--string', '-s', type=str,
        help='Целевая строка для поиска.',
    )
    source.add_argument(
        '--file', '-f', type=str,
        help='Путь до файла, в котором производится поиск.',
    )
    parser.add_argument(
        '--sub', '-p', nargs='+', required=True,
        help='Одна или несколько подстрок для поиска.',
    )
    parser.add_argument(
        '--case', '-c', action='store_true',
        help='Учитывать регистр (по умолчанию — нет).',
    )
    parser.add_argument(
        '--method', '-m', choices=('first', 'last'), default='first',
        help="Порядок поиска: 'first' (с начала) или 'last' (с конца).",
    )
    parser.add_argument(
        '--count', '-k', type=int, default=None,
        help='Общее количество вхождений k (по умолчанию — все).',
    )
    parser.add_argument(
        '--color', action='store_true',
        help='Выделять найденные подстроки цветом.',
    )
    parser.add_argument(
        '--limit', type=int, default=MAX_LINES,
        help=f'Максимум строк для вывода (по умолчанию {MAX_LINES}).',
    )
    return parser


def read_source(args: argparse.Namespace) -> str:
    """Читает исходный текст из строки или файла."""
    if args.string is not None:
        return args.string
    try:
        with open(args.file, 'r', encoding='utf-8') as fh:
            return fh.read()
    except OSError as exc:
        print(f'Ошибка чтения файла: {exc}', file=sys.stderr)
        sys.exit(1)


@log_execution_time
def _run_search(text, target, case_sensitivity, method, count):
    """Обёртка над search() с логированием времени выполнения."""
    return search(
        text, target,
        case_sensitivity=case_sensitivity,
        method=method,
        count=count,
    )


def _collect_matches(result, patterns):
    """Преобразует результат search() в словарь {подстрока: [индексы]}."""
    if isinstance(result, dict):
        return {p: list(result.get(p) or []) for p in patterns}
    if result is None:
        return {p: [] for p in patterns}
    return {patterns[0]: list(result)}


def print_plain(result, patterns) -> None:
    """Вывод результата без цветового выделения."""
    matches = _collect_matches(result, patterns)
    found_any = False
    for pat, positions in matches.items():
        if positions:
            found_any = True
            print(f'{pat!r}: {tuple(positions)}')
        else:
            print(f'{pat!r}: None')
    if not found_any:
        print('Совпадений не найдено.')


def _highlight_line(line: str, matches: dict, color_map: dict) -> str:
    """Раскрашивает найденные подстроки в строке."""
    positions = []
    for pat, pos_list in matches.items():
        color = color_map[pat]
        for start in pos_list:
            positions.append((start, len(pat), color))

    if not positions:
        return line

    positions.sort(key=lambda x: (x[0], -x[1]))
    out = []
    cursor = 0
    for start, length, color in positions:
        if start < cursor:
            continue
        out.append(line[cursor:start])
        out.append(f'{color}{line[start:start + length]}{Style.RESET_ALL}')
        cursor = start + length
    out.append(line[cursor:])
    return ''.join(out)


def print_colored(text: str, result, patterns) -> None:
    """Вывод текста с цветовым выделением найденных подстрок."""
    matches = _collect_matches(result, patterns)
    color_map = {p: COLORS[i % len(COLORS)] for i, p in enumerate(patterns)}

    lines = text.splitlines() or [text]
    shown = lines[:MAX_LINES]

    for line in shown:
        print(_highlight_line(line, matches, color_map))

    if len(lines) > MAX_LINES:
        print(f'... (показано {MAX_LINES} из {len(lines)} строк)')

    print('\nНайденные позиции:')
    for pat, positions in matches.items():
        if positions:
            print(f'  {color_map[pat]}{pat!r}{Style.RESET_ALL}: {tuple(positions)}')
        else:
            print(f'  {pat!r}: None')


def main(argv: Optional[list] = None) -> int:
    """Точка входа консольной утилиты."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.count is not None and args.count < 1:
        print('Параметр --count должен быть >= 1', file=sys.stderr)
        return 2

    text = read_source(args)
    patterns = args.sub
    target = patterns[0] if len(patterns) == 1 else patterns

    result = _run_search(
        text, target,
        case_sensitivity=args.case,
        method=args.method,
        count=args.count,
    )

    if args.color:
        print_colored(text, result, patterns)
    else:
        print_plain(result, patterns)

    return 0


if __name__ == '__main__':
    sys.exit(main())