from aiogram import types
from asyncio import sleep

async def message_edit(last_message: types.Message, text: str, media=None, 
                       reply_markup=None, edit: bool=True):
    if not last_message.photo is None and edit:
        await last_message.delete()
        edit = False
    
    if not edit:
        if media:
            return await last_message.answer_photo(media, text, reply_markup=reply_markup)
        return await last_message.answer(text, reply_markup=reply_markup)

    if media is None:
        return await last_message.edit_text(text, reply_markup=reply_markup)
    return await last_message.edit_media(media=media, caption=text, reply_markup=reply_markup)

