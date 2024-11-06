import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import os
import glob
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import TOKEN

logging.basicConfig(level=logging.INFO)

API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "hr-bot.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("HR").sheet1
    return sheet


def upload_file_to_drive(file_name):
    scope = ["https://www.googleapis.com/auth/drive.file"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "hr-bot.json", scope)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'mimeType': 'application/pdf'
    }
    media = MediaFileUpload(file_name, mimetype='application/pdf')

    file = service.files().create(body=file_metadata,
                                  media_body=media, fields='id').execute()
    file_id = file.get('id')

    service.permissions().create(
        fileId=file_id,
        body={
            'role': 'reader',
            'type': 'anyone'
        }
    ).execute()

    return f'https://drive.google.com/file/d/{file_id}/view'


def add_data_to_sheet(data):
    sheet = connect_to_google_sheets()
    sheet.append_row(data)


def delete_all_pdfs(directory="."):
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    for pdf_file in pdf_files:
        try:
            os.remove(pdf_file)
            print(f"{pdf_file} deleted")
        except Exception as e:
            print(f"Delete error {pdf_file}: {e}")


class ResumeForm(StatesGroup):
    name = State()
    age = State()
    position = State()
    pdf = State()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    add_resume_button = KeyboardButton("Добавить резюме")
    markup.add(add_resume_button)

    await message.answer("Привет! Я HR-бот. Я помогу тебе добавить резюме.", reply_markup=markup)


@dp.message_handler(lambda message: message.text == "Добавить резюме")
async def start_resume(message: types.Message):
    await message.answer("Введите ваше имя:")
    await ResumeForm.name.set()


@dp.message_handler(state=ResumeForm.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Добавить резюме":
        await start_resume(message)
    else:
        await state.update_data(name=message.text)
        await message.answer("Введите ваш возраст:")
        await ResumeForm.next()


@dp.message_handler(state=ResumeForm.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text == "Добавить резюме":
        await start_resume(message)
    else:
        await state.update_data(age=message.text)
        await message.answer("Введите желаемую позицию:")
        await ResumeForm.next()


@dp.message_handler(state=ResumeForm.position)
async def process_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer("Отправьте ваше резюме в формате PDF:")
    await ResumeForm.next()


@dp.message_handler(content_types=[types.ContentType.DOCUMENT], state=ResumeForm.pdf)
async def process_pdf(message: types.Message, state: FSMContext):
    if message.document.mime_type == 'application/pdf':
        pdf_file_id = message.document.file_id
        file_info = await bot.get_file(pdf_file_id)
        file_path = file_info.file_path
        downloaded_file = await bot.download_file(file_path)

        # Обработка имени файла
        safe_file_name = message.document.file_name
        safe_file_name = re.sub(r'[<>:"/\\|?*]', '_', safe_file_name)

        # Обработка и кодирование имени файла
        safe_file_name = safe_file_name.encode(
            'utf-8', errors='ignore').decode('utf-8')

        try:
            with open(safe_file_name, "wb") as f:
                f.write(downloaded_file.getvalue())

            user_data = await state.get_data()
            name = user_data['name']
            age = user_data['age']
            position = user_data['position']

            file_link = upload_file_to_drive(safe_file_name)

            data_to_add = [name, age, position, file_link]
            add_data_to_sheet(data_to_add)

            delete_all_pdfs()
            await message.answer("Заявка успешно отправлена!")
            await state.finish()
        except Exception as e:
            logging.error(f"Ошибка при сохранении файла: {e}")
            await message.answer("Произошла ошибка при сохранении файла. Пожалуйста, попробуйте еще раз.")
    else:
        await message.answer("Пожалуйста, отправьте файл в формате PDF.")


@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.answer("Команда не распознана. Введите /start или нажмите кнопку 'Добавить резюме'.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
