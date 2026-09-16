https://discord.gg/psq6P3fVvN

# Xalo Guard

Discord güvenlik botu.

## Kurulum

1. Python 3.11+ kur.
2. Bu klasörde terminal aç:
   `pip install -r requirements.txt & python -m pip install -r requirements.txt`
3. `.env.example` dosyasını `.env` olarak kopyala.
4. `.env` içine bot tokenini yaz:
   `DISCORD_TOKEN=...`
5. Botu Discord Developer Portal üzerinden şu scope'larla davet et:
   - bot
   - applications.commands

Botun mümkün olduğunca yüksek rol konumunda olması ve aşağıdaki izinlere sahip olması gerekir:
- View Audit Log
- Manage Roles
- Manage Channels
- Manage Webhooks
- Manage Messages
- Moderate Members
- Send Messages
- Embed Links
- Read Message History

## Başlatma

`python main.py`

## Otomatik davranış

Bot sunucuya girince:
- XALO GUARD kategorisi oluşturur.
- guard-logs kanalı oluşturur.
- Xalo Guard Karantina rolünü oluşturur.
- Sunucunun başlangıç snapshot'ını SQLite'a kaydeder.
- Administrator yetkisine sahip üyelere DM gönderir.
- Anti-spam / anti-mention / anti-raid izlemeyi başlatır.
- Rol/kanal/webhook değişikliklerini audit log üzerinden izler.

## Önemli

Discord botları kendilerine eksik izinleri veya rol hiyerarşisini sonradan veremez. Davet sırasında gerekli izinleri vermek gerekir.

Bot, normal yönetici işlemlerini doğrudan engellemek yerine eşik aşan şüpheli davranışlarda karantina ve alarm uygular. Böylece yanlış pozitiflerde sunucunun tamamının kilitlenmesi önlenir.
