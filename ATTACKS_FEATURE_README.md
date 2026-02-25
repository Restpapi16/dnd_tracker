# Функционал атак для мобов

## Обзор

Добавлена возможность задавать параметры атак для уникальных и групповых мобов при создании схватки.

Каждая атака содержит:
- **Название** - например, "Укус", "Когти", "Огненное дыхание"
- **Бонус к попаданию** - числовой бонус (например, +5)
- **Бонус к урону** - числовой бонус (например, +8)
- **Тип урона** - колющий, рубящий, огонь, холод и т.д.
- **Дальность** - "ближний бой", "30 фт", "80/320 фт" и т.д.

## Изменения в коде

### Backend

1. **app/schemas.py**
   - Добавлена схема `Attack`
   - Поле `attacks: Optional[List[Attack]]` добавлено в `UniqueMonsterInput` и `GroupMonsterInput`
   - Поле `attacks` добавлено в `EncounterParticipantGM` и `EncounterParticipantPlayer`

2. **app/models.py**
   - Поле `attacks: Column(Text, nullable=True)` добавлено в модель `Participant`

3. **app/crud.py**
   - Сериализация атак в JSON при создании участников (`add_participants_to_encounter`)
   - Десериализация атак из JSON при получении состояния (`get_encounter_state_for_gm`, `get_encounter_state_for_player`)

### Frontend

4. **static/attacks_addon.js** (новый файл)
   - JavaScript модуль для управления атаками
   - UI для добавления/удаления атак
   - Функции для интеграции с campaigns.html

### База данных

5. **migration_add_attacks.sql**
   - SQL скрипт для добавления поля `attacks` в таблицу `participants`

## Инструкции по установке

### 1. Подтянуть изменения с GitHub

```bash
cd /path/to/dnd_tracker
git pull origin main
```

### 2. Применить миграцию базы данных

```bash
sqlite3 dnd.db < migration_add_attacks.sql
```

Или вручную:

```bash
sqlite3 dnd.db
ALTER TABLE participants ADD COLUMN attacks TEXT;
.quit
```

### 3. Интегрировать фронтенд

См. подробные инструкции в [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)

Кратко:
1. Добавьте `<script src="/static/attacks_addon.js"></script>` в campaigns.html
2. Обновите `addUniqueBtn.onclick` для использования `getAttacksForMonster()`
3. Добавьте отображение атак в `renderSetupUnique()`
4. (Опционально) Добавьте отображение атак в gm_encounter.html

### 4. Перезапустить сервер

```bash
# Если используете systemd
sudo systemctl restart dnd_tracker

# Или вручную
# Остановите текущий процесс
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Примеры использования

### API запрос

```json
POST /encounters/{encounter_id}/participants
{
  "players": [
    {
      "character_id": 1,
      "initiative_total": 15
    }
  ],
  "unique_monsters": [
    {
      "name": "Гоблин вождь",
      "max_hp": 21,
      "ac": 17,
      "initiative_mod": 2,
      "is_enemy": true,
      "attacks": [
        {
          "name": "Шкимитар",
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
  "group_monsters": [
    {
      "name": "Гоблин",
      "count": 4,
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
        }
      ]
    }
  ]
}
```

### Ответ API (GET /encounters/{id}/state?role=gm)

```json
{
  "encounter_id": 1,
  "campaign_id": 1,
  "status": "active",
  "round": 1,
  "current_index": 0,
  "participants": [
    {
      "id": 5,
      "type": "npc_unique",
      "name": "Гоблин вождь",
      "is_enemy": true,
      "max_hp": 21,
      "current_hp": 21,
      "ac": 17,
      "initiative_total": 18,
      "is_alive": true,
      "attacks": [
        {
          "name": "Шкимитар",
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
  ]
}
```

## Особенности

- Атаки **опциональны** - можно создавать мобов без атак
- Атаки хранятся в JSON формате в базе данных
- Один моб может иметь несколько атак
- Атаки видны и GM, и игрокам (это открытая информация в D&D)
- Старые участники будут иметь `attacks: null`

## Структура файлов

```
dnd_tracker/
├── app/
│   ├── schemas.py          # Обновлено: Attack, UniqueMonsterInput, etc.
│   ├── models.py           # Обновлено: Participant.attacks
│   └── crud.py             # Обновлено: сериализация/десериализация
├── static/
│   ├── campaigns.html      # Требует интеграции
│   ├── gm_encounter.html   # Требует интеграции
│   └── attacks_addon.js    # НОВЫЙ: модуль управления атаками
├── migration_add_attacks.sql         # НОВЫЙ: SQL миграция
├── MIGRATION_INSTRUCTIONS.md         # НОВЫЙ: инструкции по миграции
├── FRONTEND_INTEGRATION.md           # НОВЫЙ: инструкции по фронтенду
└── ATTACKS_FEATURE_README.md         # НОВЫЙ: этот файл
```

## Troubleshooting

### Ошибка: "duplicate column name: attacks"
Миграция уже применена. Пропустите этот шаг.

### Ошибка: "getAttacksForMonster is not defined"
Убедитесь, что подключили attacks_addon.js в campaigns.html.

### Атаки не отображаются в бою
Проверьте:
1. Применена ли миграция БД
2. Перезапущен ли сервер
3. Обновлен ли gm_encounter.html для отображения атак

### Старые мобы не имеют атак
Это нормально. Старые участники будут иметь `attacks: null`. Атаки опциональны.

## Контакты

При вопросах или проблемах создайте issue в GitHub репозитории.
