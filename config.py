"""
FinBERTx Trading Bot - Configuration & API Keys
Comprehensive configuration with Compounding Trading, Multi-Timeframe Analysis,
All CFD Forex Pairs, and Dynamic Volatility-Based Risk Management.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load optional .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# ==========================================
# 1. Capital.com Broker API Credentials
# ==========================================
CAPITAL_EMAIL = os.getenv("CAPITAL_EMAIL", "yahia.x@outlook.sa")
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY", "ut2RpxSbx6fiDdHv")
CAPITAL_API_PASSWORD = os.getenv("CAPITAL_API_PASSWORD", "Yahia@1411")

CAPITAL_DEMO_URL = "https://demo-api-capital.backend-capital.com/api/v1"
CAPITAL_LIVE_URL = "https://api-capital.backend-capital.com/api/v1"
CAPITAL_STREAMING_URL = "wss://api-streaming-capital.backend-capital.com/"

# Trading Mode: "DEMO" (Paper Trading) or "LIVE" (Real Trading)
DEFAULT_TRADING_MODE = os.getenv("TRADING_MODE", "DEMO")

# Target Highest Leverage (1:100)
LEVERAGE = 100

# ==========================================
# 2. Telegram Bot & Channel
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8833615675:AAE-NKK9yStPi0NAeRnbJ8p_gZLpcj_8-7E")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004325895118")

# ==========================================
# 3. Macro & Economic Calendar Data APIs (FMP, FRED, Finnhub)
# ==========================================
FMP_API_KEY = os.getenv("FMP_API_KEY", "Jh4bsnzdHnXSVvou5ehHKBbffdrEfrYa")
FRED_API_KEY = os.getenv("FRED_API_KEY", "d295bdec801d4faf6f55e5a5ea34eb07")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d96hs19r01qr77dkhss0d96hs19r01qr77dkhssg")

# ==========================================
# 4. FinBERT Model Settings (Forced on CPU)
# ==========================================
MODEL_NAME = "ProsusAI/finbert"
FORCE_DEVICE = "cpu"
CONFIDENCE_THRESHOLD = 0.55  # Minimum sentiment score threshold

# ==========================================
# 5. Multi-Timeframe Analysis Settings (قرارات أكيدة)
# ==========================================
# Required timeframes for multi-timeframe confirmation
ANALYSIS_TIMEFRAMES = ["M5", "M15", "M30", "H1", "H4", "D1"]
MIN_TIMEFRAME_ALIGNMENT = 4  # At least 4 of 6 timeframes must align for a confirmed trade

# ==========================================
# 6. Compounding Trading Engine (التداول التراكمي)
# ==========================================
COMPOUNDING_ENABLED = True
COMPOUNDING_RISK_PERCENT = float(os.getenv("COMPOUNDING_RISK_PERCENT", "3.0"))  # 3% of real-time balance per trade
MIN_COMPOUND_LOT = 10.0      # Minimum units
MAX_COMPOUND_LOT = 50000.0   # Cap to protect liquidity

# Dynamic Risk Management: Dynamic ATR / Volatility SL/TP
DYNAMIC_SL_ATR_MULTIPLIER = 1.5
DYNAMIC_TP_ATR_MULTIPLIER = 3.0

# ==========================================
# 7. All CFD Currency Pairs (28 Major, Minor & Cross Pairs)
# ==========================================
TRACKED_PAIRS = [
    # Majors
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    # Euro Crosses
    "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD",
    # Pound Crosses
    "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
    # Yen Crosses
    "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
    # Commodity & Minor Crosses
    "AUDCAD", "AUDCHF", "AUDNZD", "CADCHF", "NZDCAD", "NZDCHF"
]

CHECK_INTERVAL_SECONDS = 30  # Responsive monitoring loop
BACKTEST_BROADCAST_INTERVAL = int(os.getenv("BACKTEST_INTERVAL_SEC", 21600))  # 6 hours

STATE_FILE = BASE_DIR / "bot_state.json"
