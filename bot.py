import random
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot_functions import (engine, session, interface_choice, check_result, DictEditor,
                           WorkingForDictionary, CustomKeyboard, bot_token)
from models import create_tables, Users, Lexicon, User_words

bot = Bot(token=bot_token)
dp = Dispatcher()

create_tables(engine)
variable_storage = MemoryStorage()

print('Start telegram bot...')


class FSMEditDict(StatesGroup):
    action_for_dict = State()
    add_new_word = State()
    add_eng_word = State()
    add_rus_word = State()
    del_eng_word = State()
    del_rus_word = State()
    confirm_del_word = State()


@dp.callback_query(F.data.in_({'edit_dict'}))
async def edit_dict(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMEditDict.action_for_dict)
    LEXICON: dict[str, str] = {
        'add_new_word': '📝 Добавить новое слово',
        'del_word': '⁉️ Удалить слово',
        'exit': '🚪 Выход'}
    await callback.message.answer(
        text='Что вы хотите сделать 👷‍?',
        reply_markup=CustomKeyboard.create_inline_kb
        (1, LEXICON, 'add_new_word', 'del_word', 'exit'))


@dp.callback_query(F.data.in_({'add_new_word'}))
async def add_new_word(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMEditDict.add_eng_word)
    await callback.message.answer(
        text='Введите английское слово: 🇬🇧',
        reply_markup=ReplyKeyboardRemove())


@dp.message(FSMEditDict.add_eng_word)
async def add_eng_word(message: Message, state: FSMContext):
    await state.update_data(eng_word=message.text.lower())
    await state.set_state(FSMEditDict.add_rus_word)
    await message.answer(
        text='Введите русское слово: 🇷🇺')


@dp.message(FSMEditDict.add_rus_word)
async def add_rus_word(message: Message, state: FSMContext):
    await state.update_data(rus_word=message.text.lower())
    editor = DictEditor()
    LEXICON: dict[str, str] = {
        'add_new_word': '📝 Добавить новое слово',
        'del_word': '⁉️ Удалить слово',
        'exit': '🚪 Выход'}
    new_word_in_dict = await state.get_data()
    ru_word = new_word_in_dict['rus_word']
    eng_word = new_word_in_dict['eng_word']
    insert_new_word = editor.add_new_word(eng_word=eng_word, rus_word=ru_word, id_user=str(message.from_user.id))
    await message.answer(
        text=f'{insert_new_word}\n\n'
             f'Что вы хотите сделать ещё? 👷‍',
        reply_markup=CustomKeyboard.create_inline_kb(1, LEXICON, 'add_new_word', 'del_word', 'exit'))

    print(await state.get_data())
    await state.clear()


@dp.callback_query(F.data.in_({'del_word'}))
async def del_word(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMEditDict.del_eng_word)
    await callback.message.answer(
        text='Введите английское слово: 🇬🇧',
        reply_markup=ReplyKeyboardRemove())


@dp.message(FSMEditDict.del_eng_word)
async def del_eng_word(message: Message, state: FSMContext):
    await state.update_data(eng_word=message.text.lower())
    await state.set_state(FSMEditDict.del_rus_word)
    await message.answer(
        text='Введите русское слово: 🇷🇺')


@dp.message(FSMEditDict.del_rus_word)
async def del_rus_word(message: Message, state: FSMContext):
    await state.update_data(rus_word=message.text.lower())
    editor = DictEditor()
    LEXICON: dict[str, str] = {
        'add_new_word': '📝 Добавить новое слово',
        'del_word': '⁉️ Удалить слово',
        'exit': '🚪 Выход'}
    del_word_in_dict = await state.get_data()
    ru_word = del_word_in_dict['rus_word']
    eng_word = del_word_in_dict['eng_word']
    delete_word = editor.delete_word(eng_word=eng_word, rus_word=ru_word, id_user=str(message.from_user.id))
    await message.answer(
        text=f'{delete_word}\n\n'
             f'Что вы хотите сделать ещё? 👷',
        reply_markup=CustomKeyboard.create_inline_kb(1, LEXICON, 'add_new_word', 'del_word', 'exit'))


@dp.callback_query(F.data.in_({'begin_learn_new'}))
async def learn_new_words(callback: CallbackQuery, state: FSMContext):
    rand_words = WorkingForDictionary.random_of_lexicon()
    right_choice = random.choice(rand_words)
    await state.set_state({'status': 'learn_new_words', 'right_choice': right_choice, 'rand_words': rand_words})
    await interface_choice(rand_words, right_choice, callback)


@dp.callback_query(F.data.in_({'repeat_words'}))
async def repeat_words(callback: CallbackQuery, state: FSMContext):
    rand_words = WorkingForDictionary.random_of_user_words(callback.from_user.id)
    right_choice = random.choice(rand_words)
    await state.set_state({'status': 'repeat_words', 'right_choice': right_choice, 'rand_words': rand_words})
    await interface_choice(rand_words, right_choice, callback)


@dp.callback_query(F.data.in_({'next'}))
async def next_question(callback: CallbackQuery, state: FSMContext):
    status = await state.get_state()
    rand_words = WorkingForDictionary.random_of_lexicon()
    right_choice = random.choice(rand_words)
    await interface_choice(rand_words, right_choice, callback)
    await state.set_state({'rand_words': rand_words, 'right_choice': right_choice, 'status': status.get('status')})


@dp.callback_query(F.data.in_({'but_1', 'but_2', 'but_3', 'but_4'}))
async def user_choice(callback: CallbackQuery, state: FSMContext):
    get_info = await state.get_state()
    await check_result(get_info['rand_words'],
                       get_info['right_choice'],
                       callback, get_info['status'])


@dp.callback_query(F.data.in_({'exit'}))
async def choice(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        text='Вы вышли из режима, Чем займёмся теперь?👷',
        reply_markup=CustomKeyboard.start_keyboard()

    )


@dp.callback_query(F.data.in_({'download_dict'}))
async def download_dict(callback: CallbackQuery):
    await callback.message.answer(
        text='Загрузка словаря...⏳',
    )
    await callback.message.answer(
        text=WorkingForDictionary.filing_dict(),
        reply_markup=CustomKeyboard.start_keyboard()
    )


@dp.message(CommandStart())
async def command_start(message: Message):
    keyboard = CustomKeyboard.start_keyboard()
    with session as sn:
        users_in_base = sn.query(Users.id_telegram)
        check_lexicon_dict = sn.query(Lexicon).count()
        check_user_words = sn.query(User_words).count()
        try:
            new_user = Users(id_telegram=message.from_user.id, name=message.chat.username)
            sn.add(new_user)
            sn.commit()
            print(f'User added.\nUsername: {message.chat.username}\nUser ID: {message.from_user.id}')
        except:
            print(f'This user already exists.\nUsername: {message.chat.username}\nUser ID: {message.from_user.id}')
    if check_lexicon_dict == 0:
        await message.answer(
            text='Здравствуйте!👋\n'
                 'Я 🤖 бот предназначенный для изучения английских слов 🇬🇧\n'
                 'Я буду показывать одно слово на русском языке 🇷🇺,\n'
                 'И давать четыре 🔢 варианта ответа на английском,\n'
                 'Вам нужно выбрать правильный вариант ✅.\n\n'
                 'По ходу изучения вам будет открыт режим повторения изученных слов 🔁.\n\n'
                 'Я могу загрузить предустановленный словарь из 2000 английских слов👨‍💻.\n\n'
                 'Также вы можете добавлять новые слова в словарь самостоятельно✍️.\n\n'
                 'Чтобы загрузить словарь, нажмите "Загрузить словарь 📚"\n'
                 'Или "Редактировать словарь ✍️" для добавления новых слов\n\n',
            reply_markup=keyboard)
    elif check_user_words > 50:
        await message.answer(
            text='Здравствуйте! 👋\n'
                 'Я 🤖 бот предназначенный для изучения английских слов 🇬🇧\n'
                 'Я буду показывать одно слово на русском языке 🇷🇺,\n'
                 'И давать четыре 🔢 варианта ответа на английском,\n'
                 'Вам нужно выбрать правильный вариант ✅.\n\n'
                 'По ходу изучения вам будет открыт режим повторения изученных слов 🔁.\n\n'
                 'Также вы можете добавлять новые слова в словарь ✍️\n\n'
                 'Я заметил, что вы уже изучили достаточно новых слов,\n'
                 'Вам доступен режим повторения изученного 🔁, удачи!\n\n'
                 'Если хотите изучить новые слова, нажмите "Начать изучение 👨‍🏫",\n'
                 'Если хотите повторить изученные слова, нажмите "Повторяем изученное 🔁",\n'
                 'Или нажмите "Редактировать словарь ✍️" для добавления новых слов\n\n',
            reply_markup=keyboard)

    else:
        await message.answer(
            text='Здравствуйте! 👋\n'
                 'Я 🤖 бот предназначенный для изучения английских слов 🇬🇧\n'
                 'Я буду показывать одно слово на русском языке 🇷🇺,\n'
                 'И давать четыре 🔢 варианта ответа на английском,\n'
                 'Вам нужно выбрать правильный вариант ✅.\n\n'
                 'По ходу изучения вам будет открыт режим повторения изученных слов 🔁.\n\n'
                 'Также вы можете добавлять новые слова в словарь ✍️\n\n'
                 'Если хотите изучить новые слова, нажмите "Начать изучение 👨‍🏫"\n'
                 'Или нажмите "Редактировать словарь ✍️" для добавления новых слов\n\n',
            reply_markup=keyboard)


if __name__ == '__main__':
    dp.run_polling(bot)
