# plc_logging

Логгирование сообщений от ПЛК.

[Ссылка](https://github.com/Konstantin-Dudersky/plc_logging) на репозиторий.

[TOC]

## Описание

ПЛК посылает сообщения с помощью TSEND. Разделитель: `\r`

Сервер python принимает сообщения по указанному порту через [asyncio streams](https://docs.python.org/3/library/asyncio-stream.html). Логгирование в консоль и в текстовый файл.

Формат сообщения:

```
LEVEL | TIMESTAMP | BLOCK_TITLE
MESSAGE
--------------------------------------------------------------------------------
```

- LEVEL - уровень сообщения
- TIMESTAMP - метка времени ПЛК
- BLOCK_TITLE - блок, в котором было сгенерировано данное сообщение
- MESSAGE - текст сообщение

Предусмотрены уровни логгирования:

| Уровень  | Численное значение | Комментарий               |
| -------- | ------------------ | ------------------------- |
| NOTSET   | 0                  | Логгируются все сообщения |
| DEBUG    | 10                 |                           |
| INFO     | 20                 |                           |
| WARNING  | 30                 |                           |
| ERROR    | 40                 |                           |
| CRITICAL | 50                 |                           |
| DISABLE  | 100                | Ничего не логгируется     |

Уровень логгирования задается в двух местах - глобально и в каждом FC/FB, в которых создаются сообщения. Чтобы сообщение попало в лог, необходимо, чтобы его уровень был не ниже обоих заданных уровней. Например

| Глобальный уровень | Уровень в блоке | Сообщение | Результат |
| ------------------ | --------------- | --------- | --------- |
| DEBUG              | DEBUG           | DEBUG     | в лог     |
| DEBUG              | DEBUG           | INFO      | в лог     |
| DEBUG              | INFO            | DEBUG     | игнор     |
| INFO               | DEBUG           | DEBUG     | игнор     |

Чтобы заблокировать все сообщения в ПЛК - установить глобальный уровень DISABLE.

## Скрипт Python

Работу проверял в python3.10. Должен работать начиная с версии 3.7, но это не точно.

Кроме вывода в терминал, создаются текстовые файлы в папке log.

### Linux

Как правило, python уже предустановлен. Команды для установки актуальной версии python на debian-based дистрибутивах - [ссылка](https://gist.github.com/Konstantin-Dudersky/2e5dfad8ff49c749e4421f87574b6713).

Установка [poetry](https://python-poetry.org/):

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

Закрываем консоль и открываем опять. Переходим в папку, в которой будут храниться файлы. Скачиваем репозиторий github:

```sh
curl -L -O https://github.com/Konstantin-Dudersky/plc_logging/archive/refs/heads/main.zip
unzip -uo main.zip
mv plc_logging-main/ plc_logging
rm main.zip
```

Устанавливаем

```sh
cd plc_logging
poetry install
```

Запускать командой

```sh
poetry run python plc_logging.py PORT
```

PORT - номер порта, опциональный параметр, если не указать, то назначается 8000

### Windows

Устанавливаем актуальный [python](https://www.python.org/).

Установка [poetry](https://python-poetry.org/) через PowerShell:

```powershell
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
```

Закрывает PowerShell и открываем опять. Переходим в папку, в которой будут храниться файлы. Скачиваем репозиторий из github:

```powershell
Invoke-WebRequest https://github.com/Konstantin-Dudersky/plc_logging/archive/refs/heads/main.zip -OutFile .\repo.zip
Expand-Archive .\repo.zip .\
Rename-Item .\plc_logging-main .\plc_logging
Remove-Item .\repo.zip
```

Устанавливаем

```powershell
cd plc_logging
poetry install
```

Запускать командой:

```powershell
poetry run python plc_logging.py PORT
```

PORT - номер порта, опциональный параметр, если не указать, то назначается 8000

## Настройка в контроллере

### Siemens

#### FB LoggerFB

Основной FB - LoggerFb, и связанный с ним блок данных logger. Блок нужно вызывать в OB1. Пример вызова:

```pascal
"logger"(global_logger_level := "LoggerLevels".NOTSET,
         ip_1 := 10,
         ip_2 := 101,
         ip_3 := 50,
         ip_4 := 17,
         port_number := 8000,
         interface_id := "Local~PROFINET_interface_1"
);
```

- ip и port - адрес и порт ПК, на котором запущен скрипт python.
- interface_id - идентификатор интерфейса, через который ПЛК посылает сообщения
- global_logger_level - глобальный уровень логгирования.

Настройки блока считываются при первом запуске. Если необходимо поменять настройки "на лету", нужно установить флаг init в True.

#### FC logger.config_in_block

В начале каждого блока, в котором логгируются сообщения, необходимо вызывать
функцию logger.config_in_block:

```pascal
"logger.config_in_block"(level := "LoggerLevels".DEBUG,
                         block_title := 'test_logger_block');
```

- block_title - строка, которая добавляется к каждому сообщению, для идентификации
  блока в логе сообщений
- level - минимальный уровень сообщений для логгирования.
  Например, если установлен уровень INFO, то логгируются сообщения уровнем
  INFO и выше. Также учитывается глобальный уровень логгирования

#### FC logger.LEVEL_NUM

Разные функции, в зависимости от уровня сообщения и кол-ва вспомогательных параметров. Например:

- logger.debug_0
- logger.debug_1
- logger.info_0
- logger.info_1
- и т.д.

LEVEL - уровень логгирования сообщения, NUM - кол-во вспомогательных параметров.

Пример вызова:

```pascal
#sp := 10;
#pv := 11;
"logger.debug_2"(msg := 'test debug message, SP: {0}, PV: {1}',
                 value_0 := REAL_TO_STRING(#sp),
                 value_1 := REAL_TO_STRING(#pv)
);
```

- msg - текст сообщения, тип STRING - т.е. поддерживаются только символы ASCII. В фигурных скобках {} можно указать место вставки доп. значений value. Нумерация начинается с 0.
- value - доп. значения в формате STRING.

В журнале будет сгенерировано подобное сообщение:

```
DEBUG | 2022-07-30 16:42:56,937619669 | test_logger_block
test debug message, SP: +1.000000E+1, PV: +1.100000E+1, add: +1.200000E+1
--------------------------------------------------------------------------------
```

