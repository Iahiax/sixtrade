"""
CLI Utility to run Backtest on FinBERTx strategy
Usage:
    python3 run_backtest.py
    python3 run_backtest.py --timeframe H1 --days 30 --broadcast
"""
import sys
import argparse
from backtest_engine import backtest_engine
from telegram_manager import telegram_manager

def main():
    parser = argparse.ArgumentParser(description="FinBERTx Strategy Backtester")
    parser.add_argument("--timeframe", type=str, default="H1", help="Timeframe (M15, H1, H4, D1)")
    parser.add_argument("--days", type=int, default=30, help="Lookback days")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital in USD")
    parser.add_argument("--leverage", type=float, default=30.0, help="Leverage multiplier")
    parser.add_argument("--broadcast", action="store_true", help="Send report to Telegram Channel")
    args = parser.parse_args()

    print(f"[*] تشغيل الباكتيست: فريم={args.timeframe}، فترة={args.days} يوم، رافعة={args.leverage}x...")
    result = backtest_engine.run_backtest(
        timeframe=args.timeframe,
        lookback_days=args.days,
        initial_capital=args.capital,
        leverage=args.leverage
    )

    report = backtest_engine.format_telegram_report(result)
    print("\n" + report + "\n")

    if args.broadcast:
        print("[*] إرسال التقرير إلى قناة تيلجرام...")
        ok = telegram_manager.send_channel_broadcast(report)
        print("حالة الإرسال:", "نجح ✅" if ok else "فشل ❌")

if __name__ == "__main__":
    main()
