# Компиляция C++ модулей для Kiwiyd Antivirus
1
## Структура файлов

```
moduls/
├── scanner.cpp       - Модуль сканирования системы
├── scanner.dll       - Скомпилированная DLL (создается после компиляции)
├── quarantine.cpp    - Модуль карантина файлов
├── quarantine.dll    - Скомпилированная DLL (создается после компиляции)
└── COMPILATION.md    - Этот файл
```

## Требования

- **Visual Studio 2019 или 2022** (рекомендуется)
- **Windows SDK**
- **C++17 или выше**

## Вариант 1: Компиляция через командную строку (MSVC)

### Шаг 1: Открыть Developer Command Prompt для Visual Studio

Найти в меню "Developer Command Prompt for VS 2022" (или VS 2019)

### Шаг 2: Перейти в директорию проекта

```bash
cd c:\Users\bearr\Documents\GitHub\kiwiyd-antivirus\moduls
```

### Шаг 3: Скомпилировать scanner.cpp

```bash
cl.exe /D_USRDLL /D_WINDLL /EHsc /std:c++17 scanner.cpp /link /DLL /OUT:scanner.dll
```

### Шаг 4: Скомпилировать quarantine.cpp

```bash
cl.exe /D_USRDLL /D_WINDLL /EHsc /std:c++17 quarantine.cpp /link /DLL /OUT:quarantine.dll
```

## Вариант 2: Компиляция через Visual Studio IDE

### Для scanner.cpp:

1. Открыть Visual Studio
2. File → New → Project from existing code
3. Выбрать папку `moduls/`
4. В Project Settings:
   - **Project type**: Dynamic Library (DLL)
   - **Output file name**: scanner.dll
5. В C/C++ properties:
   - C/C++ → Language Standard: ISO C++17 (/std:c++17)
   - C/C++ → Code Generation: Multi-threaded DLL (/MD)
6. Build → Build Solution

### Для quarantine.cpp:

1. Повторить то же самое для quarantine.cpp
2. Output file: quarantine.dll

## Вариант 3: Компиляция через G++ (MinGW)

```bash
# Для scanner.dll
g++ -shared -fPIC scanner.cpp -o scanner.dll -std=c++17 -lstdc++fs

# Для quarantine.dll
g++ -shared -fPIC quarantine.cpp -o quarantine.dll -std=c++17 -lstdc++fs
```

## Использование из Python

После компиляции DLL автоматически загружаются в app.py:

```python
import eel
import ctypes
import json

# DLL автоматически загружаются при запуске app.py
# из папки moduls/

# Сканирование системы
result = start_scan()
# Возвращает JSON:
# {
#   "status": "completed",
#   "timestamp": "2024-01-24 12:34:56",
#   "total_suspicious": 5,
#   "files": [...]
# }

# Карантин файлов
result = quarantine([
    "C:\\path\\to\\file1.exe",
    "C:\\path\\to\\file2.zip"
])
# Возвращает JSON:
# {
#   "status": "completed",
#   "quarantined_count": 2,
#   "failed_count": 0,
#   "quarantine_location": "C:\\Users\\user\\.kiwiyd_quarantine",
#   ...
# }

# Получить список файлов в карантине
result = get_quarantine_list()
```

## Функции в scanner.dll

### scanSystem()
- Сканирует Downloads, Temp, Documents
- Проверяет расширения файлов
- Ограничивает глубину поиска до 3 уровней
- Возвращает JSON со списком подозрительных файлов

## Функции в quarantine.dll

### quarantineFiles(filePaths)
- Принимает пути файлов (разделены `;`)
- Перемещает файлы в `.kiwiyd_quarantine`
- Добавляет временную метку к имени
- Возвращает JSON с результатом

### getQuarantineList()
- Возвращает JSON со списком файлов в карантине
- Показывает размер и путь каждого файла

### restoreFromQuarantine(quarantinedPath, restorePath)
- Восстанавливает файл из карантина
- Перемещает в указанную директорию

## Список проверяемых расширений

```
.exe .bat .cmd .com .pif .scr .vbs .js .jar
.zip .rar .7z .dll .sys .drv .bin .app .pkg
.dmg .deb .rpm .sh .bash .py
```

## Директория карантина

Все файлы сохраняются в:
```
C:\Users\YourUsername\.kiwiyd_quarantine
```

С временной меткой в имени:
```
20240124_123456_malware.exe
```

## Решение проблем

### DLL не загружается
- Проверить что файлы scanner.dll и quarantine.dll в папке `moduls/`
- Убедиться что приложение запущено с правами администратора
- Проверить совместимость разрядности (32/64 бит)

### Ошибка "File not found"
- Проверить пути к файлам в функции quarantine()
- Убедиться что пути разделены символом `;`

### Ошибка компиляции
- Убедиться что установлен Visual Studio с поддержкой C++17
- Проверить версию Windows SDK
