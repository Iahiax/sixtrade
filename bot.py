"""
FinBERTx - Main Autonomous CFD Trading Bot Daemon
Integrates:
- FinBERT NLP Engine on CPU (ProsusAI/finbert)
- Multi-Timeframe Analysis Engine (M5, M15, M30, H1, H4, D1) for Confirmed Decisions (قرارات أكيدة)
- Capital.com Broker API (Demo / Live, 1:100 Highest Leverage, Market Hours Check)
- Compounding Trading Engine (Live balance query & exponential growth reinvestment)
- Dynamic Volatility-Based Stop Loss and Take Profit
- FMP, FRED, and Finnhub Financial News & Macro Feeds
- Telegram Bot 18 Command Listener & Channel Broadcaster
- Automated Periodic Backtest Engine
"""
import sys
import time
import signal
import json
from pathlib import Path
from typing import Dict, Any

import config
from finbert_engine import finbert_engine
from capital_broker import capital_broker
from economic_calendar import economic_calendar
from telegram_manager import telegram_manager
from backtest_engine import backtest_engine
from mtf_engine import mtf_engine

class FinBERTxTradingBot:
    def __init__(self):
        self.is_running = False
        self.market_was_open = None
        self.last_backtest_broadcast = 0
        self.last_scan_time = 0
        self.tracked_pairs = config.TRACKED_PAIRS
        self.state_file = config.STATE_FILE

        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    mode = data.get("trading_mode", config.DEFAULT_TRADING_MODE)
                    capital_broker.set_mode(mode)
                    self.last_backtest_broadcast = data.get("last_backtest_broadcast", 0)
                    print(f"[*] تم استرجاع حالة البوت: وضع={mode}")
            except Exception as e:
                print(f"[!] تعذر قراءة ملف الحالة: {e}")

    def _save_state(self):
        try:
            data = {
                "trading_mode": capital_broker.mode,
                "last_backtest_broadcast": self.last_backtest_broadcast,
                "timestamp": time.time(),
                "time_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] تعذر حفظ ملف الحالة: {e}")

    def start(self):
        """بدء تشغيل البوت الذاتي والتراكمي"""
        self.is_running = True
        print("\n" + "="*55)
        print("  🚀 تشغيل بوت التداول الذاتي والتراكمي FinBERTx")
        print("  المحرك: ProsusAI/finbert على المعالج CPU")
        print(f"  الوسيط: Capital.com ({capital_broker.mode}) - رافعة 1:{config.LEVERAGE}")
        print(f"  نظام الفريمات: M5, M15, M30, H1, H4, D1 لقرارات أكيدة")
        print(f"  التداول التراكمي: مفعّل بنسبة {config.COMPOUNDING_RISK_PERCENT}% من الرصيد")
        print(f"  القناة: {config.TELEGRAM_CHAT_ID}")
        print("="*55 + "\n")

        # 1. تسجيل الدخول إلى Capital.com
        if not capital_broker.authenticate():
            print("[!] تحذير: فشل الاتصال الأولي مع Capital.com، سيتم إعادة المحاولة في الحلقة الرئيسية.")

        # 2. تسجيل الأوامر في Telegram Bot API وبدء الاستماع
        telegram_manager.register_commands_with_telegram_api()
        telegram_manager.start_polling_in_background()

        # 3. توليد الرابط العام للواجهة الرسومية عبر النفق السحابي وبثه
        from tunnel_manager import tunnel_manager
        public_url = tunnel_manager.start_tunnel()

        # 4. إرسال إشعار بدء التشغيل في القناة
        summary = capital_broker.get_account_summary()
        welcome_broadcast = (
            f"🚀 *تم بدء تشغيل بوت التداول الذاتي والتراكمي FinBERTx*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🧠 *محرك الذكاء الاصطناعي:* `ProsusAI/finbert` على الـ CPU\n"
            f"🔍 *نظام التحليل:* متعدد الفريمات (M5, M15, M30, H1, H4, D1)\n"
            f"💼 *الوسيط المعتمد:* Capital.com ({capital_broker.mode})\n"
            f"💰 *الرصيد المستعلم عنه:* `${summary.get('balance', 0.0):.2f}`\n"
            f"📈 *التداول التراكمي (Compounding):* مفعّل بنسبة `{config.COMPOUNDING_RISK_PERCENT}%`\n"
            f"⚖️ *الرافعة المالية:* `1:{config.LEVERAGE}` (أعلى رافعة 100:1)\n"
            f"📊 *الأزواج النشطة:* {len(self.tracked_pairs)} زوج CFD بالكامل\n"
            f"🌐 *رابط الواجهة العام المباشر:*\n{public_url}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ البوت يرصد الفرص الأكيدة وينفذ الصفقات آلياً."
        )
        telegram_manager.send_channel_broadcast(welcome_broadcast)

        # 4. تشغيل حلقة التداول الرئيسية
        self._main_loop()

    def _main_loop(self):
        while self.is_running:
            try:
                # أ. فحص حالة السوق
                is_open, market_status = capital_broker.is_market_open("EURUSD")

                # إذا تغيرت حالة السوق (افتتح أو أغلق)
                if self.market_was_open is not None and self.market_was_open != is_open:
                    telegram_manager.broadcast_market_status(is_open, market_status)
                self.market_was_open = is_open

                if not is_open:
                    print(f"[{time.strftime('%H:%M:%S')}] ⏸ السوق مغلق حالياً ({market_status}). البوت في وضع الاستعداد...")
                    time.sleep(config.CHECK_INTERVAL_SECONDS)
                    continue

                # ب. فحص الباكتيست الدوري وبثه في القناة
                now = time.time()
                if (now - self.last_backtest_broadcast) >= config.BACKTEST_BROADCAST_INTERVAL:
                    print("[*] تشغيل التقرير الدوري للباكتيست وبثه في القناة...")
                    backtest_data = backtest_engine.run_backtest(timeframe="H1", lookback_days=30, leverage=config.LEVERAGE)
                    telegram_manager.send_channel_broadcast(backtest_engine.format_telegram_report(backtest_data))
                    self.last_backtest_broadcast = now
                    self._save_state()

                # ج. فحص الفرص المؤكدة للأزواج عبر جميع الفريمات (MTF)
                self._scan_markets_and_trade()

            except Exception as e:
                print(f"[!] خطأ في الحلقة الرئيسية للبوت: {e}")

            time.sleep(config.CHECK_INTERVAL_SECONDS)

    def _scan_markets_and_trade(self):
        """فحص أزواج العملات عبر جميع الفريمات (MTF) وتنفيذ الصفقات المؤكدة تراكمياً"""
        open_positions = capital_broker.get_open_positions()
        active_epics = [p["epic"] for p in open_positions]

        # جلب أحدث الأخبار المالية من FMP و Finnhub
        news = economic_calendar.get_latest_financial_news(limit=25)
        if not news:
            return

        print(f"[{time.strftime('%H:%M:%S')}] مسح الفريمات والأخبار لـ {len(self.tracked_pairs)} زوج CFD...")

        for pair in self.tracked_pairs:
            # تجنب فتح صفقة مكررة لنفس الزوج
            if pair in active_epics:
                continue

            # التحليل المتعدد الفريمات (M5, M15, M30, H1, H4, D1)
            mtf_res = mtf_engine.analyze_pair_mtf(pair, news)
            is_confirmed = mtf_res.get("is_confirmed", False)
            decision = mtf_res.get("decision")

            # لا يتم الدخول إلا إذا كان القرار أكيداً بتوافق الفريمات
            if is_confirmed and decision in ["CONFIRMED_BUY", "CONFIRMED_SELL"]:
                trade_dir = "BUY" if decision == "CONFIRMED_BUY" else "SELL"
                print(f"[!] قرار تداول أكيد على {pair}: {trade_dir} (توافق الفريمات: {mtf_res.get('alignment_pct')}%)")

                # تنفيذ الأمر في Capital.com بحجم عقد تراكمي ورافعة 1:100
                order_res = capital_broker.execute_order(
                    epic=pair,
                    direction=trade_dir,
                    sentiment_info={
                        "direction_ar": mtf_res.get("decision_ar"),
                        "confidence": mtf_res.get("alignment_pct", 80) / 100.0,
                        "sample_headline": f"توافق فريمات {mtf_res.get('alignment_count')}/{mtf_res.get('total_timeframes')}"
                    }
                )

                if order_res.get("success"):
                    print(f"[✓] تم تنفيذ الصفقة التراكمية على {pair}! المرجع: {order_res.get('dealReference')}")
                    # بث فوري للقناة
                    telegram_manager.broadcast_trade_entry(order_res)
                    active_epics.append(pair)
                else:
                    print(f"[!] فشل تنفيذ أمر {pair}: {order_res.get('error')}")

    def stop(self):
        print("\n[*] إيقاف تشغيل بوت FinBERTx...")
        self.is_running = False
        telegram_manager.stop_polling()
        self._save_state()
        print("[✓] تم حفظ الحالة وإيقاف البوت بنجاح.")

# Entry point
if __name__ == "__main__":
    bot = FinBERTxTradingBot()

    def handle_signal(sig, frame):
        bot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()
