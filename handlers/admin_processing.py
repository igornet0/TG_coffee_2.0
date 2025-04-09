from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
import string, random

from database.orm_query import (
    orm_get_category_podcategory,
    orm_get_product,
    orm_delete_product,
    orm_get_banners,
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_get_user_carts,
    orm_reduce_product_in_cart,
    User
)
from kbds.inline import (
    get_callback_btns,
    get_user_catalog_btns,
    get_user_main_btns,
    get_user_local_btns,
    get_main_btns,
)

from kbds.admin_inline import (
    get_admin_podcatalog_btns,
    get_banners_btns,
    get_admin_product,
    get_admin_products_btns,
    get_cancel_btns,
    get_admin_catalog_btns
)

from kbds.reply import get_keyboard

def generate_random_word(length):
    letters = string.ascii_lowercase  # Используем только строчные буквы
    return ''.join(random.choice(letters) for _ in range(length))

ADMIN_KB = get_keyboard(
    # "Добавить товар",
    "Добавить кофейню",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)

BACK_KB = get_keyboard(
    "Назад",
    "Отмена",
    placeholder="Выберите действие",
    sizes=(1, 1),
)

CANCEL_KB = get_keyboard(
    "Отмена",
    placeholder="Выберите действие",
    sizes=(1, 1),
)

EDIT_KB = get_keyboard(
    "Изменить",
    "Отмена",
    placeholder="Выберите действие",
    sizes=(2,),
)

async def catalog(session, level, menu_name, category, podcategory):
    message = "Error!"
    state = None
    kbds = None
    if category is None:
        if "catalog" in menu_name:
            message = "Выберете категорию" 
            categories = await orm_get_categories(session)
            kbds = get_admin_catalog_btns(level=level, menu_name="catalog", categoris=categories)
        elif "add" in menu_name:
            message = "прикрепите фото меню и введите название категори"
            state = "catalog_add"
            kbds = get_cancel_btns(level=level, menu_name="catalog")
    elif isinstance(category, int):
        if "add" in menu_name:
            message = "Введите название меню"
            state = "podcatalog_add"
            kbds = get_cancel_btns(level=level, menu_name="catalog", category=category)
        elif "change" in menu_name:
            message = "Отправти новое фото"
            kbds = get_cancel_btns(level=level, menu_name="catalog", category=category)
            state = "catalog_add"
        else:
            message = "Выберете пункты меню"
            podcategorys = await orm_get_category_podcategory(session, category)
            if not podcategory is None:
                message = "Выберете продукт"
                products = await orm_get_products(session, category_id=category, podcategory_id=podcategory if podcategory != -1 else None)
                kbds = get_admin_products_btns(level=level, menu_name=menu_name, products=products, category=category, podcategory=podcategory)
            else:
                kbds = get_admin_podcatalog_btns(level=level, podcategorys=podcategorys, 
                                        menu_name=menu_name, category=category, sizes=(1,))

    return {"kbds": kbds, "message": message, "state": state}


async def product(session, level, menu_name, 
                  product_id, category, podcategory):
    state = None 
    kbds = None
    message = "Error!"

    if not product_id is None:
        product = await orm_get_product(session, product_id)

        if "delete" in menu_name:
            await orm_delete_product(session, product_id)
            return await catalog(session, level-1, "catalog", category=product.category_id, podcategory=product.podcategory_id if not product.podcategory_id is None else -1)
        elif "value" in menu_name:
            message = f"Введите новый объём в формате числа или через /"
            state = "value"
            kbds = get_cancel_btns(level=level, menu_name="product", product_id=product_id)
        elif "price" in menu_name:
            message = f"Введите новые цену в формате числа или через /\n(!!! Кол-во числе через / должно совпадать с количетсвом чисел через / у объёма)"
            state = "price"
            kbds = get_cancel_btns(level=level, menu_name="product", product_id=product_id)
        else:
            message = f"Название - {product.name}\n"
            message += f"Объём - {product.weight}\n"
            message += f"Цена - {product.price}₽"
            kbds = get_admin_product(level=level, product_id=product_id, category=product.category_id, podcategory=product.podcategory_id)
    elif "add" in menu_name:
        if "price" in menu_name:
            message = "Введите цену товару, если несколько цен, введите их через /"
            kbds = get_cancel_btns(level=level, menu_name="add", category=category, podcategory=podcategory)
            state = "next" if not "back" in menu_name else menu_name
        elif "weight" in menu_name:
            message = "Введите объём товара, если несколько позиций, введите их через /"
            kbds = get_cancel_btns(level=level, menu_name="add_back_product_price", category=category, podcategory=podcategory)
            state = "next"
        else:
            message = "Введите название товара"
            state = "product_add"
            kbds = get_cancel_btns(level=level-1, menu_name="choise", category=category, podcategory=podcategory)


    return {"kbds": kbds, "message": message, "state": state}

async def banner_change(session, level, menu_name, category):
    state = None
    if category is None:
        banners = await orm_get_banners(session)
        kbds = get_banners_btns(data=banners, level=level, menu_name=menu_name)
        message = "Выберите баннер для изменения"
    elif "change_desc" in menu_name:
        message = "Введите новое описание"
        kbds = get_cancel_btns(level=level, menu_name="banner", category=category)
        state = "banner_description"
    else:
        banner = await orm_get_banner(session, category)
        message = f"✅Название: {banner.name}\n🔄Описание: {banner.description}"

        btns = {"Изменить описание": "change_desc",
                "Назад": "back"}
        kbds = get_banners_btns(data=btns, level=level, 
                              menu_name=menu_name, category=category)

    return {"kbds": kbds, "message": message, "state": state}

async def get_admin_menu(session: AsyncSession,
                         level: int, 
                         menu_name: str,
                         podcategory: int | str | None = None,
                         category: int | str | None = None,
                         product_id: int | None = None):
    if level == 1:
        return await catalog(session, level, menu_name, category, podcategory)
    elif level == 2:
        return await product(session, level, menu_name, product_id, category, podcategory)
    elif level == 3:
        return await banner_change(session, level, menu_name, category)