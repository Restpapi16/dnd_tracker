# app/parsers/spell_crawler.py
"""
Краулер для получения списка всех заклинаний с next.dnd.su через Selenium
"""

import re
import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class SpellCrawler:
    """Краулер для получения списка заклинаний через Selenium"""

    BASE_URL = "https://next.dnd.su"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def start(self):
        """Запустить браузер"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")

        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )

        # Используем системный chromedriver
        service = Service("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        print("✅ Selenium браузер запущен")

    def stop(self):
        """Остановить браузер"""
        if self.driver:
            self.driver.quit()
            print("✅ Selenium браузер остановлен")

    def get_all_spell_links(self, max_scrolls: int = 20) -> List[Dict]:
        """
        Получить все ссылки на заклинания со страницы /spells/

        Returns:
            [{'external_id': 123, 'slug': 'heroism', 'name': 'Героизм'}, ...]
        """
        if not self.driver:
            raise RuntimeError(
                "Браузер не запущен. Вызови start() или используй контекстный менеджер.")

        url = f"{self.BASE_URL}/spells/"
        print(f"🔍 Открываем {url}")

        self.driver.get(url)
        time.sleep(3)

        print("🔄 Прокручиваем страницу для загрузки всех заклинаний...")

        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")

            if new_height == last_height:
                print(
                    f"  ✅ Достигнут конец страницы после {scrolls} прокруток")
                break

            last_height = new_height
            scrolls += 1

            if scrolls % 5 == 0:
                print(f"  🔄 Прокручено: {scrolls}/{max_scrolls}")

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        spell_links: List[Dict] = []

        for link in soup.find_all("a", href=True):
            href = link.get("href") or ""

            match = re.match(r"/spells/(\d+)(?:-([\w-]+))?/?$", href)
            if match:
                external_id = int(match.group(1))
                slug = match.group(2) if match.group(2) else str(external_id)
                name = (link.text or "").strip()

                if name and external_id:
                    spell_links.append(
                        {
                            "external_id": external_id,
                            "slug": slug,
                            "name": name,
                        }
                    )

        seen = set()
        unique_spells: List[Dict] = []
        for spell in spell_links:
            if spell["external_id"] not in seen:
                seen.add(spell["external_id"])
                unique_spells.append(spell)

        print(f"\n✅ Найдено {len(unique_spells)} уникальных заклинаний")

        if unique_spells:
            print("\n📝 Первые 5 заклинаний:")
            for spell in unique_spells[:5]:
                print(
                    f"  - {spell['name']} "
                    f"(ID: {spell['external_id']}, slug: {spell['slug']})"
                )
            print()

        return unique_spells

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
