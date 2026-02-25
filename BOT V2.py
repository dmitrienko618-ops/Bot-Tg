import asyncio
import logging
import random
import string
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, InputMediaPhoto)

# Включаем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = "8680822714:AAFtCdKlaozCdM6SMeWQmOkkwUvGcIrGzPg"
ADMIN_ID = 1000853183
BOT_USERNAME = "F2FF3_bot"

# ID картинок
MAIN_PHOTO_ID = "AgACAgIAAxkBAAMKaZ1-mKw0Ysq2pg3sK9BJlbykvsIAAqEWaxu5O-lIQXgdlS8uPYQBAAMCAAN5AAM6BA"
LINK_PHOTO_ID = "AgACAgIAAxkBAAIBEmmd4MTtSozx5iMTZWB6Rd2a3X8KAAIREGsbT1nwSF8D2r_fsmx5AQADAgADeQADOgQ"
VPN_PHOTO_ID = "AgACAgIAAxkBAAIBEWmd4HBJBVFPvi1QV6LlEu1b8MvHAAILEGsbT1nwSLtVQzbj1hR3AQADAgADeQADOgQ"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==================== НАСТРОЙКИ ====================
CLEANUP_TIME = 30  # минут неактивности для очистки
LINK_EXPIRE_TIME = 60  # минут жизни ссылки

# ==================== ЯЗЫКОВЫЕ НАСТРОЙКИ ====================

# Хранилище языков пользователей {user_id: 'ru'/'en'}
user_language = {}

# Русский язык
RU = {
    'start_description': '🔐 *Анонимный файлообменник*\n\n'
                         '• Полностью анонимный обмен файлами и сообщениями\n'
                         '• Переписки не хранятся и автоматически удаляются\n'
                         '• End-to-end шифрование — даже создатель не видит сообщения\n'
                         '• Подключайся через VPN для обхода блокировок в России\n\n'
                         '_Ваша приватность — наш главный приоритет_',
    
    'btn_msg': '📨 Сообщение админу',
    'btn_crypto': '💰 Крипто',
    'btn_link': '🔗 ПОЛУЧИТЬ ССЫЛКУ 🔗',
    'btn_vpn': '🔒 VPN',
    
    'write_msg': '✍️ Напишите сообщение, и я передам его создателю',
    'crypto_text': 'TRC20\nTPnv8C9UfimDRNC6sAyYMGCwFonV9uZHcn\n\nTON\nUQBgSeJbR6BwIhvghAlC4KWw60n-tOm8_x73J0pcF0HNh9hp',
    'vpn_text': '🔒 *VPN*\n\n• Обход блокировок в России\n• Скрытие реального IP\n• Маскировка трафика под белые списки',
    'back': '◀️ Назад',
    'go': '🚀 ПЕРЕЙТИ',
    'your_link': '🔗 Это ВАША ссылка. Поделитесь ей!',
    'link_expires': f'Ссылка активна {LINK_EXPIRE_TIME} мин',
    'chat_active': '💬 Чат активен',
    'connected': '🔗 *Подключено!*\nАнонимный чат с шифрованием',
    'someone_joined': '🔔 Кто-то подключился!',
    'partner_left': '👋 Собеседник покинул чат',
    'chat_ended': 'Чат завершен',
    'exit': '🚪 Выйти из чата',
    'banned': '🚫 Вы забанены',
    'link_expired': '❌ Ссылка истекла',
    'chat_occupied': '❌ Чат уже занят',
    'waiting_for_partner': '⏳ Ожидание подключения второго участника...',
    'reply': '📝 Ответить',
    'ban': '🚫 Забанить',
    'reply_prompt': '✍️ Напишите ответ (будет отправлен пользователю):',
    'reply_sent': '✅ Ответ отправлен!',
    'user_banned': '✅ Пользователь забанен',
    
    'broadcast_prompt': '📢 Отправьте сообщение для рассылки:',
    'cancelled': '❌ Отменено',
    'no_users': '📭 Нет пользователей',
    'broadcasting': '📤 Рассылка {count} пользователям...',
    'progress': '📤 Прогресс: {current}/{total}',
    'broadcast_complete': '✅ Рассылка завершена: {success}/{total} отправлено',
    'unban_usage': 'Использование: /unban @username',
    'user_unbanned': '✅ @{username} разбанен',
    'user_not_found': '❌ @{username} не найден',
    
    'users_list': '📊 Пользователи:\n\n',
    'no_users_yet': '📭 Пока нет пользователей',
}

# Английский язык
EN = {
    'start_description': '🔐 *Anonymous File Exchange*\n\n'
                         '• Completely anonymous file and message exchange\n'
                         '• Chats are not stored and are automatically deleted\n'
                         '• End-to-end encryption — even the creator cannot read messages\n'
                         '• Use VPN to bypass internet restrictions in Russia\n\n'
                         '_Your privacy is our top priority_',
    
    'btn_msg': '📨 Message Admin',
    'btn_crypto': '💰 Crypto',
    'btn_link': '🔗 GET LINK 🔗',
    'btn_vpn': '🔒 VPN',
    
    'write_msg': '✍️ Write a message, and I\'ll pass it to the creator',
    'crypto_text': 'TRC20\nTPnv8C9UfimDRNC6sAyYMGCwFonV9uZHcn\n\nTON\nUQBgSeJbR6BwIhvghAlC4KWw60n-tOm8_x73J0pcF0HNh9hp',
    'vpn_text': '🔒 *VPN*\n\n• Bypass Russian blocks\n• Hide your real IP\n• Mask traffic as whitelisted',
    'back': '◀️ Back',
    'go': '🚀 GO',
    'your_link': '🔗 This is YOUR link. Share it!',
    'link_expires': f'Link expires in {LINK_EXPIRE_TIME} min',
    'chat_active': '💬 Chat active',
    'connected': '🔗 *Connected!*\nAnonymous encrypted chat',
    'someone_joined': '🔔 Someone joined!',
    'partner_left': '👋 Partner left the chat',
    'chat_ended': 'Chat ended',
    'exit': '🚪 Exit Chat',
    'banned': '🚫 You are banned',
    'link_expired': '❌ Link expired',
    'chat_occupied': '❌ Chat occupied',
    'waiting_for_partner': '⏳ Waiting for second participant to join...',
    'reply': '📝 Reply',
    'ban': '🚫 Ban',
    'reply_prompt': '✍️ Write your reply (will be sent to the user):',
    'reply_sent': '✅ Reply sent!',
    'user_banned': '✅ User banned',
    
    'broadcast_prompt': '📢 Send message to broadcast:',
    'cancelled': '❌ Cancelled',
    'no_users': '📭 No users',
    'broadcasting': '📤 Broadcasting to {count} users...',
    'progress': '📤 Progress: {current}/{total}',
    'broadcast_complete': '✅ Broadcast complete: {success}/{total} sent',
    'unban_usage': 'Usage: /unban @username',
    'user_unbanned': '✅ @{username} unbanned',
    'user_not_found': '❌ @{username} not found',
    
    'users_list': '📊 Users:\n\n',
    'no_users_yet': '📭 No users yet',
}

def get_text(user_id, key):
    """Получить текст на языке пользователя"""
    lang = user_language.get(user_id, 'ru')
    return RU[key] if lang == 'ru' else EN[key]


# ==================== ХРАНИЛИЩА ДАННЫХ ====================

user_last_message = {}  # время последнего сообщения
banned_users = {}  # забаненные пользователи
anonymous_chats = {}  # {token: [user1_id, user2_id]}
user_chat_token = {}  # {user_id: token}
pending_links = {}  # {token: (creator_id, expiry_time)}
chat_messages = {}  # {token: [message_ids]}
user_first_start = {}  # {user_id: datetime первого запуска}
user_usernames = {}  # {user_id: username}


class ReplyState(StatesGroup):
    waiting_reply = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


# ==================== КЛАВИАТУРЫ ====================

def language_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
             InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
        ]
    )

def main_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, 'btn_msg'), callback_data="btn_1"),
             InlineKeyboardButton(text=get_text(user_id, 'btn_crypto'), callback_data="btn_2")],
            [InlineKeyboardButton(text=get_text(user_id, 'btn_link'), callback_data="btn_3")],
            [InlineKeyboardButton(text=get_text(user_id, 'btn_vpn'), callback_data="btn_4")]
        ]
    )


def back_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, 'back'), callback_data="back")]]
    )


def vpn_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, 'go'), url="https://t.me/NosokVPNBot?start=partner_1000853183")],
            [InlineKeyboardButton(text=get_text(user_id, 'back'), callback_data="back_to_main")]
        ]
    )


def admin_actions_keyboard(user_id: int, username: str, lang_user: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang_user, 'reply'), callback_data=f"reply_{user_id}")],
            [InlineKeyboardButton(text=get_text(lang_user, 'ban'), callback_data=f"ban_{user_id}_{username}")]
        ]
    )


def chat_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, 'exit'), callback_data="exit_chat")]]
    )


# ==================== УТИЛИТЫ ====================

def generate_link_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


async def cleanup_chat_messages(token: str):
    if token in chat_messages:
        for chat_id, msg_id in chat_messages[token]:
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        del chat_messages[token]


async def cleanup_old_data():
    while True:
        await asyncio.sleep(300)
        now = datetime.now()
        
        inactive_users = [
            uid for uid, last_time in user_last_message.items()
            if now - last_time > timedelta(minutes=CLEANUP_TIME)
        ]
        
        for user_id in inactive_users:
            if user_id in user_chat_token:
                token = user_chat_token[user_id]
                if token in anonymous_chats:
                    await cleanup_chat_messages(token)
                    del anonymous_chats[token]
                    for uid in list(user_chat_token.keys()):
                        if user_chat_token[uid] == token:
                            del user_chat_token[uid]
            del user_last_message[user_id]
            logger.info(f"🧹 Очищен неактивный пользователь {user_id}")
        
        expired_links = [token for token, (_, exp) in pending_links.items() if now > exp]
        for token in expired_links:
            if token in anonymous_chats:
                await cleanup_chat_messages(token)
                del anonymous_chats[token]
            del pending_links[token]
            logger.info(f"🧹 Очищена истекшая ссылка {token}")


# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        await message.answer(get_text(user_id, 'banned'))
        return
    
    if message.from_user.username:
        user_usernames[user_id] = f"@{message.from_user.username}"
    else:
        user_usernames[user_id] = message.from_user.full_name or "No username"
    
    if user_id not in user_first_start:
        user_first_start[user_id] = datetime.now()
        logger.info(f"Новый пользователь {user_usernames[user_id]} запустил бота")
    
    args = message.text.split()
    if len(args) > 1:
        await handle_link_click(message, args[1])
        return
    
    if user_id not in user_language:
        await message.answer_photo(
            photo=MAIN_PHOTO_ID,
            caption="🌐 *Choose language / Выберите язык*",
            parse_mode="Markdown",
            reply_markup=language_keyboard()
        )
        return
    
    user_last_message[user_id] = datetime.now()
    
    await message.answer_photo(
        photo=MAIN_PHOTO_ID,
        caption=get_text(user_id, 'start_description'),
        parse_mode="Markdown",
        reply_markup=main_keyboard(user_id)
    )


@dp.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    
    user_language[user_id] = lang
    
    await callback.message.delete()
    
    await callback.message.answer_photo(
        photo=MAIN_PHOTO_ID,
        caption=get_text(user_id, 'start_description'),
        parse_mode="Markdown",
        reply_markup=main_keyboard(user_id)
    )
    await callback.answer()


@dp.message(Command("infousers"))
async def infousers_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 This command is only for admin")
        return
    
    if not user_first_start:
        await message.answer(get_text(ADMIN_ID, 'no_users_yet'))
        return
    
    sorted_users = sorted(user_first_start.items(), key=lambda x: x[1], reverse=True)
    
    users_list = []
    for user_id, first_start in sorted_users:
        username = user_usernames.get(user_id, f"ID:{user_id}")
        date_str = first_start.strftime("%d.%m.%Y %H:%M")
        users_list.append(f"{username} — {date_str}")
    
    result = get_text(ADMIN_ID, 'users_list') + "\n".join(users_list)
    
    if len(result) > 4000:
        parts = []
        current_part = get_text(ADMIN_ID, 'users_list')
        
        for line in users_list:
            if len(current_part) + len(line) + 1 > 4000:
                parts.append(current_part)
                current_part = line + "\n"
            else:
                current_part += line + "\n"
        
        if current_part:
            parts.append(current_part)
        
        for part in parts:
            await message.answer(part)
    else:
        await message.answer(result)


async def handle_link_click(message: Message, token: str):
    user_id = message.from_user.id
    
    if token not in anonymous_chats:
        await message.answer_photo(
            photo=LINK_PHOTO_ID,
            caption=get_text(user_id, 'link_expired'),
            reply_markup=main_keyboard(user_id)
        )
        return
    
    creator_id, participant_id = anonymous_chats[token]
    
    if user_id == creator_id:
        await message.answer_photo(
            photo=LINK_PHOTO_ID,
            caption=get_text(user_id, 'your_link'),
            reply_markup=chat_keyboard(user_id)
        )
        return
    
    if participant_id is not None:
        await message.answer_photo(
            photo=LINK_PHOTO_ID,
            caption=get_text(user_id, 'chat_occupied'),
            reply_markup=main_keyboard(user_id)
        )
        return
    
    anonymous_chats[token][1] = user_id
    user_chat_token[user_id] = token
    user_chat_token[creator_id] = token
    chat_messages[token] = []
    
    try:
        await bot.send_message(
            creator_id,
            get_text(creator_id, 'someone_joined'),
            reply_markup=chat_keyboard(creator_id)
        )
    except:
        pass
    
    if token in pending_links:
        del pending_links[token]
    
    await message.answer_photo(
        photo=LINK_PHOTO_ID,
        caption=get_text(user_id, 'connected'),
        parse_mode="Markdown",
        reply_markup=chat_keyboard(user_id)
    )


# ==================== ФУНКЦИЯ ДЛЯ ОТПРАВКИ МЕДИА ====================

async def send_media_by_type(message: Message, chat_id: int, caption: str = None):
    """Отправляет медиа в зависимости от типа (полностью анонимно)"""
    try:
        if message.text:
            return await bot.send_message(chat_id, message.text)
        elif message.photo:
            return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption)
        elif message.document:
            return await bot.send_document(chat_id, message.document.file_id, caption=caption)
        elif message.video:
            return await bot.send_video(chat_id, message.video.file_id, caption=caption)
        elif message.audio:
            return await bot.send_audio(chat_id, message.audio.file_id, caption=caption)
        elif message.voice:
            return await bot.send_voice(chat_id, message.voice.file_id, caption=caption)
        elif message.sticker:
            return await bot.send_sticker(chat_id, message.sticker.file_id)
        elif message.animation:
            return await bot.send_animation(chat_id, message.animation.file_id, caption=caption)
        else:
            return await message.copy_to(chat_id)
    except Exception as e:
        logger.error(f"Error in send_media_by_type: {e}")
        return None


# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@dp.callback_query(F.data == "btn_1")
async def button_1(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(get_text(user_id, 'write_msg'))


@dp.callback_query(F.data == "btn_2")
async def button_2(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    await callback.answer()
    await callback.message.edit_caption(
        caption=get_text(user_id, 'crypto_text'),
        reply_markup=back_keyboard(user_id)
    )


@dp.callback_query(F.data == "btn_3")
async def button_3(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    
    if user_id in user_chat_token:
        token = user_chat_token[user_id]
        if token in anonymous_chats:
            creator_id, participant_id = anonymous_chats[token]
            
            if participant_id is None:
                link = f"https://t.me/{BOT_USERNAME}?start={token}"
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=LINK_PHOTO_ID,
                        caption=f"🔗 {link}\n\n{get_text(user_id, 'link_expires')}"
                    ),
                    reply_markup=chat_keyboard(user_id)
                )
                await callback.answer()
                return
            else:
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=LINK_PHOTO_ID,
                        caption=get_text(user_id, 'chat_active')
                    ),
                    reply_markup=chat_keyboard(user_id)
                )
                await callback.answer()
                return
    
    token = generate_link_token()
    anonymous_chats[token] = [user_id, None]
    user_chat_token[user_id] = token
    pending_links[token] = (user_id, datetime.now() + timedelta(minutes=LINK_EXPIRE_TIME))
    chat_messages[token] = []
    
    link = f"https://t.me/{BOT_USERNAME}?start={token}"
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=LINK_PHOTO_ID,
            caption=f"🔗 {link}\n\n{get_text(user_id, 'link_expires')}"
        ),
        reply_markup=chat_keyboard(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "btn_4")
async def button_4(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=VPN_PHOTO_ID,
            caption=get_text(user_id, 'vpn_text'),
            parse_mode="Markdown"
        ),
        reply_markup=vpn_keyboard(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "exit_chat")
async def exit_chat(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_chat_token:
        await callback.answer(get_text(user_id, 'chat_ended'), show_alert=True)
        return
    
    token = user_chat_token[user_id]
    
    if token in anonymous_chats:
        creator_id, participant_id = anonymous_chats[token]
        other_user = creator_id if user_id == participant_id else participant_id
        
        await cleanup_chat_messages(token)
        
        if other_user:
            try:
                await bot.send_message(other_user, get_text(other_user, 'partner_left'))
                await bot.send_photo(
                    chat_id=other_user,
                    photo=MAIN_PHOTO_ID,
                    caption=get_text(other_user, 'start_description'),
                    parse_mode="Markdown",
                    reply_markup=main_keyboard(other_user)
                )
            except:
                pass
        
        del anonymous_chats[token]
        if creator_id in user_chat_token:
            del user_chat_token[creator_id]
        if participant_id and participant_id in user_chat_token:
            del user_chat_token[participant_id]
    
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=MAIN_PHOTO_ID,
        caption=get_text(user_id, 'start_description'),
        parse_mode="Markdown",
        reply_markup=main_keyboard(user_id)
    )
    await callback.answer(get_text(user_id, 'chat_ended'))


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=MAIN_PHOTO_ID,
            caption=get_text(user_id, 'start_description'),
            parse_mode="Markdown"
        ),
        reply_markup=main_keyboard(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back_button(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in banned_users:
        await callback.answer(get_text(user_id, 'banned'), show_alert=True)
        return
    
    user_last_message[user_id] = datetime.now()
    await callback.message.edit_caption(
        caption=get_text(user_id, 'start_description'),
        parse_mode="Markdown",
        reply_markup=main_keyboard(user_id)
    )


# ==================== ОБРАБОТЧИКИ КНОПОК АДМИНА ====================

@dp.callback_query(F.data.startswith("reply_"))
async def reply_button(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    
    if user_id in banned_users:
        await callback.message.answer(get_text(ADMIN_ID, 'user_banned'))
        await callback.answer()
        return
    
    await state.update_data(target_user=user_id)
    await state.set_state(ReplyState.waiting_reply)
    await callback.message.answer(get_text(ADMIN_ID, 'reply_prompt'))
    await callback.answer()


@dp.callback_query(F.data.startswith("ban_"))
async def ban_button(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    
    parts = callback.data.split("_")
    user_id = int(parts[1])
    username = parts[2] if len(parts) > 2 else None
    
    banned_users[user_id] = username
    
    if user_id in user_last_message:
        del user_last_message[user_id]
    if user_id in user_chat_token:
        token = user_chat_token[user_id]
        if token in anonymous_chats:
            await cleanup_chat_messages(token)
            del anonymous_chats[token]
        del user_chat_token[user_id]
    
    try:
        await bot.send_message(user_id, get_text(user_id, 'banned'))
    except:
        pass
    
    await callback.message.edit_text(f"✅ User {f'@{username}' if username else user_id} banned")
    await callback.answer()


# ==================== ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ ====================

@dp.message()
async def message_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id in banned_users:
        return
    
    user_last_message[user_id] = datetime.now()
    
    # Если пользователь не выбрал язык, просим выбрать
    if user_id not in user_language and user_id != ADMIN_ID:
        await message.answer_photo(
            photo=MAIN_PHOTO_ID,
            caption="🌐 *Choose language / Выберите язык*",
            parse_mode="Markdown",
            reply_markup=language_keyboard()
        )
        return
    
    # === АНОНИМНЫЙ ЧАТ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ===
    if user_id in user_chat_token:
        token = user_chat_token[user_id]
        if token in anonymous_chats:
            creator_id, participant_id = anonymous_chats[token]

            # Определяем получателя
            if user_id == creator_id:
                receiver = participant_id
            elif user_id == participant_id:
                receiver = creator_id
            else:
                receiver = None

            # Если оба участника в чате
            if receiver and participant_id is not None and creator_id is not None:
                # Просто пересылаем сообщение получателю (полная анонимность)
                sent = await send_media_by_type(message, receiver)

                # Сохраняем ID сообщения для авто-удаления
                if sent and token in chat_messages:
                    chat_messages[token].append((receiver, sent.message_id))

                # Не отправляем подтверждение отправителю
                return
            else:
                # Если второй участник ещё не подключился
                await message.answer(get_text(user_id, 'waiting_for_partner'))
                return
    
    # === АДМИН ===
    if user_id == ADMIN_ID:
        current_state = await state.get_state()
        
        if current_state == ReplyState.waiting_reply.state:
            data = await state.get_data()
            target_user = data.get("target_user")
            
            if target_user:
                try:
                    if message.text:
                        await bot.send_message(
                            target_user,
                            f"👤 Creator:\n{message.text}"
                        )
                        await message.answer(get_text(ADMIN_ID, 'reply_sent'))
                        
                    elif message.photo:
                        await bot.send_photo(
                            target_user,
                            message.photo[-1].file_id,
                            caption="👤 Creator"
                        )
                        await message.answer(get_text(ADMIN_ID, 'reply_sent'))
                        
                    elif message.document:
                        await bot.send_document(
                            target_user,
                            message.document.file_id,
                            caption="👤 Creator"
                        )
                        await message.answer(get_text(ADMIN_ID, 'reply_sent'))
                        
                    else:
                        await message.forward(target_user)
                        await message.answer(get_text(ADMIN_ID, 'reply_sent'))
                    
                    logger.info(f"Admin reply sent to user {target_user}")
                    
                except Exception as e:
                    await message.answer(f"❌ Error: {e}")
                
                await state.clear()
                return
            
        elif current_state == BroadcastState.waiting_for_message.state:
            return
        
        return
    
    # === ОБЫЧНОЕ СООБЩЕНИЕ АДМИНУ ===
    if message.from_user.username:
        user_display = f"@{message.from_user.username}"
    else:
        user_display = message.from_user.full_name
    
    if message.text:
        await bot.send_message(
            ADMIN_ID,
            f"👤 {user_display} (ID: {user_id}):\n{message.text}",
            reply_markup=admin_actions_keyboard(user_id, message.from_user.username, ADMIN_ID)
        )
    else:
        sent_media = await send_media_by_type(message, ADMIN_ID)
        await bot.send_message(
            ADMIN_ID,
            f"👤 {user_display} (ID: {user_id})",
            reply_markup=admin_actions_keyboard(user_id, message.from_user.username, ADMIN_ID)
        )
    
    try:
        await message.delete()
    except:
        pass
    
    await message.answer_photo(
        photo=MAIN_PHOTO_ID,
        caption=get_text(user_id, 'start_description'),
        parse_mode="Markdown",
        reply_markup=main_keyboard(user_id)
    )


# ==================== АДМИН-КОМАНДЫ ====================

@dp.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(get_text(ADMIN_ID, 'broadcast_prompt'))
    await state.set_state(BroadcastState.waiting_for_message)


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer(get_text(ADMIN_ID, 'cancelled'))


@dp.message(BroadcastState.waiting_for_message)
async def broadcast_message(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    
    users = set(user_last_message.keys()) | {uid for uid in user_chat_token.keys()}
    users.discard(ADMIN_ID)
    
    if not users:
        await message.answer(get_text(ADMIN_ID, 'no_users'))
        return
    
    status = await message.answer(get_text(ADMIN_ID, 'broadcasting').format(count=len(users)))
    
    success = 0
    for i, uid in enumerate(users):
        try:
            if message.text:
                await bot.send_message(uid, f"📢 {message.text}")
            elif message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=message.caption)
            else:
                await message.forward(uid)
            success += 1
        except:
            pass
        
        if (i + 1) % 10 == 0:
            await status.edit_text(get_text(ADMIN_ID, 'progress').format(current=i+1, total=len(users)))
    
    await status.edit_text(get_text(ADMIN_ID, 'broadcast_complete').format(success=success, total=len(users)))


@dp.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        username = message.text.split()[1].replace("@", "")
        for uid, uname in list(banned_users.items()):
            if uname and uname.lower() == username.lower():
                del banned_users[uid]
                await message.answer(get_text(ADMIN_ID, 'user_unbanned').format(username=username))
                return
        await message.answer(get_text(ADMIN_ID, 'user_not_found').format(username=username))
    except:
        await message.answer(get_text(ADMIN_ID, 'unban_usage'))


# ==================== ЗАПУСК ====================

async def main():
    logger.info("🚀 Бот запускается...")
    asyncio.create_task(cleanup_old_data())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
