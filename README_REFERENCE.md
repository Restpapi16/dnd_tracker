# D&D Reference System

Система справочника по D&D для бота dnd_tracker.

## Возможности

- 🧙 **Заклинания**: полная информация о заклинаниях, фильтрация по уровню и школе
- ⚔️ **Предметы**: оружие, доспехи, снаряжение, магические предметы
- 🐉 **Существа**: бестиарий с характеристиками и способностями
- 🔍 **Автодополнение**: быстрый поиск с подсказками при вводе

## Архитектура

```
app/
├── models_reference.py      # Модели SQLAlchemy для справочника
├── schemas_reference.py     # Pydantic схемы для API
├── crud_reference.py        # CRUD операции
├── routers/
│   └── reference.py          # API эндпоинты
└── parsers/
    └── dndsu_parser.py       # Парсер next.dnd.su

scripts/
└── load_reference_data.py   # Скрипт загрузки данных

static/
└── reference.html           # Mini App интерфейс (будет создан)
```

## Установка

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Применить миграции базы данных

```python
# В app/database.py или отдельном скрипте
from app.models_reference import ReferenceSpell, ReferenceItem, ReferenceCreature
from app.database import engine, Base

Base.metadata.create_all(bind=engine)
```

### 3. Добавить роутер в FastAPI

В `app/main.py`:

```python
from app.routers import reference

app.include_router(reference.router)
```

### 4. Загрузить данные

```bash
# Загрузить заклинания
python scripts/load_reference_data.py --type spells --limit 10

# Загрузить предметы
python scripts/load_reference_data.py --type items --limit 10

# Загрузить существа
python scripts/load_reference_data.py --type creatures --limit 5

# Загрузить все
python scripts/load_reference_data.py --all
```

## API Эндпоинты

### Автодополнение

```
GET /reference/search/suggestions?q=файр&limit=5
```

Возвращает подсказки по всем типам (spells, items, creatures).

### Заклинания

```
GET /reference/spells/search?q=огонь&level=3&limit=10
GET /reference/spells/{spell_id}
```

### Предметы

```
GET /reference/items/search?q=меч&category=оружие&limit=10
GET /reference/items/{item_id}
```

### Существа

```
GET /reference/creatures/search?q=дракон&cr=13&limit=10
GET /reference/creatures/{creature_id}
```

## Использование в Frontend

### Пример автодополнения

```javascript
let searchTimeout;
const searchInput = document.getElementById('search');

searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length < 2) {
        hideSuggestions();
        return;
    }
    
    searchTimeout = setTimeout(async () => {
        const response = await fetch(
            `/reference/search/suggestions?q=${encodeURIComponent(query)}&limit=5`,
            {
                headers: {
                    'Authorization': `tma ${window.Telegram.WebApp.initData}`
                }
            }
        );
        const suggestions = await response.json();
        showSuggestions(suggestions);
    }, 300);
});
```

## TODO

- [ ] Улучшить парсер (HTML-селекторы под реальную структуру сайта)
- [ ] Добавить парсинг списков со страниц /spells/, /equipment/, /bestiary/
- [ ] Создать Mini App интерфейс (reference.html)
- [ ] Добавить full-text search индексы в PostgreSQL
- [ ] Реализовать систему избранного
- [ ] Интегрировать с системой боя (encounter)
- [ ] Добавить кэширование популярных запросов

## Примечания

1. **Парсер базовый**: Нужно адаптировать под реальную HTML-структуру next.dnd.su
2. **Rate limiting**: Добавьте задержки между запросами при массовой загрузке
3. **Индексы**: Для улучшения поиска установите `pg_trgm` расширение в PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```
