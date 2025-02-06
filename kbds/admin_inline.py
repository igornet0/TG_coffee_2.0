from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, Message, 
                           InlineQueryResultArticle, InputTextMessageContent)
from aiogram.utils.keyboard import InlineKeyboardBuilder

class AdminCallBack(CallbackData, prefix="admin"):
    level: int 
    menu_name: str  
    data: str | None = None
    category: int | None = None


def get_banners_btns(*, data: list | dict, level: int, menu_name: str, category: int | None = None, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    if isinstance(data, dict):
        for text, item in data.items():
            if item == "back":
                keyboard.add(InlineKeyboardButton(text=text,
                                                callback_data=AdminCallBack(
                                                    level=level,
                                                    menu_name=menu_name,
                                                    category=None,
                                                ).pack()))
                continue
            keyboard.add(InlineKeyboardButton(text=text,
                                                callback_data=AdminCallBack(
                                                    level=level+1,
                                                    menu_name=item,
                                                    category=category
                                                ).pack()))
    else:
        for item in data:
            keyboard.add(InlineKeyboardButton(text=item.name,
                                            callback_data=AdminCallBack(level=level, menu_name=menu_name,
                                                                        category=item.id).pack()))
        


    return keyboard.adjust(*sizes).as_markup()

def get_cancel_btns(*, level, menu_name, category: int | None = None):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Назад",
                                    callback_data=AdminCallBack(
                                        level=level-1,
                                        menu_name=menu_name,
                                        category=category,
                                    ).pack()))
    
    return keyboard.as_markup()