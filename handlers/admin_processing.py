from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_get_banners,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_place,
    orm_get_categories,
    orm_get_products,
    orm_get_user_carts,
    orm_reduce_product_in_cart,
    User
)
from kbds.inline import (
    get_products_btns,
    get_user_cart,
    get_callback_btns,
    get_user_catalog_btns,
    get_user_main_btns,
    get_user_local_btns,
    get_main_btns,
)

from kbds.admin_inline import (
    get_banners_btns,
    get_cancel_btns
)

from kbds.reply import get_keyboard

ADMIN_KB = get_keyboard(
    "Добавить товар",
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

async def get_edit_banner(session: AsyncSession, level: int, menu_name: str, category: int | None = None):
    if category is None:
        banners = await orm_get_banners(session)
        kb = get_banners_btns(data=banners, level=level, menu_name=menu_name)
        message = "Выберите баннер для изменения"
        image = None
    else:
        banner = await orm_get_banner(session, category)
        message = f"✅Название: {banner.name}\n🔄Описание: {banner.description}"

        if banner.image:
            image = InputMediaPhoto(media=banner.image, caption=message)
        else:
            image = None
            message += "\n❌ Нет изображения"

        btns = {"Изменить описание": "change_desc",
                "Изменить картинку": "change_image",
                "Назад": "back"}

        kb = get_banners_btns(data=btns, level=level, 
                              menu_name=menu_name, category=category)
    
    return image, message, kb

async def change(level: int, menu_name: str, category: int):
    if menu_name == "change_desc":
        message = "Введите новое описание"
    elif menu_name == "change_image":
        message = "Отправти новое изображение"

    kb = get_cancel_btns(level=level,menu_name=menu_name,category=category)

    return None, message, kb

async def get_admin_menu(session: AsyncSession,
                         level: int, 
                         menu_name: str,
                         category: int | None = None,):
    if level == 1:
        return await get_edit_banner(session, level, menu_name, category)
    elif level == 2:
        return await change(level=level, menu_name=menu_name, category=category)
