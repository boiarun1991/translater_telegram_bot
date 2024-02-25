import configparser
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.sql.expression import func
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import Lexicon, User_words
import requests
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read('config.ini')
bot_token = config['params']['bot_token']
user = config['params']['user']
password = config['params']['password']
host = config['params']['host']
port = config['params']['port']
base_name = config['params']['base_name']

DSN = f'postgresql://{user}:{password}@{host}:{port}/{base_name}'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


class WorkingForDictionary:
    @staticmethod
    def filing_dict():
        rs = requests.get('http://www.7english.ru/dictionary.php?id=2000&letter=all')
        root = BeautifulSoup(rs.content, 'html.parser')
        for tr in root.select('tr[onmouseover]'):
            td_list = [td.text.strip() for td in tr.select('td')]
            if len(td_list) != 9 or not td_list[1] or not td_list[5]:
                continue
            en = td_list[1]
            ru = td_list[5].split(', ')[0]
            with session as sn:
                lexicon = Lexicon(eng_word=en, rus_word=ru)
                sn.add(lexicon)
                sn.commit()
        print('Dictionary is empty. Filling...')
        return '📚 Словарь успешно загружен ✅, Вы можете приступать к изучению новых слов! 📖'

    @staticmethod
    def random_of_lexicon():
        with session as sn:
            query = sn.query(Lexicon.eng_word, Lexicon.rus_word, Lexicon.id).order_by(func.random()).limit(4).all()
        return query

    @staticmethod
    def random_of_user_words(id_user):
        try:
            with session as sn:
                query = sn.query(Lexicon.eng_word, Lexicon.rus_word, User_words.id_lexicon) \
                    .join(Lexicon).filter(User_words.id_user == str(id_user), Lexicon.id == User_words.id_lexicon) \
                    .order_by(func.random()).limit(4).all()

            return query
        except:
            print('Words not found')


class CustomKeyboard:
    @staticmethod
    def start_keyboard():
        with session as sn:
            check_user_words = sn.query(User_words).count()
            check_lexicon_dict = sn.query(Lexicon).count()
        learn_new_words = InlineKeyboardButton(
            text='Начать изучение 👨🏻‍🏫',
            callback_data='begin_learn_new'
        )

        edit_dict = InlineKeyboardButton(
            text='Редактировать словарь ✍️',
            callback_data='edit_dict'
        )

        repeat_words = InlineKeyboardButton(
            text='Повторяем изученое 📖',
            callback_data='repeat_words'
        )
        download_dict = InlineKeyboardButton(
            text='Загрузить словарь 📚',
            callback_data='download_dict'
        )
        if check_user_words > 50:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[learn_new_words],
                                 [repeat_words],
                                 [edit_dict]])
        elif check_lexicon_dict == 0:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[download_dict],
                                 [edit_dict]])
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[learn_new_words],
                                 [edit_dict]]
            )
        return keyboard

    @staticmethod
    def create_inline_kb(width: int,
                         LEXICON,
                         *args: str) -> InlineKeyboardMarkup:
        kb_builder = InlineKeyboardBuilder()
        buttons: list[InlineKeyboardButton] = []
        if args:
            for button in args:
                buttons.append(InlineKeyboardButton(
                    text=LEXICON[button] if button in LEXICON else button,
                    callback_data=button))
        kb_builder.row(*buttons, width=width)
        return kb_builder.as_markup()


class DictEditor:
    @staticmethod
    def insert_user_word(id_user, id_lex, status):
        with session as sn:
            added_words = User_words(id_user=id_user, id_lexicon=id_lex, status=status)
            sn.add(added_words)
            sn.commit()
            print(f"A new word has been added to the user's dictionary")

    @staticmethod
    def update_status_word(id_user, id_lex, status):
        with session as sn:
            try:
                update_word = sn.query(User_words).filter(User_words.id_lexicon == id_lex,
                                                          User_words.id_user == id_user).update({'status': status})
                sn.commit()
                print(f"A word has been updated in the user's dictionary")
            except:
                print('The word has already been learned')

    @staticmethod
    def add_new_word(eng_word, rus_word, id_user):
        with session as sn:
            check_word = sn.query(Lexicon). \
                filter(Lexicon.eng_word == eng_word,
                       Lexicon.rus_word == rus_word).count()
            if check_word == 0:
                new_word = Lexicon(eng_word=eng_word, rus_word=rus_word, id_user=id_user)
                sn.add(new_word)
                sn.commit()
                return f'Слово "🇬🇧 {eng_word.capitalize()} - 🇷🇺 {rus_word.capitalize()}" ✅ добавлено в Ваш словарь'
                print(f"A new word has been added to the dictionary")
            else:
                return 'Такое слово уже есть в словаре 😎'

    @staticmethod
    def delete_word(eng_word, rus_word, id_user):
        with session as sn:
            check_word = sn.query(Lexicon).filter(Lexicon.id_user == id_user,
                                                  Lexicon.rus_word == rus_word,
                                                  Lexicon.eng_word == eng_word).count()
            if check_word > 0:
                delete_word = sn.query(Lexicon). \
                    filter(Lexicon.eng_word == eng_word,
                           Lexicon.rus_word == rus_word,
                           Lexicon.id_user == id_user).delete()
                sn.commit()
                return f'Слово "🇬🇧 {eng_word.capitalize()} - 🇷🇺 {rus_word.capitalize()}" удалено из Вашего словаря 🚫'
            else:
                return 'Такого слова нет в словаре или это слово добавлено не вами. 🤷‍♂️'


async def interface_choice(rand_words, right_choice, callback):
    LEXICON: dict[str, str] = {
        'but_1': f'1️⃣ {rand_words[0][0].capitalize()}',
        'but_2': f'2️⃣ {rand_words[1][0].capitalize()}',
        'but_3': f'3️⃣ {rand_words[2][0].capitalize()}',
        'but_4': f'4️⃣ {rand_words[3][0].capitalize()}',
        'exit': '🚪 Выход',
        'next': 'Дальше ➡️'}

    keyboard_words = CustomKeyboard.create_inline_kb(2, LEXICON, 'but_1', 'but_2', 'but_3', 'but_4', 'exit',
                                                     'next')
    await callback.message.edit_text(
        text=f'Выберите правильный вариант перевода слова - "{right_choice[1].capitalize()} 🇬🇧"? 🤔',
        reply_markup=keyboard_words)


async def check_result(rand_word, right_choice, callback, status):
    editor = DictEditor()
    LEXICON: dict[str, str] = {
        'next': 'Дальше ➡️',
        'exit': '🚪 Выход'}
    callback_choice = callback.message.reply_markup.inline_keyboard[0:2]
    variants = {}
    for item in callback_choice:
        for text in item:
            if text == text:
                variants.setdefault(text.callback_data, text.text.lower())
    if status == 'learn_new_words':
        if right_choice[0] in variants.get(callback.data):
            add_user_words = editor.insert_user_word(
                id_user=callback.from_user.id,
                id_lex=right_choice[2],
                status=True)
            keyboard_r = CustomKeyboard.create_inline_kb(1, LEXICON, 'next', 'exit')
            await callback.message.edit_text(
                text=f'🧐 Отлично! Это правильный ответ! ✔️\n\n'
                     f'"{right_choice[0].capitalize()} 🇬🇧" переводится как "{right_choice[1].capitalize()} 🇷🇺"\n'
                     f'Идём дальше? 🤔\n\n'
                     f'Нажмите "Дальше ➡️" для продолжения или "🚪 Выход" чтобы выйти из режима изучения',
                reply_markup=keyboard_r)
        else:
            add_user_words = editor.insert_user_word(
                id_user=callback.from_user.id,
                id_lex=right_choice[2],
                status=False)
            keyboard_r = CustomKeyboard.create_inline_kb(1, LEXICON, 'next', 'exit')
            await callback.message.edit_text(
                text=f'К сожалению, неправильно\n\n'
                     f'"{right_choice[1].capitalize()} 🇬🇧" переводится как "{right_choice[0].capitalize()} 🇷🇺"\n\n'
                     f'Запоминаем и идём дальше? 🤔\n\n'
                     f'Нажмите "Дальше ➡️" для продолжения или "🚪 Выход" чтобы выйти из режима изучения',
                reply_markup=keyboard_r)
    if status == 'repeat_words':
        if right_choice[0] in variants.get(callback.data):
            editor.update_status_word(callback.from_user.id, right_choice[2], True)
            keyboard_r = CustomKeyboard.create_inline_kb(LEXICON, 'next', 'exit')
            await callback.message.edit_text(
                text=f'🧐 Отлично! Это правильный ответ! ✔️\n\n'
                     f'"{right_choice[0].capitalize()} 🇬🇧" переводится как "{right_choice[1].capitalize()} 🇷🇺"\n'
                     f'Идём дальше? 🤔\n\n'
                     f'Нажмите "Дальше ➡️" для продолжения или "🚪 Выход" чтобы выйти из режима изучения',
                reply_markup=keyboard_r)
        else:
            keyboard_r = CustomKeyboard.create_inline_kb(1, LEXICON, 'next', 'exit')
            await callback.message.edit_text(
                text=f'К сожалению, неправильно\n\n'
                     f'"{right_choice[1].capitalize()} 🇬🇧" переводится как "{right_choice[0].capitalize()} 🇷🇺"\n\n'
                     f'Запоминаем и идём дальше? 🤔\n\n'
                     f'Нажмите "Дальше ➡️" для продолжения или "🚪 Выход" чтобы выйти из режима изучения',
                reply_markup=keyboard_r)
