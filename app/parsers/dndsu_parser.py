# app/parsers/dndsu_parser.py
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re


class DndSuParser:
    """Парсер для сайта next.dnd.su"""
    
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
        """Парсинг страницы заклинания"""
        url = f"{self.BASE_URL}/spells/{external_id}-{slug}/"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Название заклинания
            name = soup.find('h1').text.strip() if soup.find('h1') else slug
            
            # Основные характеристики (обычно в div с классом или в таблице)
            # TODO: Нужно изучить реальную структуру HTML
            data = {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'level': None,
                'school': None,
                'casting_time': None,
                'range': None,
                'components': None,
                'duration': None,
                'concentration': False,
                'ritual': False,
                'description': None,
                'at_higher_levels': None,
                'classes': []
            }
            
            # Парсинг характеристик
            # Пример: ищем паттерны в тексте
            text_content = soup.get_text()
            
            # Парсинг уровня (например: "1 уровень")
            level_match = re.search(r'(\d+)\s*уровень', text_content)
            if level_match:
                data['level'] = int(level_match.group(1))
            elif 'заговор' in text_content.lower():
                data['level'] = 0
            
            # Парсинг школы магии
            schools = ['Очарование', 'Воплощение', 'Преграждение', 'Иллюзия', 'Некромантия', 'Прорицание', 'Превращение', 'Вызов']
            for school in schools:
                if school in text_content:
                    data['school'] = school
                    break
            
            # Концентрация
            if 'Концентрация' in text_content or 'концентрац' in text_content.lower():
                data['concentration'] = True
            
            # Описание (обычно в основном блоке контента)
            description_elem = soup.find('div', class_=re.compile(r'content|description|spell-text'))
            if description_elem:
                data['description'] = description_elem.get_text(separator='\n', strip=True)
            
            return data
            
        except Exception as e:
            print(f"Error parsing spell {external_id}-{slug}: {e}")
            return None
    
    async def parse_item(self, external_id: int, slug: str) -> Optional[Dict]:
        """Парсинг страницы предмета"""
        url = f"{self.BASE_URL}/equipment/{external_id}-{slug}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name = soup.find('h1').text.strip() if soup.find('h1') else slug
            
            data = {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'category': None,
                'subcategory': None,
                'cost': None,
                'weight': None,
                'damage': None,
                'ac': None,
                'properties': [],
                'description': None
            }
            
            text_content = soup.get_text()
            
            # Парсинг характеристик предмета
            # TODO: Адаптировать под реальную структуру HTML
            
            # Стоимость
            cost_match = re.search(r'(\d+)\s*(ЗМ|СМ|ММ|ПМ|ЭМ)', text_content)
            if cost_match:
                data['cost'] = cost_match.group(0)
            
            # Вес
            weight_match = re.search(r'(\d+[\.,]?\d*)\s*фнт', text_content)
            if weight_match:
                data['weight'] = weight_match.group(0)
            
            # Урон оружия
            damage_match = re.search(r'(\d+к\d+)[^\n]*?(Колющий|Рубящий|Дробящий)', text_content)
            if damage_match:
                data['damage'] = damage_match.group(0)
            
            description_elem = soup.find('div', class_=re.compile(r'content|description'))
            if description_elem:
                data['description'] = description_elem.get_text(separator='\n', strip=True)
            
            return data
            
        except Exception as e:
            print(f"Error parsing item {external_id}-{slug}: {e}")
            return None
    
    async def parse_creature(self, external_id: int, slug: str) -> Optional[Dict]:
        """Парсинг страницы существа"""
        url = f"{self.BASE_URL}/bestiary/{external_id}-{slug}/"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name = soup.find('h1').text.strip() if soup.find('h1') else slug
            
            data = {
                'external_id': external_id,
                'slug': slug,
                'name': name,
                'source_url': url,
                'size': None,
                'creature_type': None,
                'alignment': None,
                'ac': None,
                'hp': None,
                'initiative': None,
                'speed': {},
                'strength': None,
                'dexterity': None,
                'constitution': None,
                'intelligence': None,
                'wisdom': None,
                'charisma': None,
                'saving_throws': {},
                'skills': {},
                'senses': None,
                'languages': None,
                'cr': None,
                'xp': None,
                'features': [],
                'actions': [],
                'bonus_actions': [],
                'reactions': [],
                'legendary_actions': []
            }
            
            text_content = soup.get_text()
            
            # Парсинг характеристик существа
            # TODO: Детальный парсинг структуры страницы существа
            
            # CR (Challenge Rating)
            cr_match = re.search(r'Показатель опасности[:\s]*(\d+/?\d*)', text_content)
            if cr_match:
                data['cr'] = cr_match.group(1)
            
            # КД
            ac_match = re.search(r'КД[:\s]*(\d+)', text_content)
            if ac_match:
                data['ac'] = int(ac_match.group(1))
            
            # Характеристики (СИЛ, ЛОВ и т.д.)
            stats_pattern = r'(СИЛ|ЛОВ|ТЕЛ|ИНТ|МДР|ХАР)[:\s]*(\d+)'
            stats_matches = re.findall(stats_pattern, text_content)
            
            stats_map = {
                'СИЛ': 'strength',
                'ЛОВ': 'dexterity',
                'ТЕЛ': 'constitution',
                'ИНТ': 'intelligence',
                'МДР': 'wisdom',
                'ХАР': 'charisma'
            }
            
            for stat_abbr, value in stats_matches:
                if stat_abbr in stats_map:
                    data[stats_map[stat_abbr]] = int(value)
            
            return data
            
        except Exception as e:
            print(f"Error parsing creature {external_id}-{slug}: {e}")
            return None
    
    async def get_spells_list(self, page: int = 1) -> List[Dict]:
        """Получить список заклинаний"""
        # TODO: Парсинг списка заклинаний с пагинацией
        url = f"{self.BASE_URL}/spells/"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Найти все ссылки на заклинания
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
