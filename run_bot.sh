#!/bin/bash
# ==============================================================================
# FinBERTx - Direct Runner Script with Public URL Generation on Linux VPS
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. Activate or create virtual environment
if [ ! -d "venv" ]; then
    echo "[*] إنشاء البيئة الافتراضية وتثبيت المتطلبات..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 2. Check and start public tunnel if cloudflared exists
if command -v cloudflared &> /dev/null; then
    echo "[*] توليد رابط عام فوري للواجهة الرسومية عبر Cloudflare..."
    cloudflared tunnel --url http://127.0.0.1:3000 --logfile /tmp/cloudflared.log &
    sleep 3
    PUB_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]*\.trycloudflare\.com' /tmp/cloudflared.log | head -n 1 || true)
    if [ ! -z "$PUB_URL" ]; then
        echo ""
        echo "========================================================"
        echo "  🌐 رابط واجهة التحكم العام الخاص بسيرفرك:"
        echo "     $PUB_URL"
        echo "========================================================"
        echo ""
    fi
fi

echo "========================================================"
echo "  🚀 تشغيل بوت FinBERTx الذاتي والتراكمي على الـ CPU"
echo "  الرافعة: 1:100 | الفريمات: M5-D1 | تداول حقيقي مؤتمت"
echo "========================================================"

# Run the python daemon
exec python3 bot.py
