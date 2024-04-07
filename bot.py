import telebot
import logging
import config
from speech import TTS
from data_base import DataBase

TTS = TTS()
db = DataBase()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.log",
    filemode="a",
    datefmt="%Y-%m-%d %H:%M:%S"
)

bot = telebot.TeleBot(token=config.TOKEN)

logging.info("Бот начал работу")


# все команды бота
bot.set_my_commands([
    telebot.types.BotCommand('start', 'Начать'),
    telebot.types.BotCommand('help', 'Помощь'),
    telebot.types.BotCommand('about', 'Расскажу о себе'),
    telebot.types.BotCommand('tts', 'Озвучу твой текст')
])


db.create_table()
db.create_table_history()
db.create_table_token_usage()
db.insert_token_usage_data(0)

logging.info("Бот подготовился")
print("Бот подготовлен")


# список команд для команды help
commands = {
    '/start': 'Начать общение с ботом',
    '/help': 'Показать все команды',
    '/about': 'Расскажу о себе',
    '/tts': "Озвучу твой текст"
}


# проверяет есть ли пользователь. Сбрасывает данные
def user_check(message):
    user_id = get_id(message)
    db.add_user(user_id, message.from_user.first_name)
    data = db.get_data_for_user(user_id)
    return data


# возвращает id пользователя
def get_id(message):
    return int(message.chat.id)


# обработки команды start
@bot.message_handler(commands=['start'])
def start_message(message):
    data = user_check(message)
    bot.send_message(message.chat.id,'Привет')
    bot.send_message(message.chat.id, "Напиши /help для помощи!")


# обработка команды help
@bot.message_handler(commands=['help'])
def help_message(message):
    text = "Вот список команд, которые я могу выполнить:\n"
    for command, description in commands.items():
        text += f'{command} - {description}\n'
    bot.send_message(message.chat.id, text)


# обработка команды about
@bot.message_handler(commands=['about'])
def about_message(message):
    bot.send_message(message.chat.id, config.ABOUTS)


# обработка команды tts
@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = get_id(message)
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts)


# обработка текста для озвучки
def tts(message):
    data = user_check(message)
    user_id = get_id(message)
    tokens = db.get_token_usage()
    if tokens >= config.MAX_TOKENS:
        bot.send_message(message.chat.id, "Достигнут лимит токенов бота. Генерация сценариев завершена.")
        return
    else:
        json, token1 = TTS.make_json(message.text)
        full_response = TTS.send_request(json)
        response = TTS.process_resp(full_response)
        if not response[0]:
            bot.send_message(message.chat.id, response[1])
            logging.error(response[1])
        else:
            db.add_history(user_id, message.from_user.first_name, message.text, token1)
            db.update_data(user_id, "tts_symbols", data['tts_symbols'] + token1)
            db.update_usage_token(db.get_token_usage() + token1)
            with open("output.ogg", "wb") as audio_file:
                audio_file.write(response[1])
            with open("output.ogg", "rb") as audio_file:
                bot.send_voice(message.chat.id, audio_file)
            logging.info("Бот закончил синтез")


# обработка текстовых запросов
@bot.message_handler(content_types=['text'])
def text_func(message):
    bot.send_message(message.chat.id, "Я тебя не понял!")

bot.polling()