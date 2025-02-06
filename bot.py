from sys import argv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from handlers import order_handler

# наши импорты
# импортируем наш роутер для обработки событий в личке
from handlers.user_private import user_private_router
# импортируем наш роутер для обработки событий в группе
from handlers.user_group import user_group_router
# импортируем наш роутер для администрирования
from handlers.admin_private import admin_router
from handlers.query import query_router
# импортируем функции для работы с БД
from database.engine import create_db, drop_db, session_maker
# импортируем наш промежуточный слой для сессий БД
from middlewares.db import DataBaseSession

# импортируем наши команды для бота (private - для личных сообщений)
# from common.bot_cmds_list import private

# инициализируем класс бота, передаем токен
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# создаем класс диспетчера, который отвечает за фильтрацию разных сообщений (сообщения от сервера telegram)
dp = Dispatcher(storage=MemoryStorage())

# подключаем наши роутеры (работают в том же порядке)
dp.include_routers(query_router, admin_router, user_private_router, user_group_router)

# функция старта
async def on_startup(bot):
    # удалить БД (при изменении моделей или orm)
    # await drop_db()
    # создать БД
    await create_db()


# функция выключения
async def on_shutdown(bot):
    # закрыть соединение с БД
    print("#######################")
    print('#                     #')
    print('#     Бот выключен!   #')
    print('#                     #')
    print("#######################")

# запуск бота
async def main(arguments):
    if 'drop' in arguments:
        await drop_db()
    if not 'start' in arguments:
        return

    # добавляем список id наших администраторов
    bot.my_admins_list = [880629533]
    
    # dp.include_router(order_handler.router)

    # запускаем функцию on_startup при запуске
    dp.startup.register(on_startup)
    # запускаем функцию on_shutdown при выключении
    dp.shutdown.register(on_shutdown)

    # вешаем на событие обновления промежуточный слой (после прохождения фильтров)
    # регистрируем сессию для каждого обработчика
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    # отвечаем только, когда бот онлайн
    await bot.delete_webhook(drop_pending_updates=True)
    # удалить все наши команды для лички
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())

    # отправляем все наши команды, которые будут у бота (только в личке)
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())

    # слушаем сервер telegram и постоянно спрашиваем его про наличие каких-то изменений
    # resolve_used_update_types - все изменения, которые мы используем будут отслеживаться у сервера telegram
    # например, ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']
    # можно добавить skip_events: 'edited_message' - пример, чтобы временно ограничить какие-то события

    print("#######################")
    print('#                     #')
    print('#     Бот запущен!    #')
    print('#                     #')
    print("#######################")

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    import asyncio

    if len(argv) < 2:
        print("Необходимо указать аргумент: 'start' для запуска бота или 'drop' для удаления БД.")
        exit(1)

    arguments = argv[1:]

    if 'start' in arguments or 'drop' in arguments:
        asyncio.run(main(arguments))
    else:
        print("Неизвестный аргумент. Используйте 'start' или 'drop'.")