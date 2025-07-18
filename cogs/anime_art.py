import asyncio
import io
import random
import xml.etree.ElementTree as ET
import logging
from typing import Any, Optional, Dict, List

import aiohttp
import discord
from discord.ext import commands
from utils.response import reply
log = logging.getLogger('discord')

class AnimeArtCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.danbooru_url = 'https://danbooru.donmai.us'
        self.safebooru_url = 'https://safebooru.org'
        self.danbooru_headers = {
            'User-Agent': 'Agente de Usuario del bot de discord amigo', 
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Brave";v="108"',
            'if-none-match':'W/"37ca6f8b1f9c2e77419c12599351968c"'
        }

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_xml(self, url: str, params: Optional[Dict[str, Any]] = None) -> ET.Element:
        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return ET.fromstring(text)

    async def _download_bytes(self, url: str) -> bytes:
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()
        
    @commands.hybrid_command(name="search_tags", description="Autocomplete tags for search in booru image boards")
    async def search_tags(self, ctx: commands.Context, *, query: str) -> None:
        await ctx.defer()
        if not query:
            return await reply(ctx, content='Se requiere al menos un tag.')
        try:
            data = await self._fetch_json(
                f"{self.danbooru_url}/autocomplete.json",
                params={
                    "search[query]": query,
                    "search[type]": "tag_query",
                    "version":1,
                    "limit": 10,
                }
            )
            tags = [item['value'] for item in data]
            if not tags:
                return await reply(ctx, content="No se encontraron tags.", ephemeral=True)

            embed = discord.Embed(
                title=f"Autocomplete para `{query}`",
                color=self.bot.color
            )
            embed.add_field(
                name="Tags",
                value="\n".join(f"`{t}`" for t in tags),
                inline=False
            )
            await reply(ctx, embed=embed)
        except Exception:
            log.exception("Error en search_tags")
            await reply(ctx, content="Error al buscar tags.")

    @commands.hybrid_command(name="danbooru", description="Search an image from Danbooru")
    async def danbooru(self, ctx: commands.Context, *, tags: str) -> None:
        await ctx.defer()
        if not tags:
            return await reply(ctx, content='Se requiere al menos un tag.')
        tags = tags.split()
        try:
            fixed: List[str] = []
            # Autocomplete individual tags
            for tag in tags:
                data = await self._fetch_json(
                    f"{self.danbooru_url}/autocomplete.json",
                    params={"search[query]": tag, "search[type]": "tag_query", "limit": 1}
                )
                if not data:
                    return await reply(ctx, content=f"Tag `{tag}` no encontrado.")
                fixed.append(data[0]['value'])

            posts = await self._fetch_json(
                f"{self.danbooru_url}/posts.json",
                params={"tags": " ".join(fixed)}
            )
            if not posts:
                return await reply(ctx, content="No se encontraron imágenes.")

            post = random.choice(posts)
            file_url = post.get('file_url')
            if not file_url:
                return await reply(ctx, content="Error al conseguir URL.")

            data = await self._download_bytes(file_url)
            filename = f"{post['md5']}.{post['file_ext']}"
            file = discord.File(io.BytesIO(data), filename=filename)
            content = f"Tags: `{' '.join(fixed)}`"
            await reply(ctx, content=content, file=file)
        except Exception:
            log.exception("Error en danbooru")
            await reply(ctx, content="Error al obtener imagen.")

    @commands.hybrid_command(name="danrandom", description="Search a random image from Danbooru")
    async def danrandom(self, ctx: commands.Context) -> None:
        await ctx.defer()
        try:
            post = await self._fetch_json(f"{self.danbooru_url}/posts/random.json")
            file_url = post.get('file_url')
            if not file_url:
                return await reply(ctx, content="La publicación aleatoria no tiene URL de archivo.")

            data = await self._download_bytes(file_url)
            filename = f"{post['md5']}.{post['file_ext']}"
            name = post.get('tag_string_character') or post.get('tag_string_general', '')
            file = discord.File(io.BytesIO(data), filename=filename)
            await reply(ctx, content=f"Tags: `{name}`", file=file)
        except Exception:
            log.exception("Error en danrandom")
            await reply(ctx, content="Error al obtener imagen aleatoria.")

    @commands.hybrid_command(name="safebooru", description="Search an image from Safebooru")
    async def safebooru(self, ctx: commands.Context, *, tags: str) -> None:
        await ctx.defer()
        params = {
            'page': 'dapi', 's': 'post', 'q': 'index', 'limit': 20, 'tags': tags
        }
        try:
            xml = await self._fetch_xml(f"{self.safebooru_url}/index.php", params=params)
            posts = xml.findall('post')
            if not posts:
                return await reply(ctx, content="No se encontraron imágenes.")

            elem = random.choice(posts)
            attrib = elem.attrib
            file_url = attrib.get('file_url')
            if not file_url:
                return await reply(ctx, content="La publicación no tiene URL de archivo.")

            data = await self._download_bytes(file_url)
            ext = file_url.rsplit('.', 1)[-1]
            filename = f"{attrib['md5']}.{ext}"
            source = attrib.get('source') or tags
            file = discord.File(io.BytesIO(data), filename=filename)
            await reply(ctx, content=f"Source: <{source}>", file=file)
        except Exception:
            log.exception("Error en safebooru")
            await reply(ctx, content="Error al obtener imagen safe.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeArtCog(bot))