import re
import sys


def clean_code(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден")
        return
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    if code.count('/*') != code.count('*/'):
        print("Ошибка: Незакрытый многострочный комментарий")
        return

    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    code = re.sub(r'//.*', '', code)

    lines = code.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    cleaned_code = '\n'.join(cleaned_lines)

    with open('cleaned_' + filename, 'w', encoding='utf-8') as f:
        f.write(cleaned_code)

    print(f"Очищенный код сохранен в cleaned_{filename}")
    print(f"Количество строк после очистки: {len(cleaned_lines)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        clean_code(sys.argv[1])
    else:
        clean_code("test.cpp")