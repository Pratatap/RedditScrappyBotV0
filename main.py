import asyncpraw
import asyncprawcore.exceptions
import post_sorting_kb
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

bot = Bot(token='5517810574:AAGX6ubUUITT_3JqyDcyaFtR-F8yG9r48Xo')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# создаем объект хранящий образ реддита с использованием реддит API
reddit_read_only = asyncpraw.Reddit(client_id="Y-VGlkKs7syagzy9ZhKclA",
                                    client_secret="INQr18dEf5mqN8d995JY6Df4ZoZE_w",
                                    user_agent="TelegramScrappyBot")
amount_submissions_returned = 5
subreddit_global = None


# стартовая функция, задает начальные значения
async def bot_start(self):
    global subreddit_global
    subreddit_global = await reddit_read_only.subreddit("Python")


@dp.message_handler(commands=['start', 'help'])
async def welcome(message: types.Message):
    await message.reply(''' Hello, this is RedditScraperBot, /r/Python is loaded by default,
to choose a different one use /change. 
To change the returned submission amount use /amount''')


class SubredditStates(StatesGroup):
    state = State()
    # state количества постов, которые будут показаны
    amount_to_return = State()


@dp.message_handler(state="*", commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Cancelled')


# смена сабреддита, выбор имени
@dp.message_handler(commands=['change'], state=None)
async def changesubreddit(message: types.Message):
    await SubredditStates.state.set()
    await message.reply('Enter subreddit name')


# сама смена сабреддита, обновление глобальной переменной
@dp.message_handler(state=SubredditStates.state)
async def load_subreddit_name(message: types.Message, state: FSMContext):
    subreddit_name = message.text
    subreddit = await parse_subreddit(subreddit_name, message)
    if subreddit is None:
        return
    await message.reply('Changed to ' + subreddit_name + ' successfully',
                        reply_markup=post_sorting_kb.sorting_type_kb)
    global subreddit_global
    subreddit_global = subreddit
    await state.finish()


# парсим реддит, проверяем, существует ли сабреддит под таким именем
async def parse_subreddit(subreddit_name, message: types.Message):
    try:
        subreddit = await reddit_read_only.subreddit(subreddit_name, fetch=True)
        return subreddit
    except (asyncprawcore.exceptions.NotFound, asyncprawcore.exceptions.Redirect,
            asyncprawcore.exceptions.Forbidden):
        await message.reply("There was a problem with your subreddit")
        return None


# смена количества отобржаемых постов
@dp.message_handler(commands=['amount'], state=None)
async def change_amount_to_return(message: types.Message):
    await SubredditStates.amount_to_return.set()
    await message.reply('Enter amount of submissions to return')


# обработка смены количества, идет проверка на число не число, если меньше 1, тогда остается то же число, свыше 1000
# ставится обратно 1000
@dp.message_handler(state=SubredditStates.amount_to_return)
async def load_amount_to_return(message: types.Message, state: FSMContext):
    global amount_submissions_returned
    if not (message.text.isdigit() or (message.text.startswith("-") and str(message.text[1:]).isdigit())):
        await message.reply("This is not even a number, please enter a valid number")
        return
    if message.text.startswith("-") and (int(message.text[1:]) * -1 <= 0):
        amount_submissions_returned = 5
    elif int(message.text) > 1000:
        amount_submissions_returned = 1000
    else:
        amount_submissions_returned = message.text
    await state.finish()


# возвращаем "горячие посты"
@dp.message_handler(commands='hot')
@dp.message_handler(Text(equals='hot', ignore_case=True))
async def return_hot_posts(message: types.Message):
    subreddit = subreddit_global
    async for submission in subreddit.hot(limit=amount_submissions_returned):
        output = submission.title + "\n" + submission.selftext
        await message.reply(output)


@dp.message_handler(commands='top')
@dp.message_handler(Text(equals='top', ignore_case=True))
async def return_top_posts(message: types.Message):
    subreddit = subreddit_global
    async for submission in subreddit.top(limit=amount_submissions_returned):
        output = submission.title + "\n" + submission.selftext
        await message.reply(output)


@dp.message_handler(commands='new')
@dp.message_handler(Text(equals='new', ignore_case=True))
async def return_new_posts(message: types.Message):
    subreddit = subreddit_global
    async for submission in subreddit.new(limit=amount_submissions_returned):
        output = submission.title + "\n" + submission.selftext
        await message.reply(output)


@dp.message_handler(commands='rising')
@dp.message_handler(Text(equals='rising', ignore_case=True))
async def return_rising_posts(message: types.Message):
    subreddit = subreddit_global
    async for submission in subreddit.rising(limit=amount_submissions_returned):
        output = submission.title + "\n" + submission.selftext
        await message.reply(output)


# чистим хранилище
async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


# оставил для понимания и дань уважения первой написанной функции на питоне
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


# executor.start(dp, bot_start())
executor.start_polling(dp, skip_updates=True, on_startup=bot_start, on_shutdown=shutdown)
