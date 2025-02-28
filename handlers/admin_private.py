# админка
from asyncio import sleep
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
# импортируем машину состояний
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# для работы с асинхронными сессиями
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOTNAME, BUFFER_KEY
# наши импорты
from filters.chat_types import ChatTypeFilter, IsAdmin
# генератор inline клавиатур
from kbds.admin_inline import AdminCallBack, get_admin_catalog_btns
# импортируем запросы для БД
from database.orm_query import (
    orm_add_podcatalog,
    orm_change_product,
    orn_add_product,
    orm_edit_category_photo,
    orm_change_banner_text,
    orm_get_info_pages,
    orm_get_product,
    orm_get_products,
    orm_change_product,
    orm_add_category,
    orm_get_banners,
    orm_add_category,
    orm_get_banner,
)

from . import message_edit
from handlers.admin_processing import *

# создаём роутер для админки
admin_router = Router()
# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе), добавляем проверку
# является ли пользователь админом
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

class AddCategory(StatesGroup):
    image = State()
    podcatalog = State()
    weight = State()
    price = State()
    product_name = State()
    product_weight = State()
    product_price = State()

class ChangeBanner(StatesGroup):

    banner_description = State()

# при новом запуске бота, нужно прописывать в группе c админами команду /admin, чтобы все администраторы получили доступ к админке
@admin_router.message(Command("admin"))
async def admin_main(message: types.Message):
    await message.answer("Что хотите сделать ❓", reply_markup=ADMIN_KB)

@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    data = await get_admin_menu(session=session,
                                level=1,
                                menu_name="catalog")
    
    kb = data.get("kbds")
    message_answer = data.get("message")
    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(F.text == 'Добавить/Изменить баннер')
async def admin_features(message: types.Message, session: AsyncSession):
    data = await get_admin_menu(session=session,
                                level=3,
                                menu_name="banner")
    
    kb = data.get("kbds")
    message_answer = data.get("message")
    await message.answer(message_answer, reply_markup=kb)

@admin_router.callback_query(AdminCallBack.filter())
async def add_product(callback: types.CallbackQuery, callback_data: AdminCallBack, session: AsyncSession, state: FSMContext):
    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name=callback_data.menu_name,
                                category=callback_data.category,
                                podcategory=callback_data.podcategory,
                                product_id=callback_data.product_id)
    
    kb = data.get("kbds")
    message = data.get("message")
    answer = data.get("answer")
    state_data = data.get("state")

    if not state_data is None:
        await state.update_data(callback_data=callback_data)

        if "podcatalog" in state_data and "add" in state_data:   
            await state.set_state(AddCategory.podcatalog)
        elif "catalog" in state_data and "add" in state_data:
            await state.set_state(AddCategory.image)
        elif "value" in state_data:
            await state.set_state(AddCategory.weight)
        elif "product" in state_data and "add" in state_data:   
            if "price" in state_data and "back" in state_data:
                await state.set_state(AddCategory.product_price)
            else:
                await state.set_state(AddCategory.product_name)
        elif "price" in state_data:
            await state.set_state(AddCategory.price)
        elif "banner" in state_data:
            await state.set_state(ChangeBanner.banner_description)
    else:
        await state.clear()

    if not answer is None:
        await callback.answer(answer)
    
    await message_edit(callback.message, message, reply_markup=kb)

@admin_router.message(F.text == 'Добавить кофейню')
async def admin_add_cafe(message: types.Message, session: AsyncSession):
    global BUFFER_KEY

    key = generate_random_word(6)
    URL = f"https://t.me/{BOTNAME.replace("@", "")}?start={key}"
    if len(BUFFER_KEY) >= 10:
        BUFFER_KEY = []
    BUFFER_KEY.append(key)

    await message.answer(f"Отправти эту ссылку ТГ кофейни {URL}")

@admin_router.message(AddCategory.image, F.photo)
async def admin_add_category(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data: AdminCallBack = data["callback_data"]

    image_id = message.photo[-1].file_id
    if "change" in callback_data.menu_name:
        await orm_edit_category_photo(session, callback_data.category, image_id)
        await message.answer("✅ Изменил")
    else:
        name_category = message.caption
        await orm_add_category(session, name_category, image_id)
        await message.answer("✅ Добавил")
    
    await state.clear()

    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="category",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory,
                                product_id=callback_data.product_id)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(AddCategory.podcatalog, F.text)
async def admin_add_podcatalog(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    name_category = message.text

    await orm_add_podcatalog(session, name_category, callback_data.category)
    await message.answer("✅ Добавил")
    await state.clear()

    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="podcatalog",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory,
                                product_id=callback_data.product_id)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(AddCategory.product_name, F.text)
async def admin_add_product(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    product_name = message.text
    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="add_price",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory)
    
    kb = data.get("kbds")
    message_answer = data.get("message")
    state_data = data.get("state")
    if not state_data is None and "next" in state_data:
        await state.set_state(AddCategory.product_price)
        await state.update_data(callback_data=callback_data)
    else:
        await state.clear()

    await message.answer(message_answer, reply_markup=kb)

    await state.update_data(product_name=product_name)
    # kb = get_cancel_btns(level=callback_data.level, menu_name="product", category=callback_data.category,podcategory=callback_data.podcategory)
    # await message.answer("Введите цену товару, если несколько цен, введите их через /", reply_markup=kb)
    # await state.set_state(AddCategory.product_price)

@admin_router.message(AddCategory.product_price, F.text)
async def admin_add_product(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    product_price = message.text

    if not product_price.replace("/", "").isdigit():
        message_answer = await message.answer("Ошибка ввода, повторите попытку!")
        await message.delete()
        await sleep(1)
        await message_answer.delete()
        return
    
    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="add_weight",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory)
    
    kb = data.get("kbds")
    message_answer = data.get("message")
    state_data = data.get("state")
    if not state_data is None and "next" in state_data:
        await state.set_state(AddCategory.product_weight)
        await state.update_data(callback_data=callback_data)
    else:
        await state.clear()

    await message.answer(message_answer, reply_markup=kb)

    await state.update_data(product_price=product_price)

@admin_router.message(AddCategory.product_weight, F.text)
async def admin_add_podcatalog(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    weight = message.text
    if not weight.replace("/", "").isdigit():
        message_answer = await message.answer("Ошибка ввода, повторите попытку!")
        await message.delete()
        await sleep(1)
        await message_answer.delete()
        return
    
    name_product = data["product_name"]
    price_product = data["product_price"]

    await orn_add_product(session, name_product, price_product, weight, callback_data.category,
                                podcategory_id=callback_data.podcategory if callback_data.podcategory != -1 else None)
    await message.answer("✅ Добавил")
    await state.clear()
    
    data = await get_admin_menu(session=session,
                                level=callback_data.level-1,
                                menu_name="product",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(AddCategory.price, F.text)
async def admin_add_podcatalog(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    price = message.text
    data = {"price": price}

    await orm_change_product(session, callback_data.product_id, data)
    await message.answer("✅ Изменил")
    await state.clear()

    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="product",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory,
                                product_id=callback_data.product_id)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(AddCategory.weight, F.text)
async def admin_add_podcatalog(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    weight = message.text
    data = {"weight": weight}

    await orm_change_product(session, callback_data.product_id, data)
    await message.answer("✅ Изменил")
    await state.clear()

    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="product",
                                category=callback_data.category,
                                podcategory=callback_data.podcategory,
                                product_id=callback_data.product_id)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)

@admin_router.message(ChangeBanner.banner_description, F.text)
async def admin_add_podcatalog(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()

    callback_data = data["callback_data"]

    banner_description = message.text

    await orm_change_banner_text(session, callback_data.category, banner_description)
    await message.answer("✅ Изменил")
    await state.clear()

    data = await get_admin_menu(session=session,
                                level=callback_data.level,
                                menu_name="banner",
                                category=callback_data.category)
    
    kb = data.get("kbds")
    message_answer = data.get("message")

    await message.answer(message_answer, reply_markup=kb)