#!/bin/bash
# ==============================================================================
# FinBERTx - Check Background Status & Live Logs
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================"
echo "  📊 فحص حالة FinBERTx في الخلفية"
echo "========================================================"

# فحص البوت
if [ -f "$DIR/bot.pid" ] && ps -p $(cat "$DIR/bot.pid") > /dev/null 2>&1; then
    BOT_PID=$(cat "$DIR/bot.pid")
    echo "• حالة البوت:    🟢 نشط ويعمل في الخلفية (PID: $BOT_PID)"
else
    echo "• حالة البوت:    🔴 متوقف (لتشغيله: ./start_background.sh)"
fi

# فحص الواجهة
if [ -f "$DIR/web.pid" ] && ps -p $(cat "$DIR/web.pid") > /dev/null 2>&1; then
    WEB_PID=$(cat "$DIR/web.pid")
    echo "• خادم الواجهة: 🟢 نشط على المنفذ 3000 (PID: $WEB_PID)"
else
    echo "• خادم الواجهة: 🔴 متوقف"
fi

# فحص الرابط العام
if [ -f "$DIR/logs/cloudflared.log" ]; then
    PUB_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]*\.trycloudflare\.com' "$DIR/logs/cloudflared.log" | tail -n 1 || true)
    if [ ! -z "$PUB_URL" ]; then
        echo "• الرابط العام: 🌐 $PUB_URL"
    fi
fi

echo "========================================================"
echo "  📜 آخر 15 سطر من سجل البوت الحقيقي ($DIR/logs/bot.log):"
echo "========================================================"
if [ -f "$DIR/logs/bot.log" ]; then
    tail -n 15 "$DIR/logs/bot.log"
else
    echo "لا توجد سجلات بعد."
fi
echo "========================================================"
