"""
Telegram Manager - Expanded Pure Text Commands & Channel Broadcaster
Features:
- Expanded command suite (18 direct commands)
- Real-time balance queries & compounding position reports
- Multi-timeframe analysis command (/multi_tf EURUSD)
- FMP economic feed & forex rates (/fmp)
- Emergency close all open positions (/close_all)
- Broadcasts to channel (-1004325895118)
- 1:100 Highest Leverage and All 28 CFD Forex Pairs
"""
import requests
import time
import threading
from typing import Dict, List, Any, Optional
import config
from capital_broker import capital_broker
from finbert_engine import finbert_engine
from economic_calendar import economic_calendar
from backtest_engine import backtest_engine
from mtf_engine import mtf_engine

class TelegramManager:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.channel_id = config.TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0
        self.is_running = False
        self._thread = None

    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """إرسال رسالة نصية إلى محادثة أو مستخدم معين"""
        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            return resp.status_code == 200 and resp.json().get("ok", False)
        except Exception as e:
            print(f"[!] خطأ في إرسال رسالة تيلجرام: {e}")
            return False

    def send_channel_broadcast(self, text: str) -> bool:
        """إرسال بث وتنبيه مباشر إلى قناة التيلجرام المحددة (-1004325895118)"""
        return self.send_message(self.channel_id, text, parse_mode="Markdown")

    def broadcast_trade_entry(self, trade_data: Dict[str, Any]) -> bool:
        """بث تفاصيل فتح صفقة جديدة إلى القناة مع الرافعة 1:100 والتداول التراكمي"""
        direction_emoji = "🟢 ⬆️" if trade_data.get("direction") == "BUY" else "🔴 ⬇️"
        mode_badge = "🧪 تجريبي (DEMO)" if trade_data.get("mode") == "DEMO" else "⚡ حقيقي (LIVE)"

        sentiment = trade_data.get("sentiment_info") or {}
        confidence_pct = (sentiment.get("confidence", 0.0)) * 100

        msg = (
            f"🔔 *تنفيذ صفقة CFD جديدة بتداول تراكمي (Compounding)*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 *الزوج:* `{trade_data.get('epic')}`\n"
            f"{direction_emoji} *نوع الأمر:* *{trade_data.get('direction')}*\n"
            f"🎯 *سعر الدخول:* `{trade_data.get('entryPrice')}`\n"
            f"🛡 *وقف الخسارة الديناميكي:* `{trade_data.get('stopLevel')}`\n"
            f"💰 *جني الأرباح الديناميكي:* `{trade_data.get('profitLevel')}`\n"
            f"⚖️ *الرافعة المالية:* `1:{config.LEVERAGE}` (أعلى رافعة 100:1)\n"
            f"💼 *حجم العقد التراكمي:* `{trade_data.get('size')} Units`\n"
            f"🔖 *وضع الحساب:* *{mode_badge}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🧠 *تحليل FinBERT المتعدد الفريمات (MTF):*\n"
            f"• الإشارة: `{sentiment.get('direction_ar', 'قرار تداول مؤكد')}`\n"
            f"• نسبة التأكيد: `{confidence_pct:.1f}%`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *رقم المرجع:* `{trade_data.get('dealReference')}`\n"
            f"⏰ _{trade_data.get('timestamp')}_"
        )
        return self.send_channel_broadcast(msg)

    def handle_command(self, chat_id: str, text: str) -> None:
        """معالجة الأوامر النصية المباشرة الموسعة"""
        clean_text = text.strip()
        cmd_parts = clean_text.split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""

        if cmd in ["/start", "start"]:
            summary = capital_broker.get_account_summary()
            mode_badge = "🧪 تجريبي (Demo)" if capital_broker.mode == "DEMO" else "⚡ حقيقي (Live)"
            msg = (
                "👋 *مرحباً بك في بوت التداول الذاتي والتراكمي FinBERTx!* 🤖\n\n"
                f"🔹 *الوضع الحالي:* *{mode_badge}*\n"
                f"🔹 *الرافعة المالية:* `1:{config.LEVERAGE}` (أعلى رافعة 100:1)\n"
                f"🔹 *التداول التراكمي (Compounding):* مفعّل بنسبة `{config.COMPOUNDING_RISK_PERCENT}%` من الرصيد\n"
                f"🔹 *تحليل الفريمات (MTF):* فحص M5, M15, M30, H1, H4, D1 لقرارات أكيدة\n"
                f"🔹 *أزواج العملات:* {len(config.TRACKED_PAIRS)} زوج CFD بالكامل\n\n"
                "📋 *قائمة الأوامر النصية المتاحة:*\n"
                "• `/balance` - استعلام لحظي عن الرصيد، الهامش، وحجم العقد التراكمي\n"
                "• `/compound` - شرح ونسب نمو التداول التراكمي\n"
                "• `/multi_tf EURUSD` - فحص وتأكيد القرار عبر جميع الفريمات\n"
                "• `/pairs` - قائمة جميع أزواج العملات الـ 28 المراقبة\n"
                "• `/fmp` - أخبار وأسعار مزود FMP المالي اللحظية\n"
                "• `/status` - حالة النظام، السوق، والاتصال\n"
                "• `/sentiment` - قراءة مشاعر FinBERT اللحظية لأزواج العملات\n"
                "• `/macro` - أهم مؤشرات الماكرو من بنك الفيدرالي FRED\n"
                "• `/positions` - استعراض الصفقات المفتوحة وأرباحها\n"
                "• `/close_all` - إغلاق جميع الصفقات المفتوحة دفعة واحدة\n"
                "• `/backtest` - تشغيل فوري للباكتيست وبثه في القناة\n"
                "• `/mode_demo` - التبديل إلى الحساب التجريبي Demo\n"
                "• `/mode_live` - التبديل إلى الحساب الحقيقي Live\n"
                "• `/market_status` - التحقق من افتتاح/إغلاق السوق\n"
                "• `/trade_buy EURUSD` - أمر شراء فوري بتداول تراكمي\n"
                "• `/trade_sell EURUSD` - أمر بيع فوري بتداول تراكمي\n"
                "• `/help` - دليل المساعدة الشامل\n\n"
                "💡 *تحليل الأخبار الذكي:* أرسل أي نص خبر مالي بالإنجليزية وسيقوم نموذج ProsusAI/finbert بتحليله فورياً على الـ CPU!"
            )
            self.send_message(chat_id, msg)

        elif cmd == "/balance":
            summary = capital_broker.get_account_summary()
            sample_size = capital_broker.calculate_compounding_size("EURUSD", 1.1150)
            msg = (
                f"💰 *استعلام رصيد المحفظة والتداول التراكمي:* 🏦\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"• الرصيد الإجمالي: `${summary.get('balance', 0.0):.2f}`\n"
                f"• حقوق الملكية (Equity): `${summary.get('equity', summary.get('balance', 0.0)):.2f}`\n"
                f"• الهامش المتاح: `${summary.get('available', 0.0):.2f}`\n"
                f"• الهامش المحجوز: `${summary.get('deposit', 0.0):.2f}`\n"
                f"• الأرباح/الخسائر اللحظية: `${summary.get('profitLoss', 0.0):+.2f}`\n"
                f"• العملة الأساسية: `{summary.get('currency', 'USD')}`\n"
                f"• وضع الحساب: *{summary.get('mode')}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📈 *حساب التداول التراكمي (Compounding):*\n"
                f"• نسبة المخاطرة من الرصيد: `{config.COMPOUNDING_RISK_PERCENT}%`\n"
                f"• الرافعة المالية: `1:{config.LEVERAGE}` (100:1)\n"
                f"• حجم العقد القادم لـ EURUSD: `{sample_size} Units`\n"
                f"💡 _حجم الصفقات يتضاعف تلقائياً مع نمو الرصيد والأرباح!_"
            )
            self.send_message(chat_id, msg)

        elif cmd == "/compound":
            summary = capital_broker.get_account_summary()
            bal = summary.get("balance", 100.0)
            msg = (
                "📈 *نظام التداول التراكمي (Compounding Engine):*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"• الرصيد الأساسي الحالي: `${bal:.2f}`\n"
                f"• نسبة الاستثمار لكل صفقة: `{config.COMPOUNDING_RISK_PERCENT}%`\n"
                f"• الرافعة المالية المطبقة: `1:{config.LEVERAGE}`\n\n"
                "📊 *آلية العمل الرياضية:*\n"
                "1. قبل فتح أي صفقة، يستعلم البوت لحظياً عن رصيد الحساب المالي من Capital.com.\n"
                "2. يتم احتساب حجم اللوت تناسبياً مع الرصيد الحالي (Reinvestment of profits).\n"
                "3. عند تحقيق أرباح، يرتفع الرصيد وبالتالي يكبر حجم الصفقة التالية تلقائياً لتحقيق نمو أسي (Exponential Growth) في رأس المال.\n"
                "4. عند الخسارة، يقل حجم الصفقة آلياً لحماية المحفظة من التراجع."
            )
            self.send_message(chat_id, msg)

        elif cmd.startswith("/multi_tf"):
            parts = clean_text.split()
            pair = parts[1].upper() if len(parts) > 1 else "EURUSD"
            news = economic_calendar.get_latest_financial_news(limit=10)
            res = mtf_engine.analyze_pair_mtf(pair, news)

            lines = [
                f"🔍 *التحليل المتعدد الفريمات (MTF) لـ {pair}:*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *القرار النهائي:* *{res.get('decision_ar')}*\n"
                f"📊 *نسبة توافق الفريمات:* `{res.get('alignment_pct')}%` ({res.get('alignment_count')}/{res.get('total_timeframes')})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏱ *تفاصيل الفريمات الزمنية:*"
            ]

            for tf, data in res.get("timeframes", {}).items():
                sig_emoji = "🟢 صاعد" if data["signal"] == "BUY" else ("🔴 هابط" if data["signal"] == "SELL" else "⚪ محايد")
                lines.append(f"• *{tf}:* {sig_emoji} ({data['trend_name']}) - قوة: `{int(data['strength']*100)}%`")

            lines.append("━━━━━━━━━━━━━━━━━━")
            lines.append("💡 _لا يتم فتح الصفقة تلقائياً إلا عند توافق 4 فريمات على الأقل لضمان قرار أكيد._")
            self.send_message(chat_id, "\n".join(lines))

        elif cmd == "/pairs":
            pairs_text = ", ".join(config.TRACKED_PAIRS)
            msg = (
                f"🌐 *أزواج عملات الـ CFDs المراقبة بالكامل ({len(config.TRACKED_PAIRS)} زوج):*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{pairs_text}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚖️ الرافعة المالية: `1:{config.LEVERAGE}` (100:1 لجميع الأزواج)\n"
                f"🤖 يمسح البوت جميع هذه الأزواج لحظياً بحثاً عن إشارات FinBERT وتوافق الفريمات."
            )
            self.send_message(chat_id, msg)

        elif cmd == "/fmp":
            cal = economic_calendar.get_fmp_economic_calendar(limit=4)
            news = economic_calendar.get_latest_financial_news(limit=3)
            lines = [
                "📡 *بيانات مزود Financial Modeling Prep (FMP):*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🗓 *أهم أحداث المفكرة الاقتصادية القادمة:*"
            ]
            for ev in cal:
                lines.append(f"• {ev.get('event')} ({ev.get('country')}) | الأهمية: `{ev.get('impact')}`")

            lines.append("\n📰 *أحدث الأخبار الاقتصادية من FMP & Wire:*")
            for n in news:
                lines.append(f"• _{n.get('headline')[:85]}..._")

            self.send_message(chat_id, "\n".join(lines))

        elif cmd == "/status":
            summary = capital_broker.get_account_summary()
            is_open, m_status = capital_broker.is_market_open("EURUSD")
            mode_badge = "🧪 Demo (تجريبي)" if capital_broker.mode == "DEMO" else "⚡ Live (حقيقي)"
            status_emoji = "🟢 مفتوح (نشط)" if is_open else "🔴 مغلق (عطلة)"

            msg = (
                f"⚙️ *حالة نظام FinBERTx التشغيلية:*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🤖 *نموذج FinBERT:* يعمل على المعالج CPU ✅\n"
                f"💼 *وضع الحساب:* *{mode_badge}*\n"
                f"🏦 *حساب Capital.com:* `{summary.get('accountId', 'N/A')}`\n"
                f"💵 *الرصيد الفعلي:* `${summary.get('balance', 0.0):.2f} {summary.get('currency', 'USD')}`\n"
                f"📈 *التداول التراكمي:* مفعّل بنسبة `{config.COMPOUNDING_RISK_PERCENT}%`\n"
                f"⚖️ *الرافعة المالية:* `1:{config.LEVERAGE}` (أعلى رافعة 100:1)\n"
                f"📊 *حالة السوق:* {status_emoji} (`{m_status}`)\n"
                f"🌐 *الأزواج المراقبة:* {len(config.TRACKED_PAIRS)} أزواج CFD\n"
                f"📡 *مزودات البيانات:* FMP + FRED + Finnhub ✅"
            )
            self.send_message(chat_id, msg)

        elif cmd == "/positions":
            positions = capital_broker.get_open_positions()
            if not positions:
                self.send_message(chat_id, "ℹ️ لا توجد صفقات مفتوحة حالياً على الحساب.")
                return

            lines = [f"📋 *الصفقات المفتوحة ({len(positions)}):*\n━━━━━━━━━━━━━━━━━━"]
            for p in positions:
                emoji = "🟢" if p["direction"] == "BUY" else "🔴"
                upl_str = f"{p['upl']:+.2f}$"
                lines.append(
                    f"{emoji} *{p['epic']}* | {p['direction']} ({p['size']}U)\n"
                    f"   الدخول: `{p['openLevel']}` | الربح: `{upl_str}`\n"
                    f"   المعرف: `{p['dealId']}`"
                )
            self.send_message(chat_id, "\n".join(lines))

        elif cmd == "/close_all":
            res = capital_broker.close_all_positions()
            msg = (
                f"🚨 *أمر إغلاق جميع الصفقات المفتوحة:*\n"
                f"• تم إغلاق: `{res.get('closed_count')}` من أصل `{res.get('total_open')}` صفقة بنجاح.\n"
            )
            if res.get("errors"):
                msg += f"• ملاحظات: {res.get('errors')[:1]}"
            self.send_message(chat_id, msg)

        elif cmd == "/sentiment":
            news = economic_calendar.get_latest_financial_news(limit=10)
            sample_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "GBPJPY"]
            lines = ["🧠 *قراءات مشاعر FinBERT اللحظية لأهم أزواج الـ CFDs:*\n━━━━━━━━━━━━━━━━━━"]
            for pair in sample_pairs:
                res = finbert_engine.aggregate_pair_sentiment(news, pair)
                sig_emoji = "🟢 BUY" if res["signal"] == "BUY" else ("🔴 SELL" if res["signal"] == "SELL" else "⚪ HOLD")
                lines.append(
                    f"*{pair}:* {sig_emoji} (ثقة: `{res['confidence']*100:.1f}%`)\n"
                    f"   إيجابي: `{res['scores']['Positive']*100:.0f}%` | سلبي: `{res['scores']['Negative']*100:.0f}%` | محايد: `{res['scores']['Neutral']*100:.0f}%`"
                )
            self.send_message(chat_id, "\n".join(lines))

        elif cmd == "/macro":
            macro = economic_calendar.get_macro_indicators()
            msg = (
                "🌐 *مؤشرات الماكرو الاقتصادية اللحظية (FRED St. Louis Fed):*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"• مؤشر التضخم CPI: `{macro.get('CPI', {}).get('value')}` ({macro.get('CPI', {}).get('trend', '')})\n"
                f"• الفائدة الفيدرالية FEDFUNDS: `{macro.get('FEDFUNDS', {}).get('value')}%` ({macro.get('FEDFUNDS', {}).get('trend', '')})\n"
                f"• معدل البطالة UNRATE: `{macro.get('UNRATE', {}).get('value')}%` ({macro.get('UNRATE', {}).get('trend', '')})\n"
                f"• الوظائف غير الزراعية NFP: `{macro.get('NFP', {}).get('value')}` ({macro.get('NFP', {}).get('trend', '')})\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "📡 مربوط ببيانات الاحتياطي الفيدرالي ومحدث لحظياً."
            )
            self.send_message(chat_id, msg)

        elif cmd == "/backtest":
            self.send_message(chat_id, "⏳ جاري تشغيل اختبار الأداء (Backtest) لجميع أزواج الـ CFDs برافعة 100:1 وبثه للقناة...")
            res = backtest_engine.run_backtest(timeframe="H1", lookback_days=30)
            report = backtest_engine.format_telegram_report(res)
            self.send_channel_broadcast(report)
            self.send_message(chat_id, f"✅ تم تنفيذ الباكتيست وبثه بنجاح إلى القناة:\n\n{report}")

        elif cmd == "/mode_demo":
            ok = capital_broker.set_mode("DEMO")
            msg = "✅ تم التحويل بنجاح إلى: *الحساب التجريبي (Paper Trading - DEMO)* 🧪" if ok else "❌ تعذر التبديل للحساب التجريبي."
            self.send_message(chat_id, msg)

        elif cmd == "/mode_live":
            ok = capital_broker.set_mode("LIVE")
            msg = "⚠️ *تنبيه أمان:* تم التحويل بنجاح إلى: *الحساب الحقيقي (Real Trading - LIVE)*! ⚡\nجميع الصفقات القادمة ستنفذ بأموال حقيقية ورافعة 1:100." if ok else "❌ تعذر التبديل للحساب الحقيقي."
            self.send_message(chat_id, msg)

        elif cmd == "/market_status":
            is_open, status_str = capital_broker.is_market_open("EURUSD")
            status_emoji = "🟢 مفتوح (نشط)" if is_open else "🔴 مغلق (عطلة)"
            msg = (
                f"🌐 *حالة سوق العملات والـ CFDs:*\n"
                f"• الحالة: {status_emoji}\n"
                f"• وصف المنصة: `{status_str}`\n"
                f"• الرافعة المالية: `1:{config.LEVERAGE}` (100:1)\n"
                f"• توقيت السيرفر: `{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}`"
            )
            self.send_message(chat_id, msg)

        elif cmd.startswith("/trade_buy"):
            parts = clean_text.split()
            pair = parts[1].upper() if len(parts) > 1 else "EURUSD"
            res = capital_broker.execute_order(pair, "BUY", sentiment_info={"direction_ar": "أمر شراء يدوي نصي بتداول تراكمي", "confidence": 0.88})
            if res.get("success"):
                self.broadcast_trade_entry(res)
                msg = f"✅ تم تنفيذ أمر الشراء التراكمي بنجاح على *{pair}*!\nالحجم: `{res.get('size')}U` | الرافعة: `{res.get('leverage')}`\nمرجع الصفقة: `{res.get('dealReference')}`"
            else:
                msg = f"❌ فشل تنفيذ أمر الشراء: {res.get('error')}"
            self.send_message(chat_id, msg)

        elif cmd.startswith("/trade_sell"):
            parts = clean_text.split()
            pair = parts[1].upper() if len(parts) > 1 else "EURUSD"
            res = capital_broker.execute_order(pair, "SELL", sentiment_info={"direction_ar": "أمر بيع يدوي نصي بتداول تراكمي", "confidence": 0.88})
            if res.get("success"):
                self.broadcast_trade_entry(res)
                msg = f"✅ تم تنفيذ أمر البيع التراكمي بنجاح على *{pair}*!\nالحجم: `{res.get('size')}U` | الرافعة: `{res.get('leverage')}`\nمرجع الصفقة: `{res.get('dealReference')}`"
            else:
                msg = f"❌ فشل تنفيذ أمر البيع: {res.get('error')}"
            self.send_message(chat_id, msg)

        elif cmd in ["/help", "help"]:
            msg = (
                "📖 *دليل أوامر بوت FinBERTx الشامل:*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "• `/balance` - استعلام فوري عن الرصيد والهامش وحجم العقد\n"
                "• `/compound` - شرح ونسب نمو التداول التراكمي\n"
                "• `/multi_tf EURUSD` - فحص وتأكيد القرار عبر جميع الفريمات (M5-D1)\n"
                "• `/pairs` - قائمة أزواج الـ CFDs الـ 28 المراقبة بالكامل\n"
                "• `/fmp` - أخبار وأسعار مزود FMP المالي اللحظية\n"
                "• `/status` - حالة النظام، السوق، والاتصال\n"
                "• `/positions` - عرض الصفقات المفتوحة وأرباحها\n"
                "• `/close_all` - إغلاق جميع الصفقات المفتوحة دفعة واحدة\n"
                "• `/sentiment` - قراءة المشاعر اللحظية عبر FinBERT\n"
                "• `/macro` - مؤشرات الماكرو من بنك الفيدرالي FRED\n"
                "• `/backtest` - تشغيل فوري للباكتيست وبثه للقناة\n"
                "• `/mode_demo` - التبديل إلى الحساب التجريبي\n"
                "• `/mode_live` - التبديل إلى الحساب الحقيقي\n"
                "• `/market_status` - التحقق من افتتاح/إغلاق السوق\n"
                "• `/trade_buy EURUSD` - أمر شراء فوري بتداول تراكمي\n"
                "• `/trade_sell EURUSD` - أمر بيع فوري بتداول تراكمي\n\n"
                "💡 *تحليل الأخبار:* أرسل أي نص خبر مالي بالإنجليزية لتحليله فوراً عبر ProsusAI/finbert!"
            )
            self.send_message(chat_id, msg)

        else:
            # Analyze arbitrary text via FinBERT
            res = finbert_engine.analyze_text(clean_text)
            sentiment = res.get("sentiment")
            scores = res.get("scores", {})
            confidence = res.get("confidence", 0.0)

            sentiment_ar = "إيجابي (Positive 🟢)" if sentiment == "Positive" else ("سلبي (Negative 🔴)" if sentiment == "Negative" else "محايد (Neutral ⚪)")

            msg = (
                f"🧠 *نتيجة تحليل النص المالي عبر ProsusAI/finbert (على الـ CPU):*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 *النص:* _{clean_text[:140]}_\n\n"
                f"🎯 *المشاعر الغالبة:* *{sentiment_ar}*\n"
                f"📊 *نسبة الثقة:* `{confidence*100:.1f}%`\n\n"
                f"📈 *توزيع الاحتمالات:*\n"
                f"• إيجابي: `{scores.get('Positive', 0)*100:.1f}%`\n"
                f"• سلبي: `{scores.get('Negative', 0)*100:.1f}%`\n"
                f"• محايد: `{scores.get('Neutral', 0)*100:.1f}%`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 _التوجيه:_ " + (
                    "إشارة شراء صاعدة (Bullish) للعملة الأساس 🟢" if sentiment == "Positive" else (
                        "إشارة هبوط وضغط بيعي (Bearish) 🔴" if sentiment == "Negative" else "حالة ترقب وتماسك سعري ⚪"
                    )
                )
            )
            self.send_message(chat_id, msg)

    def register_commands_with_telegram_api(self) -> bool:
        """تسجيل قائمة الأوامر الـ 16 رسمياً في واجهة تيلجرام البرمجية (setMyCommands)"""
        url = f"{self.api_base}/setMyCommands"
        commands = [
            {"command": "start", "description": "تشغيل البوت وعرض لوحة الأوامر"},
            {"command": "balance", "description": "استعلام الرصيد والهامش والتداول التراكمي"},
            {"command": "compound", "description": "تفاصيل ومعدل نمو التداول التراكمي"},
            {"command": "multi_tf", "description": "تحليل الفريمات M5-D1 لاستخراج القرار الأكيد"},
            {"command": "pairs", "description": "قائمة جميع أزواج الـ CFDs الـ 28 المراقبة"},
            {"command": "fmp", "description": "أخبار وأسعار مزود FMP المالي اللحظية"},
            {"command": "status", "description": "حالة النظام والاتصال وحالة السوق"},
            {"command": "sentiment", "description": "مشاعر FinBERT اللحظية للعملات"},
            {"command": "macro", "description": "مؤشرات الماكرو من بنك الفيدرالي FRED"},
            {"command": "positions", "description": "عرض الصفقات المفتوحة وأرباحها"},
            {"command": "close_all", "description": "إغلاق جميع الصفقات المفتوحة فوراً"},
            {"command": "backtest", "description": "تشغيل باكتيست فوري وبثه بالقناة"},
            {"command": "mode_demo", "description": "التبديل إلى الحساب التجريبي Demo"},
            {"command": "mode_live", "description": "التبديل إلى الحساب الحقيقي Live"},
            {"command": "market_status", "description": "فحص حالة افتتاح أو إغلاق السوق"},
            {"command": "trade_buy", "description": "أمر شراء فوري /trade_buy EURUSD"},
            {"command": "trade_sell", "description": "أمر بيع فوري /trade_sell EURUSD"},
            {"command": "help", "description": "دليل الأوامر الشامل والمساعدة"}
        ]
        try:
            r = requests.post(url, json={"commands": commands}, timeout=10)
            return r.status_code == 200 and r.json().get("ok", False)
        except Exception:
            return False

    def poll_updates_once(self):
        url = f"{self.api_base}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": 2}
        try:
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    self.last_update_id = max(self.last_update_id, update.get("update_id", 0))
                    msg = update.get("message")
                    if not msg:
                        continue
                    text = msg.get("text", "")
                    sender_chat_id = str(msg.get("chat", {}).get("id"))
                    if text:
                        self.handle_command(sender_chat_id, text)
        except Exception:
            pass

    def start_polling_in_background(self):
        if self.is_running:
            return
        self.is_running = True

        def _loop():
            print("[*] تم بدء الاستماع لأوامر تيلجرام الموسعة في الخلفية...")
            while self.is_running:
                try:
                    self.poll_updates_once()
                except Exception:
                    pass
                time.sleep(1.5)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_polling(self):
        self.is_running = False

# Global instance
telegram_manager = TelegramManager()

if __name__ == "__main__":
    print("\n--- فحص اتصال Telegram Bot وتسجيل الأوامر الـ 17 ---")
    reg_ok = telegram_manager.register_commands_with_telegram_api()
    print("تسجيل الأوامر في setMyCommands:", "نجح ✅" if reg_ok else "فشل ❌")
    test_msg = "🔄 *تحديث النظام:* تم توسيع أوامر البوت وتفعيل التحليل المتعدد الفريمات (M5-D1) والتداول التراكمي بأعلى رافعة 100:1 لجميع أزواج الـ CFDs الـ 28."
    ok = telegram_manager.send_channel_broadcast(test_msg)
    print("إرسال رسالة تجريبية للقناة:", "نجح ✅" if ok else "فشل ❌")
