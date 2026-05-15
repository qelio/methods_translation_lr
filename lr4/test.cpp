#include <iostream>
using namespace std;

int main() {
    int i = 1;  // объявление переменной
    int sum = 0;  // объявление переменной

    while (i <= 5) {  // цикл while
        sum = sum + i;  // присваивание и арифметика
        i = i + 1;  // присваивание
    }

    cout << sum << endl;
    return 0;
}
/* комментарий */