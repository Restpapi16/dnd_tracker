# scripts/load_reference_data.py
"""
Скрипт для загрузки данных с next.dnd.su в базу данных.

Использование:
    python scripts/load_reference_data.py --type spells --limit 10
    python scripts/load_reference_data.py --type items --limit 20
    python scripts/load_reference_data.py --type creatures --limit 5
    python scripts/load_reference_data.py --all  # Загрузить все
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.models_reference import ReferenceSpell, ReferenceItem, ReferenceCreature
from app.parsers.dndsu_parser import DndSuParser
from app import crud_reference


async def load_spells(parser: DndSuParser, limit: int = None):
    """Загрузить заклинания"""
    print(f"Начало загрузки заклинаний...")
    
    # Пример списка заклинаний для теста
    # В реальности нужно получить список со страницы https://next.dnd.su/spells/
    sample_spells = [
        {'external_id': 10222, 'slug': 'heroism'},
        {'external_id': 10057, 'slug': 'fireball'},
        {'external_id': 10145, 'slug': 'magic-missile'},
        # Добавьте больше заклинаний
    ]
    
    if limit:
        sample_spells = sample_spells[:limit]
    
    db = SessionLocal()
    loaded = 0
    skipped = 0
    
    try:
        for spell_info in sample_spells:
            external_id = spell_info['external_id']
            slug = spell_info['slug']
            
            # Проверяем, есть ли уже в базе
            existing = crud_reference.get_spell_by_external_id(db, external_id)
            if existing:
                print(f"  • Заклинание {external_id}-{slug} уже в базе, пропуск")
                skipped += 1
                continue
            
            # Парсим страницу
            print(f"  • Загружаем заклинание {external_id}-{slug}...")
            spell_data = await parser.parse_spell(external_id, slug)
            
            if spell_data:
                crud_reference.create_spell(db, spell_data)
                loaded += 1
                print(f"    ✓ Сохранено: {spell_data.get('name', slug)}")
            else:
                print(f"    ✗ Ошибка парсинга")
            
            # Небольшая задержка чтобы не перегрузить сервер
            await asyncio.sleep(1)
    
    finally:
        db.close()
    
    print(f"\nЗавершено! Загружено: {loaded}, Пропущено: {skipped}")


async def load_items(parser: DndSuParser, limit: int = None):
    """Загрузить предметы"""
    print(f"Начало загрузки предметов...")
    
    sample_items = [
        {'external_id': 36, 'slug': 'pistol'},
        {'external_id': 1, 'slug': 'longsword'},
        # Добавьте больше предметов
    ]
    
    if limit:
        sample_items = sample_items[:limit]
    
    db = SessionLocal()
    loaded = 0
    skipped = 0
    
    try:
        for item_info in sample_items:
            external_id = item_info['external_id']
            slug = item_info['slug']
            
            existing = db.query(ReferenceItem).filter(
                ReferenceItem.external_id == external_id
            ).first()
            
            if existing:
                print(f"  • Предмет {external_id}-{slug} уже в базе, пропуск")
                skipped += 1
                continue
            
            print(f"  • Загружаем предмет {external_id}-{slug}...")
            item_data = await parser.parse_item(external_id, slug)
            
            if item_data:
                crud_reference.create_item(db, item_data)
                loaded += 1
                print(f"    ✓ Сохранено: {item_data.get('name', slug)}")
            else:
                print(f"    ✗ Ошибка парсинга")
            
            await asyncio.sleep(1)
    
    finally:
        db.close()
    
    print(f"\nЗавершено! Загружено: {loaded}, Пропущено: {skipped}")


async def load_creatures(parser: DndSuParser, limit: int = None):
    """Загрузить существа"""
    print(f"Начало загрузки существ...")
    
    sample_creatures = [
        {'external_id': 21213, 'slug': 'beholder'},
        {'external_id': 1001, 'slug': 'goblin'},
        # Добавьте больше существ
    ]
    
    if limit:
        sample_creatures = sample_creatures[:limit]
    
    db = SessionLocal()
    loaded = 0
    skipped = 0
    
    try:
        for creature_info in sample_creatures:
            external_id = creature_info['external_id']
            slug = creature_info['slug']
            
            existing = db.query(ReferenceCreature).filter(
                ReferenceCreature.external_id == external_id
            ).first()
            
            if existing:
                print(f"  • Существо {external_id}-{slug} уже в базе, пропуск")
                skipped += 1
                continue
            
            print(f"  • Загружаем существо {external_id}-{slug}...")
            creature_data = await parser.parse_creature(external_id, slug)
            
            if creature_data:
                crud_reference.create_creature(db, creature_data)
                loaded += 1
                print(f"    ✓ Сохранено: {creature_data.get('name', slug)}")
            else:
                print(f"    ✗ Ошибка парсинга")
            
            await asyncio.sleep(1)
    
    finally:
        db.close()
    
    print(f"\nЗавершено! Загружено: {loaded}, Пропущено: {skipped}")


async def main():
    parser = argparse.ArgumentParser(
        description="Загрузка данных справочника D&D с next.dnd.su"
    )
    parser.add_argument(
        '--type',
        choices=['spells', 'items', 'creatures'],
        help="Тип данных для загрузки"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Загрузить все типы данных"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Ограничение количества записей"
    )
    
    args = parser.parse_args()
    
    # Создаем таблицы если их еще нет
    print("Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    
    dndsu_parser = DndSuParser()
    
    try:
        if args.all:
            await load_spells(dndsu_parser, args.limit)
            await load_items(dndsu_parser, args.limit)
            await load_creatures(dndsu_parser, args.limit)
        elif args.type == 'spells':
            await load_spells(dndsu_parser, args.limit)
        elif args.type == 'items':
            await load_items(dndsu_parser, args.limit)
        elif args.type == 'creatures':
            await load_creatures(dndsu_parser, args.limit)
        else:
            parser.print_help()
    
    finally:
        await dndsu_parser.close()


if __name__ == "__main__":
    asyncio.run(main())
