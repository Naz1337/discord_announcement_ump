import json


def get_token() -> str:
    """This is where we get our token!"""
    with open("./secrets/discord_token.json", "r") as f:
        return json.load(f)["token"]
