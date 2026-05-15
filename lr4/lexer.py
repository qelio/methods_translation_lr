import sys
from dataclasses import dataclass
from typing import List, Tuple


# Ключевые слова языка
KEYWORDS = {
    'int', 'while', 'return', 'using', 'namespace',
    'include'
}

# Операторы
OPERATORS = {'=', '<=', '+', '<<'}

# Разделители
DELIMITERS = {'(', ')', '{', '}', ';', '#', '<', '>'}

# Таблицы для хранения идентификаторов и констант
identifier_table = {}
int_const_table = {}
float_const_table = {}
string_const_table = {}
bool_const_table = {}

# Глобальный счетчик ID
next_id = 1


# Функция получения следующего уникального ID
def get_next_id():
    global next_id
    result = next_id
    next_id += 1
    return result


# Класс токена
@dataclass
class Token:
    type: str      # тип токена
    lexeme: str    # сама лексема
    line: int      # строка
    column: int    # позиция


# Класс ошибки лексера
class LexerError:
    def __init__(self, error_type: str, message: str, line: int, column: int):
        self.error_type = error_type
        self.message = message
        self.line = line
        self.column = column


# Основной класс лексического анализатора
class Lexer:
    def __init__(self, code: str):
        self.code = code                # исходный код
        self.position = 0              # текущая позиция
        self.line = 1                  # текущая строка
        self.column = 1                # текущий столбец
        self.tokens: List[Token] = []  # список токенов
        self.errors: List[LexerError] = []  # список ошибок
        self.after_include = False     # флаг после #include

    # Получить текущий символ
    def get_current_char(self) -> str:
        if self.position < len(self.code):
            return self.code[self.position]
        return ''

    # Посмотреть следующий символ
    def peek_next_char(self) -> str:
        if self.position + 1 < len(self.code):
            return self.code[self.position + 1]
        return ''

    # Сдвиг позиции
    def advance(self):
        if self.get_current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    # Пропуск пробелов
    def skip_whitespace(self):
        while self.position < len(self.code) and self.get_current_char().isspace():
            self.advance()

    # Чтение идентификатора или ключевого слова
    def read_identifier_or_keyword(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position

        # Проверка ошибки после #include
        if self.after_include and self.get_current_char().isdigit():
            while self.position < len(self.code) and (
                    self.get_current_char().isalnum() or self.get_current_char() == '_'):
                self.advance()
            lexeme = self.code[start_pos:self.position]
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Некорректная директива #include: ожидается '<' или '\"', но найдено '{lexeme}'",
                start_line, start_col
            ))
            self.after_include = False
            return 'ERROR', lexeme

        # Чтение последовательности букв/цифр/_
        while self.position < len(self.code) and (self.get_current_char().isalnum() or self.get_current_char() == '_'):
            self.advance()

        lexeme = self.code[start_pos:self.position]

        # Ошибка: идентификатор начинается с цифры
        if lexeme[0].isdigit():
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Идентификатор не может начинаться с цифры: '{lexeme}'",
                start_line, start_col
            ))
            return 'ERROR', lexeme

        # Проверка: ключевое слово или идентификатор
        if lexeme in KEYWORDS:
            return 'KEYWORD', lexeme
        else:
            if lexeme not in identifier_table:
                identifier_table[lexeme] = get_next_id()
            return 'IDENTIFIER', lexeme

    # Чтение числа
    def read_number(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        has_dot = False  # флаг для float

        # Ошибка после #include
        if self.after_include:
            while self.position < len(self.code) and (
                    self.get_current_char().isdigit() or self.get_current_char() == '.'):
                self.advance()
            lexeme = self.code[start_pos:self.position]
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Некорректная директива #include: ожидается '<' или '\"', но найдено число '{lexeme}'",
                start_line, start_col
            ))
            self.after_include = False
            return 'ERROR', lexeme

        # Чтение числа (int/float)
        while self.position < len(self.code) and (self.get_current_char().isdigit() or self.get_current_char() == '.'):
            if self.get_current_char() == '.':
                if has_dot:
                    # Ошибка: две точки
                    self.errors.append(LexerError(
                        "LEXICAL_ERROR",
                        "Некорректное число: две точки подряд",
                        start_line, start_col
                    ))
                    # пропускаем остаток
                    while self.position < len(
                            self.code) and not self.get_current_char().isspace() and self.get_current_char() not in DELIMITERS and self.get_current_char() not in OPERATORS:
                        self.advance()
                    return 'ERROR', self.code[start_pos:self.position]
                has_dot = True
            self.advance()

        lexeme = self.code[start_pos:self.position]

        # Ошибка: число + идентификатор без разделителя
        if self.position < len(self.code) and (self.get_current_char().isalpha() or self.get_current_char() == '_'):
            remaining_start = self.position
            while self.position < len(self.code) and (
                    self.get_current_char().isalnum() or self.get_current_char() == '_'):
                self.advance()
            remaining = self.code[remaining_start:self.position]
            full_lexeme = self.code[start_pos:self.position]

            if remaining in KEYWORDS:
                self.errors.append(LexerError(
                    "LEXICAL_ERROR",
                    f"Отсутствует разделитель между числом '{lexeme}' и ключевым словом '{remaining}'",
                    start_line, start_col
                ))
            else:
                self.errors.append(LexerError(
                    "LEXICAL_ERROR",
                    f"Идентификатор не может начинаться с цифры: '{full_lexeme}'",
                    start_line, start_col
                ))
            return 'ERROR', full_lexeme

        # Сохранение числа
        if has_dot:
            if lexeme not in float_const_table:
                float_const_table[lexeme] = get_next_id()
            return 'CONSTANT_FLOAT', lexeme
        else:
            if lexeme not in int_const_table:
                int_const_table[lexeme] = get_next_id()
            return 'CONSTANT_INT', lexeme

    # Чтение операторов и разделителей
    def read_operator_or_delimiter(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        current = self.get_current_char()
        next_char = self.peek_next_char()

        # Обработка #include
        if current == '#':
            self.advance()
            self.skip_whitespace()

            if self.position + 7 <= len(self.code) and self.code[self.position:self.position + 7].lower() == 'include':
                self.after_include = True
                include_lexeme = self.code[self.position:self.position + 7]
                self.position += 7
                self.column += 7
                self.tokens.append(Token('KEYWORD', include_lexeme, start_line, start_col))
                self.skip_whitespace()

                # Проверка следующего символа
                if self.position < len(self.code):
                    next_ch = self.get_current_char()
                    if next_ch.isdigit() or next_ch.isalpha():
                        self.errors.append(LexerError(
                            "LEXICAL_ERROR",
                            f"Некорректная директива #include: ожидается '<' или '\"', но найдено '{next_ch}'",
                            self.line, self.column
                        ))
                        self.advance()
                        self.after_include = False
                        return 'ERROR', next_ch
                    elif next_ch == '<' or next_ch == '"':
                        self.after_include = False
                else:
                    self.after_include = False
                return 'DELIMITER', '#'
            return 'DELIMITER', '#'

        # Двухсимвольные операторы
        double_chars = ['<<', '>=', '<=', '==', '!=', '++', '--']
        if (current + next_char) in double_chars:
            lexeme = current + next_char
            self.advance()
            self.advance()
            return 'OPERATOR', lexeme

        # Одинарные операторы
        if current in OPERATORS:
            self.advance()
            return 'OPERATOR', current

        # Разделители
        if current in DELIMITERS:
            self.advance()
            return 'DELIMITER', current

        # Неизвестный символ
        self.errors.append(LexerError(
            "LEXICAL_ERROR",
            f"Неизвестный символ: '{current}'",
            start_line, start_col
        ))
        self.advance()
        return 'ERROR', current

    # Чтение строкового литерала
    def read_string(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        self.advance()

        # Чтение до закрывающей кавычки
        while self.position < len(self.code) and self.get_current_char() != '"':
            if self.get_current_char() == '\n':
                self.errors.append(LexerError(
                    "LEXICAL_ERROR",
                    "Незакрытый строковый литерал",
                    start_line, start_col
                ))
                return 'ERROR', self.code[start_pos:self.position]
            self.advance()

        # Если не нашли закрытие
        if self.position >= len(self.code):
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                "Незакрытый строковый литерал",
                start_line, start_col
            ))
            return 'ERROR', self.code[start_pos:self.position]

        self.advance()
        lexeme = self.code[start_pos:self.position]

        # Сохраняем строку
        if lexeme not in string_const_table:
            string_const_table[lexeme] = get_next_id()
        return 'CONSTANT_STRING', lexeme

    # Основной процесс токенизации
    def tokenize(self) -> List[Token]:
        while self.position < len(self.code):
            char = self.get_current_char()

            if char.isspace():
                self.skip_whitespace()
                continue

            if char.isalpha() or char == '_':
                token_type, lexeme = self.read_identifier_or_keyword()
                if token_type != 'ERROR':
                    # обработка bool
                    if token_type == 'IDENTIFIER' and (lexeme == 'true' or lexeme == 'false'):
                        token_type = 'CONSTANT_BOOL'
                        if lexeme not in bool_const_table:
                            bool_const_table[lexeme] = get_next_id()
                    self.tokens.append(Token(token_type, lexeme, self.line, self.column - len(lexeme)))
                continue

            if char.isdigit():
                token_type, lexeme = self.read_number()
                if token_type != 'ERROR':
                    self.tokens.append(Token(token_type, lexeme, self.line, self.column - len(lexeme)))
                continue

            if char == '"':
                token_type, lexeme = self.read_string()
                if token_type != 'ERROR':
                    self.tokens.append(Token(token_type, lexeme, self.line, self.column - len(lexeme)))
                continue

            token_type, lexeme = self.read_operator_or_delimiter()
            if token_type != 'ERROR':
                self.tokens.append(Token(token_type, lexeme, self.line, self.column - len(lexeme)))
            continue

        return self.tokens

    # Вывод результата
    def print_result(self):
        print("\n" + "-" * 40)
        print(f"{'Лексема':<20} | Тип")
        print("-" * 40)
        for token in self.tokens:
            print(f"{token.lexeme:<20} | {token.type}")
        print("-" * 40)

        token_list = [(token.type, token.lexeme) for token in self.tokens]
        print("\n" + str(token_list))

        # Вывод ошибок
        if self.errors:
            print("\nОШИБКИ ЛЕКСИЧЕСКОГО АНАЛИЗА:")
            for err in self.errors:
                print(f"  {err.error_type}: Строка {err.line}, позиция {err.column} - {err.message}")
            print(f"\nЛексический анализ завершён с ошибками. Обнаружено {len(self.errors)} ошибок.")
        else:
            print("\nЛексический анализ завершён успешно. Ошибок не найдено.")

        print(f"\nКоличество токенов: {len(self.tokens)}")


# Чтение файла
def read_cleaned_code(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден")
        sys.exit(1)


# Точка входа
def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "cleaned_test.cpp"

    print(f"Лексический анализатор")
    print(f"Входной файл: {filename}")

    code = read_cleaned_code(filename)

    print("\nИсходный код для анализа:")
    print("-" * 40)
    print(code)
    print("-" * 40)

    lexer = Lexer(code)
    lexer.tokenize()
    lexer.print_result()


# Запуск программы
if __name__ == "__main__":
    main()