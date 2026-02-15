import asyncio
import time
import os
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pyquotex.stable_api import Quotex
from pyquotex.config import credentials as pq_credentials

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env vars")

# Pair name mapping for display
PAIR_ACTUAL_NAME = {
    "FB_otc": "FACEBOOK INC (OTC)",
    "INTC_otc": "Intel",
    "JNJ_otc": "Johnson & Johnson (OTC)",
    "MCD_otc": "McDonald's (OTC)",
    "MSFT_otc": "Microsoft (OTC)",
    
    "NZDCAD_otc": "NZD/CAD (OTC)",
    "NZDCHF_otc": "NZD/CHF (OTC)",
    "NZDJPY_otc": "NZD/JPY (OTC)",
    
    "PFE_otc": "Pfizer Inc (OTC)",
    "UKBrent_otc": "UKBrent (OTC)",
    "USCrude_otc": "USCrude (OTC)",
    
    "USDARS_otc": "USD/ARS (OTC)",
    "USDBDT_otc": "USD/BDT (OTC)",
    "USDCAD_otc": "USD/CAD (OTC)",
    "USDCOP_otc": "USD/COP (OTC)",
    "USDDZD_otc": "USD/DZD (OTC)",
    "USDEGP_otc": "USD/EGP (OTC)",
    "USDIDR_otc": "USD/IDR (OTC)",
    "USDINR_otc": "USD/INR (OTC)",
    "USDJPY_otc": "USD/JPY (OTC)",
    "USDMXN_otc": "USD/MXN (OTC)",
    "USDNGN_otc": "USD/NGN (OTC)",
    "USDPHP_otc": "USD/PHP (OTC)",
    "USDPKR_otc": "USD/PKR (OTC)",
    "USDTRY_otc": "USD/TRY (OTC)",
    "USDZAR_otc": "USD/ZAR (OTC)",
    
    "XAGUSD_otc": "Silver (OTC)",
    "XAUUSD_otc": "Gold (OTC)"
}


class CandleAnalyzer:
    @staticmethod
    def calculate_wick_ratio(candle: Dict) -> float:
        """Calculate wick ratio (total wick / body)"""
        body = abs(candle['close'] - candle['open'])
        if body == 0:
            return float('inf')
        
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        total_wick = upper_wick + lower_wick
        
        return total_wick / body
    
    @staticmethod
    def calculate_body_strength(candle: Dict) -> float:
        """Calculate body strength (body / total range)"""
        total_range = candle['high'] - candle['low']
        if total_range == 0:
            return 0
        
        body = abs(candle['close'] - candle['open'])
        return body / total_range
    
    @staticmethod
    def is_bullish(candle: Dict) -> bool:
        """Check if candle is bullish"""
        return candle['close'] > candle['open']
    
    @staticmethod
    def is_bearish(candle: Dict) -> bool:
        """Check if candle is bearish"""
        return candle['close'] < candle['open']
    
    @staticmethod
    def calculate_sma(candles: List[Dict], period: int = 20) -> float:
        """Calculate Simple Moving Average"""
        if len(candles) < period:
            period = len(candles)
        
        closes = [c['close'] for c in candles[-period:]]
        return sum(closes) / len(closes)
    
    @staticmethod
    def calculate_rsi(candles: List[Dict], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(candles) < period + 1:
            return 50.0
        
        closes = [c['close'] for c in candles[-(period+1):]]
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_volume_strength(candles: List[Dict], period: int = 10) -> float:
        """Calculate volume strength (current vs average)"""
        if len(candles) < period:
            return 1.0
        
        recent = candles[-period:]
        avg_range = sum([c['high'] - c['low'] for c in recent]) / period
        current_range = candles[-1]['high'] - candles[-1]['low']
        
        if avg_range == 0:
            return 1.0
        
        return current_range / avg_range
    
    @staticmethod
    def detect_pattern(candles: List[Dict]) -> str:
        """Detect candlestick patterns"""
        if len(candles) < 2:
            return "NONE"
        
        last = candles[-1]
        prev = candles[-2]
        
        body_last = abs(last['close'] - last['open'])
        range_last = last['high'] - last['low']
        body_prev = abs(prev['close'] - prev['open'])
        
        # Hammer pattern (bullish reversal)
        lower_wick = min(last['open'], last['close']) - last['low']
        upper_wick = last['high'] - max(last['open'], last['close'])
        if lower_wick > body_last * 2 and upper_wick < body_last * 0.3:
            return "HAMMER"
        
        # Shooting star (bearish reversal)
        if upper_wick > body_last * 2 and lower_wick < body_last * 0.3:
            return "SHOOTING_STAR"
        
        # Bullish engulfing
        if (CandleAnalyzer.is_bullish(last) and CandleAnalyzer.is_bearish(prev) and
            last['open'] < prev['close'] and last['close'] > prev['open']):
            return "BULLISH_ENGULFING"
        
        # Bearish engulfing
        if (CandleAnalyzer.is_bearish(last) and CandleAnalyzer.is_bullish(prev) and
            last['open'] > prev['close'] and last['close'] < prev['open']):
            return "BEARISH_ENGULFING"
        
        return "NONE"
    
    @staticmethod
    def detect_trend(candles: List[Dict]) -> str:
        """Detect trend using SMA comparison"""
        if len(candles) < 20:
            return "NEUTRAL"
        
        sma_short = CandleAnalyzer.calculate_sma(candles, 10)
        sma_long = CandleAnalyzer.calculate_sma(candles, 20)
        
        if sma_short > sma_long:
            return "BULLISH"
        elif sma_short < sma_long:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    @staticmethod
    def is_consolidating(candles: List[Dict], period: int = 10) -> bool:
        """Check if market is consolidating"""
        if len(candles) < period:
            return True
        
        recent_candles = candles[-period:]
        highs = [c['high'] for c in recent_candles]
        lows = [c['low'] for c in recent_candles]
        
        range_pct = (max(highs) - min(lows)) / min(lows) * 100
        return range_pct < 0.5  # Less than 0.5% range indicates consolidation


class TitanXStrategy:
    def __init__(self):
        self.wick_limit = 4.0
        self.body_strength_threshold = 0.3
        self.win_rate_history = []
    
    def adapt_thresholds(self):
        """Adaptive thresholds based on recent performance"""
        if len(self.win_rate_history) < 10:
            return
        
        recent_win_rate = sum(self.win_rate_history[-10:]) / 10
        
        # If win rate is low, be more conservative
        if recent_win_rate < 0.5:
            self.body_strength_threshold = 0.6
            self.wick_limit = 2.5
        # If win rate is high, be more aggressive
        elif recent_win_rate > 0.7:
            self.body_strength_threshold = 0.35
            self.wick_limit = 3.5
        else:
            self.body_strength_threshold = 0.4
            self.wick_limit = 3.0
    
    def analyze(self, candles: List[Dict], candles_5m: Optional[List[Dict]] = None) -> Tuple[str, float, str]:
        """
        Analyze candles using STRATEGY TITAN-X with advanced indicators
        Returns: (direction, confidence, strategy_name)
        """
        if len(candles) < 20:
            return "NO_TRADE", 0.0, "STRATEGY TITAN-X"
        
        last_candle = candles[-1]
        prev_candle = candles[-2]
        
        # Calculate indicators
        wick_ratio = CandleAnalyzer.calculate_wick_ratio(last_candle)
        body_strength = CandleAnalyzer.calculate_body_strength(last_candle)
        trend = CandleAnalyzer.detect_trend(candles)
        is_consolidating = CandleAnalyzer.is_consolidating(candles)
        rsi = CandleAnalyzer.calculate_rsi(candles, 14)
        volume_strength = CandleAnalyzer.calculate_volume_strength(candles, 10)
        pattern = CandleAnalyzer.detect_pattern(candles)
        
        # Multi-timeframe: Check 5M trend if available
        trend_5m = "NEUTRAL"
        if candles_5m and len(candles_5m) >= 20:
            trend_5m = CandleAnalyzer.detect_trend(candles_5m)
        
        # Rule 1: If wick ratio > limit → NO TRADE
        if wick_ratio > self.wick_limit:
            return "NO_TRADE", 0.0, "STRATEGY TITAN-X"
        
        # Rule 2: If consolidating → NO TRADE
        if is_consolidating:
            return "NO_TRADE", 0.0, "STRATEGY TITAN-X"
        
        # Rule 3: RSI extreme zones
        if rsi > 75 or rsi < 25:
            return "NO_TRADE", 0.0, "STRATEGY TITAN-X"  # Too extreme
        
        confidence = 0.0
        direction = "NO_TRADE"
        
        # Rule 4: Strong body analysis with RSI confirmation
        if body_strength > self.body_strength_threshold:
            if CandleAnalyzer.is_bullish(last_candle) and rsi < 70:
                direction = "CALL"
                confidence = body_strength * 0.7
            elif CandleAnalyzer.is_bearish(last_candle) and rsi > 30:
                direction = "PUT"
                confidence = body_strength * 0.7
        
        # Rule 5: Pattern recognition boost
        if pattern == "HAMMER" or pattern == "BULLISH_ENGULFING":
            if direction == "NO_TRADE" or direction == "CALL":
                direction = "CALL"
                confidence = max(confidence, 0.75)
        elif pattern == "SHOOTING_STAR" or pattern == "BEARISH_ENGULFING":
            if direction == "NO_TRADE" or direction == "PUT":
                direction = "PUT"
                confidence = max(confidence, 0.75)
        
        # Rule 6: Continuation pattern with volume
        if (CandleAnalyzer.is_bullish(last_candle) and 
            CandleAnalyzer.is_bullish(prev_candle) and
            volume_strength > 1.2):
            if direction == "NO_TRADE" or confidence < 0.7:
                direction = "CALL"
                confidence = max(confidence, 0.7)
        
        elif (CandleAnalyzer.is_bearish(last_candle) and 
              CandleAnalyzer.is_bearish(prev_candle) and
              volume_strength > 1.2):
            if direction == "NO_TRADE" or confidence < 0.7:
                direction = "PUT"
                confidence = max(confidence, 0.7)
        
        # Rule 7: Multi-timeframe confirmation
        if candles_5m:
            if direction == "CALL" and trend_5m == "BEARISH":
                confidence *= 0.7  # Reduce confidence
            elif direction == "PUT" and trend_5m == "BULLISH":
                confidence *= 0.7
            elif direction == "CALL" and trend_5m == "BULLISH":
                confidence = min(confidence * 1.2, 1.0)  # Boost confidence
            elif direction == "PUT" and trend_5m == "BEARISH":
                confidence = min(confidence * 1.2, 1.0)
        
        # Rule 8: RSI divergence signals
        if rsi < 35 and direction == "CALL":
            confidence = min(confidence * 1.15, 1.0)  # Oversold boost
        elif rsi > 65 and direction == "PUT":
            confidence = min(confidence * 1.15, 1.0)  # Overbought boost
        
        return direction, confidence, "STRATEGY TITAN-X"


class SignalFormatter:
    @staticmethod
    def format_signal(pair: str, direction: str, last_candle: Dict, strategy: str, for_telegram: bool = False) -> str:
        """Format signal in PYPRO BOT style"""
        actual_name = PAIR_ACTUAL_NAME.get(pair, pair).replace(" ", "").replace("(", "-").replace(")", "")
        
        # Calculate next minute for entry
        now = datetime.now()
        next_minute = now.replace(second=0, microsecond=0)
        from datetime import timedelta
        next_minute = next_minute + timedelta(minutes=1)
        entry_time = next_minute.strftime("%H:%M")
        
        # Direction emoji
        if direction == "CALL":
            direction_emoji = "🟢"
            direction_text = "𝙲𝙰𝙻𝙻"
        elif direction == "PUT":
            direction_emoji = "🔴"
            direction_text = "𝙿𝚄𝚃"
        else:
            direction_emoji = "⚪"
            direction_text = "𝙽𝙾_𝚃𝚁𝙰𝙳𝙴"
        
        # Last candle price
        last_price = last_candle['close']
        
        # Add bold tags for all text in Telegram
        if for_telegram:
            signal = f"""<b>☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲</b>

<b>╭━━━━━━━【⛨】━━━━━━━╮</b>
<b>💎 𝙰𝙲𝚃𝙸𝚅𝙴 𝙿𝙰𝙸𝚁 »» {actual_name}</b>
<b>⏰ 𝚃𝙸𝙼𝙴𝚃𝙰𝙱𝙻𝙴   »» {entry_time}</b>
<b>⏳ 𝙴𝚇𝙿𝙸𝚁𝙰𝚃𝙸𝙾𝙽  »» M1</b>
<b>💵 𝙿𝚁𝙸𝙲𝙴       »» {last_price:.5f}</b>
<b>{direction_emoji} 𝙳𝙸𝚁𝙴𝙲𝚃𝙸𝙾𝙽    »» {direction_text}</b>
<b>╰━━━━━━━━━━━━━━━━━━╯</b>

<b>☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲</b>"""
        else:
            signal = f"""☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲

╭━━━━━━━【⛨】━━━━━━━╮
💎 𝙰𝙲𝚃𝙸𝚅𝙴 𝙿𝙰𝙸𝚁 »» {actual_name}
⏰ 𝚃𝙸𝙼𝙴𝚃𝙰𝙱𝙻𝙴   »» {entry_time}
⏳ 𝙴𝚇𝙿𝙸𝚁𝙰𝚃𝙸𝙾𝙽  »» M1
💵 𝙿𝚁𝙸𝙲𝙴       »» {last_price:.5f}
{direction_emoji} 𝙳𝙸𝚁𝙴𝙲𝚃𝙸𝙾𝙽    »» {direction_text}
╰━━━━━━━━━━━━━━━━━━╯

☲☲☲☲ 【𝐏𝐘𝐏𝐑𝐎 𝐁𝐎𝐓】☲☲☲☲"""
        
        return signal
    
    @staticmethod
    def format_result(pair: str, entry_time: str, result: str, wins: int, losses: int, pair_wins: int, pair_losses: int) -> str:
        """Format result in PYPRO BOT style"""
        actual_name = PAIR_ACTUAL_NAME.get(pair, pair).replace(" ", "").replace("(", "-").replace(")", "")
        
        total = wins + losses
        win_rate = int((wins / total * 100)) if total > 0 else 0
        
        pair_total = pair_wins + pair_losses
        pair_rate = int((pair_wins / pair_total * 100)) if pair_total > 0 else 0
        
        if result == "WIN":
            result_emoji = "✅✅✅ SURE SHOT   ✅✅✅"
        elif result == "MTG WIN":
            result_emoji = "✅✅✅ MTG WIN   ✅✅✅"
        else:
            result_emoji = "❌❌❌ LOSS ❌❌❌"
        
        result_text = f"""<b>𒆜☲☲☲ 𝚁╎𝙴╎𝚂╎𝚄╎𝙻╎𝚃 ☲☲☲☲𒆜</b>

<b>╭━━━━━━━[⛨]━━━━━━━╮</b>
<b>🎃{actual_name} ┃ 🕓{entry_time}</b>
<b>╰━━━━━━━[⛨]━━━━━━━╯</b>
<b>{result_emoji}</b>

<b>╭━━━━━━━[⛨]━━━━━━━╮</b>
<b>🔥 Win:{wins:02d} |☃️ Loss:{losses:02d}◈ ({win_rate}%)</b>
<b>⚖️ Current pair :{pair_wins}x{pair_losses}◈({pair_rate}%)</b>
<b>╰━━━━━━━[⛨]━━━━━━━╯</b>

<b>☲☲☲_ 【𝐏𝐘𝐁𝐎𝐓 𝐏𝐑𝐎】☲☲☲☲</b>"""
        
        return result_text


# Premium Emoji IDs
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
    "pumpkin": "5427336991253479512",
    "clock2": "5384513813670279219",
    "cross": "6325844463109280731",
}


class TelegramNotifier:
    def __init__(self):
        self.enabled = True  # Re-enabled
        self.client = None
        self.api_id = "23255624"
        self.api_hash = "195b01ad28a4e39c07c790946c2c5366"
        self.channel = "RHKPUBLIC1"
        self.connecting = False
        print("✅ Telegram Premium enabled")
    
    async def connect(self):
        """Connect to Telegram with Telethon"""
        if self.connecting or self.client:
            return
        
        self.connecting = True
        try:
            from telethon import TelegramClient
            self.client = TelegramClient('premium_session', self.api_id, self.api_hash)
            await self.client.start()
            print("✅ Connected to Telegram with premium support")
        except ImportError:
            print("⚠️ Telethon not installed. Run: pip install telethon")
            self.enabled = False
        except Exception as e:
            print(f"⚠️ Telegram connection failed: {e}")
            self.enabled = False
        finally:
            self.connecting = False
    
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
            "🎃": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["pumpkin"]}">🎃</tg-emoji>',
            "🕓": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["clock2"]}">🕓</tg-emoji>',
            "❌": f'<tg-emoji emoji-id="{PREMIUM_EMOJIS["cross"]}">❌</tg-emoji>',
        }
        
        for standard, premium in replacements.items():
            message = message.replace(standard, premium)
        
        return message
    
    async def send_message(self, message: str):
        """Send message with premium animated emojis"""
        if not self.enabled:
            return
        
        try:
            if not self.client and not self.connecting:
                await self.connect()
            
            if self.client:
                message = self.add_premium_emojis(message)
                await self.client.send_message(self.channel, message, parse_mode='html')
                print("✅ Premium message sent")
            else:
                print("⚠️ Telegram not connected, skipping message")
        except Exception as e:
            print(f"⚠️ Telegram send failed: {e}")


class PyQuotexBot:
    def __init__(self):
        self.strategy = TitanXStrategy()
        self.pairs = list(PAIR_ACTUAL_NAME.keys())
        self.client = None
        self.wins = 0
        self.losses = 0
        self.pair_stats = {}  # Track wins/losses per pair
        self.pair_performance = {}  # Track pair win rates for ranking
        self.backtest_mode = False
        self.backtest_results = []
        self.trade_history = []  # Track all trades for summary
        self.telegram = TelegramNotifier()
    
    async def connect(self):
        """Connect to Quotex"""
        email = os.getenv("PYQUOTEX_EMAIL")
        password = os.getenv("PYQUOTEX_PASSWORD")
        if not email or not password:
            try:
                email, password = pq_credentials()
            except Exception:
                pass
        if not email or not password:
            raise RuntimeError("Set PYQUOTEX_EMAIL and PYQUOTEX_PASSWORD")
        
        self.client = Quotex(email=email, password=password, lang="pt")
        ok, reason = await self.client.connect()
        if not ok:
            raise RuntimeError(f"Connection failed: {reason}")
        print("✅ Connected to Quotex\n")
    
    async def get_candles(self, pair: str, limit: int = 199, period: int = 60) -> List[Dict]:
        """
        Fetch candles from Quotex API
        Returns candles sorted oldest → newest
        period: 60 for 1M, 300 for 5M
        """
        try:
            offset = limit * period
            end_time = time.time()
            
            candles = await self.client.get_candles(pair, end_time, offset, period)
            if not candles:
                return []
            
            # Convert to required format
            result = []
            for c in candles:
                result.append({
                    'open': float(c.get('open', 0)),
                    'high': float(c.get('max', c.get('high', 0))),
                    'low': float(c.get('min', c.get('low', 0))),
                    'close': float(c.get('close', 0)),
                    'time': c.get('time', 0)
                })
            
            return result[-limit:]  # Return last N candles
        except Exception as e:
            print(f"⚠️ Error fetching {pair}: {e}")
            return []
    

    async def scan_pair(self, pair: str) -> Optional[Tuple[str, str, str, str]]:
        """Scan a single pair for signals with multi-timeframe analysis"""
        try:
            # Fetch 1M candles
            candles_1m = await self.get_candles(pair, 199, 60)
            
            if not candles_1m or len(candles_1m) < 20:
                print(f"⚠️ {pair}: No candles")
                return None
            
            # Fetch 5M candles for multi-timeframe analysis
            candles_5m = await self.get_candles(pair, 50, 300)
            
            # Analyze with STRATEGY TITAN-X (multi-timeframe)
            direction, confidence, strategy_name = self.strategy.analyze(candles_1m, candles_5m)
            
            if direction != "NO_TRADE" and confidence > 0.3:
                last_candle = candles_1m[-1]
                
                # Format for terminal (no HTML)
                signal = SignalFormatter.format_signal(pair, direction, last_candle, strategy_name, for_telegram=False)
                # Format for Telegram (with HTML)
                signal_telegram = SignalFormatter.format_signal(pair, direction, last_candle, strategy_name, for_telegram=True)
                
                # Extract entry time from signal
                now = datetime.now()
                next_minute = now.replace(second=0, microsecond=0)
                from datetime import timedelta
                next_minute = next_minute + timedelta(minutes=1)
                entry_time = next_minute.strftime("%H:%M")
                
                return (signal, signal_telegram, direction, entry_time)
            
            return None
            
        except Exception as e:
            print(f"❌ Error scanning {pair}: {e}")
            return None
    
    def get_top_pairs(self, top_n: int = 10) -> List[str]:
        """Get top performing pairs by win rate"""
        pair_rates = []
        for pair, stats in self.pair_stats.items():
            total = stats['wins'] + stats['losses']
            if total >= 3:  # Minimum 3 trades
                win_rate = stats['wins'] / total
                pair_rates.append((pair, win_rate, total))
        
        # Sort by win rate, then by total trades
        pair_rates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        if pair_rates:
            return [p[0] for p in pair_rates[:top_n]]
        return self.pairs[:top_n]
    
    def update_pair_performance(self, pair: str, result: str):
        """Update pair performance tracking"""
        if pair not in self.pair_performance:
            self.pair_performance[pair] = {'wins': 0, 'losses': 0, 'trades': []}
        
        self.pair_performance[pair]['trades'].append({
            'result': result,
            'time': datetime.now().isoformat()
        })
        
        if result in ["WIN", "MTG WIN"]:
            self.pair_performance[pair]['wins'] += 1
        else:
            self.pair_performance[pair]['losses'] += 1
    
    def show_pair_ranking(self):
        """Display pair performance ranking"""
        print("\n🏆 PAIR PERFORMANCE RANKING 🏆")
        print("="*50)
        
        rankings = []
        for pair, perf in self.pair_performance.items():
            total = perf['wins'] + perf['losses']
            if total > 0:
                win_rate = (perf['wins'] / total) * 100
                rankings.append((pair, win_rate, perf['wins'], perf['losses'], total))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        for i, (pair, wr, w, l, t) in enumerate(rankings[:10], 1):
            name = PAIR_ACTUAL_NAME.get(pair, pair)
            print(f"{i}. {name}: {wr:.1f}% ({w}W/{l}L) - {t} trades")
        
        print("="*50 + "\n")
    
    def show_session_summary(self):
        """Display session summary when bot closes"""
        if not self.trade_history:
            print("\n⚪ No trades in this session\n")
            return
        
        total = self.wins + self.losses
        win_rate = int((self.wins / total * 100)) if total > 0 else 0
        
        # Calculate profit (assuming $10 per trade, 80% payout)
        profit_per_win = 8.0  # $10 * 0.8
        loss_per_trade = 10.0
        total_profit = (self.wins * profit_per_win) - (self.losses * loss_per_trade)
        
        summary = f"""\n========= 𝗣𝗔𝗥𝗧𝗜𝗔𝗟 ==========
━━━━━━━━━
                  **OTC-MARKET**
━━━━━━━━━・━━━━━━━━━
"""
        
        # Add trade history
        for trade in self.trade_history:
            pair_name = PAIR_ACTUAL_NAME.get(trade['pair'], trade['pair']).replace(" ", "").replace("(", "-").replace(")", "")
            direction_text = "𝙱𝚄𝚈" if trade['direction'] == "CALL" else "𝚂𝙴𝙻𝙻"
            
            if trade['result'] == "WIN":
                result_icon = "✅"
            elif trade['result'] == "MTG WIN":
                result_icon = "✅¹"
            else:
                result_icon = "❌"
            
            summary += f"⧉ {trade['time']} - {pair_name} - {direction_text} {result_icon}\n"
        
        summary += f"""━━━━━━━━━・━━━━━━━━━
 🧮 PLACER : {self.wins} x {self.losses} ⋅◈⋅ ({win_rate}%)
━━━━━━━━━・━━━━━━━━━
🚀 WIN : {self.wins} ┃ LOSS : {self.losses} ┃ ⋅◈⋅ ({win_rate}%)
━━━━━━━━━・━━━━━━━━━
💰 TOTAL PROFIT : ${total_profit:.2f}
━━━━━━━━━・━━━━━━━━━
📳 PARTIAL SEND SUCCESSFULLY\n"""
        
        print(summary)
    
    async def backtest(self, pair: str, days: int = 7):
        """Backtest strategy on historical data"""
        print(f"\n📊 BACKTESTING {pair} - Last {days} days")
        print("="*50)
        
        # Fetch historical data
        period = 60
        candles_needed = days * 24 * 60  # Total 1M candles
        offset = candles_needed * period
        
        try:
            end_time = time.time()
            candles = await self.client.get_candles(pair, end_time, offset, period)
            
            if not candles or len(candles) < 200:
                print("❌ Not enough data for backtesting")
                return
            
            # Convert candles
            formatted_candles = []
            for c in candles:
                formatted_candles.append({
                    'open': float(c.get('open', 0)),
                    'high': float(c.get('max', c.get('high', 0))),
                    'low': float(c.get('min', c.get('low', 0))),
                    'close': float(c.get('close', 0)),
                    'time': c.get('time', 0)
                })
            
            bt_wins = 0
            bt_losses = 0
            signals_found = 0
            
            # Simulate trading
            for i in range(199, len(formatted_candles) - 2):
                window = formatted_candles[i-199:i+1]
                direction, confidence, _ = self.strategy.analyze(window, None)
                
                if direction != "NO_TRADE" and confidence > 0.4:
                    signals_found += 1
                    next_candle = formatted_candles[i+1]
                    
                    # Check result
                    if direction == "CALL":
                        if next_candle['close'] > next_candle['open']:
                            bt_wins += 1
                        else:
                            bt_losses += 1
                    elif direction == "PUT":
                        if next_candle['close'] < next_candle['open']:
                            bt_wins += 1
                        else:
                            bt_losses += 1
            
            total = bt_wins + bt_losses
            win_rate = (bt_wins / total * 100) if total > 0 else 0
            
            print(f"📊 Signals Found: {signals_found}")
            print(f"✅ Wins: {bt_wins}")
            print(f"❌ Losses: {bt_losses}")
            print(f"🎯 Win Rate: {win_rate:.1f}%")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"❌ Backtest error: {e}\n")
    
    async def check_result(self, pair: str, direction: str, entry_time: str) -> str:
        """Check if prediction was correct after 1 minute, with MTG logic"""
        try:
            # Wait for the candle to close (wait until next minute + 5 seconds buffer)
            now = datetime.now()
            entry_dt = datetime.strptime(entry_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            wait_until = entry_dt.replace(second=5, microsecond=0)
            from datetime import timedelta
            wait_until = wait_until + timedelta(minutes=1)
            
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                print(f"⏳ Waiting {int(wait_seconds)} seconds for candle to close...")
                await asyncio.sleep(wait_seconds)
            
            # Fetch the result candle
            candles = await self.get_candles(pair, 2)
            if not candles or len(candles) < 1:
                return "UNKNOWN"
            
            result_candle = candles[-1]
            
            # Check if prediction was correct
            first_result = None
            if direction == "CALL":
                if result_candle['close'] > result_candle['open']:
                    first_result = "WIN"
                else:
                    first_result = "LOSS"
            elif direction == "PUT":
                if result_candle['close'] < result_candle['open']:
                    first_result = "WIN"
                else:
                    first_result = "LOSS"
            
            # If first candle is WIN, return immediately
            if first_result == "WIN":
                return "WIN"
            
            # If first candle is LOSS, check next candle for MTG
            if first_result == "LOSS":
                print("⚠️ First candle LOSS, checking MTG...")
                
                # Wait for next candle to close
                await asyncio.sleep(65)  # Wait 65 seconds for next candle
                
                # Fetch candles again
                candles = await self.get_candles(pair, 2)
                if not candles or len(candles) < 1:
                    return "LOSS"
                
                mtg_candle = candles[-1]
                
                # Check MTG candle
                if direction == "CALL":
                    if mtg_candle['close'] > mtg_candle['open']:
                        print("✅ MTG WIN!")
                        return "MTG WIN"
                    else:
                        print("❌ MTG LOSS")
                        return "LOSS"
                elif direction == "PUT":
                    if mtg_candle['close'] < mtg_candle['open']:
                        print("✅ MTG WIN!")
                        return "MTG WIN"
                    else:
                        print("❌ MTG LOSS")
                        return "LOSS"
            
            return "UNKNOWN"
            
        except Exception as e:
            print(f"❌ Error checking result: {e}")
            return "UNKNOWN"
    
    async def scan_all_pairs(self):
        """Scan all pairs for signals"""
        print("🔍 Scanning pairs with STRATEGY TITAN-X...")
        
        for i, pair in enumerate(self.pairs, 1):
            print(f"   [{i}/{len(self.pairs)}] Scanning {pair}...", end="\r")
            signal_data = await self.scan_pair(pair)
            if signal_data:
                signal, signal_telegram, direction, entry_time = signal_data
                print(signal)
                print("\n" + "="*50 + "\n")
                
                # Send signal to Telegram with premium emojis
                await self.telegram.send_message(signal_telegram)
                
                # Check result
                result = await self.check_result(pair, direction, entry_time)
                
                if result == "WIN" or result == "MTG WIN":
                    self.wins += 1
                    if pair not in self.pair_stats:
                        self.pair_stats[pair] = {"wins": 0, "losses": 0}
                    self.pair_stats[pair]["wins"] += 1
                    self.strategy.win_rate_history.append(1)
                elif result == "LOSS":
                    self.losses += 1
                    if pair not in self.pair_stats:
                        self.pair_stats[pair] = {"wins": 0, "losses": 0}
                    self.pair_stats[pair]["losses"] += 1
                    self.strategy.win_rate_history.append(0)
                
                # Update pair performance
                self.update_pair_performance(pair, result)
                
                # Save trade to history
                self.trade_history.append({
                    'time': entry_time,
                    'pair': pair,
                    'direction': direction,
                    'result': result
                })
                
                # Adapt thresholds based on performance
                self.strategy.adapt_thresholds()
                
                # Show result
                if result != "UNKNOWN":
                    pair_wins = self.pair_stats[pair]["wins"]
                    pair_losses = self.pair_stats[pair]["losses"]
                    result_msg = SignalFormatter.format_result(pair, entry_time, result, self.wins, self.losses, pair_wins, pair_losses)
                    print(result_msg)
                    print("\n" + "="*50 + "\n")
                    
                    # Send result to Telegram
                    await self.telegram.send_message(result_msg)
                
                # Don't return, continue scanning for more signals
            
            # Small delay between pairs
            await asyncio.sleep(0.3)
        
        print(f"\n✅ Scan complete - checked {len(self.pairs)} pairs\n")
    
    async def run_continuous(self, interval: int = 5):
        """Run bot continuously"""
        print("🚀 STRATEGY TITAN-X Bot Started!")
        print(f"📊 Monitoring {len(self.pairs)} pairs")
        print(f"⏰ Scan interval: {interval} seconds\n")
        
        scan_count = 0
        
        while True:
            try:
                await self.scan_all_pairs()
                scan_count += 1
                
                # Show pair ranking every 20 scans
                if scan_count % 20 == 0:
                    self.show_pair_ranking()
                
                # Small delay before next scan
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.show_session_summary()
                self.show_pair_ranking()
                if self.client:
                    await self.client.close()
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await asyncio.sleep(5)


async def main():
    """Main function to run the bot"""
    print("\n" + "="*50)
    print("🤖 STRATEGY TITAN-X BOT")
    print("="*50 + "\n")
    
    bot = PyQuotexBot()
    
    # Connect first
    await bot.connect()
    
    # Uncomment to run backtest on a pair
    # await bot.backtest("EURUSD_otc", days=7)
    
    # Run continuous mode (5 second interval)
    await bot.run_continuous(5)


if __name__ == "__main__":
    asyncio.run(main())
