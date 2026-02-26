# CSS селекторы next.dnd.su

## ✅ Проверенные селекторы

Для заклинаний (spells):

1. **Название**: `card-title`
2. **Уровень и Школа**: `school_level`
3. **Время сотворения**: `cast_time`
4. **Дистанция**: `range`
5. **Компоненты**: `components`
6. **Длительность**: `duration`
7. **Описание**: `description`

## 📝 Пример использования

```python
from bs4 import BeautifulSoup

# Название
name_elem = soup.find(class_='card-title')
name = name_elem.text.strip()

# Уровень и школа
school_level_elem = soup.find(class_='school_level')
text = school_level_elem.text.strip()  # "Пример: 1 уровень, Очарование"

# Время сотворения
cast_time_elem = soup.find(class_='cast_time')
casting_time = cast_time_elem.text.strip()  # "1 действие"

# Дистанция
range_elem = soup.find(class_='range')
spell_range = range_elem.text.strip()  # "Касание"

# Компоненты
components_elem = soup.find(class_='components')
components = components_elem.text.strip()  # "В, С"

# Длительность
duration_elem = soup.find(class_='duration')
duration = duration_elem.text.strip()  # "Концентрация, до 1 минуты"

# Описание
description_elem = soup.find(class_='description')
description = description_elem.get_text(separator='\n\n', strip=True)
```

## ✅ Статус

Парсер обновлён и готов к использованию!

## 🚀 Тестирование

```bash
# Загрузить тестовое заклинание
python scripts/load_reference_data.py --type spells --limit 1

# Проверить в API
curl "http://localhost:8000/reference/spells/search?limit=1"
```
