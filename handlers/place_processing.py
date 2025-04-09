from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
import re

from database.orm_query import (
    orm_get_place, orm_add_admin_list,
    orm_get_categories, orm_add_place,
    orm_get_user_order,
    orm_update_user_order_status
)

from kbds.inline import (
    get_place_categoris, get_back_kbds,
    get_place_btns, get_place_order_btns
)

async def choise_place(session, level, menu_name, user_id, place: str | None):
    if place is None:
        if menu_name == "add":
            kbds = get_back_kbds(level, "place", type="menu")
            message = "Введите название точки"
        else:
            places = await orm_get_place(session)
            kbds = get_place_btns(level=level, menu_name=menu_name, places=places, back=False)
            message = "Выберете место или добавти новое"
    else:
        if user_id is None:
            kbds = None
            message = "Error!"
        else:
            await orm_add_admin_list(session, user_id, place)
            kbds = None
            message = "Сохранил, Заказы будут приходить в этот чат!"
    
    return {"kbds": kbds, "message": message}
    
async def add_place(session, level, menu_name, user_id, place_name, category, categoris_choise: str):
    if not category is None:
        if str(category) in categoris_choise:
            categoris_choise = categoris_choise.replace(f"{category}/", "")
        else:
            categoris_choise += f"{category}/"

    if "add" in menu_name:
        categoris = await orm_get_categories(session)
        kbds = get_place_categoris(place_name, categoris, categoris_choise)
        message = f"Выберете категории которые продаются на точке: {place_name}"

    elif "save" in menu_name:
        place = await orm_add_place(session, place_name, categoris_choise)
        await orm_add_admin_list(session, user_id, place.id)
        kbds = None
        message = "Точка добавлена!"

    return {"kbds": kbds, "message": message}

async def place_order(session, level, menu_name, order_id):
    if "approve" in menu_name:
        kbds = get_place_order_btns(order_id, "ready")
        answer = f"🧾Заказ №{order_id:04} принят!"
        message = None
    elif "ready" in menu_name:
        kbds = None
        answer = f"✅Заказ №{order_id:04} готов!"
        message = answer
        order = await orm_get_user_order(session, order_id=order_id)
        await orm_update_user_order_status(session, order.user_id, order_id, "ready")
    elif "cancel" in menu_name:
        kbds = None
        answer = f"🚫Заказ №{order_id:04} отменён!"
        message = answer
        order = await orm_get_user_order(session, order_id=order_id)
        await orm_update_user_order_status(session, order.user_id, order_id, "cancel")

    return {"kbds": kbds, "message": message, "answer": answer}


async def get_place_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        place_name: str,
        categoris_choise: str,
        user_id: int | None = None,
        category: int | None = None,
        order_id: int | None = None):
    
    if level == -1:
        return await choise_place(session, level, menu_name, None)
    elif level == -2:
        return await add_place(session, level, menu_name, user_id, place_name, category, categoris_choise)
    elif level == -3:
        return await place_order(session, level, menu_name, order_id)