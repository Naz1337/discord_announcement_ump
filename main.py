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
async def reload(ctx: commands.Context, extension_name: str):
    try:
        bot.reload_extension("cogs." + extension_name)
    except commands.ExtensionNotFound:
        await ctx.send(f"{extension_name} does not exist!")
    except (commands.ExtensionNotLoaded, commands.ExtensionFailed):
        await ctx.send("Something went wrong while loading " + extension_name)
    finally:
        await ctx.send("Reloaded " + extension_name)


bot.run(get_token(), bot=True, reconnect=True)
