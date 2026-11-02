#!/bin/bash
# ==============================================================================
# FinBERTx - Background Daemon Runner (Zero systemd dependency)
# Works on all Linux VPS (OpenVZ, LXC, Alpine, Ubuntu, Debian, chroot)
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

mkdir -p "$DIR/logs"

echo "========================================================"
echo "  🚀 تشغيل FinBERTx في الخلفية (بدون systemd)"
echo "========================================================"

# 1. تفعيل بيئة بايثون الافتراضية
if [ -f "$DIR/venv/bin/activate" ]; then
    source "$DIR/venv/bin/activate"
elif [ -f "/opt/finbert-bot/venv/bin/activate" ]; then
    source "/opt/finbert-bot/venv/bin/activate"
else
    echo "[*] إنشاء بيئة العمل وتثبيت المتطلبات..."
    python3 -m venv "$DIR/venv"
    source "$DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt
fi

# 2. إيقاف أي عمليات سابقة إن وجدت
if [ -f "$DIR/bot.pid" ]; then
    OLD_PID=$(cat "$DIR/bot.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "[*] إيقاف النسخة السابقة (PID: $OLD_PID)..."
        kill -9 $OLD_PID 2>/dev/null || true
    fi
    rm -f "$DIR/bot.pid"
fi

# 3. تشغيل خادم الواجهة الرسومية في الخلفية
if command -v npm &> /dev/null; then
    echo "[1/3] تشغيل خادم الواجهة الرسومية على المنفذ 3000..."
    nohup npm run dev > "$DIR/logs/web.log" 2>&1 &
    echo $! > "$DIR/web.pid"
fi

# 4. تشغيل مولد الرابط العام التلقائي (Cloudflare Tunnel)
if command -v cloudflared &> /dev/null; then
    echo "[2/3] توليد رابط عام فوري للواجهة..."
    nohup cloudflared tunnel --url http://127.0.0.1:3000 --logfile "$DIR/logs/cloudflared.log" > /dev/null 2>&1 &
    echo $! > "$DIR/tunnel.pid"
    sleep 3
    PUB_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]*\.trycloudflare\.com' "$DIR/logs/cloudflared.log" | head -n 1 || true)
    if [ ! -z "$PUB_URL" ]; then
        echo ""
        echo "========================================================"
        echo "  🌐 رابط واجهة التحكم العام الخاص بسيرفرك:"
        echo "     $PUB_URL"
        echo "========================================================"
        echo ""
    fi
fi

# 5. تشغيل بوت التداول الذاتي والتراكمي في الخلفية
echo "[3/3] تشغيل بوت التداول الذاتي في الخلفية..."
nohup python3 -u "$DIR/bot.py" > "$DIR/logs/bot.log" 2>&1 &
BOT_PID=$!
echo $BOT_PID > "$DIR/bot.pid"

echo "========================================================"
echo "  ✅ يعمل البوت والواجهة الآن في الخلفية 24/7 بنجاح!"
echo "  • معرّف العملية (Bot PID): $BOT_PID"
echo "  • لعرض السجلات الحية مباشرة: ./status_background.sh"
echo "  • لإيقاف البوت في أي وقت:     ./stop_background.sh"
echo "========================================================"
