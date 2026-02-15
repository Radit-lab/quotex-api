"""
Telegram Premium Emoji Sender
Uses Telethon to send messages with animated premium emojis
"""
import os
from telethon import TelegramClient

# Your API credentials
API_ID = "23255624"
API_HASH = "195b01ad28a4e39c07c790946c2c5366"
CHANNEL_USERNAME = "RHKPUBLIC1"  # Without @ symbol

# Premium Emoji IDs (extracted from your messages)
PREMIUM_EMOJIS = {
    "diamond": "5431537486448835478",
    "crown": "6217489026711031722",
    "clock": "5215703418340908982",
    "checkmark": "6217721388736712699",
    "hourglass": "6129958422147238934",
    "green_circle": "5215327832040811010",
    "red_circle": "6222220830835739227",
    "fire": "6116349066650589320",
    "snowman": "6093818260921258328",
    "scales": "5400250414929041085",
    "check_green": "6217732620076191135",
    "sad": "6217466778780438752",
    "game": "5364250321176505463",
    "rocket": "6332517244559430568",
    "timer": "5316591603123502631",
}


class TelegramPremiumSender:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient('premium_session', API_ID, API_HASH)
        await self.client.start()
        print("✅ Connected to Telegram with premium support")
    
    async def send_premium_message(self, message: str, use_premium: bool = True):
        """Send message with premium animated emojis"""
        if not self.client:
            await self.connect()
        
        if use_premium:
            message = self.add_premium_emojis(message)
        
        await self.client.send_message(CHANNEL_USERNAME, message, parse_mode='html')
        print("✅ Premium message sent")
    
    def add_premium_emojis(self, message: str) -> str:
        """Replace standard emojis with premium animated ones"""
        replacements = {
            "💎": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["diamond"]}">💎</tg-emoji>',
            "👑": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["crown"]}">👑</tg-emoji>',
            "⏰": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["clock"]}">⏰</tg-emoji>',
            "✔️": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["checkmark"]}">✔️</tg-emoji>',
            "⏳": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["hourglass"]}">⏳</tg-emoji>',
            "🟢": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["green_circle"]}">🟢</tg-emoji>',
            "🔴": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["red_circle"]}">🔴</tg-emoji>',
            "🔥": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["fire"]}">🔥</tg-emoji>',
            "☃️": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["snowman"]}">☃️</tg-emoji>',
            "⚖️": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["scales"]}">⚖️</tg-emoji>',
            "✅": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["check_green"]}">✅</tg-emoji>',
            "😓": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["sad"]}">😓</tg-emoji>',
            "🎮": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["game"]}">🎮</tg-emoji>',
            "🚀": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["rocket"]}">🚀</tg-emoji>',
        }
        
        for standard, premium in replacements.items():
            message = message.replace(standard, premium)
        
        return message
    
    async def close(self):
        """Close connection"""
        if self.client:
            await self.client.disconnect()


# Test function
async def test_premium_sender():
    """Test premium emoji sender"""
    sender = TelegramPremiumSender()
    await sender.connect()
    
    test_message = """☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲

╭━━━━━━━【🎮】━━━━━━━╮
💎 𝙰𝙲𝚃𝙸𝚅𝙴 𝙿𝙰𝙸𝚁 »» Intel
⏰ 𝚃𝙸𝙼𝙴𝚃𝙰𝙱𝙻𝙴   »» 23:30
⏳ 𝙴𝚇𝙿𝙸𝚁𝙰𝚃𝙸𝙾𝙽  »» M1
💵 𝙿𝚁𝙸𝙲𝙴       »» 33.40700
🟢 𝙳𝙸𝚁𝙴𝙲𝚃𝙸𝙾𝙽    »» 𝙲𝙰𝙻𝙻
╰━━━━━━━━━━━━━━━━━━╯

☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲"""
    
    await sender.send_premium_message(test_message, use_premium=True)
    await sender.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_premium_sender())
