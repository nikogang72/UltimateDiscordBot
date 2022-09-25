import os
import discord
from discord.ext import commands 
from dotenv import load_dotenv
import datetime

bot = commands.Bot(command_prefix='?', description="WIP 友希那 Bot", help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("?help for commands."))
    print(f"Logged in as\n\tName: {bot.user.name}\n\tID: {bot.user.id}\nDiscord.py version: {discord.__version__}")
        

@bot.command()
async def pingpiola(ctx):
    await ctx.send('pong mas piola')

@bot.command()
async def context(ctx):
    print(ctx)
    await ctx.send(f"""context printed: 
        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#context
    """)

@bot.command()
async def help(ctx):
    print("A ver hola si amigoo")
    des = """
    ``?help`` - show this message\n
        
    """
    embed = discord.Embed(title="Yukina commands overview",url="https://cdn.discordapp.com/attachments/704225213969203261/929852105114665090/migikata3.gif?size=1024",description= des,
    timestamp=datetime.datetime.utcnow(),
    color=discord.Color.blue())
    embed.set_footer(text=f"solicitado por: {ctx.author.name}")
    embed.set_author(name="湊友希那",       
    icon_url="https://cdn.discordapp.com/attachments/704225213969203261/929852363697696788/FCjWYC3VcAEimzA.jpg?size=1024%22")

    await ctx.send(embed=embed)

def run():
    load_dotenv()
    bot.run(os.environ.get("TOKEN"))

if __name__=='__main__':
    run()