import os
import sys
import time
import threading
import subprocess
import requests

# ─── SÜRÜM BİLGİSİ ───────────────────────────────────────────────────────────
# Her yeni build'de bu numarayı artır (örn: "1.0.1", "1.0.2" ...)
# GitHub Release tag'i aynı numara olmalı (örn: v1.0.1)
CURRENT_VERSION = "1.0.0"

# ─── GITHUB AYARLARI ─────────────────────────────────────────────────────────
GITHUB_REPO    = "sametyesr7/maybachbot"
API_URL        = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
HEADERS        = {"Accept": "application/vnd.github+json", "User-Agent": "MaybachBot-Updater"}


def _version_tuple(v: str):
    """'v1.2.3' veya '1.2.3' → (1, 2, 3)"""
    return tuple(int(x) for x in v.lstrip("v").split("."))


def _current_exe() -> str | None:
    """Çalışan .exe yolunu döndürür; sadece PyInstaller ile derlenmiş çalışmada geçerli."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return None


def check_and_update(log_callback=None):
    """
    GitHub'daki son release tag'ini mevcut sürümle karşılaştırır.
    Daha yeniyse:
      1. .exe asset'ini indirir
      2. Küçük bir .bat yazar (kendini değiştirip yeniden başlatır)
      3. Bat'ı çalıştırıp mevcut süreci kapatır
    Herhangi bir hata olursa sessizce atlar — botu engellemez.
    """
    def _log(msg):
        if log_callback:
            log_callback(msg)

    try:
        resp = requests.get(API_URL, timeout=8, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        latest_tag = data.get("tag_name", "").strip()
        if not latest_tag:
            return

        if _version_tuple(latest_tag) <= _version_tuple(CURRENT_VERSION):
            return  # Zaten güncel

        _log(f"🔄 Yeni güncelleme mevcut: {latest_tag} — indiriliyor...")

        # .exe asset'ini bul
        assets = data.get("assets", [])
        exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)
        if not exe_asset:
            return

        current_exe = _current_exe()
        if not current_exe:
            return  # Script modunda çalışıyor, güncelleme atlandı

        download_url = exe_asset["browser_download_url"]
        tmp_exe      = current_exe + ".new"

        # Dosyayı indir
        with requests.get(download_url, stream=True, timeout=120, headers=HEADERS) as r:
            r.raise_for_status()
            with open(tmp_exe, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)

        _log("✅ Güncelleme indirildi, uygulama yeniden başlatılıyor...")
        time.sleep(1)

        # Bat: eski exe'yi yeni ile değiştir ve yeniden başlat
        bat_path = current_exe + "_update.bat"
        bat = (
            "@echo off\r\n"
            "timeout /t 3 /nobreak >nul\r\n"
            f'move /y "{tmp_exe}" "{current_exe}"\r\n'
            f'start "" "{current_exe}"\r\n'
            f'del "%~f0"\r\n'
        )
        with open(bat_path, "w") as f:
            f.write(bat)

        subprocess.Popen(
            bat_path,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        sys.exit(0)

    except Exception:
        pass  # Güncelleme başarısız → normal devam


def check_and_update_async(log_callback=None):
    """Güncelleme kontrolünü arka plan thread'inde çalıştırır — botu bloklamaz."""
    t = threading.Thread(
        target=check_and_update,
        args=(log_callback,),
        daemon=True,
    )
    t.start()
