import os
import uuid
import aiofiles
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.future import select

from app.database import async_session
from app.products import models as product_models
from app.orders import models as order_models
from app.bot.states import NAME, DESCRIPTION, PRICE, STOCK, IMAGE
from app.core.config import settings

# Directory to save uploaded product images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ─── Admin guard ─────────────────────────────────────────
async def check_admin(update: Update) -> bool:
    user = update.effective_user
    admin_id = settings.TELEGRAM_ADMIN_ID

    if admin_id == 0:
        await update.message.reply_text(
            "⚠️ TELEGRAM_ADMIN_ID is not configured in .env\n"
            "Send /myid to get your user ID, then add it to .env"
        )
        return False

    if user.id != admin_id:
        await update.message.reply_text(
            f"❌ Unauthorized.\n"
            f"Your Telegram ID: {user.id}\n"
            f"Configured Admin ID: {admin_id}\n\n"
            f"If this is you, update TELEGRAM_ADMIN_ID in backend/.env"
        )
        return False
    return True


# ─── /myid — helper to get the user's own Telegram ID ────
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Your Telegram User ID is:\n\n`{user.id}`\n\n"
        f"Copy this number and set it as TELEGRAM_ADMIN_ID in backend/.env",
        parse_mode="Markdown"
    )


# ─── /start ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🛍 *E-shop Admin Bot*\n\n"
        "Commands:\n"
        "• /add\\_product — Add a product via form\n"
        "• /mask\\_product <id> — Hide/show a product\n"
        "• /stats — Store statistics\n"
        "• /myid — Show your Telegram User ID\n"
        "• /cancel — Cancel current action",
        parse_mode="Markdown"
    )


# ─── /stats ──────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    async with async_session() as db:
        orders_result = await db.execute(select(order_models.Order))
        products_result = await db.execute(select(product_models.Product))
        orders = orders_result.scalars().all()
        products = products_result.scalars().all()
        active = [p for p in products if p.is_active]
        masked = [p for p in products if not p.is_active]
        revenue = sum(o.total_amount for o in orders)

    await update.message.reply_text(
        f"📊 *Store Stats*\n\n"
        f"Orders: {len(orders)}\n"
        f"Total Revenue: ${revenue:.2f}\n"
        f"Active Products: {len(active)}\n"
        f"Masked Products: {len(masked)}",
        parse_mode="Markdown"
    )


# ─── /mask_product ───────────────────────────────────────
async def mask_product_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    try:
        product_id = int(context.args[0])
        async with async_session() as db:
            result = await db.execute(
                select(product_models.Product).where(product_models.Product.id == product_id)
            )
            prod = result.scalars().first()
            if prod:
                prod.is_active = not prod.is_active
                await db.commit()
                status = "✅ visible" if prod.is_active else "🚫 hidden"
                await update.message.reply_text(f"Product #{prod.id} '{prod.name}' is now {status}.")
            else:
                await update.message.reply_text(f"❌ Product #{product_id} not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /mask_product <id>")


# ─── Add Product Conversation ─────────────────────────────
async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_admin(update):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "📦 *New Product*\n\nStep 1/5: What is the product name?",
        parse_mode="Markdown"
    )
    return NAME


async def product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Step 2/5: Write a short description.")
    return DESCRIPTION


async def product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Step 3/5: What is the price? (e.g. 25.50)")
    return PRICE


async def product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['price'] = float(update.message.text)
        await update.message.reply_text("Step 4/5: How many in stock?")
        return STOCK
    except ValueError:
        await update.message.reply_text("❌ Invalid price. Enter a number like 10.99")
        return PRICE


async def product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['stock'] = int(update.message.text)
        await update.message.reply_text(
            "Step 5/5: Send a *photo* of the product, "
            "or type a URL, or type 'skip' if none.",
            parse_mode="Markdown"
        )
        return IMAGE
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Enter a whole number like 50.")
        return STOCK


async def product_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles either a photo upload or a text URL (or 'skip')."""
    image_url = None

    if update.message.photo:
        # User sent an actual photo — download it and save locally
        photo = update.message.photo[-1]  # highest resolution
        file = await photo.get_file()
        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(IMAGES_DIR, filename)
        await file.download_to_drive(save_path)
        # Expose via the static files path
        image_url = f"/static/images/{filename}"
        await update.message.reply_text("📸 Photo saved locally.")
    elif update.message.text:
        text = update.message.text.strip()
        if text.lower() != 'skip':
            image_url = text

    async with async_session() as db:
        prod = product_models.Product(
            name=context.user_data['name'],
            description=context.user_data['description'],
            price=context.user_data['price'],
            stock=context.user_data['stock'],
            image_url=image_url,
        )
        db.add(prod)
        await db.commit()
        await db.refresh(prod)

    await update.message.reply_text(
        f"✅ *Product added!*\n\n"
        f"ID: {prod.id}\n"
        f"Name: {prod.name}\n"
        f"Price: ${prod.price:.2f}\n"
        f"Stock: {prod.stock}\n"
        f"Image: {prod.image_url or 'None'}",
        parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END
