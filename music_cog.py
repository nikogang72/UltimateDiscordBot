import discord
from discord.ext import commands 
from youtube_dl import YoutubeDL
from typing import Any, Literal

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = False
        self.is_paused = False

        class Queue(): 
            def __init__(self):
                self.song: dict[str, Any] | Literal[False] = None
                self.channel: discord.VoiceProtocol = None
                self._tail = []

            def next_song(self):
                if len(self._tail) > 0:
                    self.song = self.tail[0][0]
                    self.channel: self.tail[0][1]
                    if len(self._tail) > 0:
                        self._tail.pop(0)
                else:
                    self.song = None
                    self.channel = None

            def length(self) -> int:
                return len(self._tail) + (1 if self.song != None else 0)

            def add_new_song(self, song: dict[str, Any] | Literal[False], channel: discord.VoiceProtocol):
                if self.song == None:
                    self.song = song
                    self.channel = channel
                else:
                    self._tail.append([song, channel])
                

            def clear(self):
                self.song = None
                self.channel = None
                self._tail = []

        self.music_queue = Queue()
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

    
     #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    async def play_next(self):
        if self.music_queue.length() > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue.song['source']

            #remove the first element as you are currently playing it
            #TODO MODIFICAR ESTO QUE NO ME PIACE
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())

            self.music_queue.next_song()
        else:
            self.is_playing = False
            await self.vc.disconnect()

    # infinite loop checking 
    async def play_music(self, ctx):
        if self.music_queue.length() > 0:
            self.is_playing = True

            m_url = self.music_queue.song['source']
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue.channel.connect(self_deaf=True)
                #in case we fail to connect
                if self.vc == None:
                    await ctx.send("I couldn't connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue.channel)
            
            #remove the first element as you are currently playing it
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            self.music_queue.next_song()
        else:
            print("Not Playing")
            self.is_playing = False

    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = None
        try: #If it isn't connected to a channel, this raises an exception.
            voice_channel = ctx.author.voice.channel
        except Exception as e: 
            print("Someone wasn't connected to a channel:", e.__class__)
        if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            await ctx.send("For starters, connect to a voice channel.")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(f"Song added to the queue: {song['title']}")
                self.music_queue.add_new_song(song, voice_channel)
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()

    @commands.command(name = "resume", aliases=["r"], help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_next(ctx)


    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, self.music_queue.length()):
            # display a max of 5 songs in the current queue
            if (i > 4): break
            retval += self.music_queue.song['title'] + "\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue.clear()
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from VC")
    async def dc(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()