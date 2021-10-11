import asyncio
import json
from strings import *
from typing import *
from discord.ext import tasks, commands
import motor.motor_asyncio
import discord
import aiohttp
import bs4
from dataclasses import dataclass


@dataclass
class Announcement:
    title: str
    link: str


@dataclass
class ChannelRole:
    channel: discord.TextChannel
    role: Union[discord.Role, None]


class Announcer(commands.Cog):
    """UMP announcement grabber extension!"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # connect to locally hosted mongodb
        self.db_client = motor.motor_asyncio.AsyncIOMotorClient()
        self.db = self.db_client[DB_NAME]
        self.session = aiohttp.ClientSession()

    @commands.Cog.listener()
    async def on_ready(self):
        print("UMP announcement grabber is loaded!")

    async def post_load(self):
        if not self.bot.is_ready():
            self.bot.loop.create_task(self.post_load())
            return

        await self.login_ecomm()

        self.channel_role_list: List[ChannelRole] = []

        # channel: discord.TextChannel = self.bot.get_channel(894888338182529044)
        # self.active_channels.append(channel)

        coll = self.db[SERVER_DATA_NAME]
        cursor = coll.find({"announcement_channel": {"$exists": 1}})

        async for server_data in cursor:
            guild: Union[discord.Guild, None] = self.bot.get_guild(
                server_data["_id"])

            if guild == None:
                continue

            role: Union[discord.Role, None] = guild.get_role(
                server_data.get("role_to_mention", 0))
            text_channel: Union[discord.TextChannel, None] = self.bot.get_channel(
                server_data["announcement_channel"])

            if text_channel != None:
                self.channel_role_list.append(
                    ChannelRole(
                        text_channel,
                        role))

        self.update_announcement_db.start()

    def __del__(self):
        self.bot.loop.run_until_complete(self.session.get(
            "https://std-comm.ump.edu.my/ecommstudent/Logout"))
        self.bot.loop.run_until_complete(self.session.close())
        self.bot.loop.run_until_complete(asyncio.sleep(1))

    def cog_unload(self):
        self.bot.loop.run_until_complete(self.session.get(
            "https://std-comm.ump.edu.my/ecommstudent/Logout"))
        self.bot.loop.run_until_complete(self.session.close())
        self.bot.loop.run_until_complete(asyncio.sleep(1))

    @staticmethod
    def clean_description(html_text: str) -> str:
        soup = bs4.BeautifulSoup(html_text, "html.parser")

        something = soup.find_all("td", class_="contentBgColor")[1]

        something2 = something.find_all("font")[2]

        dirty_text: str = something2.get_text()

        little_cleaned_text = ' '.join(
            [stuff for stuff in dirty_text.split("\t") if stuff])
        little_cleaned_text = ''.join(
            [stuff for stuff in little_cleaned_text.split("\xa0") if stuff])
        little_cleaned_text = '\n'.join(
            [stuff for stuff in little_cleaned_text.split("\r\n") if stuff])
        little_cleaned_text = '\n'.join(
            [stuff for stuff in little_cleaned_text.split("\n") if stuff])
        little_cleaned_text = ' '.join(
            [stuff for stuff in little_cleaned_text.split(" ") if stuff])
        little_cleaned_text = '\n'.join(
            [stuff for stuff in little_cleaned_text.split("\n ") if stuff])
        full_cleaned_text = "\n\n".join(
            [stuff for stuff in little_cleaned_text.split("\n\n") if stuff])

        return full_cleaned_text

    async def post_announcement(self, announcement: Announcement):
        async with self.session.get(announcement.link) as response:
            html_text = await response.text()

        cleaned_description = await self.bot.loop.run_in_executor(None, self.clean_description, html_text)

        embed_data = {
            "title": announcement.title[:255],
            "type": "rich",
            "description": cleaned_description,
            "color": 0x1abc9c,  # color logo UMP aku rase
            "thumbnail": {
                "url": "https://www.ump.edu.my/download/logo-ump-jawi-2021.png"
            },
            "url": announcement.link
        }

        if len(embed_data["description"]) > 1000:
            embed_data["description"] = embed_data["description"][:1000] + "..."

        final_embed = discord.Embed.from_dict(embed_data)

        for channel_role in self.channel_role_list:
            if channel_role.role != None:
                try:
                    await channel_role.channel.send(
                        f"{channel_role.role.mention} {embed_data['title']}",
                        embed=final_embed)
                except discord.Forbidden:
                    continue
            else:
                try:
                    await channel_role.channel.send(embed=final_embed)
                    # TODO: need a special role so bot can mention them when a new announcement arrive
                except discord.Forbidden:
                    continue

            await asyncio.sleep(5)

    @tasks.loop(minutes=5.0)
    async def update_announcement_db(self):
        collection = self.db["announcement"]

        announcements = await self.get_announcements()
        announcements.reverse()  # insert the oldest first then the latest
        for announcement in announcements:
            if await collection.count_documents({"_id": announcement.link}) == 0:
                await collection.insert_one({"_id": announcement.link, "title": announcement.title})

                await self.post_announcement(announcement)

    async def get_announcements(self):
        """Get latest annoucements with the latest first

        List of announcement page
        1. https://std-comm.ump.edu.my/ecommstudent/cms/announcement/call2.jsp?action=Y
        2. https://std-comm.ump.edu.my/ecommstudent/cms/announcement/call2_general.jsp?action=Y
        3. https://std-comm.ump.edu.my/ecommstudent/cms/announcement/call2.jsp?action=N

        Number 1 seems to contain all kind of announcement, idk 100% yet
        Number 2 is the announcement you see when you first arrive in ecomm
        Number 3 is for the unofficial announcement
        """
        async with self.session.get("https://std-comm.ump.edu.my/ecommstudent/cms/announcement/call2.jsp?action=Y") as response:
            text = await response.text()
            # TODO: Check if logged in or not

        announcements = await self.bot.loop.run_in_executor(None, self.parse_announcement_html, text)

        return announcements

    @staticmethod
    def parse_announcement_html(html_text: str):
        root = "https://std-comm.ump.edu.my/ecommstudent/cms/announcement/"

        soup = bs4.BeautifulSoup(html_text, "html.parser")

        announcements: List[Announcement] = []

        announcement: bs4.element.Tag
        for announcement in soup.find_all("table")[0].find_all("tr")[1:]:
            title = announcement.get_text().replace("\t", "").replace("\n", "")

            link = root + announcement.find('a').get("href").split("'")[1]

            announcements.append(Announcement(title, link))

        for announcement in soup.find_all("table")[1].find_all("tr")[1:]:
            title = announcement.get_text().replace("\t", "").replace("\n", "")

            link = root + announcement.find('a').get("href").split("'")[1]

            announcements.append(Announcement(title, link))

        return announcements

    async def login_ecomm(self):
        with open("./secrets/login_deets.json", "r") as f:
            login_detail = json.load(f)

        await self.session.post("https://std-comm.ump.edu.my/ecommstudent/Login", data=login_detail)

    @commands.command(aliases=["set_role_to_mention"])
    @commands.has_guild_permissions(administrator=True)
    async def produce_role_form_message(self, ctx: commands.Context, role: discord.Role):
        """The role given will be used to mention when a new announcement arrive
        
        For now, there is no react to get role function so the admin need to give it manually to the people
        but you can also use another bot for this stuff!
        """
        coll = self.db[SERVER_DATA_NAME]

        result: Dict = await coll.find_one_and_update({"_id": ctx.guild.id}, {"$set": {"role_to_mention": role.id}})

        channel_id: Union[int, None] = result.get("announcement_channel", None)

        if channel_id != None:
            for channel_role in self.channel_role_list:
                if channel_role.channel.id == channel_id:
                    channel_role.role = role
                    break

        # message: discord.Message = await ctx.send(f"React :+1: to subscribe to ecomm announcement. React :-1: to remove {role.mention}")
        # await message.add_reaction("👍")
        # await message.add_reaction("👎")

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def use_this_channel(self, ctx: commands.Context):
        result: Dict = await self.db[SERVER_DATA_NAME].find_one_and_update(
            {"_id": ctx.guild.id},
            {"$set": {"announcement_channel": ctx.channel.id}})

        old_channel_id: Union[int, None] = result.get(
            "announcement_channel", None)

        if old_channel_id != None:
            for channel_role in self.channel_role_list:
                if old_channel_id == channel_role.channel.id:
                    channel_role.channel = ctx.channel
                    break
            else:
                role_id: Union[int, None] = result.get("role_to_mention", None)
                if role_id != None:
                    role = ctx.guild.get_role(role_id)
                else:
                    role = None

                role: Union[discord.Role, None]
                self.channel_role_list.append(
                    ChannelRole(
                        ctx.channel,
                        role))

        await ctx.message.delete()
        await ctx.send("Using this channel to post announcement", delete_after=5)

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def clear_role_to_mention(self, ctx: commands.Context):
        coll = self.db[SERVER_DATA_NAME]
        result: Union[Dict, None] = await coll.find_one_and_update(
            {"_id": ctx.guild.id},
            {"$unset": {"role_to_mention": ""}})

        if result != None:
            channel_id: Union[int, None] = result.get(
                "announcement_channel", None)
            if channel_id != None:
                for channel_role in self.channel_role_list:
                    if channel_role.channel.id == channel_id:
                        channel_role.role = None
                        break

        await ctx.send("Cleared role_to_mention for your server!")


def setup(bot: commands.Bot):
    bot.add_cog(Announcer(bot))
    announcer: Announcer = bot.get_cog("Announcer")
    bot.loop.create_task(announcer.post_load())
