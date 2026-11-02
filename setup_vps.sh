#!/bin/bash
# ==============================================================================
# FinBERTx - VPS Linux One-Click Setup Script (Ubuntu / Debian)
# Automated setup for FinBERT CPU Trading Bot with Capital.com & Telegram
# ==============================================================================

set -e

echo "========================================================"
echo "  🚀 بدء تثبيت وتهيئة FinBERTx على سيرفر Linux VPS"
echo "========================================================"

# 1. تحديث الحزم وتثبيت المتطلبات الأساسية
echo "[1/6] تحديث حزم النظام وتثبيت Python3 و Git و Cloudflared..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git curl

# تثبيت أداة Cloudflare Tunnel لتوليد الرابط العام التلقائي
if ! command -v cloudflared &> /dev/null; then
    echo "تنزيل وتثبيت أداة توليد الرابط العام (cloudflared)..."
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
fi

# 2. إنشاء بيئة العمل والمجلد
INSTALL_DIR="/opt/finbert-bot"
echo "[2/6] تهيئة مسار المشروع في $INSTALL_DIR..."
sudo mkdir -p $INSTALL_DIR
sudo chown -R $USER:$USER $INSTALL_DIR

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "المستودع موجود بالفعل، جاري سحب أحدث التحديثات..."
    cd $INSTALL_DIR && git pull origin main || true
else
    echo "استنساخ المستودع من GitHub..."
    git clone https://github.com/Iahiax/FinBERTx.git $INSTALL_DIR || cp -r ./* $INSTALL_DIR/
    cd $INSTALL_DIR
fi

# 3. إنشاء البيئة الافتراضية
echo "[3/6] إنشاء بيئة Python الافتراضية وتثبيت PyTorch للمعالج (CPU)..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate
pip install --upgrade pip

# تثبيت PyTorch نسخة الـ CPU خفيفة وسريعة
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 4. التحقق من تشغيل FinBERT على الـ CPU
echo "[4/6] فحص تحميل نموذج ProsusAI/finbert على الـ CPU..."
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

# 5. تثبيت خدمة Systemd لتشغيل البوت تلقائياً عند إقلاع السيرفر
echo "[5/6] تكوين خدمة Systemd (finbert-bot.service)..."
cat <<EOF | sudo tee /etc/systemd/system/finbert-bot.service
[Unit]
Description=FinBERTx Autonomous CFD Trading Bot (Capital.com & FinBERT)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable finbert-bot.service
sudo systemctl restart finbert-bot.service

echo "========================================================"
echo "  ✅ تم تثبيت FinBERTx وتشغيل الخدمة بنجاح على الـ VPS!"
echo "========================================================"
echo "  لمتابعة السجلات الحية للبوت:"
echo "    sudo journalctl -u finbert-bot.service -f"
echo ""
echo "  لإيقاف أو إعادة تشغيل البوت:"
echo "    sudo systemctl stop finbert-bot.service"
echo "    sudo systemctl restart finbert-bot.service"
echo "========================================================"
