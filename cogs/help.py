from typing import List, Tuple

import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    """Cog que provee un comando de ayuda con embed mejorado y soporte híbrido."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="ayuda",
        description="Muestra la lista de comandos disponibles",
    )
    async def _help(self, ctx: commands.Context) -> None:
        """Envía un embed con los comandos disponibles en campos separados."""
        embed = discord.Embed(
            title="Listado de Comandos del BOT",
            url="https://bandori.fandom.com/wiki/MyGO!!!!!",
            color=0x3388BB,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name="湊友希那",
            icon_url="https://cdn.discordapp.com/attachments/912080637245161583/1392672209121575032/Evening_Calm_at_5-45_PM_Event_Stamp.webp?ex=68706291&is=686f1111&hm=555f70cdf043c9fd785b0ab987b4ac5aeb6afb177321dd58b906b1ca7e34875c&",
        )
        embed.set_footer(
            text=f"Solicitado por: {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        commands_info: List[Tuple[str, str]] = [
            ("/ayuda", "Muestra este mensaje"),
            ("/play <keywords>", "Busca la canción en YouTube y la reproduce en tu canal de voz. Reanuda si estaba pausada."),
            ("/queue", "Muestra la cola de reproducción actual"),
            ("/skip", "Salta la canción en curso"),
            ("/clear", "Detiene la música y limpia la cola"),
            ("/leave", "Desconecta el bot del canal de voz"),
            ("/pause", "Pausa la canción en curso o la reanuda si ya estaba pausada"),
            ("/resume", "Reanuda la canción pausada"),
        ]

        for cmd, desc in commands_info:
            embed.add_field(name=cmd, value=desc, inline=False)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
