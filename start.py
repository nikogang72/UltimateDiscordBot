from email.message import Message
import os
import asyncio
import time
import discord
from discord.ext import commands 
from dotenv import load_dotenv
import datetime

from music_cog import MusicCog
from anime_art_cog import AnimeArtCog
from help_cog import help_cog

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='?', description="WIP 友希那 Bot", help_command=None, intents=intents)

COOLDOWN_AMOUNT = 60.0  # seconds
last_executed = 0.0
def assert_cooldown():
    global last_executed  # you can use a class for this if you wanted
    if last_executed + COOLDOWN_AMOUNT < time.time():
        last_executed = time.time()
        return True
    return False

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("?help for commands."))
    print(f"Logged in as\n\tName: {bot.user.name}\n\tID: {bot.user.id}\n\tDiscord.py version: {discord.__version__}")

@bot.listen('on_message')
async def squad_pug(message: discord.Message):
    if message.author == bot.user:
        return
    if 'squad' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send('squad amigo sale squad @Pug.exe!!!')

@bot.listen('on_message')
async def virgadas(message: discord.Message):
    if message.author == bot.user:
        return
    if ':v' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send(":'v")
    elif ':V' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send(":'V")
    elif 'virgen' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send('https://tenor.com/view/nerd-gif-24439345')
    elif 'boca' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send('https://media.discordapp.net/attachments/827962607985623071/1014018694021644360/ganoboca.gif')
    elif 'river' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send('https://tenor.com/view/river-plate-cheers-wine-tophat-emoji-gif-4831830')
    elif 'fortnite' in message.content:
        if not assert_cooldown():
            return
        await message.channel.send('https://cdn.discordapp.com/attachments/681399276978438144/1023791346890330193/unknown.png')
    
        
    

@bot.command()
async def context(ctx: commands.Context):
    print(ctx)
    await ctx.send(f"""context printed: 
        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#context
    """)


@bot.command(name='help')
async def _help(ctx: commands.Context):
    des = """
    ``?help`` - show this MESSAGE
    ``?play <keywords>`` - finds the song on youtube and plays it in your current channel.  Will resume playing the current song if it was paused
    ``?queue`` - displays the current music queue
    ``?skip`` - skips the current song being played
    ``?clear`` - Stops the music and clears the queue
    ``?leave`` - Disconnected the bot from the voice channel
    ``?pause`` - pauses the current song being played or resumes if already paused
    ``?resume`` - resumes playing the current song
    """
    embed = discord.Embed(title="友希那 commands overview",url="https://cdn.discordapp.com/attachments/704225213969203261/929852105114665090/migikata3.gif?size=1024",description= des,
    timestamp=datetime.datetime.utcnow(),
    color=discord.Color.blue())
    embed.set_footer(text=f"solicitado por: {ctx.author.name}")
    embed.set_author(name="湊友希那",       
    icon_url="https://cdn.discordapp.com/attachments/704223721233186827/1028909189164191794/6039813_0.jpg")

    await ctx.send(embed=embed)

async def setup():
    async with bot:
        load_dotenv()
        await bot.add_cog(AnimeArtCog(bot))
        await bot.add_cog(MusicCog(bot))
        await bot.start(os.environ.get("TOKEN"))

if __name__=='__main__':
    asyncio.run(setup())