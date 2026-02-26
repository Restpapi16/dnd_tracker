#!/usr/bin/env python3
# scripts/load_spells_selenium.py
"""
Боевой загрузчик заклинаний через Selenium

Примеры:
    python scripts/load_spells_selenium.py          # по умолчанию 10
    python scripts/load_spells_selenium.py --limit 50
    python scripts/load_spells_selenium.py --all
"""

import asyncio
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.parsers.dndsu_parser import DndSuParser
from app.parsers.spell_crawler import SpellCrawler
from app import crud_reference


async def load_spells_with_selenium(limit: int | None = None) -> None:
    print("✨ Запуск автоматического парсинга заклинаний с next.dnd.su\n")

    print("🛠️  Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)

    print("\n" + "=" * 60)
    print("🔍 Шаг 1: Парсинг списка заклинаний")
    print("=" * 60 + "\n")

    with SpellCrawler(headless=True) as crawler:
        spell_list = crawler.get_all_spell_links(max_scrolls=30)

    if not spell_list:
        print("❌ Не удалось получить список заклинаний")
        return

    if limit is not None:
        spell_list = spell_list[:limit]
        print(f"🔢 Ограничение: загрузим {len(spell_list)} заклинаний\n")

    print("\n" + "=" * 60)
    print(f"🚀 Шаг 2: Загрузка {len(spell_list)} заклинаний")
    print("=" * 60 + "\n")

    detail_parser = DndSuParser()
    db = SessionLocal()

    try:
        loaded = 0
        skipped = 0
        errors = 0

        total = len(spell_list)

        for i, spell_info in enumerate(spell_list, 1):
            external_id = spell_info["external_id"]
            slug = spell_info["slug"]
            name = spell_info["name"]

            existing = crud_reference.get_spell_by_external_id(db, external_id)
            if existing:
                print(f"[{i}/{total}] ⏭️  {name} - уже в базе")
                skipped += 1
                continue

            print(f"[{i}/{total}] 🔄 {name}...", end=" ", flush=True)
            spell_data = await detail_parser.parse_spell(external_id, slug)

            if spell_data:
                crud_reference.create_spell(db, spell_data)
                loaded += 1
                print("✅")
            else:
                errors += 1
                print("❌")

            if i % 10 == 0:
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"✅ Загружено: {loaded}")
        print(f"⏭️  Пропущено (уже есть): {skipped}")
        print(f"❌ Ошибок: {errors}")
        print("=" * 60 + "\n")

        if loaded > 0:
            print("✨ Справочник готов к использованию!\n")
            print("Что теперь можно сделать:")
            print("  1️⃣  Открой бота в Telegram")
            print("  2️⃣  Нажми '📚 Справочник'")
            print("  3️⃣  Начни вводить в поиске")
            print("  4️⃣  Увидишь подсказки в реальном времени ⚡\n")

    finally:
        db.close()
        await detail_parser.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Автоматическая загрузка заклинаний с next.dnd.su через Selenium"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Максимальное количество заклинаний для загрузки",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Загрузить все найденные заклинания",
    )

    args = parser.parse_args()

    if args.all:
        await load_spells_with_selenium(limit=None)
    else:
        await load_spells_with_selenium(limit=args.limit or 10)


if __name__ == "__main__":
    asyncio.run(main())
