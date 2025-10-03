import discord
from discord import app_commands
from discord.ext import commands
import random

gifs_luchito = [
    'https://media.discordapp.net/attachments/750954207174983731/1008553759917481984/caption.gif?ex=686fc5a2&is=686e7422&hm=6ecdcbdf78fa9ca0c0603276b71690395acf25cc05d3c2e0246ce490c0ba4ef2&',
    'https://media.discordapp.net/attachments/827962607985623071/1008068697266597908/captionTwo.gif?ex=686ffc22&is=686eaaa2&hm=616eb08b3389f088a562f5ae3a935440201fcd07b09f8dc9c5e32e257a7b709a&',
    'https://media.discordapp.net/attachments/827962607985623071/1008841580192481290/captionTwo.gif?ex=687028f0&is=686ed770&hm=2ace06f73133a8a64f6269ce9ea81953597fec62c176b02e7b0a03d38aee95f0&',
    'https://media.discordapp.net/attachments/827962607985623071/1008842959006994532/captionTwo.gif?ex=68702a38&is=686ed8b8&hm=1cedc590139f364962e04eb883a4ccbc25b26f760afe8643fb7edf15df3ebe3f&',
    'https://media.discordapp.net/attachments/827962607985623071/1009265584564863048/captionTwo.gif?ex=686fb992&is=686e6812&hm=989e5733d2f4454fca27583bf4ba6c38bcb4e3a6fbbe5ddcb141dac2eb0414a5&'
]

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Responde Pong!"
    )
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content.startswith("?"):
            return
        if message.content.lower().startswith("hola"):
            await message.channel.send(f"¡Hola, {message.author.mention}!")

        if 'teniente luchito' in message.content:
            await message.channel.send(random.choice(gifs_luchito))

        # await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message):
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return  

        deleter = "??"
        try:
            async for entry in message.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.message_delete
            ):
                if entry.target.id == message.author.id:
                    deleter = f"{entry.user}"
                    break
        except discord:
            self.bot.logger.exception("Error al leer audit logs")

        timestamp = int(message.created_at.timestamp())
        texto = (
            f"### Mensaje eliminado\n"
            f"#{message.channel} | {message.author} ({message.author.id}) | {deleter}\n"
            f"<t:{timestamp}:f>\n"
        )
        try:
            await message.channel.send(texto)
        except Exception:
            await message.channel.send(f"Alguien borró un mensaje viejo: @{message.author | "??"}")
            self.bot.logger.exception("Error al mandar el log de delete")

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
