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
    ephemeral: bool = False,
    edit: bool = False,
    original: Optional[discord.Message] = None
) -> Optional[discord.Message]:
    """
    Envía o edita una respuesta a un comando, ya sea prefijo o slash/hybrid.
    """
    interaction = getattr(ctx, "interaction", None)

    send_kwargs: Dict[str, Any] = {}
    if content is not None:
        send_kwargs["content"] = content
    if embed is not None:
        send_kwargs["embed"] = embed
    if file is not None:
        send_kwargs["file"] = file
    elif files:
        send_kwargs["files"] = files
    if ephemeral:
        send_kwargs["ephemeral"] = True

    # SLASH / HYBRID
    if interaction is not None and hasattr(interaction, "response"):
        if file is not None or files:
            if not interaction.response.is_done() and not edit:
                await interaction.response.send_message(**send_kwargs)
            else:
                await interaction.followup.send(**send_kwargs)
            return None
        if not interaction.response.is_done() and not edit:
            await interaction.response.send_message(**send_kwargs)
        else:
            await interaction.edit_original_response(**send_kwargs)
        return None

    # PREFIJO
    if edit and original is not None:
        await original.edit(**send_kwargs)
        return original

    if file is not None:
        msg = await ctx.send(**send_kwargs)
    elif files:
        msg = await ctx.send(**send_kwargs)
    else:
        msg = await ctx.send(**send_kwargs)
    return msg
