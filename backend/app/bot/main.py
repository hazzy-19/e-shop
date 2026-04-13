import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
from app.core.config import settings
from app.bot import handlers, states

logger = logging.getLogger(__name__)

bot_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

# Basic commands
bot_app.add_handler(CommandHandler("start", handlers.start))
bot_app.add_handler(CommandHandler("myid", handlers.myid))
bot_app.add_handler(CommandHandler("stats", handlers.stats))
bot_app.add_handler(CommandHandler("mask_product", handlers.mask_product_cmd))

# Add product conversation — accepts text OR photo at the IMAGE step
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("add_product", handlers.start_add_product)],
    states={
        states.NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_name)],
        states.DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_desc)],
        states.PRICE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_price)],
        states.STOCK:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_stock)],
        states.IMAGE: [
            # Accept an uploaded photo
            MessageHandler(filters.PHOTO, handlers.product_image),
            # Or a text URL / 'skip'
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_image),
        ],
    },
    fallbacks=[CommandHandler("cancel", handlers.cancel)],
)
bot_app.add_handler(conv_handler)


async def send_order_notification(order_id: int, total: float):
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_ID:
        message = (
            f"🚨 *New Order!*\n"
            f"Order ID: #{order_id}\n"
            f"Total: ${total:.2f}"
        )
        try:
            await bot_app.bot.send_message(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Order notification failed: {e}")


async def start_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    try:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Telegram bot started and polling.")
    except Exception as e:
        logger.warning(f"Failed to start telegram bot: {e}")


async def stop_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    try:
        if bot_app.updater and bot_app.updater.running:
            await bot_app.updater.stop()
        if bot_app.running:
            await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Telegram bot stopped.")
    except Exception as e:
        logger.warning(f"Failed to stop telegram bot: {e}")
