# Telegram signal-forwarder bot

Слушает несколько Telegram-каналов с сигналами и мгновенно пересылает каждый сигнал
в выбранные целевые каналы, переписывая текст под каждый канал: словарь замен
(слово/фраза → слово/фраза, буквально или через regex) плюс своя обёртка
(prefix/suffix — шапка, подпись, бренд, ссылка).

## Установка

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
cp .env.example .env
```

## Настройка

### 1. Telegram

1. Получите `TG_API_ID` и `TG_API_HASH` на https://my.telegram.org (API Development Tools).
2. Впишите `TG_API_ID`, `TG_API_HASH`, `TG_SESSION_NAME` в `.env`.
3. Узнайте `chat_id` источников и целевых каналов:
   ```bash
   python main.py --list-chats
   ```
   При первом запуске Telethon запросит номер телефона, код подтверждения и, при
   необходимости, пароль 2FA — после этого создастся файл сессии
   `<TG_SESSION_NAME>.session`. Это **userbot**: он работает от вашего личного
   аккаунта, поэтому может читать любые каналы, на которые вы подписаны, и
   постить туда, где у вас есть право писать/публиковать — без необходимости
   добавлять бота как администратора.

### 2. Источники, цели и правила замены (`config.yaml`)

```yaml
dry_run: true   # true = только логировать итоговый текст, ничего не отправлять

sources:
  - name: source_a
    chat_id: -1001111111111

targets:
  - name: channel_x
    chat_id: -1003333333333
    sources: [source_a]        # из каких источников ретранслировать; по умолчанию — все
    prefix: "🔥 Сигнал\n\n"
    suffix: "\n\nПодписывайся: @channel_x"
    replacements:               # применяются по порядку, до prefix/suffix
      - from: "оригинальное упоминание"
        to: "наш бренд"
      - from: "\\d+usd"          # regex, если regex: true
        to: "$0"
        regex: true
```

См. полный пример в `config.example.yaml`.

## Запуск

```bash
python main.py
```

Логи пишутся в `forwarder.log` и в stdout. Дедупликация сообщений (чтобы не переслать
один и тот же сигнал дважды при переподключении) хранится в `forward_state.db` (SQLite).

## Порядок вывода в прод

1. `dry_run: true` — погонять на реальных источниках, смотреть в логах, какой именно
   текст бот отправил бы в каждый целевой канал, проверить правила замены/обёртки.
2. Только затем `dry_run: false`.

## Тесты

```bash
python -m unittest discover -s tests -v
```

## Сборка .exe для Windows 11

Аналогично основному боту в этом репозитории: `build.bat` создаёт venv, ставит
зависимости и собирает `.exe` через `bot.spec`. Собирать нужно на самой Windows
(PyInstaller не кросс-компилирует).

1. Скопируйте папку `signal_forwarder/` на Windows-машину.
2. Запустите `build.bat`.
3. Готовый результат: `dist\signal_forwarder\signal_forwarder.exe` — переносить нужно
   всю папку `dist\signal_forwarder\` целиком.
4. Положите `config.yaml` и `.env` рядом с `signal_forwarder.exe`.
5. `signal_forwarder.exe --list-chats` — узнать chat_id.
6. `signal_forwarder.exe` — обычный запуск. Логи (`forwarder.log`) и БД
   (`forward_state.db`) создаются рядом с exe.

## Структура проекта

```
main.py                 # точка входа: Telethon-клиент + регистрация обработчика
src/config.py            # загрузка config.yaml / .env, валидация ссылок sources/targets
src/transformer.py        # применение словаря замен + prefix/suffix к тексту сигнала
src/state_store.py        # SQLite: дедупликация (source_chat_id, message_id)
src/forwarder.py          # Telethon listener -> dedup -> transform -> send (с retry на FloodWait)
src/paths.py              # определение базовой директории (для запуска из .exe)
tests/                    # юнит-тесты transformer и config
```
