# обработчики событий, которые относятся к общению бота с пользователем в личке
from asyncio import sleep
from aiogram import types, Router, F, Bot
# импортируем систему фильтрации сообщений и для работы с командами
from aiogram.filters import CommandStart, StateFilter
# для работы с асинхронными сессиями
from sqlalchemy.ext.asyncio import AsyncSession

# наши импорты
# импортируем фильтр для определения личка, группа, супергруппа
from filters.chat_types import ChatTypeFilter
# импортируем наши инлайн клавиатуры
from kbds.inline import (
    MenuCallBack, UserCallBack, PlaceCallBack,
    BackCallBack, ChoiseCallBack, 
    get_back_kbds, type_give)

# импортируем запросы для БД
from database.orm_query import (
    orm_get_user,
    orm_add_user,
    orm_get_user_order,
    orm_update_user_phone
)
from aiogram.fsm.context import FSMContext
from states.state import UserState, PlaceState
# генератор меню
from handlers.menu_processing import get_menu_content
from handlers.place_processing import get_place_content
from . import message_edit

from config import BUFFER_KEY

# создаем отдельный роутер для сообщений лички
user_private_router = Router()

# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе)
user_private_router.message.filter(ChatTypeFilter(['private']))

@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # при команде /start определяем уровень 0 и название меню - main (главная страница)
    if message.text.split()[-1] in BUFFER_KEY:
        data = await get_menu_content(session=session, level=-1, user_id=message.from_user.id,
                                      menu_name="add_place")
    else:
        data = await get_menu_content(session, level=0, 
                                      menu_name="main_start")
    reply_markup = data["kbds"]
    description = data["message"]
    await orm_add_user(session, user_id=message.from_user.id, first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name, phone=None)
        
    await message_edit(message, description, reply_markup, edit=False)

@user_private_router.message(UserState.waiting_for_phone)
async def user_get_phone(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    from_user = data["type"]
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
    
    data = await get_menu_content(session, level=1, menu_name="change_answer")

    answer = data.get("answer")
    
    await state.clear()
    await orm_update_user_phone(session, user_id=message.from_user.id, phone=phone)

    await message_question.delete()
    message = await message.answer(answer)
    if from_user == "user":
        data = await get_menu_content(session, level=0, menu_name="main")
        reply_markup = data.get("kbds")
        text_message = data.get("message")
        await sleep(1)
        await message_edit(message, text_message, reply_markup=reply_markup)
    else:
        await message.delete()

@user_private_router.callback_query(UserCallBack.filter())
async def user_local_menu(callback: types.CallbackQuery, 
                          callback_data: UserCallBack, session: AsyncSession, state: FSMContext):

    user = await orm_get_user(session, callback.from_user.id)
    data = callback_data.data.split("_")
    answer = None
    
    if "phone" in data:
        data = await get_menu_content(session, level=1,menu_name="phone_change")
        reply_markup = data.get("kbds")
        message = data.get("message")
        await callback.message.delete()
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.update_data(type="user")
        await state.set_state(UserState.waiting_for_phone)
        return
    
    elif "menu" in data:
        data = await get_menu_content(session, level=3, 
                                                              menu_name="user_main",
                                                              user_id=user)
        reply_markup = data.get("kbds")
        message = data.get("message")
    
    if not answer is None:
        await callback.answer(answer)

    await message_edit(callback.message, message, reply_markup=reply_markup)

@user_private_router.message(UserState.waiting_text)
async def user_get_text(message: types.Message, session: AsyncSession, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    message_answer:types.Message = data["message"]
    callback_message_answer:types.Message = data["callback_message"]
    order_id = data["order_id"]
    message_output = await message.answer("Записал📝")
    await message_answer.delete()
    await message_edit(callback_message_answer, "Выберите способ получения", type_give(6, message.text, order_id))
    await state.clear()
    await message_output.delete()
    return

@user_private_router.callback_query(UserState.waiting_text, BackCallBack.filter())
async def user_queru_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()

@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, 
                    callback_data: MenuCallBack, 
                    session: AsyncSession, state: FSMContext):
    
    data = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        podcategory=callback_data.podcategory,
        product_id=callback_data.product_id,
        page=callback_data.page,
        user_id=callback.from_user.id,
        data=callback_data.data,
        place=callback_data.place,
        order_id=callback_data.order_id
    )

    media = data.get("image")
    reply_markup = data.get("kbds")
    message = data.get("message")
    answer = data.get("answer")
    flag = data.get("answer_flag", False)
    edit = data.get("edit", True)

    if callback_data.level == -1 and callback_data.menu_name == "add":
        await state.update_data(callback_message=callback.message)
        await state.set_state(PlaceState.waiting_place)

    if callback_data.menu_name == "choise":
        await state.update_data(category=callback_data.category)

    if message == "phone":
        data = await get_menu_content(session, level=callback_data.level, menu_name="phone_change")
        reply_markup = data.get("kbds")
        message = data.get("message")
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.update_data(type="cart")
        await state.set_state(UserState.waiting_for_phone)
        return
    
    if message == "Напишите пожелания по заказу":
        reply_markup = get_back_kbds(callback_data.level, callback_data.menu_name)
        message = await callback.message.answer(message, reply_markup=reply_markup)
        await state.update_data(message=message)
        await state.update_data(callback_message=callback.message)
        await state.update_data(order_id=callback_data.order_id)
        await state.set_state(UserState.waiting_text)
        return

    if not answer is None:
        await callback.answer(answer)
        if not flag:
            return
    
    await message_edit(callback.message, message, media=media, reply_markup=reply_markup, edit=edit)
    
@user_private_router.callback_query(ChoiseCallBack.filter())
async def add_product(callback: types.CallbackQuery, callback_data: ChoiseCallBack, session: AsyncSession, state: FSMContext):
    data = await get_menu_content(session=session,
                                        level=callback_data.level,
                                         menu_name=callback_data.menu_name,
                                         product_id=callback_data.product_id,
                                         price=callback_data.price,
                                         weight=callback_data.weight,
                                         place=callback_data.place,
                                         user_id=callback.from_user.id,
                                         dop=callback_data.dop,
                                         sirop=callback_data.sirop)
    
    kb = data.get("kbds")
    message = data.get("message")
    answer = data.get("answer")
    
    if not answer is None:
        # await callback.message.delete()
        await callback.answer(answer)
    
    await message_edit(callback.message, message, reply_markup=kb)

@user_private_router.callback_query(PlaceCallBack.filter())
async def add_place(callback: types.CallbackQuery, callback_data: PlaceCallBack, session: AsyncSession, state: FSMContext, bot: Bot):
    data = await get_place_content(session=session,
                                        level=callback_data.level,
                                         menu_name=callback_data.menu_name,
                                         place_name=callback_data.place_name,
                                         categoris_choise=callback_data.categoris_choise,
                                         category=callback_data.category,
                                         order_id=callback_data.order_id,
                                         user_id=callback.from_user.id)
        
    kb = data.get("kbds")
    message = data.get("message")
    answer = data.get("answer")
    
    if callback_data.order_id:
        order = await orm_get_user_order(session, order_id=callback_data.order_id)
        await bot.send_message(order.user_id, answer)

    if not answer is None:
        await callback.answer(answer)
    
    await message_edit(callback.message, message, reply_markup=kb)

@user_private_router.message(PlaceState.waiting_place)
async def place_get_name(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    callback_message_answer:types.Message = data["callback_message"]
    await message.delete()
    name = message.text
    data = await get_place_content(session, -2, "add_place", name, "")
    message_answer = data.get("message")
    kbds = data.get("kbds")

    await message_edit(callback_message_answer, message_answer, kbds)
    await state.clear()

@user_private_router.message(StateFilter(None), F.text)
async def message_from_user(message: types.Message):
    await message.delete()