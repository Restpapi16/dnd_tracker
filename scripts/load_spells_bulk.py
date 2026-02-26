#!/usr/bin/env python3
# scripts/load_spells_bulk.py
"""
Боевой скрипт для массовой загрузки заклинаний с next.dnd.su

Использование:
    python scripts/load_spells_bulk.py --limit 10
    python scripts/load_spells_bulk.py  # Загрузить все из spell_ids.py
"""

import asyncio
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.parsers.dndsu_parser import DndSuParser
from app import crud_reference
from scripts.spell_ids import get_spell_list


async def load_spells_bulk(limit: int = None):
    """Массовая загрузка заклинаний"""
    
    # Создаем таблицы
    print("🛠️  Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    
    # Получаем список заклинаний
    spell_list = get_spell_list(limit=limit)
    
    if not spell_list:
        print("❌ Нет заклинаний для загрузки")
        return
    
    print(f"📚 Список: {len(spell_list)} заклинаний")
    print(f"🚀 Начинаем загрузку...\n")
    
    detail_parser = DndSuParser()
    db = SessionLocal()
    
    try:
        loaded = 0
        skipped = 0
        errors = 0
        
        for i, spell_info in enumerate(spell_list, 1):
            external_id = spell_info['external_id']
            slug = spell_info['slug']
            name = spell_info['name']
            
            # Проверяем, есть ли уже в базе
            existing = crud_reference.get_spell_by_external_id(db, external_id)
            if existing:
                print(f"[{i}/{len(spell_list)}] ⏭️  {name} - уже в базе")
                skipped += 1
                continue
            
            # Парсим детали
            print(f"[{i}/{len(spell_list)}] 🔄 {name}...", end=' ', flush=True)
            spell_data = await detail_parser.parse_spell(external_id, slug)
            
            if spell_data:
                crud_reference.create_spell(db, spell_data)
                loaded += 1
                print(f"✅")
            else:
                errors += 1
                print(f"❌")
            
            # Задержка чтобы не перегрузить сервер
            if i % 10 == 0:
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"✅ Загружено: {loaded}")
        print(f"⏭️  Пропущено (уже есть): {skipped}")
        print(f"❌ Ошибок: {errors}")
        print(f"{'='*60}\n")
        
        if loaded > 0:
            print("✅ Теперь можно проверить:")
            print("   1. Откройте бота")
            print("   2. Нажмите '📚 Справочник'")
            print("   3. Начните вводить в поиске (например, 'огонь')")
            print("   4. Увидите подсказки в реальном времени!\n")
        
    finally:
        db.close()
        await detail_parser.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Загрузка заклинаний с next.dnd.su"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Максимальное количество заклинаний"
    )
    
    args = parser.parse_args()
    
    await load_spells_bulk(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
