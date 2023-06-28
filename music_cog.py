import discord
import json
from discord.ext import commands 
from yt_dlp import YoutubeDL
from typing import Any, Literal

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {
            'format': 'm4a/bestaudio',
            # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'noplaylist': 'True',
            'default_search': 'ytsearch'
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        self.vc = None

    def add_new_song(self, song: dict[str, Any] | Literal[False], channel: discord.VoiceProtocol):
        self.music_queue.append([song, channel])
            
    def clear(self):
        self.music_queue = []

    def show_queue(self):
        retval = ""
        if len(self.music_queue) > 0:
            retval = "Currently playing: " + self.music_queue[0][0]["title"] + "\n"
            for i in range(0 ,len(self.music_queue)):
                retval += "- " + self.music_queue[i][0]['title'] + "\n"
        return retval
    
     #searching the item on youtube
    def search_yt(self, item):
        index = 0
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info(item, download=False)
                # print(json.dumps(ydl.sanitize_info(info), indent=4))
                # with open("./info.json", "w" , encoding="utf-8") as f:
                #     # info_ = ydl.sanitize_info(info)["formats"]
                #     # index = len(info_)-1
                #     # while index >= 0 and info_[index]["resolution"] != "audio only":
                #     #     index -= 1
                #     # print(index)
                #     #f.write(json.dumps(info_[index], indent=4))
                #     f.write(json.dumps(ydl.sanitize_info(info), indent=4))
                if info.get("_type", "video") == 'playlist':
                    info = info['entries'][0]
                index = len(info["formats"])-1
                while index >= 0 and info["formats"][index]["resolution"] != "audio only":
                    index -= 1
                if index < 0:
                    raise ValueError("Audio not found")
            except Exception as e: 
                print(e.__class__, e)
                return False

        print("Title", info['title'])
        print("Format", info['formats'][index]['format'])
        print("URL", info['formats'][index]['url'])
        return {'source': info['formats'][index]['url'], 'title': info['title'], 'webpage_url': info['webpage_url']}

    def play_next(self):
        if len(self.music_queue) > 1:
            self.music_queue.pop(0)
            self.is_playing = True
            #get the first url
            m_url = self.music_queue[0][0]['source']
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        elif len(self.music_queue) > 0:
            self.music_queue.pop(0)
            self.is_playing = False
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect(self_deaf=True)
                #in case we fail to connect
                if self.vc == None:
                    await ctx.send("I couldn't connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
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
            await self.resume()
        else:
            if query == "" or query == " ":
                return await ctx.send("Invalid link virgen")
            message = await ctx.send("Searching...")
            song = self.search_yt(query)
            if type(song) == type(True):
                print("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
                await message.edit(content=f'Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.')
            else:
                self.add_new_song(song, voice_channel)
                print(f"Song added to the queue: {song['title']}")
                print("--------------------------------------------")
                await message.edit(content=f"Song added to the queue:\n   {song['title']}\n   <{ self.music_queue[0][0]['webpage_url']}>")
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            await ctx.send(f"Music paused")
            await self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            await ctx.send(f"Music resumed")
            await self.vc.resume()

    @commands.command(name = "resume", aliases=["r"], help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            await ctx.send(f"Resume playing??? no se decirlo bien ayuda @jorgito")
            await self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await ctx.send(f"Skipping.")
            await self.play_next(ctx)


    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx):
        queue_string = self.show_queue()
        if queue_string != "":
            await ctx.send(queue_string)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from VC")
    async def dc(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
