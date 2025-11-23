import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Токен вашего бота, полученный от @BotFather
API_TOKEN = "Ваш_токен"

# Состояния диалога
SELECTING_ACTION, ADD_GROUP_NAME, ADD_REMINDER_DATE = range(3)

# Текст сообщений
START_MESSAGE = "Выберите действие:"
ADD_GROUP_MESSAGE = "Введите название группы:"
ADD_DATE_MESSAGE = "Введите дату напоминания (в формате DD.MM.YYYY):"
REMINDERS_LIST_MESSAGE = "Текущие напоминания:\n\n{}"
NO_REMINDERS_MESSAGE = "Нет текущих напоминаний."
DELETE_REMINDER_MESSAGE = "Выберите напоминание для удаления или вернитесь на начальный экран."
CONFIRM_DELETE_MESSAGE = "Вы уверены, что хотите удалить это напоминание?"
REMOVE_CONFIRMED_MESSAGE = "Напоминание удалено!"

# Клавиатуры
MAIN_KEYBOARD = [
    [InlineKeyboardButton("Добавить напоминание", callback_data="add")],
    [InlineKeyboardButton("Текущие напоминания", callback_data="list")],
]

ADD_GROUP_KEYBOARD = [
    [InlineKeyboardButton("Следующий шаг", callback_data="next")],
    [InlineKeyboardButton("Добавить ещё группу", callback_data="again")],
]

DATE_FORMAT = "%d.%m.%Y"

# Функция запуска бота
async def start(update: Update, context: CallbackContext):
    """Отправляет сообщение с двумя кнопками."""
    await update.message.reply_text(
        START_MESSAGE, reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD)
    )
    return SELECTING_ACTION

async def show_add_group_prompt(update: Update, context: CallbackContext):
    """Запрашивает название группы."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(ADD_GROUP_MESSAGE)
    return ADD_GROUP_NAME

async def process_group_name(update: Update, context: CallbackContext):
    """Сохраняет название группы и запрашивает дату напоминания."""
    user_data = context.user_data
    group_name = update.message.text.strip()
    if not group_name:
        await update.message.reply_text("Название группы не должно быть пустым.")
        return ADD_GROUP_NAME

    user_data["group_name"] = group_name
    await update.message.reply_text(
        ADD_DATE_MESSAGE, reply_markup=InlineKeyboardMarkup(ADD_GROUP_KEYBOARD)
    )
    return ADD_REMINDER_DATE

async def process_reminder_date(update: Update, context: CallbackContext):
    """Сохраняет дату напоминания и добавляет напоминание в список."""
    user_data = context.user_data
    date_str = update.message.text.strip()
    try:
        reminder_date = datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        await update.message.reply_text(
            f"Неверный формат даты! Пожалуйста, введите дату в формате {DATE_FORMAT}."
        )
        return ADD_REMINDER_DATE

    user_data.setdefault("reminders", []).append(
        {"group_name": user_data.pop("group_name"), "reminder_date": reminder_date}
    )
    await update.message.reply_text(
        "Напоминание успешно добавлено!",
        reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD),
    )
    return SELECTING_ACTION

async def list_reminders(update: Update, context: CallbackContext):
    """Показывает список всех текущих напоминаний."""
    user_data = context.user_data
    reminders = user_data.get("reminders")
    if not reminders:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(NO_REMINDERS_MESSAGE)
        return SELECTING_ACTION

    formatted_reminders = "\n".join(
        f"{idx + 1}. Группа: {r['group_name']} | Дата: {r['reminder_date'].strftime(DATE_FORMAT)}"
        for idx, r in enumerate(reminders)
    )
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        REMINDERS_LIST_MESSAGE.format(formatted_reminders)
    )
    return SELECTING_ACTION

async def select_delete_reminder(update: Update, context: CallbackContext):
    """Предлагает выбрать напоминание для удаления."""
    user_data = context.user_data
    reminders = user_data.get("reminders")
    if not reminders:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(NO_REMINDERS_MESSAGE)
        return SELECTING_ACTION

    keyboard = [
        [InlineKeyboardButton(f"Удалить напоминание {idx + 1}", callback_data=f"delete_{idx}")]
        for idx in range(len(reminders))
    ]
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        DELETE_REMINDER_MESSAGE, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_ACTION

async def confirm_delete_reminder(update: Update, context: CallbackContext):
    """Подтверждает удаление выбранного напоминания."""
    query = update.callback_query
    index = int(query.data.split("_")[1])
    user_data = context.user_data
    reminders = user_data.get("reminders")
    selected_reminder = reminders[index]
    await query.answer()
    await query.edit_message_text(
        CONFIRM_DELETE_MESSAGE,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Да", callback_data=f"confirm_delete_{index}"),
                    InlineKeyboardButton("Отмена", callback_data="cancel_delete"),
                ]
            ]
        ),
    )
    return SELECTING_ACTION

async def cancel_delete_reminder(update: Update, context: CallbackContext):
    """Возвращает на начальный экран после отмены удаления."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Удаление отменено.", reply_markup=InlineKeyboardMarkup(MAIN_KEYBOARD)
    )
    return SELECTING_ACTION

async def execute_delete_reminder(update: Update, context: CallbackContext):
    """Удаляет выбранное напоминание."""
    query = update.callback_query
    index = int(query.data.split("_")[2])
    user_data = context.user_data
    reminders = user_data.get("reminders")
    del reminders[index]
    user_data["reminders"] = reminders
    await query.answer()
    await query.edit_message_text(REMOVE_CONFIRMED_MESSAGE)
    return SELECTING_ACTION

def main():
    """Запускает бота."""
    application = Application.builder().token(API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(show_add_group_prompt, pattern="^add$"),
                CallbackQueryHandler(list_reminders, pattern="^list$"),
                CallbackQueryHandler(select_delete_reminder, pattern="^delete$"),
                CallbackQueryHandler(confirm_delete_reminder, pattern=r"^delete_\d+$"),
                CallbackQueryHandler(execute_delete_reminder, pattern=r"^confirm_delete_\d+$"),
                CallbackQueryHandler(cancel_delete_reminder, pattern="^cancel_delete$"),
            ],
            ADD_GROUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_group_name)],
            ADD_REMINDER_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_reminder_date)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),  # Добавляем сброс состояния при повторном вызове /start
        ],
    )

    application.add_handler(conv_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
