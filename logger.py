"""Декоратор для логирования времени выполнения функции."""

import functools
import logging
import time
from typing import Any, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)


def log_execution_time(func: Callable) -> Callable:
    """Декоратор, логирующий время выполнения функции.

    Измеряет время работы функции и записывает его в лог
    через модуль logging на уровне INFO.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            logging.info(
                'Функция %s выполнена за %.6f сек.',
                func.__name__, elapsed
            )

    return wrapper