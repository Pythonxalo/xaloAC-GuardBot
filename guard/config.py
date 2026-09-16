from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "xalo_guard.sqlite3")

LOG_CATEGORY_NAME = "🛡️ XALO GUARD"
LOG_CHANNEL_NAME = "guard-logs"
QUARANTINE_ROLE_NAME = "Xalo Guard Karantina"

JOIN_WINDOW_SECONDS = 20
JOIN_THRESHOLD = 8
NEW_ACCOUNT_DAYS = 3

MESSAGE_WINDOW_SECONDS = 8
MESSAGE_THRESHOLD = 7
MENTION_THRESHOLD = 5

ROLE_ACTION_WINDOW = 10
ROLE_ACTION_THRESHOLD = 5
CHANNEL_ACTION_WINDOW = 10
CHANNEL_ACTION_THRESHOLD = 5

TRUSTED_ROLE_NAMES = {
    "Xalo Guard",
    "x410m1s0",
    "Admin",
    "Yönetici",
    "Owner",
    "Kurucu",
}

DANGEROUS_PERMISSIONS = {
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "ban_members",
    "kick_members",
    "manage_webhooks",
}
