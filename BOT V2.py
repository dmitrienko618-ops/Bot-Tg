import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Включаем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токен бота и ID администратора
TOKEN = "8680822714:AAFtCdKlaozCdM6SMeWQmOkkwUvGcIrGzPg"
ADMIN_ID = 1000853183

# ID картинки
PHOTO_ID = "AgACAgIAAxkBAAICYmmf3Qk1SdO4QvJ5ddbpdz_bLnu1AAKkEWsb-xQAAUngIZ3CeD4tpQEAAwIAA3kAAzoE"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==================== ХРАНИЛИЩА ДАННЫХ ====================

user_file_count = {}  # {user_id: count}
user_messages_to_delete = {}  # {user_id: [message_ids]}
user_last_send = {}  # {user_id: datetime последней отправки}
banned_users = set()  # {user_id}
user_first_start = {}  # {user_id: datetime первого запуска}
user_usernames = {}  # {user_id: username}

# Настройки
SEND_COOLDOWN = 3600  # 1 час в секундах

# ==================== СОСТОЯНИЯ ====================

class SendState(StatesGroup):
    waiting_for_message = State()

# ==================== КЛАВИАТУРЫ ====================

def main_keyboard():
    """Главное меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Отправить", callback_data="send")],
            [InlineKeyboardButton(text="📄 Пользовательское соглашение", url="https://telegra.ph/Polzovatelskoe-soglashenie-02-26-26")]
        ]
    )

# ==================== ФУНКЦИИ ДЛЯ ОЧИСТКИ ====================

async def cleanup_user_messages(user_id: int, keep_message_id: int = None):
    """Удаляет все сообщения пользователя"""
    if user_id in user_messages_to_delete:
        for msg_id in user_messages_to_delete[user_id]:
            try:
                if msg_id != keep_message_id:
                    await bot.delete_message(user_id, msg_id)
            except:
                pass
        user_messages_to_delete[user_id] = []

async def add_message_to_cleanup(user_id: int, message_id: int):
    """Добавляет сообщение в список на удаление"""
    if user_id not in user_messages_to_delete:
        user_messages_to_delete[user_id] = []
    user_messages_to_delete[user_id].append(message_id)

def format_time_remaining(seconds: int) -> str:
    """Форматирует оставшееся время"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    else:
        return f"{minutes} мин"

# ==================== АДМИН-КОМАНДЫ ====================

@dp.message(Command("user"))
async def users_list(message: Message):
    """Показывает список пользователей, запускавших бота"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 Эта команда только для администратора")
        return
    
    if not user_first_start:
        await message.answer("📭 Пока нет пользователей")
        return
    
    # Сортируем пользователей по дате первого запуска (новые сверху)
    sorted_users = sorted(user_first_start.items(), key=lambda x: x[1], reverse=True)
    
    users_list = []
    for user_id, first_start in sorted_users:
        username = user_usernames.get(user_id, f"ID:{user_id}")
        date_str = first_start.strftime("%d.%m.%Y %H:%M")
        
        # Добавляем статус бана
        status = "🚫" if user_id in banned_users else "✅"
        
        # Проверяем, есть ли у пользователя отправки
        last_send = user_last_send.get(user_id)
        if last_send:
            last_send_str = last_send.strftime("%d.%m.%Y %H:%M")
            users_list.append(f"{status} {username} — {date_str} (последняя отправка: {last_send_str})")
        else:
            users_list.append(f"{status} {username} — {date_str}")
    
    # Отправляем частями, если список большой
    result = "📊 *Пользователи бота:*\n\n" + "\n".join(users_list)
    
    if len(result) > 4000:
        parts = []
        current_part = "📊 *Пользователи бота:*\n\n"
        
        for line in users_list:
            if len(current_part) + len(line) + 1 > 4000:
                parts.append(current_part)
                current_part = line + "\n"
            else:
                current_part += line + "\n"
        
        if current_part:
            parts.append(current_part)
        
        for i, part in enumerate(parts):
            await message.answer(part, parse_mode="Markdown")
    else:
        await message.answer(result, parse_mode="Markdown")

@dp.message(Command("ban"))
async def ban_user(message: Message):
    """Банит пользователя по username или ID"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 Эта команда только для администратора")
        return
    
    try:
        # Получаем аргумент команды
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: /ban @username или /ban user_id")
            return
        
        target = args[1]
        user_id_to_ban = None
        
        # Проверяем, это username или ID
        if target.startswith('@'):
            # Поиск по username
            username = target[1:]  # убираем @
            for uid, uname in user_usernames.items():
                if uname and (uname == f"@{username}" or uname == username):
                    user_id_to_ban = uid
                    break
        else:
            # Попробуем преобразовать в ID
            try:
                user_id_to_ban = int(target)
            except:
                pass
        
        if not user_id_to_ban:
            await message.answer(f"❌ Пользователь {target} не найден")
            return
        
        # Баним пользователя
        banned_users.add(user_id_to_ban)
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                user_id_to_ban,
                "🚫 *Вы были забанены*\n\nВы больше не можете пользоваться этим ботом.",
                parse_mode="Markdown"
            )
        except:
            pass
        
        username_display = user_usernames.get(user_id_to_ban, f"ID:{user_id_to_ban}")
        await message.answer(f"✅ Пользователь {username_display} забанен")
        logger.info(f"Admin banned user {username_display}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unban"))
async def unban_user(message: Message):
    """Разбанивает пользователя по username или ID"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 Эта команда только для администратора")
        return
    
    try:
        # Получаем аргумент команды
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: /unban @username или /unban user_id")
            return
        
        target = args[1]
        user_id_to_unban = None
        
        # Проверяем, это username или ID
        if target.startswith('@'):
            # Поиск по username
            username = target[1:]  # убираем @
            for uid, uname in user_usernames.items():
                if uname and (uname == f"@{username}" or uname == username):
                    user_id_to_unban = uid
                    break
        else:
            # Попробуем преобразовать в ID
            try:
                user_id_to_unban = int(target)
            except:
                pass
        
        if not user_id_to_unban:
            await message.answer(f"❌ Пользователь {target} не найден")
            return
        
        # Проверяем, забанен ли пользователь
        if user_id_to_unban not in banned_users:
            username_display = user_usernames.get(user_id_to_unban, f"ID:{user_id_to_unban}")
            await message.answer(f"❌ Пользователь {username_display} не в бане")
            return
        
        # Разбаниваем
        banned_users.remove(user_id_to_unban)
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                user_id_to_unban,
                "✅ *Вы были разблокированы*\n\nТеперь вы снова можете пользоваться ботом.",
                parse_mode="Markdown"
            )
        except:
            pass
        
        username_display = user_usernames.get(user_id_to_unban, f"ID:{user_id_to_unban}")
        await message.answer(f"✅ Пользователь {username_display} разбанен")
        logger.info(f"Admin unbanned user {username_display}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    """Главное меню"""
    user_id = message.from_user.id
    
    # Сохраняем информацию о пользователе
    if message.from_user.username:
        user_usernames[user_id] = f"@{message.from_user.username}"
    else:
        user_usernames[user_id] = message.from_user.full_name or f"ID:{user_id}"
    
    # Записываем дату первого запуска
    if user_id not in user_first_start:
        user_first_start[user_id] = datetime.now()
        logger.info(f"Новый пользователь {user_usernames[user_id]} запустил бота")
    
    # Проверка бана
    if user_id in banned_users:
        await message.answer("🚫 *Вы забанены*\n\nВы не можете использовать этого бота.", parse_mode="Markdown")
        return
    
    # Очищаем все старые сообщения пользователя
    await cleanup_user_messages(user_id, message.message_id)
    
    # Инициализируем счетчик файлов для пользователя
    if user_id not in user_file_count:
        user_file_count[user_id] = 0
    
    # Отправляем главное меню
    sent_msg = await message.answer_photo(
        photo=PHOTO_ID,
        caption="🔐 *Бот телеграм канала @Ternovka_core*\n\n"
                "Делись своими сообщениями, новостями, фотографиями через анонимный бот, "
                "администрация и создатель не видят ваши личные данные путем шифрования\n\n"
                "_нажимая на кнопку отправить вы автоматически соглашаетесь с пользовательским "
                "соглашением и правилами пользования бота_",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    # Добавляем сообщение в список на удаление
    await add_message_to_cleanup(user_id, sent_msg.message_id)

@dp.callback_query(F.data == "send")
async def send_button(callback: CallbackQuery, state: FSMContext):
    """Переход в режим отправки"""
    user_id = callback.from_user.id
    
    # Проверка бана
    if user_id in banned_users:
        await callback.answer("Вы забанены", show_alert=True)
        return
    
    # Проверяем, прошло ли достаточно времени с последней отправки
    if user_id in user_last_send:
        time_passed = (datetime.now() - user_last_send[user_id]).total_seconds()
        if time_passed < SEND_COOLDOWN:
            remaining = int(SEND_COOLDOWN - time_passed)
            time_str = format_time_remaining(remaining)
            await callback.answer(f"⏳ Подождите еще {time_str}", show_alert=True)
            return
    
    # Удаляем предыдущее сообщение
    await callback.message.delete()
    
    # Отправляем экран отправки
    sent_msg = await callback.message.answer_photo(
        photo=PHOTO_ID,
        caption="📤 *Отправь сюда файл, видео, фото, текст одним сообщением*\n\n"
                "⏳ Время обработки и пересылки 24 часа\n\n"
                f"⏰ Ограничение: 1 сообщение в час",
        parse_mode="Markdown"
    )
    
    # Добавляем сообщение в список на удаление
    await add_message_to_cleanup(user_id, sent_msg.message_id)
    
    await state.set_state(SendState.waiting_for_message)
    await callback.answer()

# ==================== ОБРАБОТЧИК СООБЩЕНИЙ ====================

@dp.message(SendState.waiting_for_message)
async def handle_user_message(message: Message, state: FSMContext):
    """Обработка сообщения от пользователя"""
    user_id = message.from_user.id
    
    # Проверка бана
    if user_id in banned_users:
        await message.answer("🚫 Вы забанены")
        await state.clear()
        return
    
    # Проверяем, прошло ли достаточно времени с последней отправки
    if user_id in user_last_send:
        time_passed = (datetime.now() - user_last_send[user_id]).total_seconds()
        if time_passed < SEND_COOLDOWN:
            remaining = int(SEND_COOLDOWN - time_passed)
            time_str = format_time_remaining(remaining)
            
            # Отправляем сообщение о времени ожидания
            wait_msg = await message.answer(f"⏳ *Подождите еще {time_str}*\n\nВы можете отправлять 1 сообщение в час", parse_mode="Markdown")
            
            # Ждем 5 секунд и удаляем
            await asyncio.sleep(5)
            await wait_msg.delete()
            
            # Возвращаем в главное меню
            await cleanup_user_messages(user_id)
            await message.delete()
            
            main_msg = await message.answer_photo(
                photo=PHOTO_ID,
                caption="🔐 *Бот телеграм канала @Ternovka_core*\n\n"
                        "Делись своими сообщениями, новостями, фотографиями через анонимный бот, "
                        "администрация и создатель не видят ваши личные данные путем шифрования\n\n"
                        "_нажимая на кнопку отправить вы автоматически соглашаетесь с пользовательским "
                        "соглашением и правилами пользования бота_",
                parse_mode="Markdown",
                reply_markup=main_keyboard()
            )
            await add_message_to_cleanup(user_id, main_msg.message_id)
            await state.clear()
            return
    
    # Записываем время отправки
    user_last_send[user_id] = datetime.now()
    
    # Увеличиваем счетчик файлов пользователя
    if user_id not in user_file_count:
        user_file_count[user_id] = 0
    user_file_count[user_id] += 1
    file_number = user_file_count[user_id]
    
    # Формируем информацию о файле
    file_info = f"*File {file_number}*"
    
    # Получаем подпись, если есть
    caption_text = message.caption if message.caption else ""
    full_caption = f"{file_info}\n\n{caption_text}" if caption_text else file_info
    
    # Определяем тип сообщения и отправляем админу
    try:
        if message.text:
            await bot.send_message(
                ADMIN_ID,
                f"{file_info}\n\n{message.text}",
                parse_mode="Markdown"
            )
            
        elif message.photo:
            await bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.video:
            await bot.send_video(
                ADMIN_ID,
                message.video.file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.document:
            await bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.audio:
            await bot.send_audio(
                ADMIN_ID,
                message.audio.file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.voice:
            await bot.send_voice(
                ADMIN_ID,
                message.voice.file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.animation:
            await bot.send_animation(
                ADMIN_ID,
                message.animation.file_id,
                caption=full_caption,
                parse_mode="Markdown"
            )
            
        elif message.sticker:
            await bot.send_sticker(ADMIN_ID, message.sticker.file_id)
            await bot.send_message(ADMIN_ID, file_info, parse_mode="Markdown")
            
        else:
            await message.forward(ADMIN_ID)
            await bot.send_message(ADMIN_ID, file_info, parse_mode="Markdown")
        
        # Отправляем информацию об отправителе
        username = message.from_user.username or "нет username"
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        await bot.send_message(
            ADMIN_ID,
            f"👤 *Отправитель:* @{username}\n"
            f"🆔 *ID:* `{user_id}`\n"
            f"⏰ *Время:* {current_time}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")
    
    # Полная очистка чата пользователя
    await cleanup_user_messages(user_id)
    
    # Удаляем текущее сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    # Отправляем подтверждение
    sent_msg = await message.answer("✅ *Отправлено* ✅", parse_mode="Markdown")
    
    # Ждем 10 секунд
    await asyncio.sleep(10)
    
    # Удаляем подтверждение
    try:
        await sent_msg.delete()
    except:
        pass
    
    # Отправляем главное меню
    main_msg = await message.answer_photo(
        photo=PHOTO_ID,
        caption="🔐 *Бот телеграм канала @Ternovka_core*\n\n"
                "Делись своими сообщениями, новостями, фотографиями через анонимный бот, "
                "администрация и создатель не видят ваши личные данные путем шифрования\n\n"
                "_нажимая на кнопку отправить вы автоматически соглашаетесь с пользовательским "
                "соглашением и правилами пользования бота_",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    # Добавляем главное меню в список на будущее удаление
    await add_message_to_cleanup(user_id, main_msg.message_id)
    
    # Очищаем состояние
    await state.clear()

# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Бот запускается...")
    logger.info(f"🤖 Admin ID: {ADMIN_ID}")
    logger.info(f"⏰ Лимит отправки: 1 сообщение в час")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
