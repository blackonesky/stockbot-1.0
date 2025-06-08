import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
import re
from datetime import datetime
import asyncio

TOKEN = '7993735550:AAHJTnOml8-xyn2rQdqmjxquxngCONn5U_U'

SEEDS = {
    "Apple", "Bamboo", "Blueberry", "Carrot", "Corn",
    "Strawberry", "Tomato", "Watermelon", "Orange Tulip", "Daffodil", "Pumpkin",
    "Coconut", "Cactus", "Dragon Fruit", "Mango", "Grape", "Mushroom", "Pepper", "Cacao",
    "Beanstalk", "Raspberry", "Pear", "Foxglove", "Lilac", "Peach", "Pineapple",
    "Pink Lily", "Purple Dahlia", "Hive Fruit", "Sunflower", "Rose"
}
EGGS = {
    "Common Egg", "Uncommon Egg", "Rare Egg", "Legendary Egg", "Mythical Egg",
    "Prismatic Egg", "Divine Egg", "Bug Egg"
}
TOOLS = {
    "Favorite Tool", "Godly Sprinkler", "Harvest Tool", "Recall Wrench", "Trowel", "Watering Can",
    "Basic Sprinkler", "Advanced Sprinkler", "Master Sprinkler", "Lightning Rod", "Chocolate Sprinkler"
}
EVENT_ITEMS = {
    "Honey Comb", "Flower Seed Pack", "Lavender", "Honey Torch", "Nectarshade", "Star Caller", "Twilight Crate"
}
BEE_ITEMS = {
    "Bee Chair", "Bee Crate", "Honey Walkway", "Bee Lamp", "Bee Table", "Bee Bed"
}

RARITY = {
    # Семена и растения
    "Carrot": "Common", "Strawberry": "Common", "Blueberry": "Uncommon",
    "Orange Tulip": "Uncommon", "Tomato": "Rare", "Corn": "Rare",
    "Daffodil": "Rare", "Watermelon": "Legendary", "Pumpkin": "Legendary",
    "Apple": "Legendary", "Bamboo": "Legendary", "Coconut": "Mythical",
    "Cactus": "Mythical", "Dragon Fruit": "Mythical", "Mango": "Mythical",
    "Grape": "Divine", "Mushroom": "Divine", "Pepper": "Divine",
    "Cacao": "Divine", "Beanstalk": "Prismatic", "Raspberry": "Rare",
    "Pear": "Rare", "Foxglove": "Rare", "Lilac": "Legendary",
    "Nectarine": "Mythical", "Peach": "Mythical", "Pineapple": "Mythical",
    "Pink Lily": "Mythical", "Purple Dahlia": "Mythical", "Hive Fruit": "Divine",
    "Sunflower": "Divine", "Rose": "Uncommon",

    # Яйца
    "Common Egg": "Common", "Uncommon Egg": "Uncommon", "Rare Egg": "Rare",
    "Legendary Egg": "Legendary", "Mythical Egg": "Mythical",
    "Prismatic Egg": "Prismatic", "Divine Egg": "Divine", "Bug Egg": "Uncommon",

    # Инструменты
    "Trowel": "Uncommon", "Watering Can": "Common",
    "Basic Sprinkler": "Rare", "Advanced Sprinkler": "Legendary",
    "Godly Sprinkler": "Mythical", "Master Sprinkler": "Divine",
    "Lightning Rod": "Mythical", "Chocolate Sprinkler": "Mythical",
    "Favorite Tool": "Legendary", "Harvest Tool": "Legendary",
    "Recall Wrench": "Rare",

    # Косметика и декор
    "Sign Crate": "Rare",
    "Common Gnome Crate": "Rare",
    "Red Tractor": "Legendary",
    "Log": "Common",
    "Viney Beam": "Uncommon",
    "Medium Circle Tile": "Common",
    "Small Stone Lantern": "Uncommon",
    "Mini TV": "Uncommon",
    "Medium Path Tile": "Common",

    # Дополнительные косметические предметы:
    "Compost Bin": "Common",
    "Flat Canopy": "Rare",
    "Hay Bale": "Uncommon",
    "Lamp Post": "Rare",
    "Large Wood Flooring": "Uncommon",
    "Small Stone Pad": "Uncommon",
    "Wood Pile": "Common"
}
RARITY_EMOJI = {
    "Common": "🔘", "Uncommon": "🟢", "Rare": "🔵", "Legendary": "🟡",
    "Mythical": "🟣", "Divine": "🔴", "Prismatic": "🌈"
}
RARITY_ORDER = {
    "Common": 1, "Uncommon": 2, "Rare": 3, "Legendary": 4,
    "Mythical": 5, "Divine": 6, "Prismatic": 7, "": 8
}
PRICES = {
    "Sign Crate": "55,000,000 ₵", "Common Gnome Crate": "56,000,000 ₵",
    "Red Tractor": "556,000,000 ₵", "Log": "1,000,000 ₵", "Viney Beam": "1,000,000 ₵",
    "Medium Circle Tile": "250,000 ₵", "Small Stone Lantern": "1,000,000 ₵",
    "Mini TV": "1,000,000 ₵", "Medium Path Tile": "550,000 ₵",
    "Compost Bin": "1,000,000 ₵", "Flat Canopy": "12,000,000 ₵",
    "Hay Bale": "750,000 ₵", "Lamp Post": "12,000,000 ₵",
    "Large Wood Flooring": "1,000,000 ₵", "Small Stone Pad": "1,000,000 ₵", "Wood Pile": "1,000,000 ₵"
}

# ====== Оповещения о погоде ======
SUBSCRIBED_USERS = set()
LAST_WEATHER = None

def pluralize_ru_units(n):
    return "шт."

def parse_amount(amount_str):
    match = re.match(r"(\d+)", amount_str)
    return int(match.group(1)) if match else 0

def format_amount(amount_str):
    n = parse_amount(amount_str)
    if n == 0:
        return amount_str
    return f"{n} {pluralize_ru_units(n)}"

async def fetch_stock():
    url = 'https://growagarden.gg/stocks'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def fetch_weather():
    url = 'https://growagarden.gg/weather'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def parse_stock(html):
    soup = BeautifulSoup(html, 'html.parser')
    categories = {
        "seeds": [],
        "eggs": [],
    }
    added = set()
    for article in soup.find_all('article'):
        name_tag = article.find('h3', class_='text-sm font-medium')
        name = name_tag.text.strip() if name_tag else None
        if not name:
            continue
        amount_tag = article.find('data')
        amount = amount_tag.text.strip() if amount_tag else None
        if not amount or amount == "нет данных":
            continue
        price = PRICES.get(name, "—")
        key = f"{name}_{amount}"
        if key in added:
            continue
        added.add(key)
        rarity = RARITY.get(name, "")
        rarity_emoji = RARITY_EMOJI.get(rarity, "")
        rarity_order = RARITY_ORDER.get(rarity, 8)
        amount_formatted = format_amount(amount)
        line = f"• {rarity_emoji} {name} — {amount_formatted} ({price}) ({rarity})" if rarity else f"• {name} — {amount_formatted} ({price})"
        if name in SEEDS:
            categories["seeds"].append((rarity_order, name, line))
        elif name in EGGS:
            categories["eggs"].append((0, name, line))
    categories["seeds"].sort(key=lambda x: (x[0], x[1]))
    categories["eggs"].sort(key=lambda x: x[1])
    blocks = []
    if categories["seeds"]:
        blocks.append("🌱 <b>Семена:</b>")
        blocks += [item[2] for item in categories["seeds"]]
    if categories["eggs"]:
        blocks.append("\n🥚 <b>Яйца:</b>")
        blocks += [item[2] for item in categories["eggs"]]
    if not blocks:
        blocks.append("В магазине пусто или структура сайта изменилась.")
    return blocks

async def parse_cosmetics(html):
    soup = BeautifulSoup(html, 'html.parser')
    cosmetics = []
    added = set()
    for article in soup.find_all('article'):
        name_tag = article.find('h3', class_='text-sm font-medium')
        name = name_tag.text.strip() if name_tag else None
        if not name:
            continue
        # Исключаем растения, яйца, инструменты, ивентовые и пчелиные предметы!
        if name in SEEDS or name in EGGS or name in TOOLS or name in EVENT_ITEMS or name in BEE_ITEMS:
            continue
        amount_tag = article.find('data')
        amount = amount_tag.text.strip() if amount_tag else None
        if not amount or amount == "нет данных":
            continue
        price = PRICES.get(name, "—")
        key = f"{name}_{amount}"
        if key in added:
            continue
        added.add(key)
        rarity = RARITY.get(name, "")
        rarity_emoji = RARITY_EMOJI.get(rarity, "")
        amount_formatted = format_amount(amount)
        line = f"• {rarity_emoji} {name} — {amount_formatted} ({price}) ({rarity})" if rarity else f"• {name} — {amount_formatted} ({price})"
        cosmetics.append((rarity, name, line))
    cosmetics.sort(key=lambda x: (RARITY_ORDER.get(x[0], 8), x[1]))
    blocks = ["💄 <b>Косметика в стоках:</b>"]
    if cosmetics:
        blocks += [item[2] for item in cosmetics]
    else:
        blocks.append("В магазине пусто или структура сайта изменилась.")
    return blocks

async def parse_event_items(html):
    soup = BeautifulSoup(html, 'html.parser')
    events = []
    added = set()
    for article in soup.find_all('article'):
        name_tag = article.find('h3', class_='text-sm font-medium')
        name = name_tag.text.strip() if name_tag else None
        if not name or name not in EVENT_ITEMS:
            continue
        amount_tag = article.find('data')
        amount = amount_tag.text.strip() if amount_tag else None
        if not amount or amount == "нет данных":
            continue
        price = PRICES.get(name, "—")
        key = f"{name}_{amount}"
        if key in added:
            continue
        added.add(key)
        rarity = RARITY.get(name, "")
        rarity_emoji = RARITY_EMOJI.get(rarity, "")
        amount_formatted = format_amount(amount)
        line = f"• {rarity_emoji} {name} — {amount_formatted} ({price}) ({rarity})" if rarity else f"• {name} — {amount_formatted} ({price})"
        events.append((rarity, name, line))
    events.sort(key=lambda x: (RARITY_ORDER.get(x[0], 8), x[1]))
    blocks = ["🎉 <b>Ивентные предметы в стоках:</b>"]
    if events:
        blocks += [item[2] for item in events]
    else:
        blocks.append("Нет ивентовых предметов или структура сайта изменилась.")
    return blocks

async def parse_weather(html):
    soup = BeautifulSoup(html, 'html.parser')
    info = []
    weathers = {
        "Дождь": "🌧",
        "Снег": "❄️",
        "Гроза": "⚡️",
        "Метеоритный дождь": "☄️",
    }
    text = soup.get_text().lower()
    for name, emoji in weathers.items():
        key = name.lower()
        if key in text:
            if "нет" in text.split(key)[1][:10]:
                info.append(f"{emoji} {name}: <b>Нет</b>")
            else:
                info.append(f"{emoji} {name}: <b>Да</b>")
        else:
            info.append(f"{emoji} {name}: <b>Нет данных</b>")
    if not info:
        info.append("Погода не найдена или структура сайта изменилась.")
    return info

def make_time_block():
    dt = datetime.now()
    updated = dt.strftime('%Y-%m-%d %H:%M:%S')
    return f"\n⏰ Обновлено: <b>{updated}</b>"

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Стоки", callback_data="show_stock")],
        [InlineKeyboardButton("💄 Косметика", callback_data="show_cosmetics")],
        [InlineKeyboardButton("🎉 Ивент", callback_data="show_event")],
        [InlineKeyboardButton("🌦 Погода", callback_data="show_weather")]
    ])

def stock_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh_stock")]
    ])

def cosmetics_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh_cosmetics")]
    ])

def event_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh_event")]
    ])

def weather_keyboard(user_id=None):
    btn = InlineKeyboardButton(
        "🔔 Выключить уведомления" if user_id in SUBSCRIBED_USERS else "🔔 Включить уведомления",
        callback_data="weather_unsubscribe" if user_id in SUBSCRIBED_USERS else "weather_subscribe"
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh_weather")],
        [btn]
    ])

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"👋 <b>Привет, {update.effective_user.first_name or 'друг'}!</b>\n\nВыбери раздел:"
    if update.message:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )

async def show_stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    stock_items = await parse_stock(html)
    message = "\n".join(stock_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=stock_keyboard()
    )

async def refresh_stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    stock_items = await parse_stock(html)
    message = "\n".join(stock_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=stock_keyboard()
    )
    await update.callback_query.answer("Обновлено!")

async def show_cosmetics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    cosmetics_items = await parse_cosmetics(html)
    message = "\n".join(cosmetics_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=cosmetics_keyboard()
    )

async def refresh_cosmetics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    cosmetics_items = await parse_cosmetics(html)
    message = "\n".join(cosmetics_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=cosmetics_keyboard()
    )
    await update.callback_query.answer("Обновлено!")

async def show_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    event_items = await parse_event_items(html)
    message = "\n".join(event_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=event_keyboard()
    )

async def refresh_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_stock()
    event_items = await parse_event_items(html)
    message = "\n".join(event_items) + make_time_block()
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=event_keyboard()
    )
    await update.callback_query.answer("Обновлено!")

async def show_weather_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_weather()
    weather = await parse_weather(html)
    message = "🌤 <b>Текущая погода:</b>\n\n" + "\n".join(weather) + make_time_block()
    user_id = update.effective_user.id
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=weather_keyboard(user_id)
    )

async def refresh_weather_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html = await fetch_weather()
    weather = await parse_weather(html)
    message = "🌤 <b>Текущая погода:</b>\n\n" + "\n".join(weather) + make_time_block()
    user_id = update.effective_user.id
    await update.callback_query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=weather_keyboard(user_id)
    )
    await update.callback_query.answer("Обновлено!")

async def weather_subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SUBSCRIBED_USERS.add(update.effective_user.id)
    await update.callback_query.answer("Уведомления включены!")
    await show_weather_callback(update, context)

async def weather_unsubscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SUBSCRIBED_USERS.discard(update.effective_user.id)
    await update.callback_query.answer("Уведомления выключены.")
    await show_weather_callback(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

# ===== Фоновая задача для оповещений о погоде =====
async def notify_weather_task(app):
    global LAST_WEATHER
    while True:
        try:
            html = await fetch_weather()
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text().lower()
            specials = []
            if "дождь" in text and "нет" not in text.split("дождь")[1][:10]:
                specials.append("🌧 Дождь")
            if "снег" in text and "нет" not in text.split("снег")[1][:10]:
                specials.append("❄️ Снег")
            if "гроза" in text and "нет" not in text.split("гроза")[1][:10]:
                specials.append("⚡️ Гроза")
            if "метеоритный дождь" in text and "нет" not in text.split("метеоритный дождь")[1][:10]:
                specials.append("☄️ Метеоритный дождь")
            specials_str = ", ".join(specials)
            if specials_str and specials_str != LAST_WEATHER:
                LAST_WEATHER = specials_str
                for uid in SUBSCRIBED_USERS.copy():
                    try:
                        await app.bot.send_message(uid, f"⚡️ Внимание! В игре особенная погода: {specials_str}")
                    except Exception:
                        SUBSCRIBED_USERS.discard(uid)
            if not specials_str:
                LAST_WEATHER = ""
        except Exception as e:
            print(f"[notify_weather_task] Ошибка: {e}")
        await asyncio.sleep(10)  # Каждые 2 минуты

# ==== Регистрация всех хендлеров ====
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(show_stock_callback, pattern="^show_stock$"))
    app.add_handler(CallbackQueryHandler(refresh_stock_callback, pattern="^refresh_stock$"))
    app.add_handler(CallbackQueryHandler(show_cosmetics_callback, pattern="^show_cosmetics$"))
    app.add_handler(CallbackQueryHandler(refresh_cosmetics_callback, pattern="^refresh_cosmetics$"))
    app.add_handler(CallbackQueryHandler(show_event_callback, pattern="^show_event$"))
    app.add_handler(CallbackQueryHandler(refresh_event_callback, pattern="^refresh_event$"))
    app.add_handler(CallbackQueryHandler(show_weather_callback, pattern="^show_weather$"))
    app.add_handler(CallbackQueryHandler(refresh_weather_callback, pattern="^refresh_weather$"))
    app.add_handler(CallbackQueryHandler(weather_subscribe_callback, pattern="^weather_subscribe$"))
    app.add_handler(CallbackQueryHandler(weather_unsubscribe_callback, pattern="^weather_unsubscribe$"))

    # Фоновая задача для погоды
    async def on_startup(app_):
        asyncio.create_task(notify_weather_task(app_))

    app.post_init = on_startup

    print("Бот запущен! Ожидает команд...")
    app.run_polling()






















