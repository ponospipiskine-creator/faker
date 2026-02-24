# bot.py — Многофункциональный рандомизатор 2026 (всё через кнопки!)
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from faker import Faker
from fake_useragent import UserAgent

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8629463424:AAFSkNFDNgqpuK6wDjtS12T2oD6Bs2TSNjk"  # ← ТВОЙ ТОКЕН

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fake = Faker('ru_RU')
ua = UserAgent()

# ==================== ДАННЫЕ ДЛЯ НОМЕРОВ ====================
COUNTRIES = {
    "RU": {"flag": "🇷🇺", "name": "Россия",       "data": ("7",  10, "XXX XXX-XX-XX", ["9"])},
    "UA": {"flag": "🇺🇦", "name": "Украина",      "data": ("380", 9,  "XX XXX XXXX",   ["6","7","9"])},
    "US": {"flag": "🇺🇸", "name": "США/Канада",   "data": ("1",  10, "XXX XXX XXXX",  [])},
    "GB": {"flag": "🇬🇧", "name": "Великобритания","data": ("44", 10, "7XXX XXX XXX",  ["7"])},
    "DE": {"flag": "🇩🇪", "name": "Германия",     "data": ("49", 10, "XXX XXXXXXXX",  [])},
    "FR": {"flag": "🇫🇷", "name": "Франция",      "data": ("33", 9,  "X XX XX XX XX", ["6","7"])},
    "IN": {"flag": "🇮🇳", "name": "Индия",        "data": ("91", 10, "XX XXXX XXXX",  ["6","7","8","9"])},
    "BR": {"flag": "🇧🇷", "name": "Бразилия",     "data": ("55", 10, "XX 9XXXX XXXX",["9"])},
    "JP": {"flag": "🇯🇵", "name": "Япония",       "data": ("81", 10, "XX XXXX XXXX",  [])},
    "AU": {"flag": "🇦🇺", "name": "Австралия",    "data": ("61", 9,  "X XXXX XXXX",   ["4"])},
    "TR": {"flag": "🇹🇷", "name": "Турция",       "data": ("90", 10, "XXX XXX XX XX",["5"])},
    "KZ": {"flag": "🇰🇿", "name": "Казахстан",    "data": ("7",  10, "XXX XXX XX XX",["7"])},
    "PL": {"flag": "🇵🇱", "name": "Польша",       "data": ("48", 9,  "XXX XXX XXX",   [])},
    "IT": {"flag": "🇮🇹", "name": "Италия",       "data": ("39", 10, "XXX XXX XXXX",  ["3"])},
    "ES": {"flag": "🇪🇸", "name": "Испания",      "data": ("34", 9,  "XXX XX XX XX",  ["6","7"])},
}

def generate_phone(country_data):
    code, local_len, fmt, mobile_prefixes = country_data
    if mobile_prefixes:
        prefix = random.choice(mobile_prefixes)
        remaining = local_len - len(prefix)
        local = prefix + ''.join(str(random.randint(0, 9)) for _ in range(remaining))
    else:
        local = ''.join(str(random.randint(0, 9)) for _ in range(local_len))

    formatted = fmt
    for digit in local:
        formatted = formatted.replace("X", digit, 1)

    return f"+{code} {formatted}" if code else formatted

# ==================== КЛАВИАТУРЫ ====================
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Генератор номеров", callback_data="category_phones")],
        [InlineKeyboardButton(text="🖥️ Генератор User-Agent", callback_data="category_ua")],
        [InlineKeyboardButton(text="🌐 Генератор Fake IP", callback_data="category_ip")],
        [InlineKeyboardButton(text="👤 Генератор фейковых личностей", callback_data="category_person")],
    ])

def get_phones_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for code, info in COUNTRIES.items():
        row.append(InlineKeyboardButton(text=f"{info['flag']} {info['name']}", callback_data=f"generate_phone_{code}"))
        if len(row) == 2:
            kb.inline_keyboard.append(row)
            row = []
    if row:
        kb.inline_keyboard.append(row)
    kb.inline_keyboard.append([InlineKeyboardButton(text="🎲 Случайная страна", callback_data="generate_phone_random")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="← Главное меню", callback_data="main")])
    return kb

def get_ua_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Случайный", callback_data="generate_ua_random")],
        [InlineKeyboardButton(text="🌐 Chrome", callback_data="generate_ua_chrome")],
        [InlineKeyboardButton(text="🦊 Firefox", callback_data="generate_ua_firefox")],
        [InlineKeyboardButton(text="🍏 Safari", callback_data="generate_ua_safari")],
        [InlineKeyboardButton(text="📱 Mobile Random", callback_data="generate_ua_mobile")],
        [InlineKeyboardButton(text="← Назад", callback_data="main")],
    ])

def get_ip_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="IPv4", callback_data="generate_ip_4")],
        [InlineKeyboardButton(text="IPv6", callback_data="generate_ip_6")],
        [InlineKeyboardButton(text="Оба", callback_data="generate_ip_both")],
        [InlineKeyboardButton(text="← Назад", callback_data="main")],
    ])

def get_person_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Сгенерировать умную личность", callback_data="generate_person")],
        [InlineKeyboardButton(text="← Назад", callback_data="main")],
    ])

# ==================== ГЕНЕРАТОРЫ ====================
def generate_personality():
    return f"""👤 **Фейковая личность** 

**Имя:** {fake.name()}
**Возраст:** {fake.random_int(18, 65)} лет
**Дата рождения:** {fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%d.%m.%Y')}
**Город:** {fake.city()}
**Адрес:** {fake.address()}
**Email:** {fake.email()}
**Телефон:** {fake.phone_number()}
**Работа:** {fake.job()}
**Компания:** {fake.company()}
**Username:** @{fake.user_name()}
**Паспорт (фейк):** {fake.passport_number()}
** @fakegeneratorBOBOBOT**"""

# ==================== ОБРАБОТЧИКИ ====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🚀 **Многофункциональный рандомизатор**\n\n"
        "Выбери раздел ниже — всё через кнопки, результат в отдельном сообщении (легко копировать):",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def callback_handler(call: CallbackQuery):
    data = call.data

    if data == "main":
        await call.message.edit_text(
            "🚀 **Выбери раздел:**",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    elif data == "category_phones":
        await call.message.edit_text(
            "📱 **Генератор телефонных номеров**\nВыбери страну:",
            reply_markup=get_phones_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    elif data == "category_ua":
        await call.message.edit_text(
            "🖥️ **Генератор User-Agent**\nВыбери тип:",
            reply_markup=get_ua_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    elif data == "category_ip":
        await call.message.edit_text(
            "🌐 **Генератор Fake IP**\nВыбери версию:",
            reply_markup=get_ip_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    elif data == "category_person":
        await call.message.edit_text(
            "👤 **Генератор фейковых личностей**\n(умная генерация на русском)",
            reply_markup=get_person_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    # === ГЕНЕРАЦИЯ НОМЕРОВ ===
    elif data.startswith("generate_phone_"):
        code = data.replace("generate_phone_", "")
        if code == "random":
            code = random.choice(list(COUNTRIES.keys()))

        info = COUNTRIES[code]
        phone = generate_phone(info["data"])

        text = f"📱 **Вот ваш сгенерированный номер**\n\nСтрана: {info['flag']} {info['name']}\n\n`{phone}`\n\n** @fakegeneratorBOBOBOT**"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🔄 Ещё для {info['name']}", callback_data=f"generate_phone_{code}")],
            [InlineKeyboardButton(text="🌍 Другая страна", callback_data="category_phones")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    # === ГЕНЕРАЦИЯ USER-AGENT ===
    elif data.startswith("generate_ua_"):
        typ = data.replace("generate_ua_", "")
        if typ == "random":
            uastr = ua.random
            name = "Случайный"
        elif typ == "chrome":
            uastr = ua.chrome
            name = "Chrome"
        elif typ == "firefox":
            uastr = ua.firefox
            name = "Firefox"
        elif typ == "safari":
            uastr = ua.safari
            name = "Safari"
        elif typ == "mobile":
            uastr = ua.random
            name = "Mobile"
        else:
            uastr = ua.random
            name = "Случайный"

        text = f"🖥️ **Вот ваш User-Agent ({name})**\n\n```{uastr}```\n\n @fakegeneratorBOBOBOT"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё такой же", callback_data=data)],
            [InlineKeyboardButton(text="Другой тип", callback_data="category_ua")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    # === ГЕНЕРАЦИЯ IP ===
    elif data.startswith("generate_ip_"):
        typ = data.replace("generate_ip_", "")
        if typ == "4":
            ip = fake.ipv4()
            name = "IPv4"
        elif typ == "6":
            ip = fake.ipv6()
            name = "IPv6"
        else:
            ip = f"IPv4: {fake.ipv4()}\nIPv6: {fake.ipv6()}"
            name = "Оба"

        text = f"🌐 **Вот ваш Fake IP ({name})**\n\n`{ip}`\n\n** @fakegeneratorBOBOBOT**"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё такой же", callback_data=data)],
            [InlineKeyboardButton(text="Другая версия", callback_data="category_ip")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    # === ГЕНЕРАЦИЯ ЛИЧНОСТИ ===
    elif data == "generate_person":
        person = generate_personality()

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё одну личность", callback_data="generate_person")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await bot.send_message(call.message.chat.id, person, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    else:
        await call.answer("Неизвестная команда", show_alert=True)

# ==================== ЗАПУСК (ИСПРАВЛЕНО) ====================
async def main():
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())