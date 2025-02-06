# from aiogram import Router, F
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.types import Message, ReplyKeyboardRemove
# from kbds.inline import menu_keyboard

# router = Router()

# class OrderCoffee(StatesGroup):
#     choosing_coffee = State()
#     confirming_order = State()

# @router.message(Command("start"))
# async def cmd_start(message: Message, state: FSMContext):
#     await message.answer(
#         text="Добро пожаловать! Пожалуйста, выберите напиток:",
#         reply_markup=menu_keyboard()
#     )
#     await state.set_state(OrderCoffee.choosing_coffee)

# @router.message(OrderCoffee.choosing_coffee, F.text.in_(["Эспрессо", "Капучино", "Латте", "Американо"]))
# async def coffee_chosen(message: Message, state: FSMContext):
#     await state.update_data(chosen_coffee=message.text)
#     await message.answer(
#         text=f"Вы выбрали {message.text}. Подтвердите заказ командой /confirm или отмените командой /cancel.",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     await state.set_state(OrderCoffee.confirming_order)

# @router.message(Command("confirm"), OrderCoffee.confirming_order)
# async def confirm_order(message: Message, state: FSMContext):
#     user_data = await state.get_data()
#     coffee = user_data.get('chosen_coffee')
#     # Здесь можно добавить логику отправки заказа на предприятие
#     await message.answer(f"Ваш заказ на {coffee} принят и отправлен на предприятие.")
#     await state.clear()

# @router.message(Command("cancel"), OrderCoffee.confirming_order)
# async def cancel_order(message: Message, state: FSMContext):
#     await message.answer("Ваш заказ отменен.", reply_markup=ReplyKeyboardRemove())
#     await state.clear()