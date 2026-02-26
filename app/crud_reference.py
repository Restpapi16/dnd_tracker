# app/crud_reference.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from . import models_reference, schemas_reference


# ============ SPELLS CRUD ============

def create_spell(db: Session, spell_data: dict) -> models_reference.ReferenceSpell:
    """Создать новое заклинание в базе"""
    db_spell = models_reference.ReferenceSpell(**spell_data)
    db.add(db_spell)
    db.commit()
    db.refresh(db_spell)
    return db_spell


def update_spell(db: Session, spell_id: int, spell_data: dict) -> Optional[models_reference.ReferenceSpell]:
    """Обновить существующее заклинание"""
    db_spell = db.query(models_reference.ReferenceSpell).filter(
        models_reference.ReferenceSpell.id == spell_id
    ).first()
    
    if not db_spell:
        return None
    
    # Обновляем все поля
    for key, value in spell_data.items():
        setattr(db_spell, key, value)
    
    db.commit()
    db.refresh(db_spell)
    return db_spell


def get_spell_by_id(db: Session, spell_id: int) -> Optional[models_reference.ReferenceSpell]:
    """Получить заклинание по ID"""
    return db.query(models_reference.ReferenceSpell).filter(
        models_reference.ReferenceSpell.id == spell_id
    ).first()


def get_spell_by_external_id(db: Session, external_id: int) -> Optional[models_reference.ReferenceSpell]:
    """Получить заклинание по external_id с dnd.su"""
    return db.query(models_reference.ReferenceSpell).filter(
        models_reference.ReferenceSpell.external_id == external_id
    ).first()


def search_spells(
    db: Session,
    query: str,
    level: Optional[int] = None,
    school: Optional[str] = None,
    limit: int = 10
) -> List[models_reference.ReferenceSpell]:
    """Поиск заклинаний по названию"""
    q = db.query(models_reference.ReferenceSpell)
    
    # Поиск по названию (без учета регистра для кириллицы)
    if query:
        q = q.filter(func.lower(models_reference.ReferenceSpell.name).like(f"%{query.lower()}%"))
    
    # Фильтр по уровню
    if level is not None:
        q = q.filter(models_reference.ReferenceSpell.level == level)
    
    # Фильтр по школе магии
    if school:
        q = q.filter(models_reference.ReferenceSpell.school == school)
    
    return q.order_by(models_reference.ReferenceSpell.name).limit(limit).all()


def get_spells_suggestions(
    db: Session,
    query: str,
    limit: int = 10
) -> List[schemas_reference.SpellSuggestion]:
    """Быстрый поиск для автодополнения (только id и name)"""
    results = db.query(
        models_reference.ReferenceSpell.id,
        models_reference.ReferenceSpell.name,
        models_reference.ReferenceSpell.level,
        models_reference.ReferenceSpell.school
    ).filter(
        func.lower(models_reference.ReferenceSpell.name).like(f"%{query.lower()}%")
    ).order_by(models_reference.ReferenceSpell.name).limit(limit).all()
    
    return [
        schemas_reference.SpellSuggestion(
            id=r.id,
            name=r.name,
            level=r.level,
            school=r.school,
            type='spell'
        )
        for r in results
    ]


# ============ ITEMS CRUD ============

def create_item(db: Session, item_data: dict) -> models_reference.ReferenceItem:
    """Создать новый предмет в базе"""
    db_item = models_reference.ReferenceItem(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item_by_id(db: Session, item_id: int) -> Optional[models_reference.ReferenceItem]:
    """Получить предмет по ID"""
    return db.query(models_reference.ReferenceItem).filter(
        models_reference.ReferenceItem.id == item_id
    ).first()


def search_items(
    db: Session,
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> List[models_reference.ReferenceItem]:
    """Поиск предметов по названию"""
    q = db.query(models_reference.ReferenceItem)
    
    if query:
        q = q.filter(func.lower(models_reference.ReferenceItem.name).like(f"%{query.lower()}%"))
    
    if category:
        q = q.filter(func.lower(models_reference.ReferenceItem.category).like(f"%{category.lower()}%"))
    
    return q.order_by(models_reference.ReferenceItem.name).limit(limit).all()


def get_items_suggestions(
    db: Session,
    query: str,
    limit: int = 10
) -> List[schemas_reference.ItemSuggestion]:
    """Быстрый поиск для автодополнения"""
    results = db.query(
        models_reference.ReferenceItem.id,
        models_reference.ReferenceItem.name,
        models_reference.ReferenceItem.category
    ).filter(
        func.lower(models_reference.ReferenceItem.name).like(f"%{query.lower()}%")
    ).order_by(models_reference.ReferenceItem.name).limit(limit).all()
    
    return [
        schemas_reference.ItemSuggestion(
            id=r.id,
            name=r.name,
            category=r.category,
            type='item'
        )
        for r in results
    ]


# ============ CREATURES CRUD ============

def create_creature(db: Session, creature_data: dict) -> models_reference.ReferenceCreature:
    """Создать новое существо в базе"""
    db_creature = models_reference.ReferenceCreature(**creature_data)
    db.add(db_creature)
    db.commit()
    db.refresh(db_creature)
    return db_creature


def get_creature_by_id(db: Session, creature_id: int) -> Optional[models_reference.ReferenceCreature]:
    """Получить существо по ID"""
    return db.query(models_reference.ReferenceCreature).filter(
        models_reference.ReferenceCreature.id == creature_id
    ).first()


def search_creatures(
    db: Session,
    query: str,
    cr: Optional[str] = None,
    creature_type: Optional[str] = None,
    limit: int = 10
) -> List[models_reference.ReferenceCreature]:
    """Поиск существ по названию"""
    q = db.query(models_reference.ReferenceCreature)
    
    if query:
        q = q.filter(func.lower(models_reference.ReferenceCreature.name).like(f"%{query.lower()}%"))
    
    if cr:
        q = q.filter(models_reference.ReferenceCreature.cr == cr)
    
    if creature_type:
        q = q.filter(func.lower(models_reference.ReferenceCreature.creature_type).like(f"%{creature_type.lower()}%"))
    
    return q.order_by(models_reference.ReferenceCreature.name).limit(limit).all()


def get_creatures_suggestions(
    db: Session,
    query: str,
    limit: int = 10
) -> List[schemas_reference.CreatureSuggestion]:
    """Быстрый поиск для автодополнения"""
    results = db.query(
        models_reference.ReferenceCreature.id,
        models_reference.ReferenceCreature.name,
        models_reference.ReferenceCreature.cr,
        models_reference.ReferenceCreature.creature_type
    ).filter(
        func.lower(models_reference.ReferenceCreature.name).like(f"%{query.lower()}%")
    ).order_by(models_reference.ReferenceCreature.name).limit(limit).all()
    
    return [
        schemas_reference.CreatureSuggestion(
            id=r.id,
            name=r.name,
            cr=r.cr,
            creature_type=r.creature_type,
            type='creature'
        )
        for r in results
    ]


# ============ COMBINED SEARCH ============

def get_all_suggestions(
    db: Session,
    query: str,
    limit_per_type: int = 5
) -> schemas_reference.AllSuggestions:
    """Получить подсказки по всем типам одновременно"""
    return schemas_reference.AllSuggestions(
        spells=get_spells_suggestions(db, query, limit_per_type),
        items=get_items_suggestions(db, query, limit_per_type),
        creatures=get_creatures_suggestions(db, query, limit_per_type)
    )
