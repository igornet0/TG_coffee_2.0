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
    podcategory: int | None = None
    product_id: int | None = None  # id продукта
    page: int | None = None
    data: str | None = None
    order_id: int | None = None

    def __str__(self):
        return f"{self.level=}_{self.menu_name=}_{self.place=}_{self.category=}_{self.podcategory=}_{self.product_id=}"
    
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
    place: int | None = None
    dop: int | None = None
    sirop: int | None = None

class PlaceCallBack(CallbackData, prefix="place"):
    level: int  
    menu_name: str
    categoris_choise: str
    place_name: str | None = None
    category: int | None = None
    order_id: int | None = None


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    # формируем инлайн клавиатуру
    keyboard = InlineKeyboardBuilder()
    # перечисляем кнопки для клавиатуры
    btns = {
        "Меню ☕️": "catalog",
        "Корзина 🛒": "cart",
        "Личный кабинет 👤": "user_menu",
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
                                              callback_data=MenuCallBack(level=3, menu_name="places_change").pack()))
        # если название меню - cart (корзина)
        elif menu_name == 'cart':
            # формируем инлайн кнопку с русским текстом, передаем 3-й уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(level=6, menu_name=menu_name).pack()))
        else:
            # для остальных их дефолтный уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_user_main_btns_mini(*, order: None = None, sizes: tuple[int] = (2,)):
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
                                              callback_data=MenuCallBack(level=3, menu_name=menu_name).pack()))
        # если название меню - cart (корзина)
        elif menu_name == 'main':
            if order:
                keyboard.add(InlineKeyboardButton(text="Отложенный заказ📑",
                                            callback_data=MenuCallBack(level=6, menu_name="orders").pack()))
            # формируем инлайн кнопку с русским текстом, передаем 3-й уровень
            keyboard.add(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(level=0, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_user_orders(*, orders: list, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()

    for i, order in enumerate(orders):
        keyboard.add(InlineKeyboardButton(text=f"Заказ №{i+1} - {order.summa:.1f}₽", 
                                          callback_data=MenuCallBack(level=6, menu_name="type",
                                                                     order_id=order.id
                                                                     ).pack()))
        if i > 5:
            break
        
    keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=6, 
                                                                 menu_name="card").pack()))
        
    return keyboard.adjust(*sizes).as_markup()

def get_place_btns(*, level, menu_name, places, back: bool | None = True, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for place in places:
        id = place.id
        keyboard.add(InlineKeyboardButton(text=place.name, callback_data=MenuCallBack(level=level, menu_name="catalog", place=id).pack()))
    if back:
        keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=0, 
                                                                 menu_name="main").pack()))
    else:
        keyboard.add(InlineKeyboardButton(text='Добавить', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name="add").pack()))
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
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                          callback_data=UserCallBack(level=level+1, data=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_user_catalog_btns(*, level, menu_name, categories: list, place:int, filter_categorys: str, sizes: tuple[int] = (3,)):
    keyboard = InlineKeyboardBuilder()
    
    for c in categories:
        name = c.name
        if not str(c.id) in filter_categorys:
            continue

        keyboard.add(InlineKeyboardButton(text=name,
                                          callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                     place=place,
                                                                     category=c.id).pack()))
    # keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
    #                                   callback_data=MenuCallBack(level=6, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name=menu_name).pack()))
    
    return keyboard.adjust(*sizes).as_markup()

def get_user_podcatalog_btns(*, level, menu_name, podcategorys: list, category: int, place:str, sizes: tuple[int] = (3,)):
    keyboard = InlineKeyboardBuilder()

    for c in podcategorys:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                     place=place,
                                                                     podcategory=c.id,
                                                                     category=category).pack()))
    # keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
    #                                   callback_data=MenuCallBack(level=6, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 place=place,
                                                                 menu_name=menu_name).pack()))
    
    return keyboard.adjust(*sizes).as_markup()


def get_products_btns(
        *,
        level: int,
        menu_name: str, 
        products: list,
        place: int,
        category: int,
        sizes: tuple[int] = (2, 2)
):
    keyboard = InlineKeyboardBuilder()

    for c in products:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=ChoiseCallBack(level=level+1, menu_name='choise',
                                                                     place=place,
                                                                     product_id=c.id).pack()))

    keyboard.add(InlineKeyboardButton(text="Назад🔙",
                                      callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                 place=place,
                                                                 category=category).pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=6, menu_name='cart').pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_cart(
        *,
        level: int,
        product_id: int,
        page: int | None,
        order: None = None
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
                    InlineKeyboardButton(text='Заказать📩',
                                 callback_data=MenuCallBack(level=level, menu_name='order').pack())])
    if order:
        keyboard.row(*[InlineKeyboardButton(text="Отложенный заказ📑",
                                            callback_data=MenuCallBack(level=6, menu_name="orders").pack())])

    return keyboard.as_markup()

def get_product_paramets_btns(product, place):
    keyboard = InlineKeyboardBuilder()
    weight = product.weight.split("/")
    price = product.price.split("/")
    buttons = []
    for item in zip(weight, price):
        text = f"{item[0]}мл - {item[1]}₽"
        buttons.append(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=4,
                                                                        menu_name="add_product",
                                                                        product_id=product.id,
                                                                        place=place,
                                                                        price=float(item[1]),
                                                                       weight=item[0]).pack()))

    keyboard.row(*buttons)
    keyboard.add(InlineKeyboardButton(text="Назад🔙",
                                      callback_data=MenuCallBack(level=3, menu_name="catalog",
                                                                 place=place,
                                                                 category=product.category_id,
                                                                 podcategory=product.podcategory_id,
                                                                 product_id=product.id).pack()))
    return keyboard.as_markup()

def get_product_dop_btns(level, menu_name, place, price, weight, product_id, dops, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    for dop in dops:
        text = f"{dop.name} +{dop.price}₽" if dop.price != 0 else f"{dop.name}"
        buttons.append(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        place=place,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=dop.id,).pack()))
    keyboard.row(*buttons)
    keyboard.row(*[InlineKeyboardButton(text="Нет❌", 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        place=place,
                                                                        product_id=product_id,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=0).pack()),
                    InlineKeyboardButton(text="Назад🔙", 
                                      callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    place=place,
                                                                    menu_name=menu_name,
                                                                    product_id=product_id).pack())])
    return keyboard.adjust(*sizes).as_markup()

def get_product_sirop_btns(level, menu_name, place, price, weight, product_id, dop, sirops):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    for sirop in sirops:
        text = f"{sirop.name}"
        buttons.append(InlineKeyboardButton(text=text, 
                                          callback_data=ChoiseCallBack(
                                                                        level=level,
                                                                        menu_name=menu_name,
                                                                        product_id=product_id,
                                                                        place=place,
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
                                                                        place=place,
                                                                        price=price,
                                                                       weight=weight,
                                                                       dop=dop,
                                                                       sirop=0).pack()),
                    InlineKeyboardButton(text="Назад🔙", 
                                      callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name=menu_name,
                                                                    place=place,
                                                                    product_id=product_id,
                                                                    price=price,
                                                                    weight=weight).pack())])
    return keyboard.as_markup()

def get_approve_product_btns(level, menu_name, place, price, weight, product_id, dop, sirop):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Добавить в 🛒", 
                                          callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    menu_name="approve",
                                                                    product_id=product_id,
                                                                    place=place,
                                                                    price=price,
                                                                    weight=weight,
                                                                    dop=dop,
                                                                    sirop=sirop).pack()))
    keyboard.add(InlineKeyboardButton(text="Изменить🔄", 
                                          callback_data=ChoiseCallBack(
                                                                    level=level,
                                                                    place=place,
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

def get_start_catalog_kbds(*, level, menu_name, place, sizes: tuple = (2,)):
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='Оставить🧾', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name=menu_name,
                                                                 place=place).pack()))
    keyboard.add(InlineKeyboardButton(text='Новый заказ🗒️', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name='new_order').pack()))
    keyboard.add(InlineKeyboardButton(text='На главную 🏠', 
                                      callback_data=MenuCallBack(level=0, 
                                                                 menu_name='main').pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_back_kbds(level, menu_name, type=None):
    keyboard = InlineKeyboardBuilder()

    if type == "menu":
        keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name=menu_name).pack()))
    else:
        keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=BackCallBack(level=level, 
                                                                 menu_name=menu_name).pack()))
    return keyboard.as_markup()

def type_give(level, text, order_id: int | None = None):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='С собой', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name="type_my", data=text[:50],
                                                                 order_id=order_id).pack()))
    keyboard.add(InlineKeyboardButton(text='В зале', 
                                      callback_data=MenuCallBack(level=level, 
                                                                 menu_name="type_zal", data=text[:50],
                                                                 order_id=order_id).pack()))
    keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=MenuCallBack(level=6, 
                                                                 menu_name="card").pack()))
    
    return keyboard.as_markup()

def send_btns(type_giv, data, order_id: int | None = None, sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Отправить?', 
                                      callback_data=MenuCallBack(level=6, 
                                                                 menu_name="send",
                                                                 data=f"{data[:50]}_{type_giv}",
                                                                 order_id=order_id).pack()))
    keyboard.add(InlineKeyboardButton(text='Отложить на завтра?', 
                                      callback_data=MenuCallBack(level=6, 
                                                                 menu_name="time",
                                                                 data=f"{data[:50]}_{type_giv}",
                                                                 order_id=order_id).pack()))
    if order_id:
        keyboard.add(InlineKeyboardButton(text='Отмена🚫', 
                                        callback_data=MenuCallBack(level=6, 
                                                                    menu_name="order_delete",
                                                                    order_id=order_id).pack()))
    keyboard.add(InlineKeyboardButton(text='Изменить🔁', 
                                      callback_data=MenuCallBack(level=6, 
                                                                 menu_name="order_change",
                                                                 order_id=order_id).pack()))
    keyboard.add(InlineKeyboardButton(text='На главную 🏠', 
                                      callback_data=MenuCallBack(level=0, 
                                                                 menu_name='main').pack()))
    
    return keyboard.adjust(*sizes).as_markup()

def send_order_btns():

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Заказать ещё📃', 
                                      callback_data=MenuCallBack(level=0, 
                                                                 menu_name='main',
                                                                 data="edit=False").pack()))
    
    return keyboard.as_markup()


def get_place_categoris(place_name: str, categoris: list, categoris_choise: str, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()

    for c in categoris:
        if str(c.id) in categoris_choise:
            text = f"✅{c.name}"
        else:
            text = f"❌{c.name}"
        keyboard.add(InlineKeyboardButton(text=text, 
                                      callback_data=PlaceCallBack(level=-2, 
                                                                 menu_name='add',
                                                                 place_name=place_name,
                                                                 categoris_choise=categoris_choise,
                                                                 category=c.id).pack()))
    keyboard.add(InlineKeyboardButton(text="Назад", 
                                      callback_data=MenuCallBack(level=-1, 
                                                                 menu_name='add').pack()))
    
    keyboard.add(InlineKeyboardButton(text="Сохранить", 
                                      callback_data=PlaceCallBack(level=-2, 
                                                                 menu_name='save',
                                                                 place_name=place_name,
                                                                 categoris_choise=categoris_choise).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_place_order_btns(order_id, menu_name="main", sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    if menu_name == "ready":
        keyboard.add(InlineKeyboardButton(text="✅Готов!", 
                                      callback_data=PlaceCallBack(level=-3, 
                                                                  order_id=order_id,
                                                                  categoris_choise="",
                                                                 menu_name=menu_name).pack()))
    else:
        keyboard.add(InlineKeyboardButton(text="🧾Принять", 
                                      callback_data=PlaceCallBack(level=-3, 
                                                                  order_id=order_id,
                                                                  categoris_choise="",
                                                                 menu_name='approve').pack()))
    keyboard.add(InlineKeyboardButton(text="🚫Отмена", 
                                      callback_data=PlaceCallBack(level=-3, 
                                                                  order_id=order_id,
                                                                  categoris_choise="",
                                                                 menu_name='cancel').pack()))
    
    return keyboard.adjust(*sizes).as_markup()
