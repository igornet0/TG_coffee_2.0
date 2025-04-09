from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, Message, 
                           InlineQueryResultArticle, InputTextMessageContent)
from aiogram.utils.keyboard import InlineKeyboardBuilder

class AdminCallBack(CallbackData, prefix="admin"):
    level: int 
    menu_name: str  
    data: str | None = None
    category: int | None = None 
    podcategory: int | None = None
    product_id: int | None = None  


def get_banners_btns(*, data: list | dict, level: int, menu_name: str, category: int | None = None, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    if isinstance(data, dict):
        for text, item in data.items():
            if item == "back":
                keyboard.add(InlineKeyboardButton(text=text,
                                                callback_data=AdminCallBack(
                                                    level=level,
                                                    menu_name=menu_name,
                                                ).pack()))
                continue
            keyboard.add(InlineKeyboardButton(text=text,
                                                callback_data=AdminCallBack(
                                                    level=level,
                                                    menu_name=item,
                                                    category=category
                                                ).pack()))
    else:
        for item in data:
            keyboard.add(InlineKeyboardButton(text=item.name,
                                            callback_data=AdminCallBack(level=level, menu_name=menu_name,
                                                                        category=item.id).pack()))
        


    return keyboard.adjust(*sizes).as_markup()

def get_admin_catalog_btns(*, level: int, menu_name: str, categoris: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for c in categoris:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                    callback_data=AdminCallBack(
                                        level=level,
                                        menu_name=menu_name,
                                        category=c.id,
                                    ).pack()))

    keyboard.add(InlineKeyboardButton(text="Добавить",
                                    callback_data=AdminCallBack(
                                        level=level,
                                        menu_name="add"
                                    ).pack()))
    

    return keyboard.adjust(*sizes).as_markup()

def get_admin_podcatalog_btns(*, level, menu_name, podcategorys: list, category: int, sizes: tuple[int] = (3,)):
    keyboard = InlineKeyboardBuilder()

    if len(podcategorys) == 0:
        keyboard.add(InlineKeyboardButton(text="Перейти к продуктам",
                                            callback_data=AdminCallBack(level=level, menu_name=menu_name,
                                                                        podcategory=-1,
                                                                        category=category).pack()))
    else:
        for c in podcategorys:
            keyboard.add(InlineKeyboardButton(text=c.name,
                                            callback_data=AdminCallBack(level=level, menu_name=menu_name,
                                                                        podcategory=c.id,
                                                                        category=category).pack()))

    keyboard.add(InlineKeyboardButton(text='Назад🔙', 
                                      callback_data=AdminCallBack(level=level, 
                                                                 menu_name="catalog").pack()))

    keyboard.add(InlineKeyboardButton(text="Добавить",
                                    callback_data=AdminCallBack(
                                        level=level,
                                        menu_name="add",
                                        category=category
                                    ).pack()))
    
    keyboard.add(InlineKeyboardButton(text="Изменить фото",
                                    callback_data=AdminCallBack(
                                        level=level,
                                        category=category,
                                        menu_name="change_photo"
                                    ).pack()))
    
    return keyboard.adjust(*sizes).as_markup()

def get_admin_products_btns(
        *,
        level: int,
        menu_name: str, 
        products: list,
        category: int,
        podcategory: int,
        sizes: tuple[int] = (2, 2)
):
    keyboard = InlineKeyboardBuilder()

    for c in products:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=AdminCallBack(level=level+1, menu_name='choise',
                                                                    category=category,
                                                                    podcategory=podcategory,
                                                                     product_id=c.id).pack()))

    keyboard.add(InlineKeyboardButton(text="Назад🔙",
                                      callback_data=AdminCallBack(level=level, menu_name=menu_name,
                                                                 category=category).pack()))
    keyboard.add(InlineKeyboardButton(text='Добавить',
                                      callback_data=AdminCallBack(level=level+1, menu_name='add', category=category,
                                                                  podcategory=podcategory).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_admin_product(
        *,
        level: int,
        product_id: int,
        category: int,
        podcategory: int,
        sizes: tuple[int] = (1, )
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🚫Удалить", callback_data=AdminCallBack(level=level,
                                                                            menu_name="delete", 
                                                                            product_id=product_id).pack()))
    
    keyboard.add(InlineKeyboardButton(text="Изменить объём", callback_data=AdminCallBack(level=level,
                                                                            menu_name="edit_value",
                                                                            product_id=product_id).pack()))
    keyboard.add(InlineKeyboardButton(text="Изменить цену", callback_data=AdminCallBack(level=level,
                                                                            menu_name="edit_price",
                                                                            product_id=product_id).pack()))

    keyboard.add(InlineKeyboardButton(text='Назад',
                                 callback_data=AdminCallBack(level=level-1, menu_name='catalog', category=category,
                                                             podcategory=podcategory if not podcategory is None else -1).pack()))

    return keyboard.adjust(*sizes).as_markup()

def get_cancel_btns(*, level, menu_name, category: int | None = None, product_id: int | None = None, podcategory: int | None = None):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Назад",
                                    callback_data=AdminCallBack(
                                        level=level,
                                        menu_name=menu_name,
                                        category=category,
                                        podcategory=podcategory,
                                        product_id=product_id,
                                    ).pack()))
    
    return keyboard.as_markup()