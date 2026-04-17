import sys
from dataclasses import dataclass
from typing import List, Tuple


KEYWORDS = {
    'int', 'while', 'return', 'using', 'namespace',
    'include'
}

OPERATORS = {'=', '<=', '+', '<<'}

DELIMITERS = {'(', ')', '{', '}', ';', '#', '<', '>'}

identifier_table = {}
int_const_table = {}
float_const_table = {}
string_const_table = {}
bool_const_table = {}
next_id = 1


def get_next_id():
    global next_id
    result = next_id
    next_id += 1
    return result


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int


class LexerError:
    def __init__(self, error_type: str, message: str, line: int, column: int):
        self.error_type = error_type
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []
        self.after_include = False

    def get_current_char(self) -> str:
        if self.position < len(self.code):
            return self.code[self.position]
        return ''

    def peek_next_char(self) -> str:
        if self.position + 1 < len(self.code):
            return self.code[self.position + 1]
        return ''

    def advance(self):
        if self.get_current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def skip_whitespace(self):
        while self.position < len(self.code) and self.get_current_char().isspace():
            self.advance()

    def read_identifier_or_keyword(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position

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

        while self.position < len(self.code) and (self.get_current_char().isalnum() or self.get_current_char() == '_'):
            self.advance()

        lexeme = self.code[start_pos:self.position]

        if lexeme[0].isdigit():
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Идентификатор не может начинаться с цифры: '{lexeme}'",
                start_line, start_col
            ))
            return 'ERROR', lexeme

        if lexeme in KEYWORDS:
            return 'KEYWORD', lexeme
        else:
            if lexeme not in identifier_table:
                identifier_table[lexeme] = get_next_id()
            return 'IDENTIFIER', lexeme

    def read_number(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        has_dot = False

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

        while self.position < len(self.code) and (self.get_current_char().isdigit() or self.get_current_char() == '.'):
            if self.get_current_char() == '.':
                if has_dot:
                    self.errors.append(LexerError(
                        "LEXICAL_ERROR",
                        "Некорректное число: две точки подряд",
                        start_line, start_col
                    ))
                    while self.position < len(
                            self.code) and not self.get_current_char().isspace() and self.get_current_char() not in DELIMITERS and self.get_current_char() not in OPERATORS:
                        self.advance()
                    return 'ERROR', self.code[start_pos:self.position]
                has_dot = True
            self.advance()

        lexeme = self.code[start_pos:self.position]

        # Проверка: после числа идут буквы или подчёркивание (нет разделителя)
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

        if has_dot:
            if lexeme not in float_const_table:
                float_const_table[lexeme] = get_next_id()
            return 'CONSTANT_FLOAT', lexeme
        else:
            if lexeme not in int_const_table:
                int_const_table[lexeme] = get_next_id()
            return 'CONSTANT_INT', lexeme

    def read_operator_or_delimiter(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        current = self.get_current_char()
        next_char = self.peek_next_char()

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

        double_chars = ['<<', '>=', '<=', '==', '!=', '++', '--']
        if (current + next_char) in double_chars:
            lexeme = current + next_char
            self.advance()
            self.advance()
            return 'OPERATOR', lexeme

        if current in OPERATORS:
            self.advance()
            return 'OPERATOR', current

        if current in DELIMITERS:
            self.advance()
            return 'DELIMITER', current

        self.errors.append(LexerError(
            "LEXICAL_ERROR",
            f"Неизвестный символ: '{current}'",
            start_line, start_col
        ))
        self.advance()
        return 'ERROR', current

    def read_string(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        self.advance()

        while self.position < len(self.code) and self.get_current_char() != '"':
            if self.get_current_char() == '\n':
                self.errors.append(LexerError(
                    "LEXICAL_ERROR",
                    "Незакрытый строковый литерал",
                    start_line, start_col
                ))
                return 'ERROR', self.code[start_pos:self.position]
            self.advance()

        if self.position >= len(self.code):
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                "Незакрытый строковый литерал",
                start_line, start_col
            ))
            return 'ERROR', self.code[start_pos:self.position]

        self.advance()
        lexeme = self.code[start_pos:self.position]

        if lexeme not in string_const_table:
            string_const_table[lexeme] = get_next_id()
        return 'CONSTANT_STRING', lexeme

    def tokenize(self) -> List[Token]:
        while self.position < len(self.code):
            char = self.get_current_char()

            if char.isspace():
                self.skip_whitespace()
                continue

            if char.isalpha() or char == '_':
                token_type, lexeme = self.read_identifier_or_keyword()
                if token_type != 'ERROR':
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

    def print_result(self):
        print("\n" + "-" * 40)
        print(f"{'Лексема':<20} | Тип")
        print("-" * 40)
        for token in self.tokens:
            print(f"{token.lexeme:<20} | {token.type}")
        print("-" * 40)

        token_list = [(token.type, token.lexeme) for token in self.tokens]
        print("\n" + str(token_list))


        if self.errors:
            print("\nОШИБКИ ЛЕКСИЧЕСКОГО АНАЛИЗА:")
            for err in self.errors:
                print(f"  {err.error_type}: Строка {err.line}, позиция {err.column} - {err.message}")
            print(f"\nЛексический анализ завершён с ошибками. Обнаружено {len(self.errors)} ошибок.")
        else:
            print("\nЛексический анализ завершён успешно. Ошибок не найдено.")

        print(f"\nКоличество токенов: {len(self.tokens)}")


def read_cleaned_code(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден")
        sys.exit(1)


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


if __name__ == "__main__":
    main()