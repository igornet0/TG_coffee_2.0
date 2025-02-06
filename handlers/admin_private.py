# админка
from asyncio import sleep
from aiogram import F, Router, types
from aiogram.types import InputMediaPhoto
from aiogram.filters import Command, StateFilter, or_f
# импортируем машину состояний
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# для работы с асинхронными сессиями
from sqlalchemy.ext.asyncio import AsyncSession

# наши импорты
from filters.chat_types import ChatTypeFilter, IsAdmin
# генератор inline клавиатур
from kbds.inline import get_callback_btns
from kbds.admin_inline import AdminCallBack
# импортируем запросы для БД
from database.orm_query import (
    orm_change_banner_image,
    orm_get_categories,
    orm_change_banner_text,
    orm_add_product,
    orm_delete_product,
    orm_get_info_pages,
    orm_get_product,
    orm_get_products,
    orm_update_product,
    orm_add_category,
    orm_get_banners,
    orm_get_banner,
)

from . import message_edit
from handlers.admin_processing import *

# создаём роутер для админки
admin_router = Router()
# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе), добавляем проверку
# является ли пользователь админом
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# при новом запуске бота, нужно прописывать в группе c админами команду /admin, чтобы все администраторы получили доступ к админке
@admin_router.message(Command("admin"))
async def admin_main(message: types.Message):
    await message.answer("Что хотите сделать ❓", reply_markup=ADMIN_KB)

class AddCategory(StatesGroup):
    image = State()

@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session)
    
    btns = {category.name: f'category_{category.id}' for category in categories}
    btns["Добавить"] = "category_add"
    await message.answer("Выберите категорию", 
                         reply_markup=get_callback_btns(btns=btns, sizes=(len(btns)//2,)))


@admin_router.callback_query(F.data.startswith('category_'))
async def choise_category(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    category_id = callback.data.split('_')[-1]

    if category_id == "add":
        await callback.message.answer(f"Отправьте фото меню.\n❗ В подписи к фото напишите для какой категории:",
                                      reply_markup=CANCEL_KB)
        await state.set_state(AddCategory.image)
        return

    products = await orm_get_products(session, int(category_id))

    if not products:
        await callback.answer("Список товаров пуст 🚫")
        return
    
    for product in products:
        unit = "мл"
        await callback.message.answer(
            text=f"<strong>{product.name}\
                                </strong>\n{product.description}\nВес: {product.weight}{unit}\nСтоимость: {product.price}₽",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                },
                sizes=(2,)
            ),
        )

    await callback.message.answer("❤️ ОК, вот список товаров ⏫")

@admin_router.message(AddCategory.image, F.photo)
async def add_category(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    category_name = message.caption.strip()

    await orm_add_category(session, category_name, image_id)
    await message.answer("✅ меню добавленo!", reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(AddCategory.image)
async def add_category2(message: types.Message, state: FSMContext):
    if "отмена" in message.text.lower():
        await state.clear()
        await admin_main(message)
        return
    
    message_answer = await message.answer("❌ Отправьте фото меню или нажмите/напишите отмена")
    await message.delete()
    await sleep(3)
    await message_answer.delete()
    

# инлайн удаление
# ловим текст из callback_query, который начинается на delete_
@admin_router.callback_query(F.data.startswith('delete_'))
# callback - наше название, для удобства
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    # удаляем delete_, оставляем только id продукта
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))

    # даем серверу телеграмм понять, что мы обработали кнопку удалить
    await callback.answer("✅ Товар удален")
    # отправляем в ответ на нажатие кнопки
    await callback.message.answer("✅ Товар удален!")


################# Микро FSM для загрузки/изменения баннеров ############################

class AddBanner(StatesGroup):
    image = State()
    change = State()


@admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    # Словарь для перевода русских названий страниц на английские
    banners = await orm_get_banners(session)

    page = {
        banner.name: banner.description for banner in banners
    }

    message =await message.answer(f"Отправьте фото баннера.\n❗ В подписи к фото напишите для какой страницы:\
                         \n{', '.join(list(page.keys()))}", reply_markup=EDIT_KB)
    await state.set_state(AddBanner.image)


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    banners = await orm_get_banners(session)

    page_translation = {
        banner.name: banner.description for banner in banners
    }

    # Список русских названий страниц для подсказки
    pages_names_russian = list(page_translation.keys())

    # получаем подпись к изображению
    for_page = message.caption.strip().lower()
    # переводим русскую подпись на английскую, которая соответствует нашим категориям баннеров
    translated_page = page_translation.get(for_page, None)

    if translated_page is None:
        await message.answer(f"❌ Введите корректное название страницы, например:\
                         \n{', '.join(pages_names_russian)}")
        return
    
    await orm_change_banner_image(session, translated_page, image_id, )
    await message.answer("✅ Баннер добавлен/изменен!", reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext, session: AsyncSession):
    if "отмена" in message.text.lower():
        await state.clear()
        await admin_main(message)
        return
    
    if "изменить" in message.text.lower():
        await message.delete()
        _, message_output, kb = await get_admin_menu(session, level=1, menu_name="change_banner")
        await message.answer(message_output, reply_markup=kb)
        await state.set_state(AddBanner.change)
        return
    
    await message.answer("❌ Отправьте фото баннера или нажмите/напишите отмена")


@admin_router.callback_query(AddBanner.change, AdminCallBack.filter())
async def change_banner(callback: types.CallbackQuery, callback_data: AdminCallBack, state: FSMContext, session: AsyncSession):
    image, message, kb = await get_admin_menu(session, 
                                              level=callback_data.level, 
                                              menu_name=callback_data.menu_name,
                                              category=callback_data.category)
    await state.update_data(callback_data=callback_data)
    await message_edit(callback.message, message, image, kb)

@admin_router.message(AddBanner.change, F.text)
async def change_banner_text(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    callback_data: AdminCallBack = data.get("callback_data", None)

    if not callback_data is None and callback_data.menu_name == "change_desc":
        await orm_change_banner_text(session, callback_data.category, message.text)
    else:
        if "отмена" in message.text.lower():
            await state.clear()
            await admin_main(message)
        else:
            await message.delete()
        return

    image, message_answer, kb = await get_admin_menu(session, 
                                              level=callback_data.level - 1, 
                                              menu_name=callback_data.menu_name,
                                              category=callback_data.category)
    await message_edit(message, message_answer, image, kb, edit=False)

@admin_router.message(AddBanner.change, F.photo)
async def change_banner_photo(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    data = await state.get_data()
    callback_data: AdminCallBack = data["callback_data"]

    await orm_change_banner_image(session, callback_data.category, image_id,)

    image, message_answer, kb = await get_admin_menu(session, 
                                              level=callback_data.level - 1, 
                                              menu_name=callback_data.menu_name,
                                              category=callback_data.category)
    
    await message_edit(message, message_answer, image, kb, edit=False)

#########################################################################################


######################### FSM для дабавления/изменения товаров админом ##################
# для добавления продукта
class AddProduct(StatesGroup):
    # перечисляем шаги (состояния, через которые будет проходить админ)
    # 1 шаг(состояние) - ввод имени
    name = State()
    # 2 шаг - ввод описания
    description = State()
    # 3 шаг - ввод категории
    category = State()
    # 4 шаг - ввод веса продукта
    weight = State()
    # 5 шаг - ввод стоимости
    price = State()
    # 6 шаг - отправка фото
    # image = State()

    # продукт, который изменяется
    product_for_change = None

    # словарь, в котором перечисляем, что будем отправлять пользователю на каждом шаге назад
    texts = {
        'AddProduct:name': 'Введите название заново! ⏬\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старое название',
        'AddProduct:description': 'Введите описание заново! ⏬\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старое описание',
        "AddProduct:category": "Выберите категорию  заново! ⏬\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старую категорию",
        'AddProduct:weight': 'Введите вес/объём заново! ⏬\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старый вес/объём товара',
        'AddProduct:price': 'Введите стоимость заново! ⏬\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старую стоимость',
        # 'AddProduct:image': 'Это последний шаг..',
    }


# инлайн изменение
# ловим текст из callback_query, который начинается на change_ и подключаем машину состояний
# становимся в ожидание ввода name
@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
# callback - наше название, для удобства
async def change_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    # удаляем change_, оставляем только id продукта
    product_id = callback.data.split("_")[-1]
    # получаем продукт из БД
    product_for_change = await orm_get_product(session, int(product_id))

    AddProduct.product_for_change = product_for_change

    # даем серверу телеграмм понять, что мы обработали кнопку изменить
    await callback.answer()
    # отправляем в ответ на нажатие кнопки и удаляем клавиатуру
    await callback.message.answer(
        "Введите название товара\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старое название",
        reply_markup=BACK_KB)
    # и переходим в состояние ввода названия продукта (далее мы пройдём все этапы, как при добавлении)
    await state.set_state(AddProduct.name)


# проверяем, что у пользователя нет активных состояний - StateFilter(None)
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
# передаем FSMContext, чтобы контролировать состояния пользователя
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        # ждём название товара от админа, удаляем админ клавиатуру
        "Введите название товара\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старое название",
        reply_markup=BACK_KB
    )
    # становимся в состояние ожидания (названия товара)
    await state.set_state(AddProduct.name)


# обработчик отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)

# обработчик для отмены всех состояний
# добавляем StateFilter('*'), где '*' - любое состояние пользователя
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # получаем текущее состояние
    current_state = await state.get_state()
    # если у пользователя нет ни одного состояния, то выходим из этого обработчика
    if current_state is None:
        return
    # если товар изменялся, а потом пользователь нажал отмена, обновляем значение product_for_change
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    # иначе очищаем все состояния у пользователя
    await state.clear()
    # пишем сообщение и возвращаем админ клавиатуру
    await message.answer("✅ Действия отменены", reply_markup=ADMIN_KB)


# обработчик, чтобы вернутся на шаг назад (на прошлое состояние)
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # получаем текущее состояние
    current_state = await state.get_state()
    # если у пользователя состояние ввода названия товара
    if current_state == AddProduct.name:
        await message.answer(
            '🚫 Предыдущего шага нет!\nВведите название товара или нажмите/напишите "отмена" для выхода')
        # выходим из обработчика
        return

    # создаем переменную для предыдущего состояния
    previous = None
    # проходимся по всем нашим состояниям в AddProduct
    for step in AddProduct.__all_states__:
        # если полученное состояние = текущему состоянию
        if step.state == current_state:
            # устанавливаем значение предыдущего состояния
            await state.set_state(previous)
            await message.answer(f'👌, Вы вернулись к предыдущему шагу.\n{AddProduct.texts[previous.state]}')
            return
        # будет обновляться, пока не попадёт в условие, а когда попадет, то станет известно предыдущее состояние
        # например, состояние description не прошёл в условие, но следующее price - прошло, значит
        # предыдущее это состояние description
        previous = step


# если пользователь находится в состоянии ввода названия товара, то
# добавляем название и ждём описание товара от админа
@admin_router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    # если точка, то берём старое название у продукта, который хотим изменить
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        # дополнительная проверка, если больше, то выходим из обработчика не меняя состояния, отправляем сообщение
        if len(message.text) > 150 or len(message.text) <= 2:
            await message.answer(
                "❌ Название товара не должно превышать 150 символов\nи должно быть больше двух символов!\nВведите название заново! ⏬"
            )
            return
        # обновляем наши данные о товаре (название) из текста пользователя
        await state.update_data(name=message.text)
    await message.answer(
        "Введите описание товара\n❗ ОТПРАВЬТЕ восклицательный знак, если:\n1️⃣ Вы хотите оставить описание ПУСТЫМ\n● ОТПРАВЬТЕ точку, если:\n2️⃣ Вы ИЗМЕНЯЕТЕ товар и хотите оставить СТАРОЕ описание")
    # становимся в состояние ожидания (описание товара)
    await state.set_state(AddProduct.description)


# если пользователь ввёл то, что не соответствует фильтрации (например F.text), пишем об ошибке данных
@admin_router.message(AddProduct.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("❌ Вы ввели недопустимые данные, введите текст названия товара!")


# если пользователь находится в состоянии ввода описания товара, то
# добавляем описание и ждём вес/объём товара от админа
@admin_router.message(AddProduct.description, F.text)
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    # если точка, то берём старое описание у продукта, который хотим изменить
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(description=AddProduct.product_for_change.description)
    elif message.text == "!":
        await state.update_data(description="")
    else:
        if len(message.text) > 300:
            await message.answer(
                "❌ Слишком длинное описание!\n Описание товара не должно превышать 300 символов.\nВведите описание заново! ⏬"
            )
            return
        # обновляем наши данные о товаре (описание) из текста пользователя
        await state.update_data(description=message.text)

    # получаем категории
    categories = await orm_get_categories(session)
    # формируем словарь имя: id категории
    btns = {category.name: str(category.id) for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(AddProduct.category)


@admin_router.message(AddProduct.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("❌ Вы ввели недопустимые данные, введите текст описания товара!")


# если пользователь находится в состоянии ввода категории товара, то
# добавляем категорию и ждём вес/объём товара от админа
@admin_router.callback_query(AddProduct.category)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    # если введенный есть в списке категорий
    if int(callback.data) in [category.id for category in await orm_get_categories(session)]:
        await callback.answer()
        await state.update_data(category=callback.data)
        await callback.message.answer(
            "Введите вес/объём товара\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старый вес/объём товара")
        # становимся в состояние ожидания (веса товара)
        await state.set_state(AddProduct.weight)
    else:
        await callback.message.answer('❌ Выберите категорию из кнопок.')
        await callback.answer()


# Ловим любые некорректные действия, кроме нажатия на кнопку выбора категории
@admin_router.message(AddProduct.category)
async def category_choice2(message: types.Message, state: FSMContext):
    await message.answer("❌ Выберите категорию из кнопок!")


# если пользователь находится в состоянии ввода веса товара, то
# добавляем вес/объём и ждём стоимость товара от админа
@admin_router.message(AddProduct.weight, F.text)
async def add_weight(message: types.Message, state: FSMContext):
    # если точка, то берём старый вес/объём у продукта, который хотим изменить
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(weight=AddProduct.product_for_change.weight)
    else:
        if len(message.text) == 0:
            await message.answer(
                "❌ Неверное значение веса!\n Вес/объём должен быть не больше 4 символов и не равен 0\nВведите вес/объём заново в граммах/литрах! ⏬"
            )
            return
        # обновляем наши данные о товаре (стоимость) из текста пользователя
        await state.update_data(weight=message.text)

    await message.answer(
        "Введите стоимость товара\n❗ Если Вы изменяете товар, отправьте точку, чтобы оставить старую стоимость")
    # становимся в состояние ожидания (стоимости товара)
    await state.set_state(AddProduct.price)


@admin_router.message(AddProduct.weight)
async def add_weight2(message: types.Message, state: FSMContext):
    await message.answer("❌ Вы ввели недопустимые данные, введите вес/объём товара в граммах/литрах!")


# если пользователь находится в состоянии ввода стоимости товара, то
# добавляем стоимость и ждём фото товара от админа
@admin_router.message(AddProduct.price, F.text)
async def add_price(message: types.Message, state: FSMContext, session: AsyncSession):
    # если точка, то берём старую цену у продукта, который хотим изменить
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        if len(message.text) == 0:
            await message.answer(
                "❌ Неверное значение цены!\n Цена должна быть не больше 4 символов и не равна 0\nВведите цену заново! ⏬"
            )
            return
        # обновляем наши данные о товаре (стоимость) из текста пользователя
        await state.update_data(price=message.text)

    # формируем все полученные данные о товаре от админа (словарь)
    data = await state.get_data()
    try:
        # если мы изменяем продукт, то вызываем запрос update
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        # иначе добавляем продукт
        else:
            await orm_add_product(session, data)
        await message.answer("✅ Товар добавлен/изменен!", reply_markup=ADMIN_KB)
        # когда пользователь прошёл все пункты состояний, очищаем машину состояний пользователя
        await state.clear()
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: \n{str(e)}\nОбратитесь к разработчику!", reply_markup=ADMIN_KB
        )
        await state.clear()
    # обновляем значение изменяемого продукта, после всех состояний
    AddProduct.product_for_change = None


# обработчик для отлова некорректных данных для состояния price
@admin_router.message(AddProduct.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("❌ Вы ввели недопустимые данные, введите корректную стоимость товара!")
