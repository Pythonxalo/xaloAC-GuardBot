import json
import discord
from .config import *

async def ensure_infrastructure(guild, db):
    me = guild.me
    if not me:
        return

    category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(
            LOG_CATEGORY_NAME,
            reason="Xalo Guard otomatik güvenlik kurulumu"
        )

    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if log_channel is None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
        }
        log_channel = await guild.create_text_channel(
            LOG_CHANNEL_NAME,
            category=category,
            overwrites=overwrites,
            reason="Xalo Guard otomatik log kanalı"
        )

    quarantine = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
    if quarantine is None:
        quarantine = await guild.create_role(
            name=QUARANTINE_ROLE_NAME,
            colour=discord.Colour.dark_grey(),
            reason="Xalo Guard otomatik karantina rolü"
        )

    snapshot = {
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "position": r.position,
                "permissions": r.permissions.value
            }
            for r in guild.roles
            if not r.is_default()
        ],
        "channels": [
            {
                "id": c.id,
                "name": c.name,
                "type": str(c.type),
                "position": c.position
            }
            for c in guild.channels
        ],
    }
    db.save_guild(guild.id, log_channel.id, quarantine.id, snapshot)

    await send_admin_bootstrap_dm(guild, log_channel)

async def send_admin_bootstrap_dm(guild, log_channel):
    embed = discord.Embed(
        title="🛡️ Xalo Guard aktif",
        description=(
            f"**{guild.name}** sunucusunda otomatik güvenlik sistemi başlatıldı.\n\n"
            "Anti-Nuke • Anti-Raid • Anti-Spam • Snapshot • Audit Monitoring"
        ),
        colour=discord.Colour.green()
    )
    embed.add_field(name="Log", value=log_channel.mention)
    embed.set_footer(text="Xalo Guard")

    for member in guild.members:
        if member.bot:
            continue
        if member.guild_permissions.administrator:
            try:
                await member.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass
