import os
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Union

import discord
from discord.ext import commands
from discord import VoiceChannel, VoiceClient
from yt_dlp import YoutubeDL

@dataclass
class QueueItem:
    source: str
    title: str
    url: str
    channel: VoiceChannel

class MusicQueue:
    def __init__(self) -> None:
        self._items: List[QueueItem] = []

    def enqueue(self, item: QueueItem) -> None:
        self._items.append(item)

    def dequeue(self) -> Optional[QueueItem]:
        return self._items.pop(0) if self._items else None

    def peek(self) -> Optional[QueueItem]:
        return self._items[0] if self._items else None

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

class MusicCog(commands.Cog):
    """Cog para reproducir música """
    def __init__(self, bot):
        self.queue = MusicQueue()
        self.vc: Optional[VoiceClient] = None
        self.cookie_path = os.path.expanduser("~/UltimateDiscordBot/cookies.txt")
        self.YDL_OPTIONS = {
            'format': 'm4a/bestaudio',
            # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'noplaylist': 'True',
            'default_search': 'ytsearch',
            'cookiefile': self.cookie_path
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -threads 2'
        }

    def _extract_info(self, query: str) -> Union[dict, None]:
        try:  
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if info.get('_type') == 'playlist':
                    info = info['entries'][0]
                # busca primer formato de audio
                for fmt in info.get('formats', []):
                    if fmt.get('acodec') != 'none':
                        return {
                            'source': fmt['url'],
                            'title': info.get('title'),
                            'url': info.get('webpage_url')
                        }
        except Exception:
            return None
        return None

    async def search_yt(self, query: str) -> Optional[dict]:
        loop = asyncio.get_running_loop() # Para no bloquear el hilo principal
        return await loop.run_in_executor(None, self._extract_info, query)

    def _after_play(self, error: Optional[Exception]) -> None:
        if error:
            self.bot.logger.error(f"Error en reproducción: {error}")
        self.bot.loop.call_soon_threadsafe(asyncio.create_task, self._play_next())

    async def _play_next(self) -> None:
        """Reproduce la siguiente canción en la cola."""
        next_item = self.queue.dequeue()
        if not next_item:
            return
        try:
            if not self.vc or not self.vc.is_connected():
                self.vc = await next_item.channel.connect(self_deaf=True)
            else:
                await self.vc.move_to(next_item.channel)
        except Exception as e:
            self.bot.logger.error(f"No se pudo conectar: {e}")
            return

        source = discord.FFmpegOpusAudio(next_item.source, **self.FFMPEG_OPTIONS)
        self.vc.play(source, after=self._after_play)

    async def play_music(self, ctx: commands.Context) -> None:
        """Inicia la reproducción."""
        if not len(self.queue):
            await ctx.send("No hay canciones en la cola.")
            return
        first = self.queue.peek()
        if not first:
            return
        await ctx.send(f"Reproduciendo: **{first.title}**")
        await self._play_next()

    @commands.hybrid_command(name="join", description="Conecta el bot a tu canal de voz y reproduce la cola.")
    async def join(self, ctx: commands.Context) -> None:
        voice_channel = getattr(ctx.author.voice, 'channel', None)
        if not voice_channel:
            return await ctx.send("Conéctate a un canal de voz primero.")
        try:
            if not self.vc or not self.vc.is_connected():
                self.vc = await voice_channel.connect(self_deaf=True)
            else:
                await self.vc.move_to(voice_channel)
        except Exception as e:
            self.bot.logger.error(f"No se pudo conectar: {e}")
            return await ctx.send("No pude conectarme al canal de voz.")
        await ctx.send(f"👋 Conectado a **{voice_channel.name}**")
        if len(self.queue):
            await self.play_music(ctx)

    @commands.hybrid_command(name="play", aliases=["p","playing"], description="Reproduce una canción de YouTube.")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        voice_channel = getattr(ctx.author.voice, 'channel', None)
        if not voice_channel:
            return await ctx.send("Conéctate a un canal de voz primero.")

        message = await ctx.send("Searching...")
        info = await self.search_yt(query)
        if not info:
            return await message.edit(content=f'Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.')

        item = QueueItem(
            source=info['source'],
            title=info['title'],
            url=info['url'],
            channel=voice_channel
        )
        self.queue.enqueue(item)
        await message.edit(content=f"Song added to the queue:\n   {item.title}\n   <{item.url}>")

        if not self.vc or not self.vc.is_playing():
            await self.play_music(ctx)


    @commands.hybrid_command(name="pause", description="Pausa o reanuda la reproducción.")
    async def pause(self, ctx: commands.Context) -> None:
        if self.vc and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("⏸️ Pausado")
        elif self.vc and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("▶️ Reanudado")
        else:
            await ctx.send("No hay nada reproduciéndose.")

    @commands.hybrid_command(name="skip", aliases=["s"], description="Salta a la siguiente canción.")
    async def skip(self, ctx: commands.Context) -> None:
        if self.vc and (self.vc.is_playing() or self.vc.is_paused()):
            self.vc.stop()
            await self._play_next()
            await ctx.send("⏭️ Siguiente canción...")
        else:
            await ctx.send("No hay nada que saltar.")

    @commands.hybrid_command(name="queue", aliases=["q"], description="Muestra la cola de reproducción.")
    async def show_queue(self, ctx: commands.Context) -> None:
        if not len(self.queue):
            return await ctx.send("La cola está vacía.")
        embed = discord.Embed(title="Lista de Reproducción", color=0x3388BB)
        for idx, item in enumerate(self.queue, start=1):
            embed.add_field(name=f"{idx}. {item.title}", value=item.url, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clear", aliases=["c"], description="Detiene y limpia la cola de reproducción.")
    async def clear(self, ctx: commands.Context) -> None:
        if self.vc and (self.vc.is_playing() or self.vc.is_paused()):
            self.vc.stop()
        self.queue.clear()
        await ctx.send("Music queue cleared")

    @commands.hybrid_command(name="leave", aliases=["disconnect", "l"], description="Desconecta al bot del canal de voz.")
    async def leave(self, ctx: commands.Context) -> None:
        if self.vc:
            await self.vc.disconnect()
            self.vc = None
            await ctx.send("👋 Desconectado.")
        else:
            await ctx.send("No estoy en ningún canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
