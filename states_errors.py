from aiogram.dispatcher.filters.state import State, StatesGroup


class DeleteBirthdayState(StatesGroup):
    Numbers = State()

class AddBirthdayState(StatesGroup):
    Name = State()
    Date = State()


class AddTimeState(StatesGroup):
    Data = State()


class Cancel(NameError):
    pass