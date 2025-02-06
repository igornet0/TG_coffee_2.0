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
    User
)
from kbds.inline import (
    get_user_main_btns_mini, send_btns,
    get_products_btns,
    get_user_cart,
    get_callback_btns,
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

def parser_replace_text(text: str, value_replace: dict[str, str]) -> str:
    matches = re.findall(r'/(.*?)/', text)
    for match in matches:
        text = text.replace(f'/{match}/', value_replace[match])

    return text


async def main_menu(session: AsyncSession, level: int, menu_name: str):
    # получаем меню, которое будет отправлено, menu_name - например, main
    
    banner = await orm_get_banner(session, menu_name)
    if banner is not None and banner.image:
        # получаем изображение меню и описание к изображению
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
    else:
        image = None

    # формируем инлайн клавиатуру, передаем уровень меню
    if menu_name == "about":
        kbds = get_main_btns(level=level)
    else:
        kbds = get_user_main_btns(level=level)

    return image, kbds, banner.description

async def user_menu(session: AsyncSession, level: int, menu_name: str, user: User):
    # получаем меню, которое будет отправлено, menu_name - например, main
    banner = await orm_get_banner(session, menu_name)

    if banner is not None and banner.image:
        # получаем изображение меню и описание к изображению
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
    else:
        image = None

    place = await orm_get_place(session, user.place)
    
    date = user.created.strftime("%d.%m.%Y")
    message = parser_replace_text(banner.description, 
                                  {"first_name": str(user.first_name),
                                   "phone": str(user.phone if user.phone else "-"),
                                   "place": str(place.name),
                                   "created": str(date)})

    # формируем инлайн клавиатуру, передаем уровень меню
    kbds = get_user_local_btns(level=level)

    return image, kbds, message

async def catalog(session: AsyncSession, menu_name: str, place: str | None):
    if place is None:
        reply_markup, description = await get_menu_content(session, level=0.1, 
                                                                menu_name="places_change")
        return None, reply_markup, description
    
    banner = await orm_get_banner(session, menu_name)

    if banner is not None and banner.image:
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
    else:
        image = None

    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(categories=categories)

    return image, kbds, banner.description, None

async def change_user(session: AsyncSession, menu_name: str):
    banner = await orm_get_banner(session, menu_name)
    if menu_name == "change_answer":
        return None, None, banner.description
    elif menu_name == "phone_change":
        kbds = get_phone_keyboard()
        return kbds, banner.description
    
    places = await orm_get_place(session)
    kbds = get_place_btns(places=places)

    return kbds, banner.description

async def place_change(session: AsyncSession, menu_name: str, place: str | None):
    if place is None:
        reply_markup, description = await get_menu_content(session, level=0.1, 
                                                                menu_name="places_change")
        return None, reply_markup, description
async def products(session: AsyncSession,menu_name: str, level: int, category: str):
    products = await orm_get_products(session, category_id=category)
    banner = await orm_get_banner(session, menu_name)
    category = await orm_get_categories(session, category)

    if category.id == 3:
        dop = "\n‼️Доступно только в Гастрокорте"
    else:
        dop = ""

    if category.image:
        # получаем изображение меню и описание к изображению
        image = InputMediaPhoto(media=category.image, caption=banner.description + dop)
    else:
        image = None

    if not products:
        return None, None, None, "🚫 Товары отсутствуют в данной категории"
    
    kbds = get_products_btns(
        level=level,
        category=category.id)

    return image, kbds, banner.description + dop, None

async def add_product(session: AsyncSession, level: int, 
                menu_name: str, user_id: int, price, product_id: int, weight: int, dop: int, sirop:int):
    answer = None
    product = await orm_get_product(session, product_id)
    if weight is None:
        message = f"Выберите объём для {product.name.lower()}"
        kbds = get_product_paramets_btns(product)

    elif dop is None and product.category_id != 3:
        dops = await orm_get_dops(session, product.category_id)
        message = "Заменить молок?" if product.category_id == 1 else "Добавить ?"
        kbds = get_product_dop_btns(level, menu_name, 
                                    price, weight, product_id, dops,
                                    sizes=(2,2))

    elif sirop is None and product.category_id == 1:
        sirops = await orm_get_sirops(session)
        message = "Добавить сироп? +30₽"
        kbds = get_product_sirop_btns(level, menu_name, price, weight, product_id, dop, sirops)
    
    else:
        # product = await orm_get_product(session, product_id)
        dop_orm = await orm_get_dop(session, dop) if dop != 0 else None
        if sirop is None:
            sirop_orm = sirop
        else:
            sirop_orm =  await orm_get_sirop(session, sirop) if sirop != 0 else None

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
                message_dop = "Добавок нет"

        if menu_name == "approve":
            await orm_add_to_cart(session, user_id, product_id, weight, dop, sirop,
                                  price)
            message = None
            kbds = None
            answer = "✅Добавил"
        else:
            message = f"Ващ заказ:\n\nНазвание: {product.name}\nОбъём: {weight}мл{message_dop}\nИтоговая цена: {price}₽"
            kbds = get_approve_product_btns(level, menu_name, price, weight, product_id, dop, sirop)

    return message, kbds, answer

async def card_menu(session: AsyncSession, level: int, menu_name: str, 
                    page: int, user_id: int, data: str | None = None, 
                    answer: str | tuple[str,bool] = None):
    
    cards = await orm_get_user_carts(session, user_id)

    if menu_name == "phone_change":
        return await change_user(session, menu_name)
        
    elif "type" in menu_name:
        type_giv = "С собой" if "my" in menu_name else "В зале"
        user = await orm_get_user(session, user_id)
        total_price = 0
        message_output = "Ваш заказ:\n"
        for i, card in enumerate(cards):
            price_card = card.price
            message_output += f"{i+1} {card.product.name}"
            if card.dop:
                dop = await orm_get_dop(session, card.dop)
                price_card += dop.price
                message_output += f"\n\t{dop.name}"
            if card.sirop:
                sirop = await orm_get_sirop(session, card.sirop)
                price_card += sirop.price
                message_output += f"\n\tСироп: {sirop.name}"
            if card.quantity > 1:
                message_output += f"\nЦена {price_card}₽ X {card.quantity} = {price_card * card.quantity}₽\n"
            else:
                message_output += f"\nЦена {price_card}₽\n"

            total_price += price_card
        
        place = await orm_get_place(session, user.place)
        message_output += f"\nМесто - {place.name}\n"
        message_output += f"Способ получения - {type_giv}\n"
        message_output += f"Пожелание к заказу - {data}\n"
        message_output += f"Итоговая цена - {total_price}₽"
        kb = send_btns(type_giv, data)

        return None, kb, message_output, answer
    
    elif "send" in menu_name:
        cards_id = ""
        user = await orm_get_user(session, user_id)
        place = user.place
        for i, card in enumerate(cards):
            cards_id += f"{card.id}/"
            if card.product.category_id == 3 and place != 3:
                return None, None, "Для отправки заказа нужно выбрать место получения - Гастрокорт в личном кабинете", None
            
            await orm_update_status_card(session, card.id, "send")

        data, type_giv = data.split("_")
        await orm_add_order(session, user_id, place, data, cards_id, type_giv)
        return None, None, f"✅Заказ отправлен, для получения продиктуйте номер {user_id}", answer

    if page is None:
        page = 0

    if len(cards) == 0:
        kb = get_user_main_btns_mini()
        message = "Корзина пуста, выберите что-то из меню"
    else:
        if menu_name == "order":
            user = await orm_get_user(session, user_id)
            if user.phone is None:
                return None, None, "phone", None
            return None, None, "Напишите пожелания по заказу", None

        if page < 0 or page >= len(cards):
            return None, None, None, "Это конец страницы"

        card = cards[page]
        product_id = card.product_id
        if menu_name == "page_delete":
            answer = ("✅ Удалил", True)
            card = await orm_delete_from_cart(session, user_id, 
                                    product_id, card.dop, card.sirop)
            
            return await card_menu(session, level, "cart", page, user_id, answer=answer)

        message = "Ваш заказ:\n"
        message += f"Товар №{page+1}\n\t{card.product.name} {card.weight}мл"
        price = card.price
        message_dop = ""
        if card.dop:
            dop = await orm_get_dop(session, card.dop)
            price += dop.price
            message_dop = f"\n\t{dop.name}"

        if card.sirop:
            sirop = await orm_get_sirop(session, card.sirop)
            price += sirop.price
            message_dop += f"\n\tСироп: {sirop.name}"
        
        if not message_dop and card.product.category_id != 3:
            message_dop = "\n\tДобавок нет"

        message += message_dop
        if card.quantity > 1:
            message += f"\nЦена {price}₽ X {card.quantity} = {price * card.quantity}₽\n"
        else:
            message += f"\nЦена {price}₽\n"

        kb = get_user_cart(level=level, product_id=product_id, page=page)

    
    return None, kb, message, answer
    


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        product_id: int | None = None,
        page: int | None = None,
        user: int | User | None = None,
        price: int | None = None,
        weight: int | None = None,
        dop: int | None = None,
        sirop: int | None = None,
        data: str | None = None,
        place: int | None = None
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 0.1:
        return await change_user(session, menu_name)
    elif level == 1:
        return await user_menu(session, level, menu_name, user)
    elif level == 2:
        return await place_change(session, menu_name, place)
    elif level == 3:
        return await catalog(session, menu_name, place)
    elif level == 4:
        return await products(session, menu_name, level, place)
    elif level == 5:
        return await add_product(session, level, 
                                 menu_name, user, price, product_id, 
                                 weight, dop, sirop)
    elif level == 6:
        return await card_menu(session, level, menu_name, page, user, data=data)