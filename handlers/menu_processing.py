from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
import re

from database.orm_query import (
    orm_add_to_cart, orm_update_status_card,
    orm_delete_from_cart, orm_add_order,
    orm_get_banner,
    orm_get_place,
    orm_get_categories,
    orm_get_products,
    orm_get_product,
    orm_get_user_carts,
    orm_get_user,
    orm_get_dops,
    orm_get_dop,
    orm_get_sirops,
    orm_get_sirop,
    orm_get_category_podcategory,
    orm_delete_user_card,
    orm_get_user_order,
    orm_update_user_order_status,
    orm_update_order,
)
from kbds.inline import (
    get_user_main_btns_mini, send_btns,
    send_order_btns,
    get_products_btns,
    get_user_cart,
    get_start_catalog_kbds,
    get_user_orders,
    get_user_podcatalog_btns,
    get_place_btns,
    get_user_catalog_btns,
    get_user_main_btns,
    get_user_local_btns,
    get_main_btns,
    get_product_paramets_btns,
    get_product_sirop_btns,
    get_product_dop_btns,
    get_approve_product_btns
)

from kbds.reply import get_phone_keyboard

from handlers.place_processing import choise_place

from datetime import datetime as dt

def parser_replace_text(text: str, value_replace: dict[str, str]) -> str:
    matches = re.findall(r'/(.*?)/', text)
    for match in matches:
        text = text.replace(f'/{match}/', value_replace[match])

    return text


async def main_menu(session: AsyncSession, level: int, menu_name: str, user_id: int | None, data: str | None = None):
    # получаем меню, которое будет отправлено, menu_name - например, main
    banner = await orm_get_banner(session, menu_name)

    # формируем инлайн клавиатуру, передаем уровень меню
    if menu_name == "about":
        kbds = get_main_btns(level=level)
        message = banner.description
        
    elif menu_name == "user_menu":
        user = await orm_get_user(session, user_id)
        date = user.created.strftime("%d.%m.%Y")
        message = parser_replace_text(banner.description, 
                                    {"first_name": str(user.first_name),
                                    "phone": str(user.phone if user.phone else "-"),
                                    "created": str(date)})

        # формируем инлайн клавиатуру, передаем уровень меню
        kbds = get_user_local_btns(level=level)
    else:
        kbds = get_user_main_btns(level=level)
        message = banner.description
    
    if not data is None and "edit" in data:
        edit = False if "False" in data else True
        return {"kbds": kbds, "message": message, "edit": edit}

    return {"kbds": kbds, "message": message}

async def catalog(session: AsyncSession, level: int, menu_name: str, user_id, 
                  place: str | None, category: int | None, podcategory: int | None,
                  answer: tuple | None = None):
    
    image = None
    
    if place is None:
        cards = await orm_get_user_carts(session, user_id)
        if menu_name != "new_order":
            if len(cards) != 0:
                place = cards[0].place
                place_name = place.name
                place_id = place.id
                message = f"Вы уже начали заказывать из {place_name}"
                kbds = get_start_catalog_kbds(level=level, menu_name=menu_name, place=place_id)

                return {"kbds": kbds, "message": message}
            
        if len(cards) != 0:
            await orm_delete_user_card(session, user_id)
            answer = "Новый заказ📃"
        
        banner = await orm_get_banner(session, "places_change")
        places = await orm_get_place(session)
        kbds = get_place_btns(level=level, menu_name=menu_name, places=places)
        return {"kbds": kbds, "message": banner.description, "answer": answer}
    
    banner = await orm_get_banner(session, menu_name)

    if category is None:
        categories = await orm_get_categories(session)
        orm_place = await orm_get_place(session, place)
        kbds = get_user_catalog_btns(level=level, menu_name=menu_name, 
                                     categories=categories, place=place, filter_categorys=orm_place.filter_categorys)
    
    else:
        category_orm = await orm_get_categories(session, category)
        image = category_orm.image
        podcategorys = await orm_get_category_podcategory(session, category)
        if len(podcategorys) == 0 or not podcategory is None:
            products = await orm_get_products(session, category_id=category, podcategory_id=podcategory)
            if len(podcategorys) == 0:
                category = None
            kbds = get_products_btns(level=level, menu_name=menu_name, products=products, place=place, category=category)
        else:
            kbds = get_user_podcatalog_btns(level=level, podcategorys=podcategorys, 
                                    menu_name=menu_name, category=category, 
                                    place=place, sizes=(1,))
    if image:
        # получаем изображение меню и описание к изображению
        image = InputMediaPhoto(media=image, caption=banner.description)
    
    return {"kbds": kbds, "message": banner.description, "image": image}

async def change_user(session: AsyncSession, level: int, menu_name: str):
    banner = await orm_get_banner(session, menu_name)
    if menu_name == "change_answer":
        return {"answer": banner.description}
    elif menu_name == "phone_change":
        kbds = get_phone_keyboard()
        return {"kbds": kbds, "message": banner.description}


async def add_product(session: AsyncSession, level: int, 
                menu_name: str, user_id: int, place:int, price: float, product_id: int, weight: int, dop: int, sirop:int):
    answer = None
    product = await orm_get_product(session, product_id)
    if weight is None:
        message = f"Выберите объём для {product.name.lower()}"
        kbds = get_product_paramets_btns(product, place)

    elif dop is None and product.category_id != 3:
        dops = await orm_get_dops(session, product.category_id)
        message = "Заменить молок?" if product.category_id == 1 else "Добавить ?"
        kbds = get_product_dop_btns(level, menu_name, place,
                                    price, weight, product_id, dops,
                                    sizes=(2,2))

    elif sirop is None and product.category_id == 1:
        sirops = await orm_get_sirops(session)
        message = "Добавить сироп? +30₽"
        kbds = get_product_sirop_btns(level, menu_name, place, price, weight, product_id, dop, sirops)
    
    else:
        # product = await orm_get_product(session, product_id)
        dop_orm = await orm_get_dop(session, dop) if dop != 0 else None
        if sirop is None:
            sirop_orm = sirop
        else:
            sirop_orm =  await orm_get_sirop(session, sirop) if sirop != 0 else None

        if menu_name == "approve":
            await orm_add_to_cart(session, user_id, place, product_id, weight, dop, sirop,
                                  price)
            return await card_menu(session, 6, "cart", 0, user_id, answer="✅Добавил")

        message_dop = "\nДобавки:"
        if dop_orm:
            price += dop_orm.price
            message_dop += f"\n\t{dop_orm.name}"

        if sirop_orm:
            price += sirop_orm.price
            message_dop += f"\n\tСироп: {sirop_orm.name}"
        
        if message_dop == "\nДобавки:":
            if product.category_id == 3:
                message_dop = ""
            else:
                message_dop = "\n\tДобавок нет"

        place_orm = await orm_get_place(session, place)
        message = f"Ващ заказ:\n\nНазвание: {product.name}\nОбъём: {weight}мл{message_dop}\nМесто получения:{place_orm.name}\nИтоговая цена: {price}₽"
        kbds = get_approve_product_btns(level, menu_name, place, price, weight, product_id, dop, sirop)
    return {"kbds": kbds, "message": message, "answer": answer}

async def card_menu(session: AsyncSession, level: int, menu_name: str, page: int | None, user_id: int, 
                    data: str | None = None, order_id: int | None = None,
                    answer: str | tuple[str,bool] = None):
    
    if isinstance(answer, tuple):
        answer = answer[0]
        flag = answer[1]
    else:
        flag = False

    cards = await orm_get_user_carts(session, user_id, status="new")

    if menu_name == "phone_change":
        return await change_user(session, level, menu_name)
    
    elif menu_name == "order_delete" and not order_id is None:
        order = await orm_get_user_order(session, user_id, 
                                             order_id=order_id, status="time")
        order = order
        for card in order.cards.split("/"):
            if card.isdigit():
                await orm_update_status_card(session, int(card), "cancel")

        await orm_update_user_order_status(session, user_id, order_id, "cancel")

        data = await main_menu(session, 0, "main", user_id)
        return {"kbds": data["kbds"], "message": data["message"], "answer": "Отменил заказ🚫", "answer_flag": True}
        
    elif "type" in menu_name:
        type_giv = "С собой" if "my" in menu_name else "В зале"
        if order_id:
            order = await orm_get_user_order(session, user_id, 
                                             order_id=order_id, status="time")
            cards_id = order.cards
            cards = await orm_get_user_carts(session, user_id, cards_id, status="time")
            data = order.data if menu_name == "type" else data
            type_giv = order.type_give if menu_name == "type" else type_giv
            if menu_name != "type":
                await orm_update_order(session, user_id, order.id, data, type_giv)

        total_price = 0
        message_output = "Ваш заказ:\n"
        for i, card in enumerate(cards):
            place_name = card.place.name
            price_card = card.price
            message_output += f"{i+1}.{card.product.name} {card.weight}мл"
            if card.dop:
                dop = await orm_get_dop(session, card.dop)
                message_output += f"\n\t{dop.name}"
            if card.sirop:
                sirop = await orm_get_sirop(session, card.sirop)
                message_output += f"\n\tСироп: {sirop.name}"
            if card.quantity > 1:
                message_output += f"\nЦена {price_card}₽ X {card.quantity} = {price_card * card.quantity}₽\n\n"
            else:
                message_output += f"\nЦена {price_card}₽\n\n"

            total_price += price_card * card.quantity

        message_output += f"Место - {place_name}\n"
        message_output += f"Способ получения - {type_giv}\n"
        message_output += f"Пожелание к заказу - {data}\n"
        message_output += f"Итоговая цена - {total_price}₽"
        kb = send_btns(type_giv, data, order_id)
        return {"kbds": kb, "message": message_output, "answer": answer, "answer_flag": flag}
    
    elif "send" in menu_name or "time" in menu_name:
        if "send" in menu_name:
            from config import TIME_ZONE
            current_time = dt.now().time()
            start_time_str, end_time_str = TIME_ZONE.split('/')
            start_time = dt.strptime(start_time_str, '%H:%M').time()
            end_time = dt.strptime(end_time_str, '%H:%M').time()
            if current_time < start_time or current_time > end_time:
                return {"kbds": None, "message": None, "answer": f"Заказ можно сдать только в рабочее врем {TIME_ZONE}", "answer_flag": False}
                
        if order_id:
            order = await orm_get_user_order(session, user_id, 
                                             order_id=order_id, status="time")
            cards_id = order.cards
            cards = await orm_get_user_carts(session, user_id, cards_id, status="time")
            summa = 0
        else:
            cards_id = ""
            place = None
            summa = 0
            
        for card in cards:
            place = card.place.id
            cards_id += f"{card.id}/"
            summa += card.price
            await orm_update_status_card(session, card.id, menu_name)

        if order_id:
            await orm_update_user_order_status(session, user_id, order.id, menu_name)
        else:
            data, type_giv = data.split("_")
            order = await orm_add_order(session, user_id, place, data, 
                                        cards_id, type_giv, summa, status=menu_name)
            order = order[-1]
        
        if "time" in menu_name:
            data = await main_menu(session, 0, "main", user_id)
            return {"kbds": data["kbds"], "message": data["message"], "answer": "✅Отложил на завтра", "answer_flag":True}

        kb = send_order_btns()
        return {"kbds": kb, "message": f"✅Заказ отправлен, для получения продиктуйте номер {order.id:04}", 
                "answer": answer}

    elif "orders" in menu_name:
        orders = await orm_get_user_order(session, user_id, 
                                             order_id=order_id, status="time")
        kb = get_user_orders(orders=orders)
        message = "Выберите заказ:"

    else:
        if len(cards) == 0 and not "order_change" == menu_name:
            orders_time = await orm_get_user_order(session, user_id, status="time")
            kb = get_user_main_btns_mini(order=orders_time)
            message = "Корзина пуста, выберете что-то из меню"
        else:
            if "order" in menu_name:
                user = await orm_get_user(session, user_id)
                if user.phone is None:
                    return {"message": "phone"}
                return {"message": "Напишите пожелания по заказу"}
            
            if page is None:
                page = 0

            if page < 0:
                page = len(cards) - 1
            elif page >= len(cards):
                page = 0

            if len(cards) > 1:
                message_col = f" {len(cards)} позиций" if len(cards) > 4 else f" {len(cards)} позиции"
            else:
                message_col = ""

            message = f"Ваш заказ{message_col}:\n"

            card = cards[page]
            product_id = card.product_id
            if menu_name == "page_delete":
                answer = "✅ Удалил"
                card = await orm_delete_from_cart(session, user_id, 
                                        product_id, card.dop, card.sirop)
                
                return await card_menu(session, level, "cart", page, user_id, answer=answer)
            
            elif "page" in menu_name and len(cards) == 1:
                return {"answer": "ℹ️У вас нет больше позиций"}

            message += f"Товар №{page + 1}\n\t{card.product.name} {card.weight}мл"
            price = card.price
            message_dop = ""
            if card.dop:
                dop = await orm_get_dop(session, card.dop)
                message_dop = f"\n\t{dop.name}"

            if card.sirop:
                sirop = await orm_get_sirop(session, card.sirop)
                message_dop += f"\n\tСироп: {sirop.name}"
            
            if not message_dop and card.product.category_id != 3:
                message_dop = "\n\tДобавок нет"

            message += message_dop
            if card.quantity > 1:
                message += f"\nЦена {price}₽ X {card.quantity} = {price * card.quantity}₽\n"
            else:
                message += f"\nЦена {price}₽\n"

            orders_time = await orm_get_user_order(session, user_id, status="time")
            kb = get_user_cart(level=level, page=page, product_id=product_id, order=orders_time)

    return {"kbds": kb, "message": message, "answer": answer}

    
async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        place: int | None = None,
        category: int | None = None,
        podcategory: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
        price: int | None = None,
        weight: int | None = None,
        dop: int | None = None,
        page: int | None = None,
        sirop: int | None = None,
        data: str | None = None,
        order_id: int | None = None
):
    if level == 0:
        return await main_menu(session, level, menu_name, user_id, data)
    elif level == 1:
        return await change_user(session, level, menu_name)
    elif level == 3:
        return await catalog(session, level, menu_name, user_id, place, category, podcategory)
    elif level == 4:
        return await add_product(session, level, 
                                 menu_name, user_id, place, price, product_id, 
                                 weight, dop, sirop)
    elif level == 6:
        return await card_menu(session, level, menu_name, page, user_id, data=data, order_id=order_id)
    
    elif level == -1:
        return await choise_place(session, level, menu_name, user_id, place=place)