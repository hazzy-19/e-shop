import os
import uuid
import zipfile
import csv
import io
import shutil
import secrets
from datetime import datetime, timezone, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.future import select

from app.database import async_session
from app.products import models as product_models
from app.orders import models as order_models
from app.bot.states import NAME, DESCRIPTION, PRICE, STOCK, IMAGE
from app.core.config import settings

# ── Image directory ───────────────────────────────────────────────
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ── In-memory 2FA code store ──────────────────────────────────────
# {uid_str: {"code": "123456", "expires": datetime}}
_2fa_codes: dict[str, dict] = {}


# ══════════════════════════════════════════════════════════════════
#  KEYBOARD LAYOUTS
# ══════════════════════════════════════════════════════════════════

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent bottom keyboard shown at all times."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📦 Add Product"), KeyboardButton("📊 Stats")],
            [KeyboardButton("🛒 Recent Orders"), KeyboardButton("🔍 Manage Products")],
            [KeyboardButton("🔐 Get 2FA Code"), KeyboardButton("❓ Help")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type 1–6…",
    )


def orders_inline_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Inline keyboard for order status changes."""
    buttons = []
    for order in orders[:5]:
        buttons.append([
            InlineKeyboardButton(
                f"#{order.id} · KSh {order.total_amount:.0f} · {order.status}",
                callback_data=f"order_{order.id}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Mark Shipped", callback_data=f"ship_{order_id}"),
            InlineKeyboardButton("🎁 Mark Delivered", callback_data=f"deliver_{order_id}"),
        ],
        [InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_{order_id}")],
        [InlineKeyboardButton("« Back to Orders", callback_data="orders_list")],
    ])


def product_manage_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products[:8]:
        status = "✅" if p.is_active else "🚫"
        buttons.append([
            InlineKeyboardButton(
                f"{status} {p.name[:28]} · KSh {p.price:.0f}",
                callback_data=f"prod_{p.id}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def product_actions_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_label = "🚫 Hide Product" if is_active else "✅ Show Product"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=f"toggle_{product_id}")],
        [InlineKeyboardButton("« Back", callback_data="products_list")],
    ])


# ══════════════════════════════════════════════════════════════════
#  ADMIN GUARD
# ══════════════════════════════════════════════════════════════════

async def check_admin(update: Update) -> bool:
    user = update.effective_user
    admin_id = settings.TELEGRAM_ADMIN_ID

    if admin_id == 0:
        await update.message.reply_text(
            "⚠️ *Admin not configured*\n\n"
            "Send /myid to get your Telegram ID, then set `TELEGRAM_ADMIN_ID` in `.env`",
            parse_mode="Markdown",
        )
        return False

    if user.id != admin_id:
        await update.message.reply_text(
            "🔒 *Access Denied*\n\n"
            f"Your ID: `{user.id}`\nAdmin ID: `{admin_id}`",
            parse_mode="Markdown",
        )
        return False
    return True


# ══════════════════════════════════════════════════════════════════
#  CORE COMMANDS
# ══════════════════════════════════════════════════════════════════

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"👤 *Your Telegram ID*\n\n`{user.id}`\n\n"
        "Set this as `TELEGRAM_ADMIN_ID` in your `.env` file.",
        parse_mode="Markdown",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_admin = user.id == settings.TELEGRAM_ADMIN_ID

    greeting = (
        f"👋 Welcome back, *{user.first_name}*!\n\n"
        "🛍️ *eshop Admin Panel*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Use the menu below or type a number:\n\n"
        "  `1` — 📦 Add Product\n"
        "  `2` — 📊 View Stats\n"
        "  `3` — 🛒 Recent Orders\n"
        "  `4` — 🔍 Manage Products\n"
        "  `5` — 🔐 Get 2FA Code\n"
        "  `6` — ❓ Help\n"
        if is_admin
        else
        f"👋 Hello, *{user.first_name}*!\n\n"
        "This is the eshop admin bot.\n"
        "Use /myid to get your Telegram ID."
    )

    await update.message.reply_text(
        greeting,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard() if is_admin else ReplyKeyboardRemove(),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show / refresh the main menu."""
    if not await check_admin(update):
        return
    await update.message.reply_text(
        "📋 *Main Menu*\n\nChoose an option below or type `1`–`6`:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


# ══════════════════════════════════════════════════════════════════
#  NUMBERED SHORTCUT ROUTER
# ══════════════════════════════════════════════════════════════════

async def handle_text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Routes numbered shortcuts and button labels to their handlers."""
    if not await check_admin(update):
        return

    text = update.message.text.strip()
    mapping = {
        "1": trigger_add_product,
        "2": stats,
        "3": recent_orders,
        "4": manage_products,
        "5": send_2fa_code,
        "6": help_cmd,
        "📦 Add Product": trigger_add_product,
        "📊 Stats": stats,
        "🛒 Recent Orders": recent_orders,
        "🔍 Manage Products": manage_products,
        "🔐 Get 2FA Code": send_2fa_code,
        "❓ Help": help_cmd,
    }
    handler = mapping.get(text)
    if handler:
        await handler(update, context)


# ══════════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════════

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    async with async_session() as db:
        orders_result = await db.execute(select(order_models.Order))
        products_result = await db.execute(select(product_models.Product))
        orders = orders_result.scalars().all()
        products = products_result.scalars().all()

    active = sum(1 for p in products if p.is_active)
    hidden = sum(1 for p in products if not p.is_active)
    revenue = sum(o.total_amount for o in orders)
    pending = sum(1 for o in orders if o.status == "pending")
    delivered = sum(1 for o in orders if o.status == "delivered")

    await update.message.reply_text(
        "📊 *Store Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Revenue:* KSh {revenue:,.0f}\n"
        f"📦 *Total Orders:* {len(orders)}\n"
        f"  ↳ ⏳ Pending: {pending}\n"
        f"  ↳ ✅ Delivered: {delivered}\n\n"
        f"🛍️ *Products:* {len(products)}\n"
        f"  ↳ ✅ Active: {active}\n"
        f"  ↳ 🚫 Hidden: {hidden}\n",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


# ══════════════════════════════════════════════════════════════════
#  RECENT ORDERS
# ══════════════════════════════════════════════════════════════════

async def recent_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    async with async_session() as db:
        result = await db.execute(
            select(order_models.Order).order_by(order_models.Order.created_at.desc()).limit(10)
        )
        orders = result.scalars().all()

    if not orders:
        await update.message.reply_text(
            "📭 No orders yet.", reply_markup=main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"🛒 *Recent Orders* ({len(orders)} shown)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap an order to manage it:",
        parse_mode="Markdown",
        reply_markup=orders_inline_keyboard(orders),
    )


# ══════════════════════════════════════════════════════════════════
#  MANAGE PRODUCTS
# ══════════════════════════════════════════════════════════════════

async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    async with async_session() as db:
        result = await db.execute(
            select(product_models.Product).order_by(product_models.Product.id.desc()).limit(8)
        )
        products = result.scalars().all()

    if not products:
        await update.message.reply_text("📭 No products yet.", reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        "🔍 *Product Manager*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap a product to toggle visibility:",
        parse_mode="Markdown",
        reply_markup=product_manage_keyboard(products),
    )


# ══════════════════════════════════════════════════════════════════
#  INLINE CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Order detail ──────────────────────────────────────────────
    if data.startswith("order_"):
        order_id = int(data.split("_")[1])
        async with async_session() as db:
            result = await db.execute(
                select(order_models.Order).where(order_models.Order.id == order_id)
            )
            order = result.scalars().first()
        if not order:
            await query.edit_message_text("❌ Order not found.")
            return
        text = (
            f"📋 *Order #{order.id}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Amount: KSh {order.total_amount:.2f}\n"
            f"📌 Status: *{order.status}*\n"
            f"🗓️ Date: {order.created_at.strftime('%d %b %Y, %H:%M')}\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=order_actions_keyboard(order_id))

    # ── Mark shipped ──────────────────────────────────────────────
    elif data.startswith("ship_"):
        order_id = int(data.split("_")[1])
        await _update_order_status(query, order_id, "shipped")

    # ── Mark delivered ────────────────────────────────────────────
    elif data.startswith("deliver_"):
        order_id = int(data.split("_")[1])
        await _update_order_status(query, order_id, "delivered")

    # ── Cancel order ──────────────────────────────────────────────
    elif data.startswith("cancel_"):
        order_id = int(data.split("_")[1])
        await _update_order_status(query, order_id, "cancelled")

    # ── Orders list ───────────────────────────────────────────────
    elif data == "orders_list":
        async with async_session() as db:
            result = await db.execute(
                select(order_models.Order).order_by(order_models.Order.created_at.desc()).limit(10)
            )
            orders = result.scalars().all()
        await query.edit_message_text(
            f"🛒 *Recent Orders*\nTap one to manage:",
            parse_mode="Markdown",
            reply_markup=orders_inline_keyboard(orders),
        )

    # ── Product detail ────────────────────────────────────────────
    elif data.startswith("prod_"):
        product_id = int(data.split("_")[1])
        async with async_session() as db:
            result = await db.execute(
                select(product_models.Product).where(product_models.Product.id == product_id)
            )
            prod = result.scalars().first()
        if not prod:
            await query.edit_message_text("❌ Product not found.")
            return
        status_str = "✅ Active" if prod.is_active else "🚫 Hidden"
        text = (
            f"📦 *{prod.name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Price: KSh {prod.price:.2f}\n"
            f"📦 Stock: {prod.stock}\n"
            f"Status: {status_str}\n"
        )
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=product_actions_keyboard(product_id, prod.is_active),
        )

    # ── Toggle product visibility ─────────────────────────────────
    elif data.startswith("toggle_"):
        product_id = int(data.split("_")[1])
        async with async_session() as db:
            result = await db.execute(
                select(product_models.Product).where(product_models.Product.id == product_id)
            )
            prod = result.scalars().first()
            if prod:
                prod.is_active = not prod.is_active
                await db.commit()
                new_status = "✅ now *visible*" if prod.is_active else "🚫 now *hidden*"
                await query.edit_message_text(
                    f"*{prod.name}* is {new_status} on the storefront.",
                    parse_mode="Markdown",
                    reply_markup=product_actions_keyboard(product_id, prod.is_active),
                )

    # ── Products list ─────────────────────────────────────────────
    elif data == "products_list":
        async with async_session() as db:
            result = await db.execute(
                select(product_models.Product).order_by(product_models.Product.id.desc()).limit(8)
            )
            products = result.scalars().all()
        await query.edit_message_text(
            "🔍 *Product Manager*\nTap a product to manage:",
            parse_mode="Markdown",
            reply_markup=product_manage_keyboard(products),
        )


async def _update_order_status(query, order_id: int, new_status: str) -> None:
    async with async_session() as db:
        result = await db.execute(
            select(order_models.Order).where(order_models.Order.id == order_id)
        )
        order = result.scalars().first()
        if order:
            order.status = new_status
            if new_status == "delivered":
                order.delivered_at = datetime.now(timezone.utc)
            await db.commit()
            status_icons = {
                "shipped": "🚚",
                "delivered": "🎁",
                "cancelled": "❌",
            }
            icon = status_icons.get(new_status, "📌")
            await query.edit_message_text(
                f"{icon} *Order #{order_id}* marked as *{new_status}*.",
                parse_mode="Markdown",
                reply_markup=order_actions_keyboard(order_id),
            )


# ══════════════════════════════════════════════════════════════════
#  2FA CODE
# ══════════════════════════════════════════════════════════════════

async def send_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return
    uid = str(update.effective_user.id)
    code = f"{secrets.randbelow(1000000):06d}"
    _2fa_codes[uid] = {
        "code": code,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    await update.message.reply_text(
        "🔐 *Your Admin 2FA Code*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  `{code}`\n\n"
        "⏱️ Valid for *5 minutes*. Do not share this code.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


def verify_2fa_code(uid: str, code: str) -> bool:
    """Called by the backend API to verify a submitted code."""
    record = _2fa_codes.get(uid)
    if not record:
        return False
    if datetime.now(timezone.utc) > record["expires"]:
        _2fa_codes.pop(uid, None)
        return False
    if record["code"] != code.strip():
        return False
    _2fa_codes.pop(uid, None)  # Single-use
    return True


# ══════════════════════════════════════════════════════════════════
#  HELP
# ══════════════════════════════════════════════════════════════════

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❓ *Help*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Use the menu buttons *or* type a number:\n\n"
        "  `1` or 📦 — Add a new product\n"
        "  `2` or 📊 — View store statistics\n"
        "  `3` or 🛒 — View and manage orders\n"
        "  `4` or 🔍 — Show/hide products\n"
        "  `5` or 🔐 — Get admin 2FA code\n"
        "  `6` or ❓ — This help message\n\n"
        "📁 Send a *ZIP file* to bulk-upload products.\n"
        "📸 During product add, send a *photo* directly.\n\n"
        "Commands: /menu /myid /cancel",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


# ══════════════════════════════════════════════════════════════════
#  ADD PRODUCT CONVERSATION
# ══════════════════════════════════════════════════════════════════

async def trigger_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start_add_product(update, context)


async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_admin(update):
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        "📦 *New Product — Step 1/5*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "What is the *product name*?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("❌ Cancel")]],
            resize_keyboard=True,
        ),
    )
    return NAME


async def product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "✏️ *Step 2/5 — Description*\n\nWrite a short product description:",
        parse_mode="Markdown",
    )
    return DESCRIPTION


async def product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    context.user_data['description'] = update.message.text
    await update.message.reply_text(
        "💰 *Step 3/5 — Price*\n\nEnter the price in KSh (e.g. `1500`):",
        parse_mode="Markdown",
    )
    return PRICE


async def product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    try:
        context.user_data['price'] = float(update.message.text.replace(",", ""))
        await update.message.reply_text(
            "📦 *Step 4/5 — Stock*\n\nHow many units are in stock?",
            parse_mode="Markdown",
        )
        return STOCK
    except ValueError:
        await update.message.reply_text("❌ Invalid price. Enter a number like `1500` or `29.99`", parse_mode="Markdown")
        return PRICE


async def product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    try:
        context.user_data['stock'] = int(update.message.text)
        await update.message.reply_text(
            "📸 *Step 5/5 — Image*\n\n"
            "• Send a *photo* directly, or\n"
            "• Paste an *image URL*, or\n"
            "• Type `skip` to continue without an image",
            parse_mode="Markdown",
        )
        return IMAGE
    except ValueError:
        await update.message.reply_text("❌ Enter a whole number like `50`")
        return STOCK


async def product_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)

    image_url = None

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(IMAGES_DIR, filename)
        await file.download_to_drive(save_path)
        image_url = f"/static/images/{filename}"
    elif update.message.text and update.message.text.strip().lower() != 'skip':
        image_url = update.message.text.strip()

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
        "✅ *Product Added!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ *{prod.name}*\n"
        f"💰 KSh {prod.price:,.2f}\n"
        f"📦 Stock: {prod.stock}\n"
        f"🖼️ Image: {'Yes' if prod.image_url else 'None'}\n\n"
        "The product is now live on the storefront!",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "❌ *Cancelled.*",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════
#  ZIP BULK UPLOAD
# ══════════════════════════════════════════════════════════════════

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_admin(update):
        return

    doc = update.message.document
    if not doc or not doc.file_name.endswith('.zip'):
        return

    msg = await update.message.reply_text(
        "📥 *ZIP received — processing...*",
        parse_mode="Markdown",
    )

    file = await context.bot.get_file(doc.file_id)
    temp_zip_path = os.path.join(IMAGES_DIR, f"temp_{uuid.uuid4().hex}.zip")
    await file.download_to_drive(temp_zip_path)

    extracted_count = 0
    errors = []

    try:
        from app.categories.models import Category
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if not csv_files:
                await msg.edit_text("❌ No CSV file found in the ZIP.")
                return

            with zip_ref.open(csv_files[0]) as f:
                content = f.read().decode('utf-8')

            reader = csv.DictReader(io.StringIO(content))
            async with async_session() as db:
                for row in reader:
                    try:
                        category_name = row.get("category", "").strip()
                        cat_id = None
                        if category_name:
                            cat_res = await db.execute(
                                select(Category).where(Category.name == category_name)
                            )
                            cat = cat_res.scalars().first()
                            if not cat:
                                slug = category_name.lower().replace(" ", "-")
                                cat = Category(name=category_name, slug=slug)
                                db.add(cat)
                                await db.commit()
                                await db.refresh(cat)
                            cat_id = cat.id

                        image_filename = row.get("image_filename", "").strip()
                        image_url = None
                        if image_filename and image_filename in zip_ref.namelist():
                            new_filename = f"{uuid.uuid4().hex}_{image_filename.replace(' ', '_')}"
                            target_path = os.path.join(IMAGES_DIR, new_filename)
                            with zip_ref.open(image_filename) as zf, open(target_path, 'wb') as f_out:
                                shutil.copyfileobj(zf, f_out)
                            image_url = f"/static/images/{new_filename}"

                        product = product_models.Product(
                            name=row.get("name", "").strip(),
                            description=row.get("description", "").strip(),
                            price=float(row.get("price", 0)),
                            stock=int(row.get("stock", 0)),
                            category_id=cat_id,
                            image_url=image_url,
                        )
                        db.add(product)
                        extracted_count += 1
                        await db.commit()
                    except Exception as e:
                        errors.append(f"Row '{row.get('name', '?')}': {e}")

        summary = (
            f"✅ *Bulk Upload Complete!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Products added: *{extracted_count}*\n"
        )
        if errors:
            summary += f"⚠️ Errors: {len(errors)}\n"
            for e in errors[:3]:
                summary += f"  • {e}\n"

        await msg.edit_text(summary, parse_mode="Markdown")

    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
