import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone

import discord

from .config import *
from .audit import find_executor

class ProtectionManager:
    def __init__(self, db):
        self.db = db
        self.messages = defaultdict(deque)
        self.joins = defaultdict(deque)
        self.mentions = defaultdict(deque)

    async def initialize_guild(self, guild):
        # Güvenlik kurulumu setup.py tarafından yapılır.
        return

    def trusted(self, member):
        if member.guild_permissions.administrator:
            return True
        if any(r.name in TRUSTED_ROLE_NAMES for r in member.roles):
            return True
        return self.db.is_trusted(member.guild.id, member.id)

    async def log(self, guild, title, description, colour=discord.Colour.orange()):
        state = self.db.get_guild(guild.id)
        if not state or not state["log_channel_id"]:
            return
        channel = guild.get_channel(state["log_channel_id"])
        if not channel:
            return
        embed = discord.Embed(
            title=title,
            description=description,
            colour=colour,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    async def quarantine(self, member, reason):
        if not member or member.bot:
            return
        state = self.db.get_guild(member.guild.id)
        if not state:
            return
        role = member.guild.get_role(state["quarantine_role_id"])
        if not role:
            return
        try:
            await member.add_roles(role, reason=f"Xalo Guard: {reason}")
            await self.log(
                member.guild,
                "🚨 Kullanıcı karantinaya alındı",
                f"{member.mention} (`{member.id}`)\n**Sebep:** {reason}",
                discord.Colour.red()
            )
        except discord.Forbidden:
            await self.log(
                member.guild,
                "⚠️ Karantina başarısız",
                f"{member.mention} için botun rol hiyerarşisi/yetkileri yetersiz."
            )

    async def handle_member_join(self, member):
        if member.bot:
            return

        now = datetime.now(timezone.utc)
        q = self.joins[member.guild.id]
        q.append(now)

        while q and (now - q[0]).total_seconds() > JOIN_WINDOW_SECONDS:
            q.popleft()

        age_days = (now - member.created_at).total_seconds() / 86400

        if len(q) >= JOIN_THRESHOLD:
            await self.log(
                member.guild,
                "🚨 RAID alarmı",
                f"{len(q)} yeni üye yaklaşık {JOIN_WINDOW_SECONDS} saniyede katıldı.",
                discord.Colour.red()
            )

        if age_days < NEW_ACCOUNT_DAYS:
            await self.log(
                member.guild,
                "⚠️ Yeni hesap",
                f"{member.mention} hesabı yaklaşık {age_days:.1f} günlük.",
                discord.Colour.orange()
            )

    async def handle_member_remove(self, member):
        return

    async def handle_message(self, message):
        guild = message.guild
        if not guild:
            return

        now = datetime.now(timezone.utc)
        key = (guild.id, message.author.id)
        q = self.messages[key]
        q.append(now)

        while q and (now - q[0]).total_seconds() > MESSAGE_WINDOW_SECONDS:
            q.popleft()

        if len(q) >= MESSAGE_THRESHOLD and not self.trusted(message.author):
            await self.quarantine(message.author, "Mesaj spam/flood")
            try:
                await message.channel.purge(
                    limit=min(len(q), 20),
                    check=lambda m: m.author.id == message.author.id
                )
            except (discord.Forbidden, discord.HTTPException):
                pass
            q.clear()

        mentions = len(message.mentions)
        if message.mention_everyone:
            mentions += 10
        if mentions:
            mq = self.mentions[key]
            for _ in range(mentions):
                mq.append(now)
            while mq and (now - mq[0]).total_seconds() > MESSAGE_WINDOW_SECONDS:
                mq.popleft()

            if len(mq) >= MENTION_THRESHOLD and not self.trusted(message.author):
                await self.quarantine(message.author, "Mention spam")
                mq.clear()

    async def action_check(self, guild, target_id, action_name, threshold, window, audit_action):
        executor = await find_executor(guild, audit_action, target_id)
        if not executor or executor.bot:
            return

        self.db.add_action(guild.id, executor.id, action_name)
        count = self.db.count_recent(guild.id, executor.id, action_name, window)

        member = guild.get_member(executor.id)
        if not member or self.trusted(member):
            return

        if count >= threshold:
            await self.quarantine(member, f"Aşırı {action_name} işlemi")
            await self.log(
                guild,
                "🛑 Anti-Nuke müdahalesi",
                f"Yetkili: {executor.mention}\nİşlem: `{action_name}`\nSayı: `{count}`",
                discord.Colour.red()
            )

    async def handle_role_delete(self, role):
        await self.action_check(
            role.guild, role.id, "role_delete",
            ROLE_ACTION_THRESHOLD, ROLE_ACTION_WINDOW,
            discord.AuditLogAction.role_delete
        )

    async def handle_role_create(self, role):
        await self.action_check(
            role.guild, role.id, "role_create",
            ROLE_ACTION_THRESHOLD, ROLE_ACTION_WINDOW,
            discord.AuditLogAction.role_create
        )

    async def handle_channel_delete(self, channel):
        await self.action_check(
            channel.guild, channel.id, "channel_delete",
            CHANNEL_ACTION_THRESHOLD, CHANNEL_ACTION_WINDOW,
            discord.AuditLogAction.channel_delete
        )

    async def handle_channel_create(self, channel):
        await self.action_check(
            channel.guild, channel.id, "channel_create",
            CHANNEL_ACTION_THRESHOLD, CHANNEL_ACTION_WINDOW,
            discord.AuditLogAction.channel_create
        )

    async def handle_webhook_update(self, channel):
        try:
            async for entry in channel.guild.audit_logs(
                limit=5, action=discord.AuditLogAction.webhook_create
            ):
                if getattr(entry.target, "channel_id", None) == channel.id:
                    member = channel.guild.get_member(entry.user.id)
                    if member and not self.trusted(member):
                        self.db.add_action(channel.guild.id, member.id, "webhook_create")
                        count = self.db.count_recent(
                            channel.guild.id, member.id, "webhook_create", 15
                        )
                        if count >= 3:
                            await self.quarantine(member, "Webhook abuse")
                            await self.log(
                                channel.guild,
                                "🚨 Webhook koruması",
                                f"{member.mention} için şüpheli webhook aktivitesi tespit edildi.",
                                discord.Colour.red()
                            )
                    break
        except (discord.Forbidden, discord.HTTPException):
            pass
