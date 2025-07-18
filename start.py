import asyncio
import logging
import logging.handlers

from typing import List, Optional

import discord
from discord.ext import commands 
from aiohttp import ClientSession
from decouple import config

class CustomBot(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        web_client: ClientSession,
        testing_guild_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions
        self.color = 0x3388BB

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            await self.load_extension(extension)

        if not self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game("/ayuda para ver los comandos."))
        print(
            f"Logged in as\n"
            f"\tName:    {self.user.name}\n"
            f"\tID:      {self.user.id}\n"
            f"\tVersion: discord.py {discord.__version__}"
        )

async def setup():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


    async with ClientSession() as our_client:
        exts = ['cogs.general', 'cogs.welcome', 'cogs.help', 'cogs.music', 'cogs.anime_art', 'cogs.utilities']
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        async with CustomBot(
            commands.when_mentioned_or('?'),
            help_command=None,
            web_client=our_client,
            initial_extensions=exts,
            intents=intents,
            testing_guild_id=config('PISHA_SERVER'),
        ) as bot:
            await bot.start(config('TOKEN'))


if __name__=='__main__':
    asyncio.run(setup())