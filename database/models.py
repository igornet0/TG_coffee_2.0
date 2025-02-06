# наши модели для БД

from sqlalchemy import DateTime, ForeignKey, Float, String, Text, BigInteger, func, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# создаем базовый класс для всех остальных
class Base(DeclarativeBase):
    # дата создания записи в БД, тип DateTime, func.now() - текущее время
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    # дата изменения записи в БД
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# класс для банера
class Banner(Base):
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # имя банера
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)


# категория товара
class Category(Base):
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    image: Mapped[str] = mapped_column(String(150), nullable=True)

# место доставки
class Place(Base):
    __tablename__ = 'place'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class Sirop(Base):
    __tablename__ = 'sirop'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[int] =  mapped_column(Float, nullable=True)

class Dop(Base):
    __tablename__ = 'dop'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[int] =  mapped_column(Float, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id', ondelete='CASCADE'), nullable=False)

# создаем таблицу для продуктов
class Product(Base):
    # название таблицы в БД
    __tablename__ = 'product'

    # поля (атрибуты), где указываем типы данных полей через Mapped
    # mapped_column - дополнительные свойства для атрибутов
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # максимальная длина 150 символов, nullable=False - не может быть пустым
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # указываем тип Text вместо VarChar, чтобы хранить больший объем текста для описания
    description: Mapped[str] = mapped_column(Text, nullable=True)
    weight: Mapped[str] = mapped_column(Text, nullable=False)  # Поле для веса товара (целое число)
    # 4 знака максимум, 2 знака после запятой
    price: Mapped[str] = mapped_column(Text, nullable=False)
    # image: Mapped[str] = mapped_column(String(150), nullable=False)
    # id категории, CASCADE - если удаляется категория, то все продукты также удалятся
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id', ondelete='CASCADE'), nullable=False)
    # ссылка на категорию товара
    category: Mapped['Category'] = relationship(backref='product')


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # идентификатор пользователя в телеграмме
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True)
    place: Mapped[int] = mapped_column(Integer, nullable=True)


class Cart(Base):
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # идентификатор пользователя в телеграмме
    # если пользователя удаляют, то его корзина тоже удаляется
    status: Mapped[str] = mapped_column(String(20), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    # если продукт удаляется, то корзина с этим товаром тоже удаляется
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    # количество товара
    quantity: Mapped[int]
    weight: Mapped[int]
    price: Mapped[float]
    dop: Mapped[int] = mapped_column(ForeignKey('dop.id', ondelete='CASCADE'), nullable=True)
    sirop: Mapped[int] = mapped_column(ForeignKey('sirop.id', ondelete='CASCADE'), nullable=True)
    # обратная взаимосвязь с таблицами user и product,
    # чтобы выбрать все корзины пользователя и дополнительную информацию о товаре, который заказан
    user: Mapped['User'] = relationship(backref='cart')
    product: Mapped['Product'] = relationship(backref='cart')


class AdminList(Base):
    __tablename__ = 'admin'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    place: Mapped[int] = mapped_column(Integer, nullable=True)

class Order(Base):
    __tablename__ = 'order'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    place: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[str] = mapped_column(String(100), nullable=False)
    cards: Mapped[str] = mapped_column(String(150), nullable=False)
    type_give: Mapped[str] = mapped_column(String(20), nullable=False)