"""Run the Telegram bot (US-06). It uses the same answers as the website.

Usage:  python manage.py run_telegram_bot
Needs TELEGRAM_BOT_TOKEN in .env (create a bot with @BotFather on Telegram).
"""
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from chat.models import ChatLog
from chat.services.messages import ERROR, WELCOME
from chat.services.rag import answer_question, save_rating

logger = logging.getLogger(__name__)


def session_for(chat_id: int) -> str:
    return f"tg-{chat_id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{WELCOME['km']}\n\n{WELCOME['en']}")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        result = await sync_to_async(answer_question)(
            update.message.text,
            channel=ChatLog.Channel.TELEGRAM,
            session_id=session_for(chat_id),
            contact=f"telegram:{chat_id}",
        )
    except Exception:
        logger.exception("Telegram answer failed")
        await update.message.reply_text(f"{ERROR['km']}\n{ERROR['en']}")
        return

    text = result.answer
    if result.sources:
        text += "\n\n📄 " + ", ".join(s["title"] for s in result.sources)

    keyboard = None
    if not result.escalated:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("👍", callback_data=f"rate:{result.log_id}:1"),
            InlineKeyboardButton("👎", callback_data=f"rate:{result.log_id}:-1"),
        ]])
    await update.message.reply_text(text, reply_markup=keyboard)


async def on_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        _, log_id, rating = query.data.split(":")
        saved = await sync_to_async(save_rating)(int(log_id), int(rating), session_for(query.message.chat.id))
    except (ValueError, AttributeError):
        saved = False
    await query.answer("Thanks! / អរគុណ!" if saved else "")
    await query.edit_message_reply_markup(reply_markup=None)


class Command(BaseCommand):
    help = "Start the Telegram bot (long polling)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is empty. Add it to your .env file.")
        app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler(["start", "help"], start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
        app.add_handler(CallbackQueryHandler(on_rate, pattern=r"^rate:"))
        self.stdout.write(self.style.SUCCESS("Telegram bot is running. Press Ctrl+C to stop."))
        app.run_polling(allowed_updates=Update.ALL_TYPES)
