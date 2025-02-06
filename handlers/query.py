from aiogram.types import InlineQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_get_products
)

from kbds.inline import get_menu

query_router = Router()

@query_router.inline_query(lambda x: True)
async def inline_query_search(inline_query: InlineQuery, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    category = data.get("category", None)
    if not category:
        return
    products = await orm_get_products(session=session, category_id=category)

    await inline_query.answer(get_menu(products, inline_query.query, category), 
                              cache_time=5, 
                              is_personal=True)