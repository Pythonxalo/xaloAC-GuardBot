import os
import asyncio
import logging
from datetime import datetime, timezone
import discord
from discord.ext import commands
from dotenv import load_dotenv

from guard.config import *
from guard.database import Database
from guard.setup import ensure_infrastructure
from guard.audit import AuditMonitor
from guard.protection import ProtectionManager
from guard.events import EventHandlers

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN .env içinde bulunamadı.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

intents = discord.Intents.all()


bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
)

db = Database(DB_PATH)
protection = ProtectionManager(db)

@bot.event
async def on_ready():
    logging.getLogger("XaloGuard").info(
        "Xalo Guard giriş yaptı: %s (%s)", bot.user, bot.user.id
    )
    for guild in bot.guilds:
        try:
            await ensure_infrastructure(guild, db)
            await protection.initialize_guild(guild)
        except Exception:
            logging.exception("Kurulum hatası: %s", guild.id)

    try:
        await bot.tree.sync()
    except Exception:
        logging.exception("Slash komutları sync edilemedi.")

@bot.event
async def on_guild_join(guild):
    try:
        await ensure_infrastructure(guild, db)
        await protection.initialize_guild(guild)
    except Exception:
        logging.exception("Guild bootstrap hatası: %s", guild.id)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await protection.handle_message(message)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    await protection.handle_member_join(member)

@bot.event
async def on_member_remove(member):
    await protection.handle_member_remove(member)

@bot.event
async def on_guild_role_delete(role):
    await protection.handle_role_delete(role)

@bot.event
async def on_guild_role_create(role):
    await protection.handle_role_create(role)

@bot.event
async def on_guild_channel_delete(channel):
    await protection.handle_channel_delete(channel)

@bot.event
async def on_guild_channel_create(channel):
    await protection.handle_channel_create(channel)

@bot.event
async def on_webhooks_update(channel):
    await protection.handle_webhook_update(channel)

@bot.tree.command(name="guard", description="Xalo Guard durumunu gösterir.")
async def guard_status(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Bu komut için Sunucuyu Yönet yetkisi gerekir.", ephemeral=True)
        return

    state = db.get_guild(interaction.guild.id)
    embed = discord.Embed(
        title="🛡️ Xalo Guard",
        description="Otomatik güvenlik sistemi aktif.",
        color=discord.Color.green()
    )
    embed.add_field(name="Anti-Nuke", value="🟢 Aktif", inline=True)
    embed.add_field(name="Anti-Raid", value="🟢 Aktif", inline=True)
    embed.add_field(name="Anti-Spam", value="🟢 Aktif", inline=True)
    embed.add_field(name="Snapshot", value="🟢 Aktif", inline=True)
    embed.add_field(name="Guild", value=str(interaction.guild.id), inline=True)
    embed.add_field(name="Log Kanalı", value=f"<#{state['log_channel_id']}>" if state and state["log_channel_id"] else "Yok", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
