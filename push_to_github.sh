#!/bin/bash
# ==============================================================================
# FinBERTx - Push to GitHub Utility
# ==============================================================================

REPO_URL="https://github.com/Iahiax/FinBERTx.git"

echo "========================================================"
echo "  🚀 رفع مشروع FinBERTx إلى مستودع GitHub"
echo "  المستودع: $REPO_URL"
echo "========================================================"

if [ -z "$1" ]; then
    echo "لرفع المشروع باستخدام رمز الوصول الشخصي (GitHub Personal Access Token):"
    echo "  ./push_to_github.sh <YOUR_GITHUB_TOKEN>"
    echo ""
    echo "أو يمكنك الرفع مباشرة عبر:"
    echo "  git push origin main"
    exit 1
fi

TOKEN=$1
AUTH_REPO="https://${TOKEN}@github.com/Iahiax/FinBERTx.git"

echo "[*] جاري الرفع إلى فرع main..."
git push $AUTH_REPO main

echo "✅ تم الرفع بنجاح إلى GitHub!"
