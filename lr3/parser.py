import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional


# =========================
# ФИКСИРОВАННЫЕ ТАБЛИЦЫ
# =========================

# Ключевые слова языка, которые используются в тестовой программе
KEYWORDS = {
    'int', 'while', 'return', 'using', 'namespace', 'include'
}

# Операторы
OPERATORS = {'=', '<=', '+', '<<'}

# Разделители
DELIMITERS = {'(', ')', '{', '}', ';', '#', '<', '>'}

# Фиксированная таблица идентификаторов из тестовой программы
IDENTIFIER_TABLE = {
    'main': 1,      # Главная функция
    'i': 2,         # Переменная-счётчик
    'sum': 3,       # Переменная для суммы
    'iostream': 4,  # Заголовочный файл
    'cout': 5,      # Объект стандартного вывода
    'endl': 6,      # Манипулятор конца строки
    'std': 7        # Стандартное пространство имён
}

# Таблицы констант
int_const_table = {}
float_const_table = {}
string_const_table = {}
bool_const_table = {}

next_const_id = 1


def get_next_const_id():
    global next_const_id
    result = next_const_id
    next_const_id += 1
    return result


# =========================
# ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР
# =========================

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

    def skip_comment(self) -> bool:
        current = self.get_current_char()
        next_char = self.peek_next_char()

        # Однострочный комментарий //
        if current == '/' and next_char == '/':
            while self.position < len(self.code) and self.get_current_char() != '\n':
                self.advance()
            return True

        # Многострочный комментарий /* ... */
        if current == '/' and next_char == '*':
            start_line = self.line
            start_col = self.column

            self.advance()
            self.advance()

            while self.position < len(self.code):
                if self.get_current_char() == '*' and self.peek_next_char() == '/':
                    self.advance()
                    self.advance()
                    return True
                self.advance()

            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                "Незакрытый многострочный комментарий",
                start_line,
                start_col
            ))
            return True

        return False

    def read_identifier_or_keyword(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position

        while self.position < len(self.code) and (
            self.get_current_char().isalnum() or self.get_current_char() == '_'
        ):
            self.advance()

        lexeme = self.code[start_pos:self.position]

        if lexeme[0].isdigit():
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Идентификатор не может начинаться с цифры: '{lexeme}'",
                start_line,
                start_col
            ))
            return 'ERROR', lexeme

        if lexeme in KEYWORDS:
            return 'KEYWORD', lexeme

        if lexeme == 'true' or lexeme == 'false':
            if lexeme not in bool_const_table:
                bool_const_table[lexeme] = get_next_const_id()
            return 'CONSTANT_BOOL', lexeme

        # Главное исправление:
        # идентификатор должен быть только из фиксированной таблицы
        if lexeme in IDENTIFIER_TABLE:
            return 'IDENTIFIER', lexeme

        self.errors.append(LexerError(
            "LEXICAL_ERROR",
            f"Недопустимый идентификатор '{lexeme}'. "
            f"Идентификатор отсутствует в фиксированной таблице идентификаторов",
            start_line,
            start_col
        ))
        return 'ERROR', lexeme

    def read_number(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        has_dot = False

        while self.position < len(self.code) and (
            self.get_current_char().isdigit() or self.get_current_char() == '.'
        ):
            if self.get_current_char() == '.':
                if has_dot:
                    self.errors.append(LexerError(
                        "LEXICAL_ERROR",
                        "Некорректное число: две точки",
                        start_line,
                        start_col
                    ))
                    while (
                        self.position < len(self.code)
                        and not self.get_current_char().isspace()
                        and self.get_current_char() not in DELIMITERS
                        and self.get_current_char() not in OPERATORS
                    ):
                        self.advance()
                    return 'ERROR', self.code[start_pos:self.position]
                has_dot = True
            self.advance()

        lexeme = self.code[start_pos:self.position]

        if self.position < len(self.code) and (
            self.get_current_char().isalpha() or self.get_current_char() == '_'
        ):
            while self.position < len(self.code) and (
                self.get_current_char().isalnum() or self.get_current_char() == '_'
            ):
                self.advance()

            full_lexeme = self.code[start_pos:self.position]

            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                f"Идентификатор не может начинаться с цифры: '{full_lexeme}'",
                start_line,
                start_col
            ))
            return 'ERROR', full_lexeme

        if has_dot:
            if lexeme not in float_const_table:
                float_const_table[lexeme] = get_next_const_id()
            return 'CONSTANT_FLOAT', lexeme

        if lexeme not in int_const_table:
            int_const_table[lexeme] = get_next_const_id()
        return 'CONSTANT_INT', lexeme

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
                    start_line,
                    start_col
                ))
                return 'ERROR', self.code[start_pos:self.position]
            self.advance()

        if self.position >= len(self.code):
            self.errors.append(LexerError(
                "LEXICAL_ERROR",
                "Незакрытый строковый литерал",
                start_line,
                start_col
            ))
            return 'ERROR', self.code[start_pos:self.position]

        self.advance()
        lexeme = self.code[start_pos:self.position]

        if lexeme not in string_const_table:
            string_const_table[lexeme] = get_next_const_id()

        return 'CONSTANT_STRING', lexeme

    def read_operator_or_delimiter(self) -> Tuple[str, str]:
        start_line = self.line
        start_col = self.column
        current = self.get_current_char()
        next_char = self.peek_next_char()

        double_operator = current + next_char
        if double_operator in OPERATORS:
            self.advance()
            self.advance()
            return 'OPERATOR', double_operator

        if current in OPERATORS:
            self.advance()
            return 'OPERATOR', current

        if current in DELIMITERS:
            self.advance()
            return 'DELIMITER', current

        self.errors.append(LexerError(
            "LEXICAL_ERROR",
            f"Неизвестный символ: '{current}'",
            start_line,
            start_col
        ))
        self.advance()
        return 'ERROR', current

    def tokenize(self) -> List[Token]:
        while self.position < len(self.code):
            char = self.get_current_char()

            if char.isspace():
                self.skip_whitespace()
                continue

            if self.skip_comment():
                continue

            if char.isalpha() or char == '_':
                start_col = self.column
                token_type, lexeme = self.read_identifier_or_keyword()
                if token_type != 'ERROR':
                    self.tokens.append(Token(token_type, lexeme, self.line, start_col))
                continue

            if char.isdigit():
                start_col = self.column
                token_type, lexeme = self.read_number()
                if token_type != 'ERROR':
                    self.tokens.append(Token(token_type, lexeme, self.line, start_col))
                continue

            if char == '"':
                start_col = self.column
                token_type, lexeme = self.read_string()
                if token_type != 'ERROR':
                    self.tokens.append(Token(token_type, lexeme, self.line, start_col))
                continue

            start_col = self.column
            token_type, lexeme = self.read_operator_or_delimiter()
            if token_type != 'ERROR':
                self.tokens.append(Token(token_type, lexeme, self.line, start_col))

        return self.tokens

    def print_result(self):
        print("\nТАБЛИЦА ТОКЕНОВ")
        print("-" * 55)
        print(f"{'Лексема':<20} | {'Тип':<15} | {'Строка':<6} | Позиция")
        print("-" * 55)

        for token in self.tokens:
            print(f"{token.lexeme:<20} | {token.type:<15} | {token.line:<6} | {token.column}")

        print("-" * 55)

        print("\nПОТОК ТОКЕНОВ:")
        print([(token.type, token.lexeme) for token in self.tokens])

        print("\nТАБЛИЦА ИДЕНТИФИКАТОРОВ")
        print("-" * 70)
        print(f"{'id':<5} | {'Лексема':<15} | {'Название лексемы':<15} | Комментарий")
        print("-" * 70)

        comments = {
            'main': 'Главная функция',
            'i': 'Переменная-счётчик',
            'sum': 'Переменная для суммы',
            'iostream': 'Заголовочный файл',
            'cout': 'Объект стандартного вывода',
            'endl': 'Манипулятор конца строки',
            'std': 'Стандартное пространство имён'
        }

        for lexeme, ident_id in sorted(IDENTIFIER_TABLE.items(), key=lambda x: x[1]):
            print(f"{ident_id:<5} | {lexeme:<15} | {'IDENTIFIER':<15} | {comments[lexeme]}")

        if self.errors:
            print("\nОШИБКИ ЛЕКСИЧЕСКОГО АНАЛИЗА:")
            for err in self.errors:
                print(f"{err.error_type}: строка {err.line}, позиция {err.column} - {err.message}")
            print(f"\nЛексический анализ завершён с ошибками. Обнаружено {len(self.errors)} ошибок.")
        else:
            print("\nЛексический анализ завершён успешно. Ошибок не найдено.")

        print(f"\nКоличество токенов: {len(self.tokens)}")


# =========================
# СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР
# =========================

@dataclass
class ASTNode:
    name: str
    value: Optional[str] = None
    children: Optional[List["ASTNode"]] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class ParserError:
    def __init__(self, message: str, line: int, column: int, expected: str):
        self.message = message
        self.line = line
        self.column = column
        self.expected = expected


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.errors: List[ParserError] = []

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def match(self, token_type: str, lexeme: Optional[str] = None):
        token = self.current_token()

        if token is None:
            self.errors.append(ParserError(
                "Неожиданный конец файла",
                -1,
                -1,
                f"{token_type} {lexeme if lexeme else ''}"
            ))
            return None

        if token.type == token_type and (lexeme is None or token.lexeme == lexeme):
            self.advance()
            return token

        self.errors.append(ParserError(
            f"Неожиданный токен '{token.lexeme}'",
            token.line,
            token.column,
            f"{token_type} {lexeme if lexeme else ''}"
        ))

        self.advance()
        return None

    def parse(self):
        return self.parse_program()

    def parse_program(self):
        root = ASTNode("Program")

        root.children.append(self.parse_include())
        root.children.append(self.parse_using_namespace())
        root.children.append(self.parse_function())

        return root

    def parse_include(self):
        node = ASTNode("IncludeNode")

        self.match("DELIMITER", "#")
        self.match("KEYWORD", "include")
        self.match("DELIMITER", "<")
        library = self.match("IDENTIFIER")
        self.match("DELIMITER", ">")

        if library:
            node.children.append(ASTNode("library", library.lexeme))

        return node

    def parse_using_namespace(self):
        node = ASTNode("UsingNamespaceNode")

        self.match("KEYWORD", "using")
        self.match("KEYWORD", "namespace")
        namespace_name = self.match("IDENTIFIER")
        self.match("DELIMITER", ";")

        if namespace_name:
            node.children.append(ASTNode("namespace_name", namespace_name.lexeme))

        return node

    def parse_function(self):
        node = ASTNode("FunctionNode")

        return_type = self.match("KEYWORD", "int")
        name = self.match("IDENTIFIER")

        self.match("DELIMITER", "(")
        self.match("DELIMITER", ")")
        self.match("DELIMITER", "{")

        body = self.parse_body()

        self.match("DELIMITER", "}")

        if return_type:
            node.children.append(ASTNode("return_type", return_type.lexeme))
        if name:
            node.children.append(ASTNode("name", name.lexeme))

        node.children.append(body)

        return node

    def parse_body(self):
        node = ASTNode("BodyNode")

        while self.current_token() and self.current_token().lexeme != "}":
            stmt = self.parse_statement()
            if stmt:
                node.children.append(stmt)

        return node

    def parse_statement(self):
        token = self.current_token()

        if token is None:
            return None

        if token.type == "KEYWORD" and token.lexeme == "int":
            return self.parse_var_decl()

        if token.type == "KEYWORD" and token.lexeme == "while":
            return self.parse_while()

        if token.type == "IDENTIFIER" and token.lexeme == "cout":
            return self.parse_cout()

        if token.type == "IDENTIFIER":
            return self.parse_assign()

        if token.type == "KEYWORD" and token.lexeme == "return":
            return self.parse_return()

        self.errors.append(ParserError(
            f"Неизвестный оператор или конструкция '{token.lexeme}'",
            token.line,
            token.column,
            "объявление переменной, while, присваивание, cout или return"
        ))
        self.advance()
        return None

    def parse_var_decl(self):
        node = ASTNode("VarDeclNode")

        var_type = self.match("KEYWORD", "int")
        name = self.match("IDENTIFIER")
        self.match("OPERATOR", "=")
        value = self.parse_expression()
        self.match("DELIMITER", ";")

        if var_type:
            node.children.append(ASTNode("var_type", var_type.lexeme))
        if name:
            node.children.append(ASTNode("name", name.lexeme))
        node.children.append(ASTNode("value", children=[value]))

        return node

    def parse_assign(self):
        node = ASTNode("AssignNode")

        left = self.match("IDENTIFIER")
        self.match("OPERATOR", "=")
        right = self.parse_expression()
        self.match("DELIMITER", ";")

        if left:
            node.children.append(ASTNode("left", left.lexeme))
        node.children.append(ASTNode("right", children=[right]))

        return node

    def parse_while(self):
        node = ASTNode("WhileNode")

        self.match("KEYWORD", "while")
        self.match("DELIMITER", "(")
        condition = self.parse_condition()
        self.match("DELIMITER", ")")
        self.match("DELIMITER", "{")

        body = self.parse_body()

        self.match("DELIMITER", "}")

        node.children.append(ASTNode("condition", children=[condition]))
        node.children.append(body)

        return node

    def parse_condition(self):
        left = self.parse_expression()
        op = self.match("OPERATOR", "<=")
        right = self.parse_expression()

        return ASTNode("BinaryOpNode", children=[
            ASTNode("operator", op.lexeme if op else ""),
            ASTNode("left", children=[left]),
            ASTNode("right", children=[right])
        ])

    def parse_expression(self):
        left = self.parse_term()

        while (
            self.current_token()
            and self.current_token().type == "OPERATOR"
            and self.current_token().lexeme == "+"
        ):
            op = self.current_token()
            self.advance()
            right = self.parse_term()

            left = ASTNode("BinaryOpNode", children=[
                ASTNode("operator", op.lexeme),
                ASTNode("left", children=[left]),
                ASTNode("right", children=[right])
            ])

        return left

    def parse_term(self):
        token = self.current_token()

        if token is None:
            self.errors.append(ParserError(
                "Неожиданный конец выражения",
                -1,
                -1,
                "идентификатор или константа"
            ))
            return ASTNode("ErrorNode")

        if token.type == "IDENTIFIER":
            self.advance()
            return ASTNode("IdentifierNode", token.lexeme)

        if token.type in ["CONSTANT_INT", "CONSTANT_FLOAT", "CONSTANT_STRING", "CONSTANT_BOOL"]:
            self.advance()
            return ASTNode("ConstantNode", token.lexeme)

        self.errors.append(ParserError(
            f"Некорректный элемент выражения '{token.lexeme}'",
            token.line,
            token.column,
            "идентификатор или константа"
        ))
        self.advance()
        return ASTNode("ErrorNode")

    def parse_cout(self):
        node = ASTNode("CoutNode")

        self.match("IDENTIFIER", "cout")

        while self.current_token() and self.current_token().lexeme == "<<":
            self.match("OPERATOR", "<<")
            value = self.match("IDENTIFIER")
            if value:
                node.children.append(ASTNode("value", value.lexeme))

        self.match("DELIMITER", ";")

        return node

    def parse_return(self):
        node = ASTNode("ReturnNode")

        self.match("KEYWORD", "return")
        value = self.parse_expression()
        self.match("DELIMITER", ";")

        node.children.append(ASTNode("value", children=[value]))

        return node

    def print_errors(self):
        if not self.errors:
            print("\nСинтаксический анализ завершён успешно. Ошибок не найдено.")
        else:
            print("\nОШИБКИ СИНТАКСИЧЕСКОГО АНАЛИЗА:")
            for err in self.errors:
                print(
                    f"SYNTAX_ERROR: строка {err.line}, позиция {err.column} - "
                    f"{err.message}. Ожидалось: {err.expected}"
                )


def print_ast(node: ASTNode, indent: str = ""):
    if node.value is not None:
        print(indent + node.name + ": " + node.value)
    else:
        print(indent + node.name)

    for child in node.children:
        print_ast(child, indent + "    ")


# =========================
# ЧТЕНИЕ ФАЙЛА И ЗАПУСК
# =========================

def read_cleaned_code(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл {filename} не найден")
        sys.exit(1)


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "cleaned_test.cpp"

    print("ЛАБОРАТОРНАЯ РАБОТА 3")
    print("Лексический и синтаксический анализатор")
    print(f"Входной файл: {filename}")

    code = read_cleaned_code(filename)

    print("\nИСХОДНЫЙ КОД")
    print("-" * 55)
    print(code)
    print("-" * 55)

    lexer = Lexer(code)
    tokens = lexer.tokenize()
    lexer.print_result()

    if lexer.errors:
        print("\nСинтаксический анализ не выполняется, так как есть лексические ошибки.")
        return

    parser = Parser(tokens)
    ast = parser.parse()

    print("\nAST")
    print("-" * 55)
    print_ast(ast)

    parser.print_errors()


if __name__ == "__main__":
    main()
