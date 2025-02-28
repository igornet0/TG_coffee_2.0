from aiogram import types
from asyncio import sleep

async def message_edit(last_message: types.Message, text: str,
                       reply_markup=None, media=None, edit: bool=True):
    
    if not last_message.photo is None and edit and media is None:
        await last_message.delete()
        edit = False
    
    if not edit:
        return await last_message.answer(text, reply_markup=reply_markup)

    if media is None:
        if text is None and not reply_markup is None:
            return await last_message.edit_reply_markup(reply_markup=reply_markup)
        return await last_message.edit_text(text, reply_markup=reply_markup)
    
    return await last_message.edit_media(media=media, caption=text, reply_markup=reply_markup)

