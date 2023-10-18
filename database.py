from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, select, Date, delete, update, extract, Time
import datetime

Base = declarative_base()
engine = create_async_engine('mysql+aiomysql://user:password@host/db')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    userid = Column(String(50), default='0')
    time = Column(Time, default=datetime.time(15, 0))


class Birthdays(Base):
    __tablename__ = 'birthdays'
    id = Column(Integer, primary_key=True)
    userid = Column(String(50), default='0')
    date = Column(Date, default=datetime.date.today())
    name = Column(String(100), default='noname')


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_user(userid):
    async with async_session() as session:
        async with session.begin():
            user = Users(userid=userid)
            session.add(user)
            await session.commit()


async def add_birthday(userid, date, name):
    async with async_session() as session:
        async with session.begin():
            birthday = Birthdays(userid=userid, date=date, name=name)
            session.add(birthday)
            await session.commit()


async def get_id_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Users.id).where(Users.userid == userid))).scalars().all()


async def get_time_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Users.time).where(Users.userid == userid))).scalars().all()


async def get_dates_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Birthdays.date).where(Birthdays.userid == userid))).scalars().all()


async def get_names_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Birthdays.name).where(Birthdays.userid == userid))).scalars().all()


async def get_birthday_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Birthdays.id).where(Birthdays.userid == userid))).scalars().all()

async def get_dates():
    async with async_session() as session:
        return (await session.execute(select(Birthdays.date))).scalars().all()


async def get_names():
    async with async_session() as session:
        return (await session.execute(select(Birthdays.name))).scalars().all()


async def get_userid():
    async with async_session() as session:
        return (await session.execute(select(Birthdays.userid))).scalars().all()

async def get_birthday_on_userid_sorted(userid):
    async with AsyncSession(engine) as session:
        # Создаем сессию
        async with session.begin():
            # Создаем запрос для выбора даты и идентификатора
            stmt = select(Birthdays.id).where(Birthdays.userid == userid).order_by(extract('month', Birthdays.date),
                extract('day', Birthdays.date))
            result = await session.execute(stmt)

            # Извлекаем идентификаторы
            ids = [row[0] for row in result.fetchall()]

            # Возвращаем список идентификаторов
            return ids


async def delete_birthday(id):
    async with async_session() as session:
        await session.execute(delete(Birthdays).where(Birthdays.id == id))
        await session.commit()


async def update_time(userid, time):
    async with async_session() as session:
        async with session.begin():
            stmt = update(Users).where(Users.userid == userid).values(time=time)
            await session.execute(stmt)
            await session.commit()
