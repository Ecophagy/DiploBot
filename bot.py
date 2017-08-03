import discord
from discord.ext import commands
import asyncio
import json

description = '''Bot for receiving diplomacy commands'''
bot = commands.Bot(command_prefix='!', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def sleep():
    """Sleep for 5 seconds"""
    await asyncio.sleep(5)
    await bot.say('Done sleeping')


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


with open('config.json') as data_file:
    data = json.load(data_file)

bot.run(data["token"])