from typing import Optional

import discord
from discord import Member, Guild, TextChannel
from discord.ext import commands

class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        """Saluda al miembro en el canal del sistema o en un canal 'welcome'."""
        guild: Guild = member.guild

        channel: Optional[TextChannel] = guild.system_channel
        if channel is None:
            channel = discord.utils.get(guild.text_channels, name="welcome")
        if channel is None:
            self.bot.logger.warning(
                f"No se encontró canal de bienvenida en el servidor {guild.name!r} ({guild.id})"
            )
            return

        embed = discord.Embed(
            title="¡Bienvenido!",
            description=f"{member.mention} se ha unido a **{guild.name}** \n Account creation date: {str(member.created_at)[0:10]}",
            color=discord.Color.green(),
            timestamp=member.joined_at or discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Miembro #{guild.member_count}")

        await channel.send(embed=embed)

        try:
            dm_msg = (
                f"¡Hola {member.name}! Bienvenido a **{guild.name}**.\n"
                "Échale un vistazo a los canales y diviértete 😊"
            )
            await member.send(dm_msg)
        except discord.Forbidden:
            # Alguien deshabilitó DMs de desconocidos
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        guild: Guild = member.guild
        channel: Optional[TextChannel] = guild.system_channel
        roles = [r for r in member.roles if r.name != "@everyone"]
        rankname = roles[-1].name if roles else "virguito"
        await channel.send(f"**{str(member)}** ({rankname}) abandonó el server.")

async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))