#!/bin/bash
# ==============================================================================
# FinBERTx - Stop Background Daemon
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================"
echo "  🛑 إيقاف عمليات FinBERTx في الخلفية"
echo "========================================================"

# 1. إيقاف البوت
if [ -f "$DIR/bot.pid" ]; then
    BOT_PID=$(cat "$DIR/bot.pid")
    echo "[*] إيقاف بوت التداول (PID: $BOT_PID)..."
    kill -15 $BOT_PID 2>/dev/null || kill -9 $BOT_PID 2>/dev/null || true
    rm -f "$DIR/bot.pid"
fi

# 2. إيقاف خادم الواجهة
if [ -f "$DIR/web.pid" ]; then
    WEB_PID=$(cat "$DIR/web.pid")
    echo "[*] إيقاف خادم الواجهة الرسومية (PID: $WEB_PID)..."
    kill -15 $WEB_PID 2>/dev/null || kill -9 $WEB_PID 2>/dev/null || true
    rm -f "$DIR/web.pid"
fi

# 3. إيقاف النفق السحابي
if [ -f "$DIR/tunnel.pid" ]; then
    TUNNEL_PID=$(cat "$DIR/tunnel.pid")
    echo "[*] إيقاف النفق السحابي (PID: $TUNNEL_PID)..."
    kill -15 $TUNNEL_PID 2>/dev/null || kill -9 $TUNNEL_PID 2>/dev/null || true
    rm -f "$DIR/tunnel.pid"
fi

# تنظيف أي عمليات متبقية إن وجدت
pkill -f "python3.*bot.py" 2>/dev/null || true

echo "✅ تم إيقاف جميع العمليات بنجاح!"
