# Инструкция по интеграции справочника D&D

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Обновление app/main.py

Добавьте импорт роутера в `app/main.py`:

```python
# В начале файла
from app.routers import reference

# После создания app = FastAPI()
app.include_router(reference.router)
```

## Шаг 3: Добавление моделей в базу данных

В `app/database.py` или в начале `app/main.py` добавьте:

```python
# Импортируем модели справочника
from app.models_reference import ReferenceSpell, ReferenceItem, ReferenceCreature

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)
```

## Шаг 4: Добавление кнопки в бот

В `bot.py` добавьте кнопку для открытия справочника:

```python
BTN_REFERENCE = "📚 Справочник"

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ROLL), KeyboardButton(text=BTN_INFO)],
            [KeyboardButton(text=BTN_CRIT), KeyboardButton(text=BTN_REFERENCE)],
        ],
        resize_keyboard=True,
    )

# Обработчик кнопки
@dp.message(F.text == BTN_REFERENCE)
async def on_btn_reference(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📚 Открыть справочник",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/static/reference.html")
        )]
    ])
    await message.answer(
        "📚 D&D Справочник\n\n"
        "Заклинания, предметы и существа D&D 5e.",
        reply_markup=kb
    )
```

## Шаг 5: Загрузка тестовых данных

```bash
# Загрузить первые заклинания
python scripts/load_reference_data.py --type spells --limit 3

# Проверить работу API
curl -X GET "http://localhost:8000/reference/spells/search?limit=10"
```

## Шаг 6: Улучшение парсера (ВАЖНО!)

Текущий парсер в `app/parsers/dndsu_parser.py` - **базовый шаблон**.

Вам нужно:

1. Открыть страницу https://next.dnd.su/spells/10222-heroism/ в браузере
2. Открыть DevTools (F12) и изучить HTML-структуру
3. Найти CSS-селекторы для:
   - Названия заклинания
   - Уровня и школы
   - Времени сотворения, дистанции, компонентов
   - Описания
4. Обновить метод `parse_spell()` с конкретными селекторами

Пример:
```python
# Вместо
name = soup.find('h1').text.strip()

# Используйте точный селектор
name = soup.find('div', class_='spell-name').text.strip()
```

## Шаг 7: Массовая загрузка

После улучшения парсера:

```bash
# Загрузить все данные (может занять время)
python scripts/load_reference_data.py --all

# Или постепенно
python scripts/load_reference_data.py --type spells
python scripts/load_reference_data.py --type items
python scripts/load_reference_data.py --type creatures
```

## Шаг 8: Оптимизация поиска (PostgreSQL)

Для улучшения поиска по частичному совпадению:

```sql
-- Подключитесь к PostgreSQL
psql -U your_user -d your_database

-- Установите расширение pg_trgm
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создайте индексы
CREATE INDEX idx_spell_name_trgm ON reference_spells USING gin (name gin_trgm_ops);
CREATE INDEX idx_item_name_trgm ON reference_items USING gin (name gin_trgm_ops);
CREATE INDEX idx_creature_name_trgm ON reference_creatures USING gin (name gin_trgm_ops);
```

## Тестирование

### 1. Проверка API

```bash
# Автодополнение
curl "http://localhost:8000/reference/search/suggestions?q=огон&limit=5"

# Поиск заклинаний
curl "http://localhost:8000/reference/spells/search?q=геро&level=1"

# Получить конкретное заклинание
curl "http://localhost:8000/reference/spells/1"
```

### 2. Проверка в боте

1. Отправьте `/start` боту
2. Нажмите "📚 Справочник"
3. Откроется Mini App
4. Попробуйте поиск с автодополнением
5. Откройте детальную информацию о заклинании

## Следующие шаги

- [ ] Улучшить парсер под реальную структуру сайта
- [ ] Добавить парсинг списков со страниц /spells/, /equipment/, /bestiary/
- [ ] Реализовать систему избранного
- [ ] Интегрировать с encounter (например, добавить существо в бой прямо из справочника)
- [ ] Добавить фильтры в UI
- [ ] Кэширование часто используемых запросов

## Помощь

Если возникли проблемы:

1. **Ошибка импорта модулей**: Проверьте, что все файлы скопированы из ветки `feature/reference-system`
2. **Таблицы не создаются**: Выполните `Base.metadata.create_all(bind=engine)` вручную
3. **Парсер не работает**: Это нормально, нужно адаптировать под HTML-структуру сайта
4. **API возвращает 401**: Проверьте `get_current_tg_user_id` dependency

## Структура проекта

```
dnd_tracker/
├── app/
│   ├── models_reference.py        # Новые модели
│   ├── schemas_reference.py       # Новые схемы
│   ├── crud_reference.py          # Новые CRUD
│   ├── routers/
│   │   └── reference.py            # Новый роутер
│   └── parsers/
│       └── dndsu_parser.py         # Новый парсер
├── static/
│   ├── reference.html             # Новый Mini App
│   └── reference.js               # Новая логика
├── scripts/
│   └── load_reference_data.py     # Новый скрипт
├── requirements.txt               # Обновлено
├── README_REFERENCE.md            # Новая документация
└── INTEGRATION_GUIDE.md           # Этот файл
```

## Успехов в разработке! 🎲
