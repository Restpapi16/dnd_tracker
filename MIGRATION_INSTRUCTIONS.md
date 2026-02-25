# Инструкции по миграции базы данных

## Добавление поля attacks (25.02.2026)

### Что изменилось

Добавлена возможность задавать атаки для мобов (уникальных и групповых).

Каждая атака включает:
- Название (например, "Укус")
- Бонус к попаданию
- Бонус к урону
- Тип урона (например, "колющий")
- Дальность (например, "ближний бой")

### Как применить миграцию

#### Вариант 1: Через sqlite3 CLI

```bash
# Подключитесь к базе данных
sqlite3 dnd.db

# Выполните миграцию
.read migration_add_attacks.sql

# Выйдите из sqlite3
.quit
```

#### Вариант 2: Одной командой

```bash
sqlite3 dnd.db < migration_add_attacks.sql
```

#### Вариант 3: Через Python

```python
import sqlite3

conn = sqlite3.connect('dnd.db')
cursor = conn.cursor()

# Выполните миграцию
cursor.execute('ALTER TABLE participants ADD COLUMN attacks TEXT')
conn.commit()

print('Миграция успешно применена!')

conn.close()
```

### Проверка

После применения миграции проверьте структуру таблицы:

```bash
sqlite3 dnd.db
.schema participants
```

Вы должны увидеть поле `attacks TEXT` в конце списка полей.

### Важно

- Миграция не затронет существующие данные
- Новое поле опционально (nullable)
- Для старых участников поле будет NULL
- После миграции перезапустите FastAPI сервер

### Откат миграции

SQLite не поддерживает DROP COLUMN. Если нужно откатить изменения:

1. Сделайте резервную копию: `cp dnd.db dnd.db.backup`
2. Создайте новую таблицу без поля attacks
3. Скопируйте данные из старой таблицы
4. Удалите старую и переименуйте новую

Или просто восстановите из резервной копии.

### Пример использования API

```json
POST /encounters/{encounter_id}/participants
{
  "players": [...],
  "unique_monsters": [
    {
      "name": "Гоблин",
      "max_hp": 7,
      "ac": 15,
      "initiative_mod": 2,
      "is_enemy": true,
      "attacks": [
        {
          "name": "Короткий меч",
          "hit_bonus": 4,
          "damage_bonus": 2,
          "damage_type": "рубящий",
          "range": "ближний бой"
        },
        {
          "name": "Короткий лук",
          "hit_bonus": 4,
          "damage_bonus": 2,
          "damage_type": "колющий",
          "range": "80/320 фт"
        }
      ]
    }
  ],
  "group_monsters": []
}
```
