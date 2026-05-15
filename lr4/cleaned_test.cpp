#include <iostream>
using namespace std;
int main() {
int i = true;
int sum = 0;
while (i <= 5) {
sum = sum + i;
i = i + 1;
}
cout << sum << endl;
return 0;
}
