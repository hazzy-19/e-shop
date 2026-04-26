import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from app.core.config import settings
from app.bot import handlers, states

logger = logging.getLogger(__name__)

bot_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

# ── Add product conversation ──────────────────────────────────────
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("add_product", handlers.start_add_product),
        # Triggered by the menu button / number shortcut
        MessageHandler(
            filters.Regex(r"^(1|📦 Add Product)$") & filters.TEXT,
            handlers.trigger_add_product,
        ),
    ],
    states={
        states.NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_name)],
        states.DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_desc)],
        states.PRICE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_price)],
        states.STOCK:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_stock)],
        states.IMAGE: [
            MessageHandler(filters.PHOTO, handlers.product_image),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.product_image),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", handlers.cancel),
        MessageHandler(filters.Regex(r"^❌ Cancel$"), handlers.cancel),
    ],
    allow_reentry=True,
)
bot_app.add_handler(conv_handler)

# ── Basic commands ────────────────────────────────────────────────
bot_app.add_handler(CommandHandler("start", handlers.start))
bot_app.add_handler(CommandHandler("menu", handlers.menu))
bot_app.add_handler(CommandHandler("myid", handlers.myid))
bot_app.add_handler(CommandHandler("stats", handlers.stats))
bot_app.add_handler(CommandHandler("help", handlers.help_cmd))
bot_app.add_handler(CommandHandler("cancel", handlers.cancel))

# ── Inline button callbacks ───────────────────────────────────────
bot_app.add_handler(CallbackQueryHandler(handlers.handle_callback))

# ── ZIP document upload ───────────────────────────────────────────
bot_app.add_handler(MessageHandler(filters.Document.ZIP, handlers.handle_document))

# ── Numbered/button menu shortcuts (must come AFTER conversation) ─
bot_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            r"^(2|3|4|5|6|📊 Stats|🛒 Recent Orders|🔍 Manage Products|🔐 Get 2FA Code|❓ Help)$"
        ),
        handlers.handle_text_menu,
    )
)


# ── Order notification helper ─────────────────────────────────────
async def send_order_notification(order_id: int, total: float):
    if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_ID):
        return
    message = (
        "🚨 *New Order Received!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Order ID: *#{order_id}*\n"
        f"💰 Total: *KSh {total:,.2f}*\n\n"
        "Tap 🛒 Recent Orders to manage it."
    )
    try:
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 View Order", callback_data=f"order_{order_id}"),
        ]])
        await bot_app.bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_ID,
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning(f"Order notification failed: {e}")


# ── Lifecycle ─────────────────────────────────────────────────────
async def start_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("No TELEGRAM_BOT_TOKEN set — bot disabled.")
        return
    try:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot started and polling.")
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
