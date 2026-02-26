# app/parsers/dndsu_parser.py
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re
import asyncio


class DndSuParser:
    """Парсер для next.dnd.su с правильными CSS-селекторами"""
    
    BASE_URL = "https://next.dnd.su"
    TIMEOUT = 30.0
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=self.TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def close(self):
        """Закрыть HTTP клиент"""
        await self.client.aclose()
    
    async def parse_spell(self, external_id: int, slug: str) -> Optional[Dict]:
        """Парсинг заклинания с next.dnd.su"""
        url = f"{self.BASE_URL}/spells/{external_id}/"
        
        try:
            response = await self.client.get(url)
            
            # Обработка 503 - сервер перегружен
            if response.status_code == 503:
                print(f"  ⚠️  503 для ID {external_id}, пропускаем")
                return None
            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            html_text = soup.get_text()
            
            # 1. Название - card-title
            name_elem = soup.find(class_='card-title')
            name = name_elem.text.strip() if name_elem else slug
            
            # 2-3. Уровень и Школа - school_level
            school_level_elem = soup.find(class_='school_level')
            level = None
            school = None
            
            if school_level_elem:
                text = school_level_elem.text.strip()
                # Уровень
                if 'заговор' in text.lower():
                    level = 0
                else:
                    level_match = re.search(r'(\d+)\s*уровень', text)
                    if level_match:
                        level = int(level_match.group(1))
                
                # Школа
                schools = ['Очарование', 'Воплощение', 'Преграждение', 
                           'Иллюзия', 'Некромантия', 'Прорицание', 
                           'Превращение', 'Вызов']
                for s in schools:
                    if s in text:
                        school = s
                        break
            
            # 4. Время сотворения - cast_time
            cast_time_elem = soup.find(class_='cast_time')
            casting_time = cast_time_elem.text.strip() if cast_time_elem else None
            
            # 5. Дистанция - range
            range_elem = soup.find(class_='range')
            spell_range = range_elem.text.strip() if range_elem else None
            
            # 6. Компоненты - components
            components_elem = soup.find(class_='components')
            components = components_elem.text.strip() if components_elem else None
            
            # 7. Длительность - duration
            duration_elem = soup.find(class_='duration')
            duration = duration_elem.text.strip() if duration_elem else None
            
            # Концентрация
            concentration = False
            if duration and 'концентрац' in duration.lower():
                concentration = True
            
            # 8. Классы - ищем **Классы:** в тексте
            classes = []
            classes_match = re.search(r'\*\*Классы:\*\*([^\*]+)', html_text)
            if classes_match:
                classes_text = classes_match.group(1).strip()
                # Разбиваем по запятой
                classes = [c.strip() for c in classes_text.split(',') if c.strip()]
            
            # 9. Подклассы - ищем **Подклассы:** в тексте
            subclasses = []
            subclasses_match = re.search(r'\*\*Подклассы:\*\*([^\*\n]+)', html_text)
            if subclasses_match:
                subclasses_text = subclasses_match.group(1).strip()
                # Разбиваем по запятой
                subclasses = [s.strip() for s in subclasses_text.split(',') if s.strip()]
            
            # 10. Описание - subsection (правильный класс!)
            description = None
            at_higher_levels = None
            
            subsection_elem = soup.find(class_='subsection')
            if subsection_elem:
                full_text = subsection_elem.get_text(separator='\n\n', strip=True)
                
                # Разделяем основное описание и "На более высоких уровнях"
                if 'на более высоких уровнях' in full_text.lower():
                    parts = re.split(r'На более высоких уровнях', full_text, 
                                    maxsplit=1, flags=re.IGNORECASE)
                    description = parts[0].strip()
                    if len(parts) > 1:
                        at_higher_levels = 'На более высоких уровнях. ' + parts[1].strip()
                else:
                    description = full_text
            
            # Ритуал
            ritual = 'ритуал' in html_text.lower()
            
            return {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'level': level,
                'school': school,
                'casting_time': casting_time,
                'range': spell_range,
                'components': components,
                'duration': duration,
                'concentration': concentration,
                'ritual': ritual,
                'description': description,
                'at_higher_levels': at_higher_levels,
                'classes': classes,
                'subclasses': subclasses
            }
            
        except Exception as e:
            print(f"Error parsing spell {external_id}: {e}")
            return None
    
    async def parse_item(self, external_id: int, slug: str) -> Optional[Dict]:
        """Парсинг предмета"""
        url = f"{self.BASE_URL}/equipment/{external_id}-{slug}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name_elem = soup.find(class_='card-title')
            name = name_elem.text.strip() if name_elem else slug
            
            description_elem = soup.find(class_='description')
            description = description_elem.get_text(separator='\n', strip=True) if description_elem else None
            
            text_content = soup.get_text()
            
            category = None
            if 'оружие' in text_content.lower():
                category = 'Оружие'
            elif 'доспех' in text_content.lower():
                category = 'Доспехи'
            
            cost_match = re.search(r'(\d+)\s*(зм|см|мм)', text_content, re.IGNORECASE)
            cost = cost_match.group(0) if cost_match else None
            
            weight_match = re.search(r'(\d+[\.,]?\d*)\s*фнт', text_content)
            weight = weight_match.group(0) if weight_match else None
            
            damage_match = re.search(r'\d+к\d+', text_content)
            damage = damage_match.group(0) if damage_match else None
            
            ac_match = re.search(r'КД[:\s]*(\d+)', text_content)
            ac = int(ac_match.group(1)) if ac_match else None
            
            return {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'category': category,
                'subcategory': None,
                'cost': cost,
                'weight': weight,
                'damage': damage,
                'ac': ac,
                'properties': [],
                'description': description
            }
            
        except Exception as e:
            print(f"Error parsing item {external_id}-{slug}: {e}")
            return None
    
    async def parse_creature(self, external_id: int, slug: str) -> Optional[Dict]:
        """Парсинг существа"""
        url = f"{self.BASE_URL}/bestiary/{external_id}-{slug}/"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name_elem = soup.find(class_='card-title')
            name = name_elem.text.strip() if name_elem else slug
            
            text_content = soup.get_text()
            
            size = None
            sizes = ['Крошечный', 'Маленький', 'Средний', 'Большой', 'Огромный', 'Громадный']
            for s in sizes:
                if s in text_content:
                    size = s
                    break
            
            cr_match = re.search(r'(Показатель опасности|CR)[:\s]*(\d+/?\d*)', text_content)
            cr = cr_match.group(2) if cr_match else None
            
            ac_match = re.search(r'КД[:\s]*(\d+)', text_content)
            ac = int(ac_match.group(1)) if ac_match else None
            
            hp_match = re.search(r'(\d+)\s*\((\d+к\d+)', text_content)
            hp = hp_match.group(0) if hp_match else None
            
            stats = {}
            stats_pattern = r'(СИЛ|ЛОВ|ТЕЛ|ИНТ|МДР|ХАР)[:\s]*(\d+)'
            stats_matches = re.findall(stats_pattern, text_content)
            
            stats_map = {'СИЛ': 'strength', 'ЛОВ': 'dexterity', 'ТЕЛ': 'constitution',
                        'ИНТ': 'intelligence', 'МДР': 'wisdom', 'ХАР': 'charisma'}
            
            for stat_abbr, value in stats_matches:
                if stat_abbr in stats_map:
                    stats[stats_map[stat_abbr]] = int(value)
            
            return {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'size': size,
                'creature_type': None,
                'alignment': None,
                'ac': ac,
                'hp': hp,
                'initiative': None,
                'speed': {},
                'strength': stats.get('strength'),
                'dexterity': stats.get('dexterity'),
                'constitution': stats.get('constitution'),
                'intelligence': stats.get('intelligence'),
                'wisdom': stats.get('wisdom'),
                'charisma': stats.get('charisma'),
                'saving_throws': {},
                'skills': {},
                'senses': None,
                'languages': None,
                'cr': cr,
                'xp': None,
                'features': [],
                'actions': [],
                'bonus_actions': [],
                'reactions': [],
                'legendary_actions': []
            }
            
        except Exception as e:
            print(f"Error parsing creature {external_id}-{slug}: {e}")
            return None
    
    async def get_spells_list(self, page: int = 1) -> List[Dict]:
        """Получить список заклинаний"""
        url = f"{self.BASE_URL}/spells/"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            spell_links = soup.find_all('a', href=re.compile(r'/spells/\d+-[\w-]+/'))
            
            spells = []
            for link in spell_links:
                href = link.get('href')
                match = re.search(r'/spells/(\d+)-([\w-]+)/', href)
                if match:
                    spells.append({
                        'external_id': int(match.group(1)),
                        'slug': match.group(2),
                        'name': link.text.strip()
                    })
            
            return spells
            
        except Exception as e:
            print(f"Error getting spells list: {e}")
            return []
