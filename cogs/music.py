from __future__ import annotations
import os
import asyncio
from dataclasses import dataclass
from start import CustomBot
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
    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.queue = MusicQueue()
        self.vc: Optional[VoiceClient] = None
        self._voice_lock = asyncio.Lock() 
        self.cookie_path = os.path.expanduser("~/UltimateDiscordBot/cookies.txt")
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            # 'postprocessors': [{  # Extract audio using ffmpeg
            #     'key': 'FFmpegExtractAudio',
            #     'preferredcodec': 'm4a',
            # }],
            'noplaylist': True,
            'default_search': 'ytsearch',
            "quiet": True,
            "retries": 3,
            "nocheckcertificate": True,
            'cookiefile': self.cookie_path if os.path.exists(self.cookie_path) else None
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -loglevel warning -fflags +nobuffer -flags low_delay -max_interleave_delta 0 -reorder_queue_size 0 -probesize 32k -analyzeduration 0'
        }

    def _extract_info(self, query: str) -> Union[dict, None]:
        try:  
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if info.get('_type') == 'playlist':
                    info = info['entries'][0]
                
                url = None
                # preferred opus/webm
                fmts = info.get("formats", [])
                preferred = sorted(
                    (f for f in fmts if f.get("acodec") and f["acodec"] != "none" and f.get("url")),
                    key=lambda f: (
                        0 if (f.get("acodec", "").startswith("opus") or "webm" in f.get("ext", "")) else 1,
                        -(f.get("abr") or 0)
                    )
                )
                if preferred:
                    url = preferred[0]["url"]
                if not url:
                    return None
                return {
                    "source": url,
                    "title": info.get("title") or "Unknown title",
                    "url": info.get("webpage_url") or query
                }
        except Exception:
            self.bot.logger.exception("Error en extract info")
        return None

    async def search_yt(self, query: str) -> Optional[dict]:
        loop = asyncio.get_running_loop() # Para no bloquear el hilo principal
        return await loop.run_in_executor(None, self._extract_info, query)

    def _after_play(self, error: Optional[Exception]) -> None:
        if error:
            self.bot.logger.error(f"Error en reproducción: {error}")
        self.bot.loop.call_soon_threadsafe(asyncio.create_task, self._play_next())

    async def _reset_voice(self):
        try:
            if self.vc:
                await self.vc.disconnect(force=True)
        except Exception:
            pass
        finally:
            self.vc = None
        await asyncio.sleep(1.5)

    async def _ensure_connected(self, channel: VoiceChannel) -> bool:
        async with self._voice_lock:
            try:
                if not self.vc or not self.vc.is_connected():
                    # evitar reanudar sesiones inválidas
                    self.vc = await channel.connect(self_deaf=True, reconnect=False)
                elif self.vc.channel != channel:
                    await self.vc.move_to(channel)
                return True
            except Exception as e:
                self.bot.logger.error(f"No se pudo conectar/mover: {e}")
                return False

    async def _play_next(self) -> None:
        """Reproduce la siguiente canción en la cola."""
        if not len(self.queue):
            return
        current = self.queue.peek()

        try:
            if not await self._ensure_connected(current.channel):
                await self._reset_voice()
                if not await self._ensure_connected(current.channel):
                    return
        except Exception as e:
            self.bot.logger.error(f"No se pudo conectar: {e}")
            return

        try:
            source = discord.FFmpegPCMAudio(current.source, **self.FFMPEG_OPTIONS)
        except Exception as e:
            self.bot.logger.error(f"FFmpegOpusAudio falló: {e}")
            self.queue.dequeue()
            return await self._play_next()

        self.queue.dequeue()
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
        embed = discord.Embed(title="Lista de Reproducción", color=self.bot.color)
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
