import discord
from discord.ext import commands
from typing import List, Optional, Dict, Any

async def reply(
        ctx: commands.Context,
        *,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        file: Optional[discord.File] = None,
        files: Optional[List[discord.File]] = None,
        ephemeral: bool = False
    ) -> None:
        """Envía respuesta compatible tanto con prefijo (ctx.send) como con slash (followup)."""
        interaction = getattr(ctx, 'interaction', None)
        # Si es slash/hybrid y la interacción existe
        if interaction is not None and hasattr(interaction, 'response'):
            # Defer si no hemos respondido aun
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)
            send_kwargs: Dict[str, Any] = {}
            if content is not None:
                send_kwargs['content'] = content
            if embed is not None:
                send_kwargs['embed'] = embed
            if file is not None:
                send_kwargs['file'] = file
            elif files:
                send_kwargs['files'] = files
            if ephemeral:
                send_kwargs['ephemeral'] = True
            await interaction.followup.send(**send_kwargs)
        else:
            # Comando con prefijo
            if file is not None:
                await ctx.send(content=content, embed=embed, file=file)
            elif files:
                await ctx.send(content=content, embed=embed, files=files)
            else:
                await ctx.send(content=content, embed=embed)
