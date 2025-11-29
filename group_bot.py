from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

TOKEN = ""

# Словари для подсчета сообщений
message_counts_total = {}   # {user_id: total_messages}
message_counts_today = {}   # {user_id: {date_string: count}}

# Словарь для хранения ID сообщений
user_messages = {}  # {user_id: [message_ids]}

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен! Используй /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/mute - мут пользователя на 7 дней\n"
        "/unmute - снять мут\n"
        "/kick - кикнуть пользователя\n"
        "/ban - забанить пользователя\n"
        "/admins - показать администраторов\n"
        "/stats - показать статистику сообщений\n"
        "/delall - удалить все сообщения пользователя за всё время"
    )
    await update.message.reply_text(help_text)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, которого хотите замутить.")
        return
    user = update.message.reply_to_message.from_user
    chat = update.message.chat
    until_date = datetime.now() + timedelta(days=7)
    await chat.restrict_member(user.id, ChatPermissions(can_send_messages=False), until_date=until_date)
    await update.message.reply_text(f"{user.first_name} замучен на 7 дней.")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, чтобы снять мут.")
        return
    user = update.message.reply_to_message.from_user
    chat = update.message.chat
    await chat.restrict_member(user.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text(f"{user.first_name} больше не замучен.")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, чтобы кикнуть.")
        return
    user = update.message.reply_to_message.from_user
    chat = update.message.chat
    await chat.kick_member(user.id)
    await update.message.reply_text(f"{user.first_name} был кикнут.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, чтобы забанить.")
        return
    user = update.message.reply_to_message.from_user
    chat = update.message.chat
    await chat.ban_member(user.id)
    await update.message.reply_text(f"{user.first_name} был забанен.")

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    admin_list = await chat.get_administrators()
    msg = "Администраторы:\n" + "\n".join([f"- {admin.user.first_name}" for admin in admin_list])
    await update.message.reply_text(msg)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    user = update.message.from_user
    total = message_counts_total.get(user.id, 0)
    today_count = message_counts_today.get(user.id, {}).get(today, 0)
    await update.message.reply_text(f"Сообщений всего: {total}\nСообщений сегодня: {today_count}")

# --- Удаление всех сообщений пользователя ---
async def delete_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение пользователя, чьи сообщения нужно удалить.")
        return

    user = update.message.reply_to_message.from_user
    chat = update.message.chat
    user_id = user.id

    if user_id not in user_messages or not user_messages[user_id]:
        await update.message.reply_text("Нет сохранённых сообщений этого пользователя.")
        return

    deleted = 0
    for msg_id in user_messages[user_id]:
        try:
            await chat.delete_message(msg_id)
            deleted += 1
        except:
            pass

    user_messages[user_id] = []

    await update.message.reply_text(f"Удалено сообщений: {deleted}")

# --- Отслеживание сообщений ---
async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    today = datetime.now().strftime("%Y-%m-%d")

    # Общий счет
    message_counts_total[user.id] = message_counts_total.get(user.id, 0) + 1

    # За сегодня
    if user.id not in message_counts_today:
        message_counts_today[user.id] = {}
    message_counts_today[user.id][today] = message_counts_today[user.id].get(today, 0) + 1

    # Сохраняем ID сообщений
    if user.id not in user_messages:
        user_messages[user.id] = []
    user_messages[user.id].append(update.message.message_id)

# --- Запуск бота ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("delall", delete_all_messages))

    # Отслеживание всех сообщений
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), count_messages))

    print("Бот запущен...")
    app.run_polling()

