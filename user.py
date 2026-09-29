from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import WEBAPP_URL, COMPANY_NAME, MANAGER_USERNAME
from database.requests import get_or_create_user, get_setting, get_orders_with_payments
from filters.subscription import get_unsubscribed_channels
from keyboards.user_kb import open_app_inline_kb, main_menu_kb, subscription_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed:
        await message.answer(
            "👋 Botdan to'liq foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling!",
            reply_markup=subscription_kb(unsubscribed),
        )
        return

    await send_welcome(message)


async def send_welcome(message: Message):
    text = (
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n"
        f"🛋 <b>{COMPANY_NAME}</b> botiga xush kelibsiz!\n\n"
        f"Quyidagi menyudan foydalaning 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())

    if WEBAPP_URL:
        await message.answer(
            "🖼 Bizning ilgari qilgan ishlarimizni ko'rish uchun ilovani oching:",
            reply_markup=open_app_inline_kb(),
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)
    if unsubscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    await callback.message.delete()
    await send_welcome(callback.message)
    await callback.answer()


# ---------- PASTKI MENYU TUGMALARI ----------

@router.message(F.text == "🖼 Ishlarimiz")
async def show_works_fallback(message: Message):
    # WEBAPP_URL sozlanmagan holatda ham foydalanuvchi biror narsa ko'rsin
    await message.answer("🖼 Bizning ishlarimiz bilan tanishish uchun Mini App tez orada ishga tushadi.")


@router.message(F.text == "📞 Menejer bilan bog'lanish")
async def contact_manager(message: Message):
    if not MANAGER_USERNAME:
        await message.answer("📞 Menejer bilan bog'lanish hozircha sozlanmagan. Iltimos, keyinroq urinib ko'ring.")
        return
    await message.answer(f"📞 Menejerimiz bilan bog'lanish uchun bosing: @{MANAGER_USERNAME}")


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    text = await get_setting("about_us_text")
    if not text:
        text = f"🛋 <b>{COMPANY_NAME}</b> — zamonaviy mebel ustaxonasi.\n\nBatafsil ma'lumot tez orada qo'shiladi."
    await message.answer(text)


@router.message(F.text == "💡 Yordam")
async def show_help(message: Message):
    await message.answer(
        "💡 <b>Yordam</b>\n\n"
        "🖼 Ishlarimiz — bizning oldingi ishlarimiz bilan tanishing\n"
        "📦 Buyurtmalarim — buyurtmangiz holati, narx va to'lovlar\n"
        "📞 Menejer bilan bog'lanish — to'g'ridan-to'g'ri chat\n"
        "ℹ️ Biz haqimizda — kompaniya haqida ma'lumot\n\n"
        "Buyurtma berish uchun bizning do'konimizga tashrif buyuring — "
        "menejerimiz sizga yordam beradi!"
    )


@router.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):
    from database.requests import get_user
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return

    rows = await get_orders_with_payments(user.id)
    if not rows:
        await message.answer("📦 Sizda hali buyurtma yo'q.\n\nBuyurtma berish uchun do'konimizga tashrif buyuring!")
        return

    status_labels = {
        "new": "🆕 Yangi", "confirmed": "✅ Kelishuv va to'lov", "in_production": "🛠 Ishlab chiqarilmoqda",
        "delivered": "🚚 Yetkazib berildi", "cancelled": "❌ Bekor qilingan",
    }

    for row in rows:
        order = row["order"]
        text = (
            f"📦 <b>Buyurtma #{order.id}</b> — {status_labels.get(order.status, order.status)}\n\n"
            f"📝 {order.description or '—'}\n"
        )
        if order.agreed_price:
            text += (
                f"💰 Kelishilgan summa: {order.agreed_price:,} so'm\n".replace(",", " ")
                + f"✅ To'langan: {row['paid']:,} so'm\n".replace(",", " ")
                + f"⏳ Qarzdorlik: {row['debt']:,} so'm\n".replace(",", " ")
            )
        else:
            text += "💰 Narx hali kelishilmagan\n"
        await message.answer(text)
