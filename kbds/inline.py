from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, Message, 
                           InlineQueryResultArticle, InputTextMessageContent)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# создаем свой callback для инлайнового меню
# начальный маркер у всех - menu_
class MenuCallBack(CallbackData, prefix="menu"):
    # перечисляем поля, которые будут
    level: int  # уровень меню
    menu_name: str  # название меню
    place: int | None = None
    category: int | None = None  # категория меню
    product_id: int | None = None  # id продукта
    page: int | None = None
    data: str | None = None

    def __str__(self):
        return f"{self.level=}_{self.menu_name=}_{self.category=}_{self.product_id=}"
    
class BackCallBack(CallbackData, prefix="back"):
    level: int = 0
    menu_name: str | None = None

class UserCallBack(CallbackData, prefix="user"):
    data: str | None = None
    level: int = 0
    message: Message | None = None

class ChoiseCallBack(CallbackData, prefix="add_product"):
    level: int  # уровень меню
    menu_name: str  # название меню
    product_id: int # id продукта
    weight: str | None = None
    price: int | None = None
    dop: int | None = None
    sirop: int | None = None


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    # формируем инлайн клавиатуру
    keyboard = InlineKeyboardBuilder()
    # перечисляем кнопки для клавиатуры
    btns = {
        "Меню ☕️": "catalog",
        "Корзина 🛒": "cart",
        "Личный кабинет 👤": "user",
        "О нас ℹ️": "about",
        # "Доставка 📦": "shipping",
    }
    # перебираем словарь
    for text, menu_name in btns.items():
        # если название меню - catalog
        if menu_name == 'catalog':
            # формируем инлайн кнопку с русским текстом, передаем уровень + 1
            # pack - формирует строку из полученного callback
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level + 2, menu_name=menu_name).pack()))
        # если название меню - cart (корзина)
        elif menu_name == 'cart':
            # формируем инлайн кнопку с русским текстом, передаем 3-й уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(level=5, menu_name=menu_name).pack()))
        elif menu_name == 'user':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=UserCallBack(data='user_menu').pack()))
        else:
            # для остальных их дефолтный уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_user_main_btns_mini(*, sizes: tuple[int] = (2,)):
    # формируем инлайн клавиатуру
    keyboard = InlineKeyboardBuilder()
    # перечисляем кнопки для клавиатуры
    btns = {
        "Меню ☕️": "catalog",
        'На главную 🏠': "main"
    }
    # перебираем словарь
    for text, menu_name in btns.items():
        # если название меню - catalog
        if menu_name == 'catalog':
            # формируем инлайн кнопку с русским текстом, передаем уровень + 1
            # pack - формирует строку из полученного callback
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=2, menu_name=menu_name).pack()))
        # если название меню - cart (корзина)
        elif menu_name == 'main':
            # формируем инлайн кнопку с русским текстом, передаем 3-й уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(level=0, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_place_btns(*, places, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for place in places:
        id = place.id
        keyboard.add(InlineKeyboardButton(text=place.name, callback_data=MenuCallBack(level=3, menu_name=f"place_{id}", place=id).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_local_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    btns = {
        # "Изменить 📍": "change_place",
        "Изменить 📞": "change_phone",
        "На главную 🏠": "main"
    }

    for text, menu_name in btns.items():
        if menu_name == "main":
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level-1, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                          callback_data=UserCallBack(level=level, data=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_user_catalog_btns(*, categories: list, sizes: tuple[int] = (3,)):
    keyboard = InlineKeyboardBuilder()

    for c in categories:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=MenuCallBack(level=3, menu_name="choise",
                                                                     category=c.id).pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=5, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='На главную 🏠',
                                      callback_data=MenuCallBack(level=0, menu_name='main').pack()))
    
    return keyboard.adjust(*sizes).as_markup()


def get_menu(products, text, category):

    result = []
    for product in products:
        if product.name.lower().startswith(text.lower()):
            result.append(InlineQueryResultArticle(
                id=str(product.id),
                title=product.name,
                description=product.description,
                input_message_content=InputTextMessageContent(message_text=f"{product.id}.{category}")
            ))
            if len(result) == 10:
                break

    return result


def get_products_btns(
        *,
        level: int,
        category: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Меню🔎", switch_inline_query_current_chat=''))

    keyboard.add(InlineKeyboardButton(text='Назад',
                                      callback_data=MenuCallBack(level=level - 1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=5, menu_name='cart').pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_cart(
        *,
        level: int,
        product_id: int,
        page: int | None,
):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    buttons.append(InlineKeyboardButton(text="⏪️", callback_data=MenuCallBack(level=level,
                                                                            menu_name="page_back",
                                                                            page=page-1, product_id=product_id).pack()))
    buttons.append(InlineKeyboardButton(text="❌", callback_data=MenuCallBack(level=level,
                                                                            menu_name="page_delete",
                                                                            page=page, product_id=product_id).pack()))
    buttons.append(InlineKeyboardButton(text="⏩️", callback_data=MenuCallBack(level=level,
                                                                            menu_name="page_next",
                                                                            page=page+1, product_id=product_id).pack()))
    keyboard.row(*buttons)
    keyboard.row(*[InlineKeyboardButton(text='На главную 🏠',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()),
                    InlineKeyboardButton(text='Заказать',
                                 callback_data=MenuCallBack(level=level, menu_name='order').pack())])

    return keyboard.as_markup()

def get_product_paramets_btns(product):
    keyboard = InlineKeyboardBuilder()
    weight = product.weight.split("/")
    price = product.price.split("/")

    for item in zip(weight, price):
        text = f"{item[0]}мл - {item[1]}₽"
        keyboard.add(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=4,
                                                                        menu_name="add_product",
                                                                        product_id=product.id,
                                                                        price=float(item[1]),
                                                                       weight=item[0]).pack()))

    return keyboard.as_markup()

def get_product_dop_btns(level, menu_name, price, weight, product_id, dops, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    for dop in dops:
        text = f"{dop.name} +{dop.price}₽" if dop.price != 0 else f"{dop.name}"
        buttons.append(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=dop.id,).pack()))
    keyboard.row(*buttons)
    keyboard.row(*[InlineKeyboardButton(text="Нет❌", 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=0).pack()),
                    InlineKeyboardButton(text="Назад🔙", 
                                      callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name=menu_name,
                                                                    product_id=product_id).pack())])
    return keyboard.adjust(*sizes).as_markup()

def get_product_sirop_btns(level, menu_name, price, weight, product_id, dop, sirops):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    for sirop in sirops:
        text = f"{sirop.name}"
        buttons.append(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=dop,
                                                                       sirop=sirop.id).pack()))
        if len(buttons) == 2:
            keyboard.row(*buttons)
            buttons = []
    keyboard.row(*[InlineKeyboardButton(text="Нет❌", 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=dop,
                                                                       sirop=0).pack()),
                    InlineKeyboardButton(text="Назад🔙", 
                                      callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name=menu_name,
                                                                    product_id=product_id,
                                                                    price=price,
                                                                    weight=weight).pack())])
    return keyboard.as_markup()

def get_approve_product_btns(level, menu_name, price, weight, product_id, dop, sirop):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Добавить в 🛒", 
                                          callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name="approve",
                                                                    product_id=product_id,
                                                                    price=price,
                                                                    weight=weight,
                                                                    dop=dop,
                                                                    sirop=sirop).pack()))
    keyboard.add(InlineKeyboardButton(text="Изменить🔄", 
                                          callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name=menu_name,
                                                                    product_id=product_id).pack()))

    return keyboard.as_markup()

def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,), typeCallback: str = None):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        if typeCallback == "user":
            data = UserCallBack(data=data).pack()
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

def get_main_btns(level: int):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='На главную 🏠', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name='main').pack()))
    
    return keyboard.as_markup()

def get_back_kbds(level, menu_name):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад⏪', 
                                      callback_data=BackCallBack(level=level, 
                                                                 menu_name=menu_name).pack()))
    
    return keyboard.as_markup()

def type_give(level, text):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='С собой', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name="type_my", data=text).pack()))
    keyboard.add(InlineKeyboardButton(text='В зале', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name="type_zal", data=text).pack()))
    
    return keyboard.as_markup()

def send_btns(type_giv, data):

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Отправить?', 
                                      callback_data=MenuCallBack(level=5, 
                                                                 menu_name="send",
                                                                 data=f"{data}_{type_giv}").pack()))
    keyboard.add(InlineKeyboardButton(text='На главную 🏠', 
                                      callback_data=MenuCallBack(level=0, 
                                                                 menu_name='main').pack()))
    
    return keyboard.as_markup()