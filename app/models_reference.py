# app/models_reference.py
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from .database import Base
from datetime import datetime


class ReferenceSpell(Base):
    """Заклинания из справочника D&D"""
    __tablename__ = "reference_spells"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True)  # ID с dnd.su
    slug = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Основные характеристики
    level = Column(Integer, nullable=False, index=True)  # 0-9 (0 = заговор)
    school = Column(String)  # Очарование, Воплощение и т.д.
    casting_time = Column(String)  # "Действие", "Бонусное действие"
    range = Column(String)  # "Касание", "30 футов"
    components = Column(String)  # "В, С, М"
    duration = Column(String)  # "Концентрация, 1 минута"
    concentration = Column(Boolean, default=False)
    ritual = Column(Boolean, default=False)
    
    # Описание и эффекты
    description = Column(Text)
    at_higher_levels = Column(Text, nullable=True)
    
    # Классы, которые могут использовать
    classes = Column(JSON)  # ["Бард", "Паладин"]
    subclasses = Column(JSON, nullable=True)
    
    # Мета-информация
    source_url = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReferenceItem(Base):
    """Предметы и снаряжение из справочника D&D"""
    __tablename__ = "reference_items"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Основные характеристики
    category = Column(String, index=True)  # "Воинское Дальнобойное оружие"
    subcategory = Column(String, nullable=True)  # "Оружие", "Доспех", "Инструмент"
    cost = Column(String, nullable=True)  # "250 ЗМ"
    weight = Column(String, nullable=True)  # "3 фнт"
    
    # Характеристики оружия/доспехов
    damage = Column(String, nullable=True)  # "1к10, Колющий"
    ac = Column(String, nullable=True)  # Для доспехов
    properties = Column(JSON, nullable=True)  # Свойства оружия
    
    # Описание
    description = Column(Text)
    
    # Мета
    source_url = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReferenceCreature(Base):
    """Существа из бестиария D&D"""
    __tablename__ = "reference_creatures"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Основная информация
    size = Column(String)  # "Большая"
    creature_type = Column(String)  # "Аберрация"
    alignment = Column(String)  # "Принципиально-Злая"
    
    # Боевые характеристики
    ac = Column(Integer)
    hp = Column(String)  # "190 (20к10 + 80)"
    initiative = Column(String)  # "+12 (22)"
    speed = Column(JSON)  # {"walk": "5 футов", "fly": "40 футов"}
    
    # Характеристики (Ability Scores)
    strength = Column(Integer)
    dexterity = Column(Integer)
    constitution = Column(Integer)
    intelligence = Column(Integer)
    wisdom = Column(Integer)
    charisma = Column(Integer)
    
    # Модификаторы характеристик
    str_mod = Column(String, nullable=True)
    dex_mod = Column(String, nullable=True)
    con_mod = Column(String, nullable=True)
    int_mod = Column(String, nullable=True)
    wis_mod = Column(String, nullable=True)
    cha_mod = Column(String, nullable=True)
    
    # Спасброски и навыки
    saving_throws = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    
    # Защиты и уязвимости
    damage_resistances = Column(String, nullable=True)
    damage_immunities = Column(String, nullable=True)
    condition_immunities = Column(String, nullable=True)
    
    # Чувства и языки
    senses = Column(String)
    languages = Column(String)
    
    # CR и опыт
    cr = Column(String, index=True)  # "13"
    xp = Column(Integer)  # 10000
    
    # Способности (JSON для гибкости)
    features = Column(JSON)  # Особенности
    actions = Column(JSON)  # Действия
    bonus_actions = Column(JSON, nullable=True)
    reactions = Column(JSON, nullable=True)
    legendary_actions = Column(JSON, nullable=True)
    
    # Описание и лор
    description = Column(Text, nullable=True)
    environment = Column(String, nullable=True)  # Среда обитания
    
    # Мета
    source_url = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Создаем индексы для быстрого поиска (требует расширения pg_trgm в PostgreSQL)
# Index('idx_spell_name_trgm', ReferenceSpell.name, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
# Index('idx_item_name_trgm', ReferenceItem.name, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
# Index('idx_creature_name_trgm', ReferenceCreature.name, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
