# Audit log yardımcıları. Discord audit log erişimi botun View Audit Log yetkisine bağlıdır.
import discord

async def find_executor(guild, action, target_id):
    try:
        async for entry in guild.audit_logs(limit=8, action=action):
            if getattr(entry.target, "id", None) == target_id:
                return entry.user
    except (discord.Forbidden, discord.HTTPException):
        return None
    return None

class AuditMonitor:
    pass
