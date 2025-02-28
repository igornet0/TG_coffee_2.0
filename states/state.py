from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    waiting_for_phone = State()
    waiting_text = State()

class PlaceState(StatesGroup):
    waiting_place = State()