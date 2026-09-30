import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

TOKEN = "8632344295:AAH3rqMllvkMMTFl4XIdrb1-QCitgje4kL4"

dp = Dispatcher()

# Testlarni vaqtincha xotirada saqlash uchun lug'at
TESTS_DATABASE = {}

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Salom, {html.bold(message.from_user.full_name)}! Test tekshiruvchi botga xush kelibsiz.\n\n"
        "📖 <b>Mavjud testlarni ko'rish uchun:</b> /tests\n"
        "✍️ <b>Javob yuborish tartibi:</b>\n"
        "<code>&lt;test_raqami&gt; &lt;javoblar&gt;</code> (Masalan: <code>1 abcd...</code>)"
    )

# Admin test qo'shishi uchun
@dp.message(F.caption.startswith("/addtest") | F.text.startswith("/addtest"))
async def add_test_handler(message: Message) -> None:
    text_content = message.caption if message.caption else message.text
    
    args = text_content.split(maxsplit=2)
    
    if len(args) < 3:
        await message.answer("⚠️ Xato! To'g'ri format: <code>/addtest &lt;test_raqami&gt; &lt;kalitlar&gt;</code>\nMisol uchun PDF faylga izoh qilib: <code>/addtest 1 abcd</code> deb yuboring.")
        return
    
    test_id = args[1].strip()
    key = args[2].strip().lower()
    
    if not message.document:
        await message.answer("⚠️ Iltimos, test matni solingan <b>PDF faylni</b> biriktirib, izohiga <code>/addtest raqam kalitlar</code> deb yuboring!")
        return
    
    file_id = message.document.file_id
    
    TESTS_DATABASE[test_id] = {
        "key": key,
        "pdf": file_id,
        "filename": message.document.file_name
    }
    
    await message.answer(
        f"✅ <b>{test_id}-raqamli test muvaffaqiyatli qo'shildi!</b>\n"
        f"📄 Fayl: {message.document.file_name}\n"
        f"🔑 Kalitlar: <code>{key}</code>"
    )

# Mavjud testlar ro'yxati
@dp.message(Command("tests"))
async def list_tests_handler(message: Message) -> None:
    if not TESTS_DATABASE:
        await message.answer("⚠️ Hozircha bazada testlar mavjud emas.")
        return
    
    text = "📚 <b>Mavjud testlar ro'yxati:</b>\n\n"
    for t_id, data in TESTS_DATABASE.items():
        text += f"📌 <b>Test raqami:</b> {t_id}\n📄 Fayl: {data['filename']}\n📥 Yuklab olish uchun <code>/get_{t_id}</code> deb yuboring\n\n"
    
    await message.answer(text)

# Testni PDF sifatida yuklab olish
@dp.message(F.text.startswith("/get_"))
async def get_test_pdf(message: Message) -> None:
    test_id = message.text.replace("/get_", "").strip()
    
    if test_id not in TESTS_DATABASE:
        await message.answer("⚠️ Bunday raqamli test topilmadi.")
        return
    
    test_data = TESTS_DATABASE[test_id]
    await message.answer_document(
        document=test_data["pdf"],
        caption=f"📄 <b>{test_id}-raqamli test materiali.</b>\n\n"
                f"Javoblarni yuborish tartibi:\n"
                f"<code>{test_id} &lt;javoblaringiz&gt;</code>\n"
                f"Masalan: <code>{test_id} abcd...</code>"
    )

# O'quvchi javobini tekshirish
@dp.message()
async def check_student_answers(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split(maxsplit=1)
    
    if len(parts) < 2:
        return
    
    test_id = parts[0].strip()
    student_answers = parts[1].strip().lower()
    
    if test_id not in TESTS_DATABASE:
        await message.answer(f"⚠️ {test_id}-raqamli test bazada topilmadi yoki bot qayta ishga tushgani uchun o'chib ketgan.")
        return
    
    test_data = TESTS_DATABASE[test_id]
    correct_key = test_data["key"]
    
    if len(student_answers) != len(correct_key):
        await message.answer(
            f"⚠️ Xatolik! Siz yuborgan javoblar soni ({len(student_answers)} ta) "
            f"bu testdagi savollar soniga ({len(correct_key)} ta) mos kelmayapti!"
        )
        return
    
    correct_count = 0
    result_details = []
    
    for i in range(len(correct_key)):
        q_num = i + 1
        s_ans = student_answers[i]
        t_ans = correct_key[i]
        
        if s_ans == t_ans:
            correct_count += 1
            result_details.append(f"{q_num}-savol: {s_ans.upper()} ✅")
        else:
            result_details.append(f"{q_num}-savol: {s_ans.upper()} ❌ (To'g'risi: {t_ans.upper()})")
            
    score_text = (
        f"📊 <b>{test_id}-test natijasi:</b>\n\n"
        f"To'g'ri javoblar: <b>{correct_count} / {len(correct_key)}</b>\n\n"
        f"<b>Batafsil tahlil:</b>\n" + "\n".join(result_details)
    )
    
    await message.answer(score_text)

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
