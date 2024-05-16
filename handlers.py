import subprocess
import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import flags
from aiogram.fsm.context import FSMContext
import utils
from states import Gen
import kb
import text

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=kb.menu)

@router.message(F.text == "Меню")
@router.message(F.text == "меню")
@router.message(F.text == "Выйти в меню")
@router.message(F.text == "◀️ Выйти в меню")
async def menu(msg: Message):
    await msg.answer(text.menu, reply_markup=kb.menu)

@router.callback_query(F.data == "generate_text")
async def input_text_prompt(clbck: CallbackQuery, state: FSMContext):
    await state.set_state(Gen.text_prompt)
    await clbck.message.edit_text(text.gen_text)
    await clbck.message.answer(text.gen_exit, reply_markup=kb.exit_kb)

@router.message(Gen.text_prompt)
@flags.chat_action("typing")
async def generate_text(msg: Message, state: FSMContext):
    prompt = msg.text
    mesg = await msg.answer(text.gen_wait)
    res = await utils.generate_text(prompt)
    if not res:
        return await mesg.edit_text(text.gen_error, reply_markup=kb.iexit_kb)
    await mesg.edit_text(res[0] + text.text_watermark, disable_web_page_preview=True)

@router.callback_query(F.data == "generate_image")
async def input_image_prompt(clbck: CallbackQuery, state: FSMContext):
    await state.set_state(Gen.img_prompt)
    await clbck.message.edit_text(text.gen_image)
    await clbck.message.answer(text.gen_exit, reply_markup=kb.exit_kb)

@router.message(Gen.img_prompt)
@flags.chat_action("upload_photo")
async def generate_image(msg: Message, state: FSMContext):
    prompt = msg.text
    mesg = await msg.answer(text.gen_wait)
    img_res = await utils.generate_image(prompt)
    if len(img_res) == 0:
        return await mesg.edit_text(text.gen_error, reply_markup=kb.iexit_kb)
    await mesg.delete()
    await mesg.answer_photo(photo=img_res[0], caption=text.img_watermark)

@router.callback_query(F.data == "scan")
async def scan_prompt(clbck: CallbackQuery, state: FSMContext):
    await clbck.message.edit_text("Пожалуйста, введите IP-адрес для сканирования, например: 8.8.8.8")
    await state.set_state(Gen.scan_prompt)

@router.message(Gen.scan_prompt)
async def scan_handler(msg: Message, state: FSMContext):
    logging.info("Команда /scan получена")
    ip = msg.text
    if not ip:
        await msg.reply("Пожалуйста, укажите IP-адрес. Например: /scan 8.8.8.8")
        logging.info("IP-адрес не указан")
        return

    logging.info(f"IP-адрес для сканирования: {ip}")

    # Запускаем masscan
    try:
        result = subprocess.run(['masscan', ip, '--top-ports', '100', '--rate', '1000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logging.error(f"Ошибка выполнения masscan: {result.stderr}")
            await msg.reply(f"Ошибка выполнения masscan: {result.stderr}")
        else:
            logging.info("masscan выполнен успешно")
            await msg.reply(f"<pre>{result.stdout}</pre>", parse_mode=types.ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await msg.reply(f"Ошибка: {str(e)}")

    await state.clear()
