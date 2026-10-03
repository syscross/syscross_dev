
# C++ (Windows)

```cpp
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include <tchar.h> // _tWinMain

int APIENTRY _tWinMain(HINSTANCE, HINSTANCE, LPTSTR, INT) {
	MessageBox(NULL, TEXT("Hello"), TEXT("Hello, C++ Windows."), MB_OK);
	return 0;
}
```
