import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.client.session.aiohttp import AiohttpSession

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token va channel ID
bot_token = "7751289706:AAFGTuI3Z3ix8Qg7n-zecz3C12OK3mYoPLA"
channel_id = "@get_info_type"  # Kanal username to'g'ri formatda

# Create a session
session = AiohttpSession()

# Initialize the Bot and Dispatcher
bot = Bot(token=bot_token, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Define FSM states
class Form(StatesGroup):
    vacancy = State()
    name = State()
    phone_number = State()
    id_card = State()
    diploma = State()
    resume = State()
    language_certificate = State()
    criminal_record = State()
    confirmation = State()

# Telefon raqamini tekshirish funksiyasi
async def validate_phone_number(phone_number: str) -> bool:
    return (phone_number.startswith("+998") and len(phone_number) == 13) or len(phone_number) == 9

# /start komandasi uchun handler
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.set_state(Form.vacancy)
    vacancy_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'quv bo'limi / Uslubchi", callback_data="vacancy_1")],
        [InlineKeyboardButton(text="Matematik", callback_data="vacancy_2")],
        [InlineKeyboardButton(text="Informatik", callback_data="vacancy_3")]
    ])
    await message.answer("Iltimos, vakansiyani tanlang:", reply_markup=vacancy_keyboard)

# Vakansiya tanlash
@dp.callback_query(Form.vacancy)
async def handle_vacancy(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(vacancy=callback_query.data)
    await callback_query.message.answer("Iltimos, ism va familiyangizni kiriting:")
    await state.set_state(Form.name)

# Ism va familiyani kiritish
@dp.message(Form.name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Telefon raqamingizni kiriting:")
    await state.set_state(Form.phone_number)

# Telefon raqamini kiritish
@dp.message(Form.phone_number)
async def handle_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text

    if await validate_phone_number(phone_number):
        if len(phone_number) == 9:
            phone_number = f"+998{phone_number}"

        await state.update_data(phone_number=phone_number)
        await message.answer("Shaxsni tasdiqlovchi hujjatni yuboring:")
        await state.set_state(Form.id_card)
    else:
        await message.answer("Iltimos, telefon raqamingizni to'g'ri formatda kiriting!")

# Pasport yoki ID karta rasm yoki fayl qabul qilish
@dp.message(Form.id_card)
async def handle_id_card_file(message: types.Message, state: FSMContext):
    if message.photo or message.document:
        await state.update_data(id_card=message.document.file_id if message.document else message.photo[-1].file_id)
        await message.answer("Nomzodning shaxsiy varaqasi (ma'lumotnoma-obyektivka) ni yuborishingizni so'raymiz:")
        await state.set_state(Form.resume)
    else:
        await message.answer("Iltimos, rasm yoki fayl yuboring!")

# Resume qabul qilish
@dp.message(Form.resume)
async def handle_resume_file(message: types.Message, state: FSMContext):
    if message.photo or message.document:
        await state.update_data(resume=message.document.file_id if message.document else message.photo[-1].file_id)
        await message.answer("Oliy ma’lumotga ega bakalavr/magistraturani tamomlaganligi to‘g‘risidagi hujjat:")
        await state.set_state(Form.diploma)
    else:
        await message.answer("Iltimos, rasm yoki fayl yuboring!")

# Diplom rasm yoki fayl qabul qilish
@dp.message(Form.diploma)
async def handle_diploma_file(message: types.Message, state: FSMContext):
    if message.photo or message.document:
        await state.update_data(diploma=message.document.file_id if message.document else message.photo[-1].file_id)
        await message.answer("ELTS/TOEFL/DTM sertifikatingizni yuklang (malaka talablariga mos ravishda):", 
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="Menda bunday ma'lumot yo'q", callback_data="no_certificate")]
                             ]))
        await state.set_state(Form.language_certificate)
    else:
        await message.answer("Iltimos, rasm yoki fayl yuboring!")

# Til sertifikati uchun callback handler
@dp.callback_query(lambda c: c.data == "no_certificate")
async def handle_language_certificate_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(language_certificate="Yo'q")
    await handle_criminal_record_step(callback_query.message, state)
    await callback_query.answer()

# Sudlanganlik uchun callback handler
@dp.callback_query(lambda c: c.data == "no_criminal_record")
async def handle_criminal_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(criminal_record="Yo'q")
    await handle_confirmation(callback_query.from_user.id, state)
    await callback_query.answer()

# Sudlanganlik qadami uchun funksiya
async def handle_criminal_record_step(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Menda bunday ma'lumot yo'q", callback_data="no_criminal_record")]
    ])
    await message.answer(
        "Sudlanganlik haqidagi rasm yoki faylni yuboring yoki 'Menda bunday ma'lumot yo'q' tugmasini bosing:", 
        reply_markup=keyboard
    )
    await state.set_state(Form.criminal_record)

# Til sertifikati uchun message handler
@dp.message(Form.language_certificate)
async def handle_language_certificate_file(message: types.Message, state: FSMContext):
    if message.photo or message.document:
        file_id = message.document.file_id if message.document else message.photo[-1].file_id
        await state.update_data(language_certificate=file_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Menda bunday ma'lumot yo'q", callback_data="no_criminal_record")]
        ])
        await message.answer(
            "Sudlanganlik haqidagi rasm yoki faylni yuboring yoki 'Menda bunday ma'lumot yo'q' tugmasini bosing:", 
            reply_markup=keyboard
        )
        await state.set_state(Form.criminal_record)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Menda bunday ma'lumot yo'q", callback_data="no_certificate")]
        ])
        await message.answer(
            "Iltimos, rasm yoki fayl yuboring yoki 'Menda bunday ma'lumot yo'q' tugmasini bosing!", 
            reply_markup=keyboard
        )

# Sudlanganlik uchun fayl qabul qilish
@dp.message(Form.criminal_record)
async def handle_criminal_record_file(message: types.Message, state: FSMContext):
    if message.photo or message.document:
        await state.update_data(criminal_record=message.document.file_id if message.document else message.photo[-1].file_id)
        await handle_confirmation(message.from_user.id, state)
    elif message.text == "Menda bunday ma'lumot yo'q":
        await state.update_data(criminal_record="Yo'q")
        await handle_confirmation(message.from_user.id, state)  # Tasdiqlashga o'tish
    else:
        await message.answer("Iltimos, rasm yoki fayl yuboring yoki 'Menda bunday ma'lumot yo'q' deb yozing!")

async def handle_confirmation(user_id: int, state: FSMContext):
    data = await state.get_data()

    # Vakansiya nomini to'g'rilash
    vacancy_names = {
        "vacancy_1": "O'quv bo'limi / Uslubchi",
        "vacancy_2": "Matematik",
        "vacancy_3": "Informatik"
    }
    vacancy = vacancy_names.get(data.get('vacancy'), data.get('vacancy'))

    # Chiroyli formatdagi xabar
    message_text = (
        "📋 <b>Sizning ma'lumotlaringiz:</b>\n\n"
        f"👔 <b>Vakansiya:</b> {vacancy}\n"
        f"👤 <b>F.I.O:</b> {data['name']}\n"
        f"📱 <b>Telefon:</b> {data['phone_number']}\n\n"
        "📎 <b>Yuborilgan hujjatlar:</b>\n"
    )
    
    await bot.send_message(
        user_id, 
        message_text, 
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, tasdiqlash", callback_data="confirm"),
                InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data="cancel")
            ]
        ])
    )
    
    await state.set_state(Form.confirmation)

# Tasdiqlash natijasi
@dp.callback_query(Form.confirmation)
async def confirmation_response(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback_query.data == "confirm":
        try:
            vacancy_names = {
                "vacancy_1": "O'quv bo'limi / Uslubchi",
                "vacancy_2": "Matematik",
                "vacancy_3": "Informatik"
            }
            vacancy = vacancy_names.get(data.get('vacancy'), data.get('vacancy'))

            channel_message = (
                "🆕 <b>Yangi ariza!</b>\n\n"
                f"👔 <b>Vakansiya:</b> {vacancy}\n"
                f"👤 <b>F.I.O:</b> {data['name']}\n"
                f"📱 <b>Telefon:</b> {data['phone_number']}\n\n"
                "📎 <b>Yuborilgan hujjatlar:</b>"
            )
            
            # Asosiy xabarni yuborish
            await bot.send_message(
                chat_id="@get_info_type",
                text=channel_message,
                parse_mode="HTML"
            )

            # Hujjatlarni yuborish - rasm yoki fayl ekanligini tekshirib
            async def send_file(file_id, caption):
                try:
                    # Avval document sifatida yuborishga harakat qilish
                    await bot.send_document("@get_info_type", file_id, caption=caption)
                except Exception:
                    try:
                        # Agar document sifatida yuborib bo'lmasa, rasm sifatida yuborish
                        await bot.send_photo("@get_info_type", file_id, caption=caption)
                    except Exception as e:
                        print(f"Faylni yuborishda xatolik: {e}")

            # Hujjatlarni yuborish
            if data.get('id_card'):
                await send_file(data['id_card'], "🪪 Pasport/ID")
            if data.get('diploma'):
                await send_file(data['diploma'], "🎓 Diplom")
            if data.get('language_certificate') and data['language_certificate'] != "Yo'q":
                await send_file(data['language_certificate'], "🌐 Til sertifikati")
            if data.get('criminal_record') and data['criminal_record'] != "Yo'q":
                await send_file(data['criminal_record'], "📄 Sudlanganlik ma'lumotnomasi")

            await callback_query.message.answer(
                "✅ <b>Sizning arizangiz muvaffaqiyatli yuborildi!</b>\n\n"
                "Tez orada siz bilan bog'lanamiz.",
                parse_mode="HTML"
            )
            
        except Exception as e:
            print(f"Xatolik tafsilotlari: {e}")
            await callback_query.message.answer(
                f"❌ <b>Xatolik yuz berdi!</b>\n\n"
                f"Xatolik haqida ma'lumot: {str(e)}",
                parse_mode="HTML"
            )
        finally:
            await state.clear()
    
    elif callback_query.data == "cancel":
        await callback_query.message.answer(
            "❌ <b>Ariza bekor qilindi.</b>\n\n"
            "Qaytadan boshlash uchun /start buyrug'ini yuboring.",
            parse_mode="HTML"
        )
        await state.clear()

# Main function to run the bot
async def main():
    await dp.start_polling(bot)

# Run the bot using asyncio
if __name__ == "__main__":
    asyncio.run(main())
