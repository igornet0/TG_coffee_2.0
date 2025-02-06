# обработчики событий, которые относятся к общению бота с пользователем в личке
from asyncio import sleep
from aiogram import F, types, Router
# импортируем систему фильтрации сообщений и для работы с командами
from aiogram.filters import CommandStart
# для работы с асинхронными сессиями
from sqlalchemy.ext.asyncio import AsyncSession

# наши импорты
# импортируем фильтр для определения личка, группа, супергруппа
from filters.chat_types import ChatTypeFilter
# импортируем наши инлайн клавиатуры
from kbds.inline import (
    MenuCallBack, UserCallBack, 
    BackCallBack, ChoiseCallBack, 
    get_back_kbds, type_give)
# импортируем запросы для БД
from database.orm_query import (
    orm_get_user,
    orm_update_user_place,
    orm_add_user,
    orm_update_user_phone,
    User
)
from aiogram.fsm.context import FSMContext
from states.state import UserState
# генератор меню
from handlers.menu_processing import get_menu_content
from . import message_edit

# создаем отдельный роутер для сообщений лички
user_private_router = Router()
# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе)
user_private_router.message.filter(ChatTypeFilter(['private']))

@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # при команде /start определяем уровень 0 и название меню - main (главная страница)

    media, reply_markup, description = await get_menu_content(session, level=0, menu_name="main_start")
    await orm_add_user(session, user_id=message.from_user.id, first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name, phone=None)
        
    await message_edit(message, description, media, reply_markup, edit=False)

async def user_change_place(user: User, id_place: str, session: AsyncSession):
    media, reply_markup, message = await get_menu_content(session, level=0, menu_name="main")
    answer = await get_menu_content(session, level=0.1, menu_name="change_answer")

    await orm_update_user_place(session, user_id=user.user_id, place_id=id_place)
    return media, reply_markup, message, answer

@user_private_router.message(UserState.waiting_for_phone)
async def user_get_phone(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    message_question: types.Message = data["message"]

    if message.contact is None:
        phone = message.text
    else:
        phone = '+' + message.contact.phone_number
    
    await message.delete()

    if len(phone) != 12 or phone[:2] != "+7":
        message = await message.answer("Номер телефона введен неверно!\nФормат: +79999999999")
        await sleep(3)
        await message.delete()
        return
    
    answer = await get_menu_content(session, level=0.1, menu_name="change_answer")
    
    await state.clear()
    await orm_update_user_phone(session, user_id=message.from_user.id, phone=phone)

    await message_question.delete()
    message = await message.answer(answer)
    media, reply_markup, text_message = await get_menu_content(session, level=0, menu_name="main")
    await sleep(2)
    await message_edit(message, text_message, media=media, reply_markup=reply_markup)

@user_private_router.callback_query(UserCallBack.filter())
async def user_local_menu(callback: types.CallbackQuery, 
                          callback_data: UserCallBack, session: AsyncSession, state: FSMContext):

    user = await orm_get_user(session, callback.from_user.id)
    data = callback_data.data.split("_")
    answer = None
    media = None
    
    if "place" in data:
        if "change" in data:
            reply_markup, message = await get_menu_content(session, level=0.1, 
                                                               menu_name="places_change")
        else:
            media, reply_markup, message, answer = await user_change_place(user, data[-1], session)
    
    elif "phone" in data:
        reply_markup, message = await get_menu_content(session, level=0.1,menu_name="phone_change")
        await callback.message.delete()
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.set_state(UserState.waiting_for_phone)
        return
    
    elif "menu" in data:
        media, reply_markup, message = await get_menu_content(session, level=1, 
                                                              menu_name="user_main",
                                                              user=user)
    
    if not answer is None:
        await callback.answer(answer)

    await message_edit(callback.message, message, media=media, reply_markup=reply_markup)

@user_private_router.message(UserState.waiting_text)
async def user_get_text(message: types.Message, session: AsyncSession, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    message_answer:types.Message = data["message"]
    message_output = await message.answer("Записал📝")
    await message_answer.delete()
    await message.answer("Выберите способ получения", reply_markup=type_give(5, message.text))
    await state.clear()
    await message_output.delete()
    return


@user_private_router.callback_query(UserState.waiting_text, BackCallBack.filter())
async def user_queru_back(callback: types.CallbackQuery, 
                    callback_data: MenuCallBack, 
                    session: AsyncSession, state: FSMContext):
    await callback.message.delete()
    await state.clear()

@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, 
                    callback_data: MenuCallBack, 
                    session: AsyncSession, state: FSMContext):
    
    media, reply_markup, *message = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        product_id=callback_data.product_id,
        page=callback_data.page,
        user=callback.from_user.id,
        data=callback_data.data,
        place=callback_data.place
    )

    if len(message) > 1:
        if isinstance(message[1], tuple):
            answer, flag = message[1]
        else:
            answer = message[1]
            flag = False
    else:
        answer = None

    message = message[0]

    if callback_data.menu_name == "choise":
        await state.update_data(category=callback_data.category)

    # elif callback_data.menu_name == "send":
    #     await callback.message.answer(message)

    if message == "phone":
        reply_markup, message = await get_menu_content(session, level=callback_data.level, menu_name="phone_change")
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.set_state(UserState.waiting_for_phone)
        return
    
    if message == "Напишите пожелания по заказу":
        reply_markup = get_back_kbds(callback_data.level, callback_data.menu_name)
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.set_state(UserState.waiting_text)
        return

    if not answer is None:
        await callback.answer(answer)
        if not flag:
            return
    
    await message_edit(callback.message, message, media=media, reply_markup=reply_markup)
    

@user_private_router.callback_query(ChoiseCallBack.filter())
async def add_product(callback: types.CallbackQuery, callback_data: ChoiseCallBack, session: AsyncSession, state: FSMContext):
    message, kb, answer = await get_menu_content(session=session,
                                        level=callback_data.level,
                                         menu_name=callback_data.menu_name,
                                         product_id=callback_data.product_id,
                                         price=callback_data.price,
                                         weight=callback_data.weight,
                                         user=callback.from_user.id,
                                         dop=callback_data.dop,
                                         sirop=callback_data.sirop)
    
    if not answer is None:
        await callback.message.delete()
        return await callback.answer(answer)
    
    await message_edit(callback.message, message, reply_markup=kb)

@user_private_router.message()
async def message_from_user(message: types.Message, session: AsyncSession):
    if not message.via_bot is None and message.via_bot.is_bot:
        id_product, category =list(map(int, message.text.split(".")))

        message_output, kb, _ = await get_menu_content(session=session, level=4, menu_name="add_product",
                                             product_id=id_product)
        
        await message.answer(message_output, reply_markup=kb)
    
    await message.delete()