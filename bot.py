import telebot
import requests
import json
from datetime import datetime, timedelta
import urllib.parse
import qrcode
from io import BytesIO

DOMAIN = 'http://127.0.0.1:8000/'
BOT_TOKEN = '6266043956:AAHtnHEkXDWgoPwe0ERJWUYE-h0Bbeh6VoE'

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
state = ''
current_links = {}
current_link = {}
new_link = {}
current_call = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row('Мої посилання', 'Скоротити посилання')
    tg_id = message.from_user.id
    payload = {'telegram_id':tg_id}
    create = requests.post(DOMAIN+'api/v1/user/create', headers={'Content-Type':'application/json'}, data = json.dumps(payload)).json()
    if tg_id not in user_states:
        user_states[tg_id] = []
    if tg_id not in current_links:
        current_links[tg_id] = []
    if tg_id not in current_link:
        current_link[tg_id] = []
    if tg_id not in new_link:
        current_link[tg_id] = []
    if tg_id not in current_call:
        current_link[tg_id] = []
    global state
    state = 'MainMenu'
    if create['status'] != 'ok':
        bot.reply_to(message, "Вітаю!", reply_markup = user_markup)
    elif create['status'] == 'ok':
        bot.reply_to(message, "Ви були успішно зарєстровані!", reply_markup = user_markup)
    else:
        bot.reply_to(message, "Сталася помилка (((")


@bot.message_handler(func=lambda message: message.text == 'Мої посилання')
def get_links(message):
    raw_json = requests.get(DOMAIN + 'api/v1/link/?user_id=' + str(1)).json()
    change_state(message.chat.id, 'MyLinks')
    current_links[message.chat.id] = raw_json
    link_markup = telebot.types.InlineKeyboardMarkup()
    for i in raw_json:
        url = DOMAIN + i['url']
        link_markup.add(telebot.types.InlineKeyboardButton(url, callback_data=str(i['id'])))
    bot.reply_to(message, "Ваші посилання:" , reply_markup = link_markup, parse_mode="HTML")



@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    change_state(call.message.chat.id, 'LinkCallBack')
    link_id = call.data
    filtered_dict = [d for d in current_links[call.message.chat.id] if d["id"] == int(link_id)]
    link = filtered_dict[0]
    current_link[call.message.chat.id] = link
    current_call[call.message.chat.id] = call
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row('Редагувати', 'Видалити','Статистика','QR Code','Назад')
    response_message = "Скорочене посилання: " + full_link(link['url']) + "\nОригінальне посилання: " + link['redirect_url']
    bot.reply_to(call.message,response_message, reply_markup=user_markup, parse_mode="HTML")


@bot.message_handler(func=lambda message: message.text == 'Редагувати')
def edit_link(message):
    chat_id = message.chat.id
    change_state(chat_id, 'EditLink')
    edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    edit_link_markup.row('URL', 'Оригінальне посилання','Назад')
    bot.send_message(chat_id, 'Оберіть що потрібно змінити', reply_markup=edit_link_markup)

@bot.message_handler(func=lambda message: message.text == 'URL')
def edit_url(message):
    chat_id = message.chat.id
    change_state(chat_id, 'EditUrl')
    edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    edit_link_markup.row('Назад')
    msg = bot.reply_to(message, 'Введіть новий url', reply_markup=edit_link_markup)
    bot.register_next_step_handler(msg, edit_url2)

def edit_url2(message):
    if message.text == 'Назад':
        print(user_states[message.chat.id])
        handle_back(message)
        return
    update_url = message.text
    link = current_link[message.chat.id]
    update_link = link
    update_link['url'] = update_url
    json_data = json.dumps(update_link)
    response = requests.put(DOMAIN + "api/v1/link/" + str(link['id']) + "/update", headers={'Content-Type':'application/json'}, data = json_data)
    if response.status_code == 200:
        bot.reply_to(message, 'Url був успішно змінений!')
        send_welcome(message)
    else:
        bot.reply_to(message, 'Така адреса не коректна або вона вже існує')
        edit_url(message)

@bot.message_handler(func=lambda message: message.text == 'Оригінальне посилання')
def edit_orig(message):
    chat_id = message.chat.id
    change_state(chat_id, 'EditOrig')
    edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    edit_link_markup.row('Назад')
    msg = bot.reply_to(message, 'Введіть нове посилання', reply_markup=edit_link_markup)
    bot.register_next_step_handler(msg, edit_orig2)

def edit_orig2(message):
    if message.text == 'Назад':
        handle_back(message)
        return
    update_redirect = message.text
    link = current_link[message.chat.id]
    update_link = link
    update_link['redirect_url'] = update_redirect
    json_data = json.dumps(update_link)
    response = requests.put(DOMAIN + "api/v1/link/" + str(link['id']) + "/update", headers={'Content-Type':'application/json'}, data = json_data)
    if response.status_code == 200:
        bot.reply_to(message, 'Посилання було успішно змінено!')
        send_welcome(message)
    else:
        bot.reply_to(message, 'Така адреса не коректна')
        edit_orig(message)

@bot.message_handler(func=lambda message: message.text == 'Видалити')
def delete_link(message):
    chat_id = message.chat.id
    change_state(chat_id, 'DeleteLink')
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Так', 'Ні')
    msg = bot.reply_to(message, 'Ви впевнені що хочете видалити це посилання?', reply_markup=markup)
    bot.register_next_step_handler(msg, delete_link2)

def delete_link2(message):
    if message.text == 'Ні':
        handle_back(message)
        return
    chat_id = message.chat.id
    answer = message.text
    if answer == 'Так':
        link_id = current_link[message.chat.id]['id']
        response = requests.delete(DOMAIN+"api/v1/link/" + str(link_id) + "/delete")
        if response.status_code == 204:
            bot.reply_to(message, 'Посилання успішно видалено!')
            send_welcome(message)
        else:
            get_links(message)
    elif answer == 'Ні':
        get_links(message)

@bot.message_handler(func=lambda message: message.text == 'Скоротити посилання')
def cut_link(message):
    chat_id = message.chat.id
    change_state(chat_id, 'CutLink')
    edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    edit_link_markup.row('Назад')
    msg = bot.reply_to(message, 'Введіть посилання яке потрібно скоротити', reply_markup=edit_link_markup)
    bot.register_next_step_handler(msg, cut_link_step1)

def cut_link_step1(message):
    redirect_link = message.text
    if redirect_link == 'Назад':
        send_welcome(message)
        return
    new_link[message.chat.id] = {'redirect_link':redirect_link, 'my_link':''}
    edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    edit_link_markup.row('Назад')
    msg = bot.reply_to(message, 'Введіть закінчення яке хочете мати у вашого нового посилання', reply_markup=edit_link_markup)
    bot.register_next_step_handler(msg, cut_link_step2)
def cut_link_step2(message):
    backhalf_link = message.text
    if message.text == 'Назад':
        message.text = new_link[message.chat.id]['redirect_link']
        cut_link(message)
        return
    new_link[message.chat.id]['my_link'] = backhalf_link
    data = {'url':backhalf_link, 'telegram_id': message.chat.id, 'reidrect_url': new_link[message.chat.id]['redirect_link']}
    json_data = json.dumps(data)
    response = requests.post(DOMAIN + "api/v1/link/", headers={'Content-Type':'application/json'}, data = json_data)
    if response.status_code == 200:
        edit_link_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        edit_link_markup.row('Назад')
        msg = bot.reply_to(message, 'Ваше скорочене посилання було успішно створено!', reply_markup=edit_link_markup)
        send_welcome(message)
    else:
        msg = bot.reply_to(message, 'Ваші дані некоректні, давайте спробуємо ще')
        bot.register_next_step_handler(message, cut_link)



@bot.message_handler(func=lambda message: message.text == 'Статистика')
def stats(message):
    chat_id = message.chat.id
    change_state(chat_id, 'Stats')
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Коротка статистика', 'Детальна статистика', 'Назад')
    msg = bot.reply_to(message, 'Оберіть яку саме статистику ви хочете отримати', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Детальна статистика')
def detailed_stats(message):
    chat_id = message.chat.id
    change_state(chat_id, 'DetailedStats')
    link = current_link[message.chat.id]
    url = link['url']
    date_to = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+"+03:00"
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+"+03:00"
    date_from = urllib.parse.quote_plus(date_from)
    date_to = urllib.parse.quote_plus(date_to)
    stat_link = DOMAIN + "?link=" + url +"&date_from=" + date_from + "&date_to=" + date_to
    keyboard = telebot.types.InlineKeyboardMarkup()
    url_button = telebot.types.InlineKeyboardButton(text='Перейти', url=stat_link)
    keyboard.add(url_button)
    bot.send_message(message.chat.id, 'Натисніть на кнопку для перегляду статистики', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'QR Code')
def get_qr(message):
    link = DOMAIN + current_link[message.chat.id]['url']
    qr_code = create_qr_code(link)
    photo = BytesIO()
    qr_code.save(photo, 'PNG')
    photo.seek(0)
    bot.send_photo(message.chat.id, photo)

@bot.message_handler(func=lambda message: message.text == 'Назад')
def handle_back(message):
    chat_id = message.chat.id
    print(user_states[chat_id])
    global state
    print("State "+ state)
    state = ""
    current_state = user_states[chat_id].pop()
    if current_state == 'MainMenu':
        send_welcome(message)
    elif current_state == 'EditUrl':
        edit_link(message)
    elif current_state == 'EditOrig':
        edit_link(message)
    elif current_state == 'EditLink':
        edit_link(message)
    elif current_state == 'DeleteLink':
        handle_callback_query(current_call[message.chat.id])
    elif current_state == 'MyLinks':
        handle_callback_query(current_call[message.chat.id])
    elif current_state == 'Stats':
        handle_callback_query(current_call[message.chat.id])
    elif current_state == 'CutLink':
        cut_link(message)
    elif current_state == 'DetailedStats':
        detailed_stats(message)
    elif current_state == 'LinkCallBack':
        handle_callback_query(current_call[message.chat.id])

def change_state(chat_id, state_new):
    global state
    if state == "":
        state = "CHANGE"
        return
    elif state == "CHANGE":
        state = state_new
        return
    user_states[chat_id].append(state)
    state = state_new


def full_link(url):
    return DOMAIN+url
def create_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    qr_code = qr.make_image(fill_color="black", back_color="white")
    return qr_code
bot.infinity_polling()