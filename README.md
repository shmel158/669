# Telegram → Hyperliquid TWAP mirror-bot

Слушает Telegram-канал с whale-tracker сигналами вида:

```
🟩 $185.70K покупка VVV в течении 16.5 часа

Цена: $11.77
Объем: $5.25M (3.54%)
Субъект: 0x...
```

и открывает свою TWAP-позицию на Hyperliquid в ту же сторону/по тому же тикеру,
но с размером/плечом/риском из **своего** конфига, а не из объёма сигнала.

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
2. Узнайте ID нужного чата/канала:
   ```bash
   python -m src.telegram_listener --list-chats
   ```
   При первом запуске Telethon запросит номер телефона, код подтверждения и, при
   необходимости, пароль 2FA — после этого создастся файл сессии `<TG_SESSION_NAME>.session`.
3. Впишите `TG_API_ID`, `TG_API_HASH`, `TG_SESSION_NAME`, `TG_SOURCE_CHAT_ID` в `.env`.

### 2. Hyperliquid — agent (API) wallet

**Не используйте приватный ключ основного кошелька напрямую.** Hyperliquid поддерживает
делегирование подписи через отдельный agent wallet: он может подписывать ордера, но не
может выводить средства и не виден как "владелец" аккаунта.

Проще всего создать его через UI: https://app.hyperliquid.xyz/API → "Create API Wallet" →
скопируйте приватный ключ в `HL_AGENT_PRIVATE_KEY`, а адрес **основного** кошелька — в
`HL_ACCOUNT_ADDRESS`.

Либо программно, разово, через сам SDK:
```python
from eth_account import Account
from hyperliquid.exchange import Exchange

main_wallet = Account.from_key("0x<приватный ключ основного кошелька>")
exchange = Exchange(main_wallet)
_, agent_private_key = exchange.approve_agent()
print(agent_private_key)  # положить в HL_AGENT_PRIVATE_KEY
```

### 3. Риск-параметры (`config.yaml`)

Все параметры сделки (не берутся из сигнала!):

| Параметр | Смысл |
|---|---|
| `pct_of_equity` | доля депозита на одну сделку |
| `leverage`, `margin_mode` | плечо и cross/isolated |
| `max_concurrent_positions` | лимит одновременно открытых TWAP |
| `stop_loss_pct`, `take_profit_pct` | SL/TP от цены входа, ставятся после завершения TWAP-окна |
| `coin_whitelist` / `coin_blacklist` | фильтр монет |
| `max_twap_duration_hours` / `min_twap_duration_minutes` | кап на длительность из сигнала |
| `randomize_twap` | джиттер таймингов сабордеров TWAP |
| `dry_run` | true = только считает и логирует, ничего не отправляет |
| `use_testnet` | true = торговать на Hyperliquid testnet |

## Запуск

```bash
python main.py
```

Логи пишутся в `bot.log` и в stdout. Состояние (открытые TWAP, дедупликация сообщений)
хранится в `bot_state.db` (SQLite).

## ⚠️ Порядок вывода в прод

1. `use_testnet: true`, `dry_run: false` — реально разместить TWAP на testnet-балансе,
   проверить в UI Hyperliquid testnet направление/размер/длительность.
2. `use_testnet: false`, `dry_run: true` — погонять на mainnet в режиме симуляции,
   смотреть в логах, что бы бот сделал по реальным сигналам.
3. Только затем `dry_run: false` на mainnet, начиная с малого `pct_of_equity`.

## Тесты

```bash
python -m unittest discover -s tests -v
```

## Сборка .exe для Windows 11

Собрать `.exe` можно только на самой Windows (PyInstaller не кросс-компилирует —
ему нужен запущенный Windows-интерпретатор). В репозитории уже есть `build.bat` и `bot.spec`,
которые делают всё автоматически.

### Что нужно установить на Windows заранее

1. **Python 3.11 или 3.12** (3.13 тоже подойдёт) — https://www.python.org/downloads/windows/
   При установке обязательно поставьте галочку **"Add python.exe to PATH"**.
   Больше ничего вручную ставить не нужно — `build.bat` сам создаст виртуальное окружение
   и поставит все зависимости (`telethon`, `hyperliquid-python-sdk`, `pyinstaller` и т.д.)
   через pip.
2. (Опционально, но рекомендуется) **Microsoft Visual C++ Redistributable** — некоторые
   зависимости (`coincurve`, криптография) используют скомпилированные расширения, которые
   иногда требуют его для запуска на "чистой" Windows. Скачать:
   https://aka.ms/vs/17/release/vc_redist.x64.exe
3. Никакого Wine/WSL не требуется — сборка и запуск идут нативно на Windows.

### Шаги сборки

1. Скопируйте всю папку проекта на Windows-машину (или склонируйте репозиторий).
2. Дважды кликните `build.bat` (или запустите его из `cmd`/PowerShell в папке проекта).
3. Скрипт создаст `venv`, поставит зависимости и соберёт exe. Готовый результат:
   `dist\whale_mirror_bot\whale_mirror_bot.exe` (папка `dist\whale_mirror_bot\` — это всё,
   что нужно переносить целиком, exe не самодостаточен без соседних файлов внутри неё).

### Запуск exe

1. Положите `config.yaml` и `.env` **рядом с `whale_mirror_bot.exe`** (в ту же папку
   `dist\whale_mirror_bot\`) — бот ищет их именно там, а не в текущей директории запуска.
2. Первый раз узнайте ID нужного Telegram-чата:
   ```
   whale_mirror_bot.exe --list-chats
   ```
   (запросит телефон/код от Telegram при первом входе, создаст файл сессии рядом с exe)
3. Обычный запуск:
   ```
   whale_mirror_bot.exe
   ```
   Логи (`bot.log`) и БД (`bot_state.db`) тоже создаются рядом с exe.

### Автозапуск / работа в фоне на Windows

- Проще всего — оставить открытым окно консоли с запущенным exe.
- Для запуска в фоне без окна можно создать ярлык с `pythonw`-подобным поведением через
  Планировщик заданий Windows (Task Scheduler): создать задачу, которая запускает
  `whale_mirror_bot.exe`, триггер "при входе в систему", опция "Запускать скрыто".
- Каждый рестарт бот подхватывает состояние из `bot_state.db`, так что дедупликация
  сообщений и список открытых TWAP не теряются.

## Структура проекта

```
main.py                    # точка входа: Telethon-клиент + фоновый watcher SL/TP
src/config.py               # загрузка config.yaml / .env
src/signal_parser.py        # regex-парсер сообщений сигнала
src/risk.py                 # расчёт размера позиции, округление, кап длительности
src/hyperliquid_client.py   # обёртка над hyperliquid-python-sdk + сырой twapOrder-экшен
src/position_store.py       # SQLite: открытые TWAP, дедупликация сообщений
src/telegram_listener.py    # Telethon-слушатель нужного чата
src/bot.py                  # оркестратор: сигнал -> валидация -> sizing -> ордер -> SL/TP
tests/                      # юнит-тесты парсера и risk-модуля
```

## Важное про TWAP на Hyperliquid

Официальный `hyperliquid-python-sdk` (на момент написания — v0.24.0) **не имеет** метода
для размещения TWAP-ордера — только `Info.user_twap_slice_fills()` для чтения истории уже
исполняющихся TWAP. Поэтому `hyperliquid_client.py` строит и подписывает сырой L1-экшен
`{"type": "twapOrder", "twap": {...}}` вручную, той же функцией `sign_l1_action`, которую
сам SDK использует внутри `order()`/`update_leverage()`. Это официально поддерживаемый на
уровне протокола способ, просто ещё не обёрнутый в SDK.
