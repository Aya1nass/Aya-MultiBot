import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
print(f"Проверка файла: {os.path.exists('.env')}")
print(f"Токен из файла: {os.getenv('TELEGRAM_TOKEN')}")

import logging
import random
import string
import httpx
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логов
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
# Вставь свои данные сюда:
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
# --- МЕНЮ С КНОПКАМИ ---
def main_menu_keyboard():
    keyboard = [
        ["Joke 🎭", "Advice 💡"],
        ["Currency 💸", "Remind ⏳"],
        ["Dice 🎲", "Password 🔑"],
        ["Weather 🌤️", "Help ❓"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
# --- ФУНКЦИИ ПОМОЩНИКИ ---

async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"In {city.capitalize()}: {temp}°C, {desc}. 🌍"
            return f"Sorry, I couldn't find the city: {city}."
        except:
            return "Weather service error."

async def get_currency(amount, base, to):
    url = f"https://open.er-api.com/v6/latest/{base.upper()}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            rate = data['rates'][to.upper()]
            converted = round(float(amount) * rate, 2)
            return f"Done! {amount} {base.upper()} = {converted} {to.upper()}. 💸"
        except:
            return "Currency error. Example: convert 100 usd to kzt"

async def reminder_callback(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.chat_id, text=f"🔔 REMINDER: {context.job.data}")

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Greetings! I am Aya ❤️. Choose an option or type a command:",
        reply_markup=main_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    # 1. ШУТКИ И СОВЕТЫ
    if "Joke" in text:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://v2.jokeapi.dev/joke/Any?safe-mode&type=single")
            await update.message.reply_text(res.json().get("joke", "No jokes found."))

    elif "Advice" in text:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.adviceslip.com/advice")
            await update.message.reply_text(res.json().get("slip", {}).get("advice", "Be yourself."))
    elif "Dice" in text:
        number = random.randint(1, 6)
        await update.message.reply_text(f"You rolled a {number}! 🎲")

    elif "Password" in text:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for i in range(12))
        await update.message.reply_text(f"Your secure password: {password}", parse_mode='Markdown')


    # 2. ВАЛЮТА
    elif "Currency" in text:
        await update.message.reply_text("Type like this: convert 100 usd to kzt", parse_mode='Markdown')

    elif "convert" in text.lower():
        try:
            parts = text.split(" ")
            # Ожидаем: convert [1] [usd] to [kzt]
            msg = await get_currency(parts[1], parts[2], parts[4])
            await update.message.reply_text(msg)
        except:
            await update.message.reply_text("Error. Format: convert 50 eur to usd")

    # 3. НАПОМИНАНИЯ (любое время и текст)
    elif "Remind" in text:
        await update.message.reply_text("Type like this: remind me in 10 minutes to call mom", parse_mode='Markdown')

    elif "remind me in" in text.lower():
        try:
            parts = text.split(" ")
            minutes = int(parts[3])
            # Собираем всё, что после слова 'to'
            task = text.split("to ", 1)[1]
            context.job_queue.run_once(reminder_callback, minutes * 60, data=task, chat_id=chat_id)
            await update.message.reply_text(f"⏳ OK! I'll remind you to '{task}' in {minutes} minutes.")
        except:
            await update.message.reply_text("Error. Format: remind me in [X] minutes to [task]")

    # 4. ПОГОДА (любой город)
    elif "weather" in text.lower():
        if text == "Weather 🌤️":
            await update.message.reply_text("Type like this: weather Almaty or weather London", parse_mode='Markdown')
        else:
            try:
                city = text.split(" ", 1)[1]
                await update.message.reply_text(await get_weather(city))
            except:
                await update.message.reply_text("Please type: weather [city]")

    elif "Help" in text:
        await update.message.reply_text("I can help with jokes, advice, weather, currency and reminders! 🤍")

# --- ЗАПУСК ---
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Aya is online with dynamic functions!")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")