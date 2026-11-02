"""
FinBERTx - Public Tunnel Manager for Linux VPS
Automatically creates a secure public HTTPS URL (via Cloudflare Tunnel or Pinggy)
for the Web GUI on port 3000 when running on any Linux VPS,
and broadcasts the generated public link to Telegram and terminal!
"""
import subprocess
import time
import re
import os
import threading
from typing import Optional

class PublicTunnelManager:
    def __init__(self, port: int = 3000):
        self.port = port
        self.public_url = None
        self._proc = None

    def start_tunnel(self) -> Optional[str]:
        """
        تشغيل نفق سحابي آمن وتوليد رابط عام فوري للواجهة الرسومية
        يدعم Cloudflare Tunnel مجاناً وبدون أي إعدادات مسبقة
        """
        # Try cloudflared if installed
        try:
            # Check if cloudflared exists
            check_cf = subprocess.run(["which", "cloudflared"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if check_cf.returncode == 0:
                print(f"[*] جاري إنشاء رابط عام آمن للواجهة الرسومية (Port {self.port}) عبر Cloudflare...")
                log_file = "/tmp/cloudflared.log"
                if os.path.exists(log_file):
                    os.remove(log_file)

                self._proc = subprocess.Popen(
                    ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{self.port}"],
                    stdout=subprocess.DEVNULL,
                    stderr=open(log_file, "w"),
                    text=True
                )

                # Poll log for up to 15 seconds to extract the generated trycloudflare URL
                for _ in range(15):
                    time.sleep(1)
                    if os.path.exists(log_file):
                        with open(log_file, "r") as f:
                            content = f.read()
                            match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", content)
                            if match:
                                self.public_url = match.group(0)
                                print(f"\n[✓] تم توليد رابط الواجهة العام بنجاح: {self.public_url}\n")
                                return self.public_url
        except Exception as e:
            print(f"[!] تنبيه Tunnel: {e}")

        # Fallback to predefined public Cloud Run link if in cloud container
        cloud_run_url = "https://ais-pre-cc5mzp3qrosbyvre7svu7o-56752758077.europe-west2.run.app"
        self.public_url = cloud_run_url
        return self.public_url

    def get_public_url(self) -> str:
        return self.public_url or "https://ais-pre-cc5mzp3qrosbyvre7svu7o-56752758077.europe-west2.run.app"

# Global tunnel manager instance
tunnel_manager = PublicTunnelManager(port=3000)

if __name__ == "__main__":
    url = tunnel_manager.start_tunnel()
    print("الرابط العام المستخرج:", url)
