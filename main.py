import asyncio
import logging
import random
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from faker import Faker
from fake_useragent import UserAgent
import aiohttp

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8629463424:AAFSkNFDNgqpuK6wDjtS12T2oD6Bs2TSNjk"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fake = Faker('ru_RU')
ua = UserAgent()

# Хранилище (email + токен для mail.tm)
temp_sessions: dict[int, dict] = {}

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

    return f"+{code} {formatted}"

# ==================== MAIL.TM API (стабильный 2026) ====================
async def get_domains():
    headers = {"User-Agent": ua.random}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.mail.tm/domains", headers=headers) as resp:
            data = await resp.json()
            return [item["domain"] for item in data.get("hydra:member", [])]

async def create_temp_account():
    domains = await get_domains()
    domain = random.choice(domains)
    username = fake.user_name().lower().replace(" ", "") + str(random.randint(1000, 9999))
    email = f"{username}@{domain}"
    password = "TempPass123!"

    headers = {"User-Agent": ua.random, "Content-Type": "application/json"}

    # Создаём аккаунт
    async with aiohttp.ClientSession() as session:
        payload = {"address": email, "password": password}
        async with session.post("https://api.mail.tm/accounts", json=payload, headers=headers) as resp:
            if resp.status not in (201, 200):
                raise Exception("Не удалось создать почту")

    # Получаем токен
    async with aiohttp.ClientSession() as session:
        payload = {"address": email, "password": password}
        async with session.post("https://api.mail.tm/token", json=payload, headers=headers) as resp:
            data = await resp.json()
            token = data["token"]

    return email, token

async def get_inbox(token: str):
    headers = {"Authorization": f"Bearer {token}", "User-Agent": ua.random}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.mail.tm/messages", headers=headers) as resp:
            data = await resp.json()
            return data.get("hydra:member", [])

async def read_message(token: str, msg_id: str):
    headers = {"Authorization": f"Bearer {token}", "User-Agent": ua.random}
    url = f"https://api.mail.tm/messages/{msg_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.json()

# ==================== КЛАВИАТУРЫ ====================
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Генератор номеров", callback_data="category_phones")],
        [InlineKeyboardButton(text="🖥️ Генератор User-Agent", callback_data="category_ua")],
        [InlineKeyboardButton(text="🌐 Генератор Fake IP", callback_data="category_ip")],
        [InlineKeyboardButton(text="👤 Генератор фейковых личностей", callback_data="category_person")],
        [InlineKeyboardButton(text="📧 Одноразовая почта", callback_data="category_temp_mail")],
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

def get_temp_mail_menu(email: str = None):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if email:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"📧 {email}", callback_data="dummy")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Новый ящик", callback_data="new_temp_mail")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="📬 Проверить почту", callback_data="check_temp_mail")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="← Главное меню", callback_data="main")])
    return kb

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
        "🚀 **Многофункциональный рандомизатор 2026**\n\nВыбери раздел ниже:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def callback_handler(call: CallbackQuery):
    data = call.data
    chat_id = call.message.chat.id

    if data == "main":
        await call.message.edit_text("🚀 **Выбери раздел:**", reply_markup=get_main_menu(), parse_mode="Markdown")
        await call.answer()

    # ==================== ОДНОРАЗОВАЯ ПОЧТА (mail.tm) ====================
    elif data == "category_temp_mail":
        if chat_id not in temp_sessions:
            try:
                email, token = await create_temp_account()
                temp_sessions[chat_id] = {"email": email, "token": token}
            except:
                await call.answer("Сервис временно перегружен, попробуй через 10 сек", show_alert=True)
                return
        else:
            email = temp_sessions[chat_id]["email"]

        await call.message.edit_text(
            f"📧 **Одноразовая почта (mail.tm)**\n\nТекущий ящик:\n`{email}`\n\nПисьма приходят мгновенно!",
            reply_markup=get_temp_mail_menu(email),
            parse_mode="Markdown"
        )
        await call.answer()

    elif data == "new_temp_mail":
        try:
            email, token = await create_temp_account()
            temp_sessions[chat_id] = {"email": email, "token": token}
            await call.message.edit_text(
                f"📧 **Новый ящик создан!**\n\n`{email}`",
                reply_markup=get_temp_mail_menu(email),
                parse_mode="Markdown"
            )
            await call.answer("✅ Новый ящик готов!")
        except:
            await call.answer("Не удалось создать ящик, попробуй снова", show_alert=True)

    elif data == "check_temp_mail":
        if chat_id not in temp_sessions:
            await call.answer("Сначала создай ящик!", show_alert=True)
            return
        session = temp_sessions[chat_id]
        messages = await get_inbox(session["token"])

        if not messages:
            text = f"📭 **Ящик пуст**\n\n`{session['email']}`"
            kb = get_temp_mail_menu(session["email"])
        else:
            text = f"📬 **Входящие** ({len(messages)} шт)\n\n"
            kb_list = []
            for m in messages:
                subj = m.get("subject") or "Без темы"
                fr = m.get("from", {})
                from_addr = fr.get("address", "—") if isinstance(fr, dict) else "—"
                text += f"• {subj} от {from_addr}\n"
                kb_list.append([InlineKeyboardButton(
                    text=f"Открыть #{m['id'][:8]}",
                    callback_data=f"read_temp_{m['id']}"
                )])
            kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
            kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="check_temp_mail")])
            kb.inline_keyboard.append([InlineKeyboardButton(text="🔄 Новый ящик", callback_data="new_temp_mail")])
            kb.inline_keyboard.append([InlineKeyboardButton(text="← Главное меню", callback_data="main")])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif data.startswith("read_temp_"):
        if chat_id not in temp_sessions:
            await call.answer("Ящик устарел, создай новый", show_alert=True)
            return
        msg_id = data.split("_")[-1]
        session = temp_sessions[chat_id]
        letter = await read_message(session["token"], msg_id)

        body = letter.get("text") or letter.get("html") or letter.get("intro") or "Текст отсутствует"
        from_addr = letter.get("from", {}).get("address", "—")
        subject = letter.get("subject", "Без темы")
        date = letter.get("createdAt", "—")

        text = f"""📧 **Письмо**

**От:** {from_addr}
**Тема:** {subject}
**Дата:** {date}

━━━━━━━━━━━━━━━
{body}
━━━━━━━━━━━━━━━

`{session['email']}`"""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить ящик", callback_data="check_temp_mail")],
            [InlineKeyboardButton(text="🔄 Новый ящик", callback_data="new_temp_mail")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Письмо открыто")

    # ==================== СТАРЫЕ РАЗДЕЛЫ (без изменений) ====================
    elif data == "category_phones":
        await call.message.edit_text("📱 **Генератор телефонных номеров**\nВыбери страну:", reply_markup=get_phones_menu(), parse_mode="Markdown")
        await call.answer()

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
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    elif data == "category_ua":
        await call.message.edit_text("🖥️ **Генератор User-Agent**\nВыбери тип:", reply_markup=get_ua_menu(), parse_mode="Markdown")
        await call.answer()

    elif data.startswith("generate_ua_"):
        typ = data.replace("generate_ua_", "")
        if typ == "random": uastr, name = ua.random, "Случайный"
        elif typ == "chrome": uastr, name = ua.chrome, "Chrome"
        elif typ == "firefox": uastr, name = ua.firefox, "Firefox"
        elif typ == "safari": uastr, name = ua.safari, "Safari"
        elif typ == "mobile": uastr, name = ua.random, "Mobile"
        else: uastr, name = ua.random, "Случайный"

        text = f"🖥️ **Вот ваш User-Agent ({name})**\n\n```{uastr}```\n\n @fakegeneratorBOBOBOT"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё такой же", callback_data=data)],
            [InlineKeyboardButton(text="Другой тип", callback_data="category_ua")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    elif data == "category_ip":
        await call.message.edit_text("🌐 **Генератор Fake IP**\nВыбери версию:", reply_markup=get_ip_menu(), parse_mode="Markdown")
        await call.answer()

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
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    elif data == "category_person":
        await call.message.edit_text("👤 **Генератор фейковых личностей**\n(умная генерация на русском)", reply_markup=get_person_menu(), parse_mode="Markdown")
        await call.answer()

    elif data == "generate_person":
        person = generate_personality()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё одну личность", callback_data="generate_person")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])
        await bot.send_message(chat_id, person, parse_mode="Markdown", reply_markup=kb)
        await call.answer("✅ Готово!")

    else:
        await call.answer("Неизвестная команда", show_alert=True)

# ==================== ЗАПУСК ====================
async def main():
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
