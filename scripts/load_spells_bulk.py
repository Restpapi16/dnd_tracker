#!/usr/bin/env python3
# scripts/load_spells_bulk.py
"""
Боевой скрипт для массовой загрузки заговоров с next.dnd.su

Использование:
    python scripts/load_spells_bulk.py --limit 50
    python scripts/load_spells_bulk.py --all  # Загрузить все
"""

import asyncio
import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.parsers.dndsu_parser import DndSuParser
from app import crud_reference
import httpx
from bs4 import BeautifulSoup


class SpellListParser:
    """Парсер списка заклинаний с next.dnd.su"""
    
    BASE_URL = "https://next.dnd.su"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
    
    async def close(self):
        await self.client.aclose()
    
    async def get_all_spell_links(self) -> List[Dict[str, any]]:
        """
        Получить все ссылки на заклинания.
        Возвращает список: [{'external_id': 123, 'slug': 'heroism', 'name': 'Героизм'}, ...]
        """
        print(f"🔍 Парсим список заклинаний с {self.BASE_URL}/spells/...")
        
        try:
            # Запрашиваем страницу списка
            response = await self.client.get(f"{self.BASE_URL}/spells/")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем все ссылки на заклинания
            # Формат: /spells/12345-spell-name/ или /spells/12345/
            spell_links = []
            
            # Вариант 1: Ищем все <a> с href как /spells/
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                
                # Проверяем формат: /spells/123-name/ или /spells/123/
                match = re.match(r'/spells/(\d+)(?:-([\w-]+))?/?$', href)
                if match:
                    external_id = int(match.group(1))
                    slug = match.group(2) if match.group(2) else str(external_id)
                    name = link.text.strip()
                    
                    if name and external_id:
                        spell_links.append({
                            'external_id': external_id,
                            'slug': slug,
                            'name': name
                        })
            
            # Удаляем дубликаты по external_id
            seen = set()
            unique_spells = []
            for spell in spell_links:
                if spell['external_id'] not in seen:
                    seen.add(spell['external_id'])
                    unique_spells.append(spell)
            
            print(f"✅ Найдено {len(unique_spells)} уникальных заклинаний")
            
            # Выводим первые 5 для проверки
            if unique_spells:
                print("\n📝 Первые 5 заклинаний:")
                for spell in unique_spells[:5]:
                    print(f"  - {spell['name']} (ID: {spell['external_id']}, slug: {spell['slug']})")
                print()
            
            return unique_spells
            
        except Exception as e:
            print(f"❌ Ошибка парсинга списка: {e}")
            import traceback
            traceback.print_exc()
            return []


async def load_spells_bulk(limit: int = None):
    """Массовая загрузка заклинаний"""
    
    # Создаем таблицы
    print("🛠️  Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    
    # Инициализируем парсеры
    list_parser = SpellListParser()
    detail_parser = DndSuParser()
    
    db = SessionLocal()
    
    try:
        # 1. Получаем список всех заклинаний
        spell_list = await list_parser.get_all_spell_links()
        
        if not spell_list:
            print("❌ Не удалось получить список заклинаний")
            return
        
        # Применяем лимит
        if limit:
            spell_list = spell_list[:limit]
            print(f"🔢 Ограничение: загрузим {limit} заклинаний")
        
        print(f"\n🚀 Начинаем загрузку {len(spell_list)} заклинаний...\n")
        
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
            print(f"[{i}/{len(spell_list)}] 🔄 {name}...", end=' ')
            spell_data = await detail_parser.parse_spell(external_id, slug)
            
            if spell_data:
                crud_reference.create_spell(db, spell_data)
                loaded += 1
                print(f"✅ OK")
            else:
                errors += 1
                print(f"❌ FAIL")
            
            # Задержка чтобы не перегрузить сервер
            if i % 10 == 0:
                await asyncio.sleep(2)  # Каждые 10 заклинаний - пауза 2с
            else:
                await asyncio.sleep(0.5)  # Между запросами
        
        print(f"\n{'='*60}")
        print(f"✅ Загружено: {loaded}")
        print(f"⏭️  Пропущено (уже есть): {skipped}")
        print(f"❌ Ошибок: {errors}")
        print(f"{'='*60}\n")
        
    finally:
        db.close()
        await list_parser.close()
        await detail_parser.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Боевая загрузка заклинаний с next.dnd.su"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Максимальное количество заклинаний для загрузки"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Загрузить все заклинания"
    )
    
    args = parser.parse_args()
    
    if args.all:
        await load_spells_bulk(limit=None)
    elif args.limit:
        await load_spells_bulk(limit=args.limit)
    else:
        # По умолчанию загружаем 10
        await load_spells_bulk(limit=10)


if __name__ == "__main__":
    asyncio.run(main())
