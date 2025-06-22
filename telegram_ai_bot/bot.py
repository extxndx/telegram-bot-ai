import logging
import asyncio
from telegram import Update, LabeledPrice, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from database import init_db, add_user, get_all_users, set_premium, is_user_premium, set_user_language, get_user_language
from clip_utils import compare_image_to_text

TELEGRAM_TOKEN = 'your_telegram_token_here'
PROVIDER_TOKEN = 'your_stripe_provider_token_here'
ADMIN_ID = 123456789  # замените на свой Telegram ID

logging.basicConfig(level=logging.INFO)

LANGUAGES = {
    'en': {
        'welcome': "👋 Hi! Send me a product description or photo and I’ll find it.",
        'premium_required': "🔒 This feature is only for premium users. Use /buy to activate.",
        'thanks': "🎉 Thank you for your purchase! Premium activated.",
        'users': "👤 Users:",
        'premium': "⭐️ Premium",
        'free': "Free",
        'choose_lang': "🌐 Choose your language",
    },
    'ru': {
        'welcome': "👋 Привет! Пришли описание или фото товара, и я найду его.",
        'premium_required': "🔒 Эта функция доступна только для премиум-пользователей. Напиши /buy.",
        'thanks': "🎉 Спасибо за покупку! Премиум активирован.",
        'users': "👤 Пользователи:",
        'premium': "⭐️ Премиум",
        'free': "Бесплатно",
        'choose_lang': "🌐 Выберите язык",
    },
    'uk': {
        'welcome': "👋 Привіт! Надішли опис або фото товару — я знайду його.",
        'premium_required': "🔒 Ця функція доступна лише для преміум-користувачів. Напиши /buy.",
        'thanks': "🎉 Дякуємо за покупку! Преміум активовано.",
        'users': "👤 Користувачі:",
        'premium': "⭐️ Преміум",
        'free': "Безкоштовно",
        'choose_lang': "🌐 Оберіть мову",
    }
}

def get_text(lang, key):
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, key)

user_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.message.chat_id, update.message.from_user.username)
    lang = await get_user_language(update.message.chat_id) or 'en'
    await update.message.reply_text(
        get_text(lang, 'welcome'),
        reply_markup=ReplyKeyboardMarkup(
            [["🇺🇦 Українська", "🇷🇺 Русский", "🇬🇧 English"]],
            resize_keyboard=True
        )
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_map = {"🇷🇺 Русский": "ru", "🇺🇦 Українська": "uk", "🇬🇧 English": "en"}
    lang = lang_map.get(update.message.text)
    if lang:
        await set_user_language(update.message.chat_id, lang)
        await update.message.reply_text(get_text(lang, "welcome"))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Access denied")
        return
    users = await get_all_users()
    text = get_text('en', 'users') + "\n"
    for uid, username, premium in users:
        status = get_text('en', 'premium') if premium else get_text('en', 'free')
        text += f"{username or uid} — {status}\n"
    await update.message.reply_text(text)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = [LabeledPrice("Премиум доступ", 499 * 100)]
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="Премиум подписка",
        description="Безлимитный доступ к распознаванию и поиску",
        payload="premium-purchase",
        provider_token=PROVIDER_TOKEN,
        currency="USD",
        prices=prices,
        start_parameter="buy-premium"
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_premium(update.message.chat_id)
    lang = await get_user_language(update.message.chat_id) or 'en'
    await update.message.reply_text(get_text(lang, "thanks"))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.message.chat_id, update.message.from_user.username)
    lang = await get_user_language(update.message.chat_id) or 'en'
    if not await is_user_premium(update.message.chat_id):
        await update.message.reply_text(get_text(lang, "premium_required"))
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"photo_{update.message.message_id}.jpg"
    await file.download_to_drive(file_path)
    texts = ["PlayStation 1", "Game Boy", "Sega Mega Drive", "iPod Classic"]
    best_match, confidence = compare_image_to_text(file_path, texts)
    await update.message.reply_text(f"Detected: {best_match} ({confidence:.2f})")

async def main():
    await init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🇷🇺|🇺🇦|🇬🇧"), set_language))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())