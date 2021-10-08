import json
import motor.motor_asyncio
import pymongo.errors
import discord


def get_token() -> str:
    """This is where we get our token!"""
    with open("./secrets/discord_token.json", "r") as f:
        return json.load(f)["token"]


async def init_server_db(guild: discord.Guild, collection: motor.motor_asyncio.AsyncIOMotorCollection):
    """|coro|"""
    try:
        await collection.insert_one({"_id": guild.id})
    except pymongo.errors.DuplicateKeyError:
        pass  # server is already in the db
