import os
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")  # Flask-сервер
BOT_API_KEY = os.getenv("BOT_API_KEY")  # тот же ключ, что в backend/.env

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # то, что после /start

    # Если аргументы пустые, выводим инструкцию
    if not args:
        await update.message.reply_text(
            f"Привет, {user.first_name if user else 'пользователь'}!\n"
            "Для авторизации на сайте напишите /start <код>, который вам был отправлен."
        )
        return

    payload = args[0]
    if payload.startswith("login_"):
        code = payload.removeprefix("login_")

        if not BOT_API_KEY:
            await update.message.reply_text("Ошибка: BOT_API_KEY не настроен на стороне бота.")
            return

        # Подтверждаем на backend (Flask-сервер)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BACKEND_URL}/auth/telegram/confirm",  # Эндпоинт для подтверждения
                    json={
                        "code": code,
                        "telegram_id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    headers={"X-BOT-KEY": BOT_API_KEY},  # Защита с помощью ключа
                    timeout=aiohttp.ClientTimeout(total=10),  # Тайм-аут для запроса
                ) as resp:
                    data = await resp.json(content_type=None)  # Получаем ответ от Flask
                    if resp.status == 200 and 'token' in data:
                        await update.message.reply_text("✅ Готово! Ваш вход подтвержден. Можете перейти на сайт.")
                    else:
                        await update.message.reply_text(f"❌ Не удалось подтвердить вход: {data.get('error', 'Неизвестная ошибка')}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка связи с сервером: {e}")
        return

    await update.message.reply_text("Неизвестный параметр /start. Используйте /start <код> для авторизации.")

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы написали: {update.message.text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Ошибка:", context.error)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))  # Команда /start
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))  # Эхо-сообщение
    app.add_error_handler(error_handler)  # Обработчик ошибок
    print("Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
