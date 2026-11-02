#!/bin/bash
# ==============================================================================
# FinBERTx - Linux VPS Setup Script (NO Systemd Required)
# Fully compatible with OpenVZ, LXC, Alpine, Ubuntu, Debian, chroot, and containers
# ==============================================================================

set -e

echo "========================================================"
echo "  🚀 بدء تثبيت وتهيئة FinBERTx على Linux VPS (بدون systemd)"
echo "========================================================"

# 1. تحديث الحزم وتثبيت المتطلبات الأساسية
echo "[1/5] تثبيت Python3 و Git و Cloudflared..."
if command -v apt &> /dev/null; then
    sudo apt update -y
    sudo apt install -y python3 python3-pip python3-venv git curl
elif command -v yum &> /dev/null; then
    sudo yum install -y python3 python3-pip git curl
elif command -v apk &> /dev/null; then
    apk add python3 py3-pip git curl bash
fi

# تثبيت أداة Cloudflare Tunnel لتوليد الرابط العام التلقائي
if ! command -v cloudflared &> /dev/null; then
    echo "تنزيل وتثبيت أداة توليد الرابط العام (cloudflared)..."
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared 2>/dev/null || mv /tmp/cloudflared /usr/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared 2>/dev/null || chmod +x /usr/bin/cloudflared
fi

# 2. إنشاء بيئة العمل والمجلد
INSTALL_DIR="/opt/finbert-bot"
echo "[2/5] تهيئة مسار المشروع في $INSTALL_DIR..."
sudo mkdir -p $INSTALL_DIR 2>/dev/null || mkdir -p $INSTALL_DIR
sudo chown -R $USER:$USER $INSTALL_DIR 2>/dev/null || true

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "المستودع موجود بالفعل، جاري سحب أحدث التحديثات..."
    cd $INSTALL_DIR && git pull origin main || true
else
    echo "نسخ ملفات المشروع إلى $INSTALL_DIR..."
    cp -r ./* $INSTALL_DIR/ 2>/dev/null || git clone https://github.com/Iahiax/FinBERTx.git $INSTALL_DIR
    cd $INSTALL_DIR
fi

# إعطاء صلاحيات التنفيذ لجميع السكربتات
chmod +x $INSTALL_DIR/*.sh

# 3. إنشاء البيئة الافتراضية
echo "[3/5] إنشاء بيئة Python وتثبيت PyTorch للمعالج (CPU)..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate
pip install --upgrade pip

# تثبيت PyTorch نسخة الـ CPU السريعة
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 4. التحقق من تشغيل FinBERT على الـ CPU
echo "[4/5] فحص نموذج ProsusAI/finbert على الـ CPU..."
python3 -c '
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

device = torch.device("cpu")
MODEL_NAME = "ProsusAI/finbert"
print(f"تحميل {MODEL_NAME} على الـ CPU...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.to(device)
print("يعمل النموذج الآن بكفاءة على الـ CPU!")
'

# 5. إعداد التشغيل التلقائي عند إعادة إقلاع السيرفر عبر Crontab (@reboot) بدون systemd
echo "[5/5] إعداد التشغيل التلقائي عبر Crontab (@reboot)..."
CRON_JOB="@reboot cd $INSTALL_DIR && ./start_background.sh > /dev/null 2>&1"
( crontab -l 2>/dev/null | grep -Fv "$INSTALL_DIR/start_background.sh" ; echo "$CRON_JOB" ) | crontab - || true

# 6. تشغيل البوت في الخلفية الآن فوراً
echo "[*] تشغيل FinBERTx في الخلفية..."
cd $INSTALL_DIR && ./start_background.sh

echo "========================================================"
echo "  ✅ تم تثبيت وتشغيل FinBERTx بنجاح تام في الخلفية 24/7!"
echo "  (يعمل بدون systemd ومتوافق مع جميع أنواع خوادم VPS)"
echo "========================================================"
echo "  أوامر إدارة البوت السريعة:"
echo "    • لفحص الحالة ومتابعة السجلات الحية:  ./status_background.sh"
echo "    • لإيقاف البوت في أي وقت:              ./stop_background.sh"
echo "    • لتشغيل البوت في الخلفية:             ./start_background.sh"
echo "========================================================"
