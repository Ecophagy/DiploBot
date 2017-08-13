import discord
from discord.ext import commands
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Movelist, Base, Database_Location, Country
from contextlib import contextmanager

description = '''Bot for receiving diplomacy commands'''
bot = commands.Bot(command_prefix='!', description=description)


def user_is_gm(user):
    with open('config.json') as data_file:
        data = json.load(data_file)
        gm_id = data["gm"]
        return user.id == gm_id


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    engine = create_engine(Database_Location)
    Base.metadata.Bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    engine = create_engine(Database_Location)
    Base.metadata.create_all(engine)
    print('Database created')


@bot.command(pass_context=True)
async def moves(ctx):
    """Send your moves to the bot"""
    if ctx.message.channel.is_private:
        with session_scope() as session:
            moves = session.query(Movelist).filter(Movelist.discord_id == ctx.message.author.id).one()
            if not moves.eliminated:
                moves.moveset = ctx.message.content
                await bot.say('Moves received! If you wish to change them, please resubmit them in their entirety')
            else:
                await bot.say('You have been eliminated so moves have not been recorded')
    else:
        await bot.say('You can only send moves in private!')


@bot.command(pass_context=True)
async def add(ctx):
    """Country Name

    Add a player to the game as country"""
    command, country, player = ctx.message.content.split(" ")
    if country in Country.__members__:
        member = discord.utils.find(lambda m: m.name == player, ctx.message.channel.server.members)
        if member != None:
            with session_scope() as session:
                if session.query(Movelist).filter(Movelist.country == country).one_or_none() is None:
                    new_movelist = Movelist(country=country,
                                        playername=player,
                                        discord_id=member.id,
                                        moveset=None)
                    session.add(new_movelist)
                    await bot.say('Player added')
                else:
                    await bot.say('That country has already been allocated')
        else:
            await bot.say('Invalid Player')
    else:
        await bot.say('Invalid Country')

@bot.command()
async def submitted():
    """Find out how many people have submitted moves"""
    with session_scope() as session:
        total = session.query(Movelist).filter(Movelist.eliminated == False).count()
        submitted = session.query(Movelist).filter(Movelist.moveset != None).count()
    await bot.say(str(submitted) + "/" + str(total) + " players have submitted")

@bot.command(pass_context=True)
async def eliminate(ctx):
    """GM Only: Eliminate a country"""
    if user_is_gm(ctx.message.author):
        with session_scope() as session:
            command, country = ctx.message.content.split(" ")
            row = session.query(Movelist).filter(Movelist.country == country).one_or_none()
            if row is None:
                await bot.say("Invalid Country")
            else:
                row.eliminated = True
                await bot.say('Country Eliminated')
    else:
        await bot.say('Only the GM can eliminate players!')


@bot.command(pass_context=True)
async def reset(ctx):
    """GM Only: Reset moves for a new turn"""
    if user_is_gm(ctx.message.author):
        with session_scope() as session:
            for row in session.query(Movelist):
                row.moveset = None
        await bot.say('Moves reset')
    else:
        await bot.say('Only the GM can reset moves')


@bot.command(pass_context=True)
async def test(ctx):
    if ctx.message.channel.is_private:
        counter = 0
        tmp = await bot.say('Calculating messages...')
        async for log in bot.logs_from(ctx.message.channel, limit=100):
            if log.author == ctx.message.author:
                counter += 1

        await bot.edit_message(tmp, 'You have {} messages.'.format(counter))
    else:
        await bot.say('I only test in private')


def main():
    with open('config.json') as data_file:
        data = json.load(data_file)

    bot.run(data["token"])

if __name__ == "__main__":
    main()