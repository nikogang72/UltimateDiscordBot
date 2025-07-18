from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
from start import CustomBot

import aiohttp
import discord
from discord.ext import commands

from utils.response import reply  # helper para respuestas prefijo/slash

class UtilitiesCog(commands.Cog):
    """Cog de utilidades: definiciones de palabras mediante DictionaryAPI."""
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        # Cierra la sesión HTTP al descargar el cog
        asyncio.create_task(self.session.close())

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    @commands.hybrid_command(
        name="define",
        aliases=["dic", "dict"],
        description="Obtiene la definición de una palabra (inglés)."
    )
    async def define(self, ctx: commands.Context, *, word: str) -> None:
        # await reply(ctx, content=f"🔍 Buscando definición de `{word}`...")
        await ctx.defer()
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip()}"
        try:
            data = await self._fetch_json(url)
            # la API devuelve una lista de entradas
            if not isinstance(data, list) or not data:
                return await reply(ctx, content=f"❌ No se encontró definición para `{word}`.")
            entry = data[0]
            word_text = entry.get('word', word)
            phonetics = entry.get('phonetics', [])
            meanings = entry.get('meanings', [])

            embed = discord.Embed(
                title=f"📖 Definición de {word_text}",
                color=self.bot.color
            )
            # Añadir pronunciación si existe
            phon_texts: List[str] = [p.get('text', '') for p in phonetics if p.get('text')]
            if phon_texts:
                embed.add_field(
                    name="🔊 Pronunciación",
                    value=", ".join(phon_texts),
                    inline=False
                )
            # Añadir hasta tres tipos de parte del habla
            for meaning in meanings[:3]:
                part = meaning.get('partOfSpeech', '')
                defs = meaning.get('definitions', [])
                if defs:
                    definition = defs[0].get('definition', '')
                    example = defs[0].get('example', '')
                    value = definition
                    if example:
                        value += f"\n✏️ Ejemplo: {example}"
                    embed.add_field(name=part.capitalize(), value=value, inline=False)

            await reply(ctx, embed=embed)

        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return await reply(ctx, content=f"❌ No se encontró definición para `{word}`.")
            self.bot.logger.error("HTTP error en define")
            await reply(ctx, content="⚠️ Error al conectar con el servicio de definiciones.")
        except Exception:
            self.bot.logger.exception("Error inesperado en define")
            await reply(ctx, content="⚠️ Ocurrió un error inesperado al buscar la definición.")
    
    @commands.hybrid_command(
        name="urban",
        aliases=["ud"],
        description="Busca la definición de slang en Urban Dictionary."
    )
    async def urban(self, ctx: commands.Context, *, term: str) -> None:
        #await reply(ctx, content=f"🔍 Buscando en Urban Dictionary: `{term}`...")
        await ctx.defer()
        url = "https://api.urbandictionary.com/v0/define"
        try:
            data = await self._fetch_json(url, params={"term": term.strip()})
            definitions = data.get('list', [])
            if not definitions:
                return await reply(ctx, content=f"❌ No se encontró definición para `{term}` en Urban Dictionary.")

            sorted_defs = sorted(definitions, key=lambda d: d.get('thumbs_up', 0), reverse=True)[:3]
            embed = discord.Embed(
                title=f"Urban Dictionary: {term}",
                color=self.bot.color
            )
            for idx, entry in enumerate(sorted_defs, start=1):
                raw_def = entry.get('definition', '').replace('[', '').replace(']', '')
                definition = "\n".join(f"> {line}" for line in raw_def.splitlines())
                value = definition
                raw_ex = entry.get('example', '').replace('[', '').replace(']', '')
                if raw_ex:
                    example_fmt = "\n".join(f"⠀⠀{line}" for line in raw_ex.splitlines())
                    value += f"\n⠀*Ejemplo:*\n{example_fmt}"
                embed.add_field(name=f"Definición {idx}", value=value, inline=False)

            await reply(ctx, embed=embed)
        except Exception:
            self.bot.logger.exception("Error en urban")
            await reply(ctx, content="⚠️ Error al buscar en Urban Dictionary.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UtilitiesCog(bot))
