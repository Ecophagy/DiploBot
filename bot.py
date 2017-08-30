import discord
from discord.ext import commands
import json
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from db import Movelist, Base, Database_Location, Country
from contextlib import contextmanager

description = '''Bot for receiving diplomacy commands'''
bot = commands.Bot(command_prefix='!', description=description)

userlist = []
gm = None


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
    print('------')
    populate_user_list()
    print('User list created')
    set_gm()
    print('Set GM')


def populate_user_list():
    """Populate list of users from players"""
    with session_scope() as session:
        for server in bot.servers: #NOTE: If the bot is in more than one server this will need something smarter
            for row in session.query(Movelist):
                member = discord.utils.find(lambda m: m.id == row.discord_id, server.members)
                userlist.append(member)


def set_gm():
    """Find and set gm"""
    with session_scope() as session:
        for server in bot.servers:
            for row in session.query(Movelist):
                member = discord.utils.find(lambda m: m.id == row.discord_id, server.members)
                if user_is_gm(member):
                    global gm
                    gm = member
                    return

@bot.command(pass_context=True)
async def moves(ctx):
    """Send your moves to the bot"""
    if ctx.message.channel.is_private:
        with session_scope() as session:
            row = session.query(Movelist).filter(Movelist.discord_id == ctx.message.author.id).one()
            if not row.eliminated:
                row.moveset = ctx.message.content[7:]  # Remove "!moves"
                await bot.say('Moves received! If you wish to change them, please resubmit them in their entirety')
                #If all players have submitted moves, tell the GM
                if session.query(Movelist).filter(and_(Movelist.moveset == None), (Movelist.eliminated == False)).count() == 0:
                    await bot.send_message(gm, 'All moves have been submitted')
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
                    userlist.append(member)
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
        total = session.query(Movelist).filter(Movelist.eliminated.is_(False)).count()
        submitted = session.query(Movelist).filter(Movelist.moveset.isnot(None)).count()
    await bot.say(str(submitted) + "/" + str(total) + " players have submitted")


@bot.command(pass_context=True)
async def eliminate(ctx):
    """GM Only: Eliminate a country"""
    if ctx.message.author == gm:
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
    if ctx.message.author == gm:
        with session_scope() as session:
            for row in session.query(Movelist):
                row.moveset = None
        await bot.say('Moves reset')
    else:
        await bot.say('Only the GM can reset moves')


@bot.command(pass_context=True)
async def getmoves(ctx):
    """GM Only: Get the moves"""
    if ctx.message.author == gm:
        with session_scope() as session:
            for country, moves in session.query(Movelist.country, Movelist.moveset).all():
                msg = '``` __{0}__ \r {1}```'.format(country, moves)
                await bot.send_message(ctx.message.author, msg)


def main():
    with open('config.json') as data_file:
        data = json.load(data_file)

    bot.run(data["token"])

if __name__ == "__main__":
    main()