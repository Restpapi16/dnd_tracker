# scripts/spell_ids.py
"""
Ручной список популярных заклинаний D&D 5e с next.dnd.su

Получено из:
- https://next.dnd.su/spells/10222-heroism/
- https://next.dnd.su/spells/
"""

# Популярные заклинания (заговоры - 0 уровень)
CANTRIPS = [
    {'external_id': 10222, 'slug': 'heroism', 'name': 'Героизм'},
    {'external_id': 10007, 'slug': 'acid-splash', 'name': 'Кислотный всплеск'},
    {'external_id': 10015, 'slug': 'blade-ward', 'name': 'Защита от оружия'},
    {'external_id': 10071, 'slug': 'fire-bolt', 'name': 'Огненный снаряд'},
    {'external_id': 10147, 'slug': 'mage-hand', 'name': 'Волшебная рука'},
    {'external_id': 10148, 'slug': 'mending', 'name': 'Исправление'},
    {'external_id': 10208, 'slug': 'prestidigitation', 'name': 'Престидиджитация'},
    {'external_id': 10221, 'slug': 'ray-of-frost', 'name': 'Луч холода'},
    {'external_id': 10245, 'slug': 'shocking-grasp', 'name': 'Шокирующее касание'},
    {'external_id': 10295, 'slug': 'true-strike', 'name': 'Верный удар'},
]

# 1 уровень
LEVEL_1 = [
    {'external_id': 10019, 'slug': 'burning-hands', 'name': 'Пылающие руки'},
    {'external_id': 10036, 'slug': 'charm-person', 'name': 'Очарование личности'},
    {'external_id': 10050, 'slug': 'cure-wounds', 'name': 'Исцеление ран'},
    {'external_id': 10052, 'slug': 'detect-magic', 'name': 'Обнаружение магии'},
    {'external_id': 10145, 'slug': 'magic-missile', 'name': 'Волшебная стрела'},
    {'external_id': 10241, 'slug': 'shield', 'name': 'Щит'},
    {'external_id': 10247, 'slug': 'sleep', 'name': 'Сон'},
    {'external_id': 10289, 'slug': 'thunderwave', 'name': 'Громовая волна'},
]

# 2 уровень
LEVEL_2 = [
    {'external_id': 10020, 'slug': 'blur', 'name': 'Размытый образ'},
    {'external_id': 10054, 'slug': 'darkness', 'name': 'Тьма'},
    {'external_id': 10083, 'slug': 'hold-person', 'name': 'Удержание личности'},
    {'external_id': 10093, 'slug': 'invisibility', 'name': 'Невидимость'},
    {'external_id': 10132, 'slug': 'levitate', 'name': 'Левитация'},
    {'external_id': 10150, 'slug': 'mirror-image', 'name': 'Зеркальное отображение'},
    {'external_id': 10166, 'slug': 'misty-step', 'name': 'Туманный шаг'},
    {'external_id': 10244, 'slug': 'scorching-ray', 'name': 'Опаляющий луч'},
]

# 3 уровень
LEVEL_3 = [
    {'external_id': 10042, 'slug': 'counterspell', 'name': 'Отражение заклинания'},
    {'external_id': 10058, 'slug': 'dispel-magic', 'name': 'Рассеивание магии'},
    {'external_id': 10057, 'slug': 'fireball', 'name': 'Огненный шар'},
    {'external_id': 10072, 'slug': 'fly', 'name': 'Полёт'},
    {'external_id': 10080, 'slug': 'haste', 'name': 'Ускорение'},
    {'external_id': 10135, 'slug': 'lightning-bolt', 'name': 'Молния'},
]

# Все заклинания вместе
ALL_SPELLS = CANTRIPS + LEVEL_1 + LEVEL_2 + LEVEL_3


def get_spell_list(limit: int = None):
    """Получить список заклинаний"""
    if limit:
        return ALL_SPELLS[:limit]
    return ALL_SPELLS
