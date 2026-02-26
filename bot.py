import asyncio
import logging
import os
import random


from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


logging.basicConfig(level=logging.INFO)


API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN")


WEBAPP_URL = "https://pavelcode.ru"
CRIT_BOT_URL = "https://t.me/dndcriticalsfbot"


D20_PHRASES = [
    "Кости брошены — судьба улыбается или скалится.",
    "Таверна стихла: все ждут, что покажет грань.",
    "Мастер прищурился. Игроки затаили дыхание.",
    "d20 по столу — и мир на секунду замер.",
    "Покровитель шепчет: «Рискни».",
    "Пахнет критом… или неприятностями.",
    "Заклинание почти готово. Осталось только удача.",
    "Ловкость рук, и никакого колдовства. Ну, почти.",
    "Сделай это броском, а не словами.",
    "На кону репутация, золото и немного достоинства.",
    "Судьба любит смелых. Иногда.",
    "Кубик знает правду. Даже если она неудобная.",
    "Где-то плачет гоблин. Или радуется.",
    "Эль в кружках замер — сейчас будет исход сцены.",
    "Критическая надежда активирована.",
    "Проверка на героизм. Без права на реткон.",
    "Если выпадет 1 — делаем вид, что это часть плана.",
    "Если выпадет 20 — делаем вид, что так и задумано.",
    "Шанс один на двадцать. Но он твой.",
    "Ветер приключений подхватил кубик.",
    "Тьма в подземелье гуще, когда бросок плохой.",
    "Стражник уже почти верит…",
    "Дракон моргнул. Это твой момент.",
    "Лут ждёт. Или ловушка.",
    "Сейчас решится: легенда или байка в таверне.",
    "Клятва дана. Бросок сделан.",
    "Пусть кубик будет милостив.",
    "Кидай смело — последствия потом.",
    "Одна грань — и вся сцена меняется.",
    "Рандом — лучший соавтор кампании.",
]


INFO_TEXT = """✨ <b>Ключевые возможности</b>


🎭 <b>Для Мастера игры (GM):</b>
• <b>Управление кампаниями</b> — создание и редактирование игровых кампаний
• <b>Библиотека врагов</b> — добавление монстров с полной статистикой (HP, КД, атаки, инициатива)
• <b>Трекер боя</b> — автоматический подсчет инициативы и порядка хода
• <b>Управление HP</b> — быстрое изменение здоровья участников (+/- кнопки)
• <b>Мультиплеер</b> — возможность приглашать игроков в свой кампейн в качестве зрителей


👥 <b>Для игроков (Наблюдатель):</b>
• <b>Просмотр порядка хода</b> — видят текущий раунд и очередность действий
• <b>Автообновление</b> — боевой экран обновляется автоматически
• <b>Интрига сохранена</b> — точные HP, КД и атаки врагов скрыты"""


BTN_ROLL = "🎲 Бросить d20"
BTN_INFO = "ℹ️ Информация"
BTN_CRIT = "💥 Крит"


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ROLL), KeyboardButton(text=BTN_INFO)],
            [KeyboardButton(text=BTN_CRIT)],
        ],
        resize_keyboard=True,
        is_persistent=False,
        one_time_keyboard=False,
        input_field_placeholder="Выбери действие…",
    )


def roll_d20_text() -> str:
    roll = random.randint(1, 20)
    phrase = random.choice(D20_PHRASES)
    if roll == 20:
        header = "💥 Натуральная 20! Крит!"
    elif roll == 1:
        header = "💀 Натуральная 1… фиаско."
    else:
        header = "🎲 Бросок d20"
    return f"{header}\n{phrase}\n\nРезультат: {roll}"


async def main():
    if not API_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в переменных окружения")

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    await bot.set_my_commands([
        BotCommand(command="roll", description="Бросить d20 🎲"),
        BotCommand(command="info", description="Информация"),
    ])

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        # Проверяем наличие deep link параметра
        start_param = message.text.split(maxsplit=1)[1] if len(
            message.text.split()) > 1 else None

        if start_param and start_param.startswith("invite_"):
            # Извлекаем токен из invite_{token}
            invite_token = start_param[7:]  # убираем "invite_"

            # Создаём inline-кнопку для перехода к join.html
            join_url = f"{WEBAPP_URL}/static/join.html?token={invite_token}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✅ Присоединиться к кампании", web_app=WebAppInfo(url=join_url))]
            ])

            await message.answer(
                "🎲 Тебя пригласили в D&D кампанию!\n\n"
                "Нажми кнопку ниже, чтобы присоединиться как наблюдатель.",
                reply_markup=kb
            )
        else:
            # Обычный старт
            await message.answer(
                "Кидай d20 — выбери действие на клавиатуре снизу.",
                reply_markup=main_kb(),
            )

    @dp.message(Command("roll"))
    async def cmd_roll(message: Message):
        await message.answer(roll_d20_text(), reply_markup=main_kb())

    @dp.message(Command("info"))
    async def cmd_info(message: Message):
        await message.answer(INFO_TEXT, parse_mode='HTML', reply_markup=main_kb())

    @dp.message(F.text == BTN_ROLL)
    async def on_btn_roll(message: Message):
        await message.answer(roll_d20_text(), reply_markup=main_kb())

    @dp.message(F.text == BTN_INFO)
    async def on_btn_info(message: Message):
        await message.answer(INFO_TEXT, parse_mode='HTML', reply_markup=main_kb())

    @dp.message(F.text == BTN_CRIT)
    async def on_btn_crit(message: Message):
        await message.answer(f"Открыть крит-бота: {CRIT_BOT_URL}", reply_markup=main_kb())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
