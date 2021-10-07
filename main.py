import os
from discord.ext import commands
from utils import *


bot = commands.Bot('.', description="Grabbing those announcement ya")

if __name__ == "__main__":
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension("cogs." + filename[:-3])


@bot.event
async def on_ready():
    print("Bot is ready!")
    print(f"Bot username: {bot.user}")

@bot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension_name: str):
    try:
        bot.reload_extension("cogs." + extension_name)
    except commands.ExtensionNotFound:
        msg = f"{extension_name} does not exist!"
    except (commands.ExtensionNotLoaded, commands.ExtensionFailed):
        msg = "Something went wrong while loading " + extension_name
    finally:
        msg = "Reloaded " + extension_name
    
    await ctx.send(msg, delete_after=5)


bot.run(get_token(), bot=True, reconnect=True)
