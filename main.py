import os
import discord
from discord.ext import commands
from utils import *
import motor.motor_asyncio
from strings import *


bot = commands.Bot('.', description="Grabbing those announcement ya")

if __name__ == "__main__":
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension("cogs." + filename[:-3])


@bot.event
async def on_ready():
    print("doing some database task... ", end="")
    coll = motor.motor_asyncio.AsyncIOMotorClient()[DB_NAME][SERVER_DATA_NAME]

    guild: discord.Guild
    for guild in bot.guilds:
        await init_server_db(guild, coll)
        
    print("DONE!")

    print("Bot is ready!")
    print(f"Bot username: {bot.user}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    coll = motor.motor_asyncio.AsyncIOMotorClient()[DB_NAME][SERVER_DATA_NAME]
    await init_server_db(guild, coll)


@bot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension_name: str):
    try:
        bot.reload_extension("cogs." + extension_name)
        msg = "Reloaded " + extension_name
    except commands.ExtensionNotFound:
        msg = f"{extension_name} does not exist!"
    except (commands.ExtensionNotLoaded, commands.ExtensionFailed):
        msg = "Something went wrong while loading " + extension_name
    
    await ctx.send(msg, delete_after=5)


bot.run(get_token(), bot=True, reconnect=True)
