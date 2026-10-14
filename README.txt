Требуется: Python 3.10 или новее.
Скачать:   https://www.python.org/downloads//

Шаг 1. Открыть cmd в папке проекта
Шаг 2. Создать .venv

    python -m venv .venv

Шаг 3. Активировать виртуальное окружение

Windows (cmd):

    .venv\Scripts\activate.bat

Шаг 4. Установить зависимости

    pip install -r requirements.txt

Шаг 5. Тесты

5.1 Модульные тесты

    python -m unittest test_search -v

Ожидаемый результат:

    Ran 3 tests in 0.00Xs

    OK

5.2 Проверка кода линтером

    pylint search.py logger.py cli.py

Ожидаемый результат:

    Your code has been rated at 10.00/10

Шаг 6. Использование утилиты

Запускается через `python cli.py` с параметрами.

6.1. Поиск в строке
    python cli.py --string "ababbababa" --sub aba

Результат:

    'aba': (0, 5, 7)

6.2. Несколько подстрок

    python cli.py --string "ababbababa" --sub aba bba

Результат:

    'aba': (0, 5, 7)
    'bba': (3,)

6.3. Цветное выделение

    python cli.py --string "ababbababa" --sub aba bba --color

Выводит строку с подсвеченными найденными подстроками и список позиций.
Каждой подстроке присваивается свой цвет.

6.4. Учёт регистра

По умолчанию регистр не учитывается. Чтобы учитывать — флаг `--case`:

    python cli.py --string "aAbCbccaAbC" --sub "abc"

    python cli.py --string "aAbCbccaAbC" --sub "abc" --case

Результат:
    'abc': (1, 8)

    'abc': None

6.5. Поиск с конца

    python cli.py --string "abcabc" --sub "abc" --method last

Результат:

    'abc': (3, 0)

6.6. Ограничение количества вхождений

    python cli.py --string "aaa" --sub "a" --count 2

Результат:

    'a': (0, 1)

6.7. Алгоритма поиска

    python cli.py --string "ababbababa" --sub aba

6.8. Поиск в файле

Создайте файл `input.txt` с текстом, например:

    Hello world
    This is a test file
    hello again, world
    Some ERROR occurred

Запуск:

    python cli.py --file input.txt --sub hello world --color

Выводит не более 10 строк текста с подсвеченными совпадениями.

6.9. Ограничение вывода

По умолчанию выводится не более 10 строк. Изменить можно флагом `--limit`:

    python cli.py --file input.txt --sub hello --limit 5


6.10. Справка по всем параметрам

    python cli.py --help
