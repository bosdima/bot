import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я ваш Телеграм-бот.')

# Функция для обработки текстовых сообщений
def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)

# Функция для обработки ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    # Замените токен на ваш
    token = '7909569845:AAE24BA_H1zLmzpLSu6zM8CbmWD-qzG04Uk'
    
    updater = Updater(token, use_context=True)
    
    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    
    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    
    # Обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    
    # Логирование ошибок
    dp.add_error_handler(error)
    
    # Запускаем бота
    updater.start_polling()
    
    # Запускаем обработку событий
    updater.idle()

if __name__ == '__main__':
    main()
