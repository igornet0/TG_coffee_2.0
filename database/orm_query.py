# файл для query запросов

import math
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Banner, Cart, Category, Product, User, Place, Dop, Sirop, Order


############### Работа с баннерами (информационными страницами) ###############

async def orm_add_banner_description(session: AsyncSession, data: dict):
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, about, cart, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    # если что-то есть, то выходим
    if result.first():
        return
    # иначе создаем баннеры
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, id: int, image: str):
    query = update(Banner).where(Banner.id == id).values(image=image)
    await session.execute(query)
    await session.commit()

async def orm_change_banner_text(session: AsyncSession, id: int, text: str):
    query = update(Banner).where(Banner.id == id).values(description=text)
    await session.execute(query)
    await session.commit()

async def orm_get_banner(session: AsyncSession, page: str | int):
    if isinstance(page, int):
        query = select(Banner).where(Banner.id == page)
    else:
        query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_banners(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()

############################ Категории ######################################

async def orm_get_categories(session: AsyncSession, id: int | None = None):
    if not id is None:
        query = select(Category).where(Category.id == id)
    else:
        query = select(Category)
    result = await session.execute(query)
    return result.scalars().all() if id is None else result.scalar()


async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()

async def orm_add_category(session: AsyncSession, name: str, image: str | None = None):
    session.add(Category(name=name, image=image))
    await session.commit()

############################ Места ######################################

async def orm_get_place(session: AsyncSession, where: None | int = None) -> list[Place] | Place:
    if where:
        query = select(Place).where(Place.id == where)
    else:
        query = select(Place)
    result = await session.execute(query)
    return result.scalars().all() if where is None else result.scalar()


async def orm_create_places(session: AsyncSession, places: list):
    query = select(Place)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Place(name=name) for name in places])
    await session.commit()

############ Админка: добавить/изменить/удалить товар ########################

async def orm_create_dop(session: AsyncSession, dop: dict):
    query = select(Dop)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Dop(name=name, price=data[0], category_id=data[1]) for name, data in dop.items()])
    await session.commit()

async def orm_get_dops(session: AsyncSession, id_category:int):
    query = select(Dop).where(Dop.category_id == id_category)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_dop(session: AsyncSession, dop_id: int):
    query = select(Dop).where(Dop.id == dop_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_sirops(session: AsyncSession):
    query = select(Sirop)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_sirop(session: AsyncSession, sirop_id: int):
    query = select(Sirop).where(Sirop.id == sirop_id)
    result = await session.execute(query)
    return result.scalar()

# запрос для добавления продукта
async def orm_add_product(session: AsyncSession, data: dict):
    # создаем продукт, используя полученные данные с помощью машины состояний
    obj = Product(
        name=data["name"],
        description=data["description"],
        weight=data["weight"],
        price=data["price"],
        category_id=int(data["category"]),
    )
    # добавляем объект к сессии
    session.add(obj)
    # сохраняем изменения данной сессии (после этого запись добавится в нашу БД)
    await session.commit()

# запрос для получения списка всех товаров
async def orm_get_products(session: AsyncSession, category_id):
    # выбираем все записи конкретной категории Product из БД
    query = select(Product).options(joinedload(Product.category)).where(Product.category_id == int(category_id))
    # выполняем наш запрос через session и сохраняем
    result = await session.execute(query)
    # возвращаем всё что получили (scalars, all - для нормального вида)
    return result.scalars().all()


# запрос для получения отдельного продукта
async def orm_get_product(session: AsyncSession, product_id: int):
    # получаем товар с переданным id
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    # возвращаем один объект
    return result.scalar()


# запрос для обновления информации о продукте
async def orm_update_product(session: AsyncSession, product_id: int, data):
    # обновляем данные у конкретного продукта
    query = update(Product).where(Product.id == product_id).values(
        name=data["name"],
        description=data["description"],
        weight=data["weight"],
        price=data["price"],
        category_id=int(data["category"]),
    )
    await session.execute(query)
    # сохраняем изменения данной сессии (после этого запись изменится в нашей БД)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    # удаляем конкретный продукт
    query = delete(Product).where(Product.id == product_id)
    # выполняем запрос
    await session.execute(query)
    # сохраняем изменения в БД
    await session.commit()


##################### Добавляем юзера в БД #####################################

async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
) -> User:
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    # если пользователя по id телеграмма, то создаем нового
    user = result.first()
    if user is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()
        return await orm_get_user(session, user_id)
    else:
        return user[0]
    
async def orm_get_user(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_update_user_place(session: AsyncSession, user_id: int, place_id: int):
    query = update(User).where(User.user_id == user_id).values(place=place_id)
    await session.execute(query)
    await session.commit()

async def orm_update_user_phone(session: AsyncSession, user_id: int, phone: str):
    query = update(User).where(User.user_id == user_id).values(phone=phone)
    await session.execute(query)
    await session.commit()


######################## Работа с корзинами #######################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int, weight: int, dop: int, sirop: int, price: float):
    query = select(Cart).where(Cart.user_id == user_id, 
                               Cart.product_id == product_id, 
                               Cart.weight==weight,
                               Cart.dop==dop,
                               Cart.sirop==sirop,
                               Cart.status=="new").options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, status="new", product_id=product_id, 
                         weight=weight, dop=dop, sirop=sirop, price=price,
                         quantity=1))
        await session.commit()


async def orm_get_user_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id, Cart.status=="new").options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, 
                               product_id: int, dop: int, sirop: int):
    query = select(Cart).where(Cart.user_id == user_id, 
                               Cart.product_id == product_id, 
                               Cart.dop == dop, Cart.sirop == sirop).options(joinedload(Cart.product))

    cart = await session.execute(query)
    cart = cart.scalar()
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return cart
    else:
        await session.delete(cart)
        await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False
    
async def orm_update_status_card(session: AsyncSession, card_id: int, new_status: str):
    query = update(Cart).where(Cart.id == card_id).values(status=new_status)
    await session.execute(query)
    await session.commit()

async def orm_add_order(session: AsyncSession, user_id: int, place: int, 
                        data: str, cards: str, type_give: str):
    # cards = "/".join([str(card.id) for card in cards])
    
    session.add(Order(user_id=user_id, status="send", place=place, 
                         data=data, cards=cards, type_give=type_give))
    await session.commit()

async def orm_add_admin(session: AsyncSession, admin_id):
    pass