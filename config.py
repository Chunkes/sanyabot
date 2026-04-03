import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# CHANNEL_ID может быть @username или числовой ID
_channel = os.getenv("CHANNEL_ID", "0")
CHANNEL_ID = int(_channel) if _channel.lstrip("-").isdigit() else _channel
