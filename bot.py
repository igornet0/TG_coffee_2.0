from sys import argv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TOKEN

from handlers.user_private import user_private_router
from handlers.admin_private import admin_router

from database.engine import create_db, drop_db, session_maker
from database.orm_query import (orm_get_orders, orm_get_placelist, orm_update_user_order_status,
                                orm_get_user_carts, orm_get_dop, orm_get_sirop)
from kbds.inline import get_place_order_btns

from middlewares.db import DataBaseSession

# инициализируем класс бота, передаем токен
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# создаем класс диспетчера, который отвечает за фильтрацию разных сообщений (сообщения от сервера telegram)
dp = Dispatcher(storage=MemoryStorage())

# подключаем наши роутеры (работают в том же порядке)
dp.include_routers(admin_router, user_private_router)

async def loop_order(session_maker):
    while True:
        async with session_maker() as session:
            placelist = await orm_get_placelist(session)
            # print(f"{placelist=}")
            for place in placelist:
                orders = await orm_get_orders(session, "send", place.place)
                for order in orders:
                    cards = await orm_get_user_carts(session, order.user_id, order.cards, status="send")
                    message = f"Новый заказ №{order.id}!\n"
                    for i, card in enumerate(cards):
                        message += f"{i+1}.{card.product.name} {card.weight}мл"
                        if card.dop:
                            dop = await orm_get_dop(session, card.dop)
                            message += f"\n\t{dop.name}"
                        if card.sirop:
                            sirop = await orm_get_sirop(session, card.sirop)
                            message += f"\n\tСироп: {sirop.name}"
                        if card.quantity > 1:
                            message += f"\nЦена {card.price}₽ X {card.quantity} = {card.price * card.quantity}₽\n\n"
                        else:
                            message += f"\nЦена {card.price}₽\n\n"

                    message += f"Способ получения - {order.type_give}\n"
                    message += f"Пожелание к заказу - {order.data}\n"
                    message += f"Итоговая цена - {order.summa}₽"
                    await orm_update_user_order_status(session, order.user_id, order.id, "give")
                    kb = get_place_order_btns(order.id)
                    await bot.send_message(place.user_id, message, reply_markup=kb)
        await asyncio.sleep(5)


# функция старта
async def on_startup(bot: Bot):
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
    bot.my_admins_list = [880629533, 5786431448]
    
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

    print("#######################")
    print('#                     #')
    print('#     Бот запущен!    #')
    print('#                     #')
    print("#######################")
    task = asyncio.create_task(loop_order(session_maker))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    task.cancel()


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