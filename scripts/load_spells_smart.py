#!/usr/bin/env python3
# scripts/load_spells_smart.py
"""
Умная загрузка заклинаний без Selenium
Автоматически находит все заклинания по диапазону ID

Использование:
    python scripts/load_spells_smart.py --limit 50
    python scripts/load_spells_smart.py --start 10000 --end 10100 --limit 50
    python scripts/load_spells_smart.py --start 10500 --end 10600 --all
"""

import asyncio
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.parsers.dndsu_parser import DndSuParser
from app import crud_reference


async def load_spells_by_range(
    start_id: int,
    end_id: int,
    limit: int = None
):
    """
    Загрузка заклинаний по диапазону ID
    
    Args:
        start_id: Начальный ID
        end_id: Конечный ID
        limit: Максимальное количество
    """
    
    print("✨ Умная загрузка заклинаний с next.dnd.su\n")
    print(f"📊 Диапазон ID: {start_id} - {end_id}")
    print("🔄 Режим: Автоматическое обновление существующих")
    print("🐌 Задержки: 3 сек между запросами, 10 сек каждые 5 заклинаний\n")
    
    # Создаем таблицы
    print("🛠️  Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    
    parser = DndSuParser()
    db = SessionLocal()
    
    try:
        loaded = 0
        updated = 0
        not_found = 0
        skipped_invalid = 0
        
        total = end_id - start_id + 1
        
        print(f"\n🚀 Начинаем сканирование {total} ID...\n")
        
        for i, external_id in enumerate(range(start_id, end_id + 1), 1):
            # Лимит
            if limit and (loaded + updated) >= limit:
                print(f"\n✅ Достигнут лимит: {limit} заклинаний")
                break
            
            # Проверка существующего
            existing = crud_reference.get_spell_by_external_id(db, external_id)
            
            # Используем ID как slug (сайт сам редиректит)
            slug = str(external_id)
            
            spell_data = await parser.parse_spell(external_id, slug)
            
            if spell_data and spell_data.get('name'):
                # ВАЛИДАЦИЯ: проверяем обязательные поля
                if spell_data.get('level') is None:
                    skipped_invalid += 1
                    print(f"[{i}/{total}] ⚠️  [{external_id}] {spell_data['name']} - пропущено (нет уровня)")
                    continue
                
                if existing:
                    # Обновляем существующее
                    crud_reference.update_spell(db, existing.id, spell_data)
                    updated += 1
                    print(f"[{i}/{total}] 🔄 [{external_id}] {spell_data['name']} - обновлено")
                else:
                    # Создаем новое
                    crud_reference.create_spell(db, spell_data)
                    loaded += 1
                    print(f"[{i}/{total}] ✅ [{external_id}] {spell_data['name']}")
            else:
                not_found += 1
                # Показываем только каждый 100-й 404
                if not_found % 100 == 0:
                    print(f"[{i}/{total}] ⚠️  Пропущено 404: {not_found}")
            
            # Rate limiting - УВЕЛИЧЕННЫЕ задержки
            if (loaded + updated) % 5 == 0 and (loaded + updated) > 0:
                print(f"  ⏸️  Пауза 10 сек для избежания блокировки...")
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"✅ Загружено новых: {loaded}")
        print(f"🔄 Обновлено: {updated}")
        print(f"⚠️  Пропущено (невалидные): {skipped_invalid}")
        print(f"❌ Не найдено (404): {not_found}")
        print(f"📊 Проверено ID: {i}")
        print(f"{'='*60}\n")
        
        if loaded > 0 or updated > 0:
            print("✨ Справочник готов!\n")
            print("Что теперь можно сделать:")
            print("  1️⃣  Откройте бота в Telegram")
            print("  2️⃣  Нажмите '📚 Справочник'")
            print("  3️⃣  Начните вводить в поиске")
            print("  4️⃣  Увидите подсказки в реальном времени! ⚡\n")
    
    finally:
        db.close()
        await parser.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Умная загрузка заклинаний по диапазону ID",
        epilog="Примеры:\n"
               "  python scripts/load_spells_smart.py --start 10000 --end 10100 --limit 20\n"
               "  python scripts/load_spells_smart.py --start 10500 --end 10600 --all\n"
               "  python scripts/load_spells_smart.py --limit 50  # использует диапазон по умолчанию",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--start',
        type=int,
        default=10000,
        help="Начальный ID (по умолчанию 10000)"
    )
    parser.add_argument(
        '--end',
        type=int,
        default=10500,
        help="Конечный ID (по умолчанию 10500)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Максимальное количество заклинаний для загрузки/обновления"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Загрузить/обновить все заклинания в диапазоне (игнорирует --limit)"
    )
    
    args = parser.parse_args()
    
    # Валидация диапазона
    if args.start > args.end:
        print("❌ Ошибка: --start должен быть меньше или равен --end")
        sys.exit(1)
    
    await load_spells_by_range(
        start_id=args.start,
        end_id=args.end,
        limit=None if args.all else args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())
