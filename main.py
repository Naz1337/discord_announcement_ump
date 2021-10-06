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

bot.run(get_token(), bot=True, reconnect=True)
