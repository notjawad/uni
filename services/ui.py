from io import BytesIO

import discord
import httpx
from httpx import Timeout

from helpers.utils import json_to_base64


class UI:
    def __init__(self, base_url: str = "http://localhost:3000/api"):
        self.base_url = base_url

    async def welcome_card(
        self, avatar: str, member_count: str, username: str
    ) -> discord.File:
        data = json_to_base64(
            {"avatar": avatar, "member_count": member_count, "username": username}
        )

        url = f"{self.base_url}/welcome?data={data}&nodeId=capture"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=Timeout(10, 60))
            return discord.File(BytesIO(response.content), "welcome.png")
