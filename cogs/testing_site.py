import discord
from cogs.ump_announcer import Announcer
from discord.ext import commands
import asyncio

class TestingDB(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Testing extension loaded!")
    
    @commands.command()
    async def stuff(self, ctx: commands.Context):
        announcer: Announcer = self.bot.get_cog("Announcer")
        db = announcer.db_client["test_db"]
        coll = db["server_data"]

    @commands.command()
    async def st(self, ctx: commands.Context):
        aha: discord.Message = await ctx.send("Whats up nation")
        await aha.add_reaction("👍")
        await asyncio.sleep(2)
        await aha.delete()
        await ctx.message.delete()


def setup(bot: commands.Bot):
    bot.add_cog(TestingDB(bot))
