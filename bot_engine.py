import os
import re
import json
import time
import requests
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class BotEngine:
    def __init__(self, url, min_amount, max_amount, button_selector, refresh_ms, continuous_mode, log_callback=None):
        self.url = url
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.button_selector = button_selector
        self.refresh_ms = refresh_ms
        self.continuous_mode = continuous_mode
        self.log_callback = log_callback
        self.is_running = False
        self.driver = None
        self.user_data_path = os.path.join(os.getcwd(), "Maybach_Hafiza")
        self.session_file = os.path.join(os.getcwd(), "chrome_session.json")
        self.debug_port = 9222
        
        # --- 2CAPTCHA API AYARI ---
        self.api_key = "af0151e64bcc5b9c954d7314e2c4e13f" 

    def log(self, message):
        if self.log_callback: self.log_callback(message)

    def _save_session(self):
        """Aktif Chrome debug adresini dosyaya kaydet."""
        try:
            data = {"debugger_address": f"127.0.0.1:{self.debug_port}"}
            with open(self.session_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def _try_reconnect(self):
        """Kaydedilmiş Chrome oturumuna bağlanmayı dene. Başarılıysa True döner."""
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            debug_addr = data.get('debugger_address')
            if not debug_addr:
                return False
            options = Options()
            options.debugger_address = debug_addr
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            # Hedef URL sekmesini ara
            found_handle = None
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                try:
                    if self.url and self.url.split('/')[2] in driver.current_url:
                        found_handle = handle
                        break
                except:
                    pass
            if found_handle is None:
                # Sekme bulunamadı, mevcut sekmeye URL'yi yükle
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(self.url)
                self.log("🌐 Hedef sayfa yeni sekmede açıldı.")
            else:
                self.log("🔗 Mevcut tarayıcı oturumuna bağlanıldı, aynı sekme üzerinden devam ediliyor...")
            self.driver = driver
            return True
        except:
            return False

    def start(self):
        self.is_running = True
        if self.driver is None:
            # Önce kaydedilmiş oturuma bağlanmayı dene
            if self._try_reconnect():
                self.monitor_loop()
                return
            # Bağlantı kurulamadı — yeni Chrome başlat
            try:
                self.log(" Maybach Bot Başlatılıyor...")
                options = Options()
                options.add_argument(f"--user-data-dir={self.user_data_path}")
                options.add_argument("--profile-directory=Default")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument(f"--remote-debugging-port={self.debug_port}")
                
                # --- ARKA PLAN ÇALIŞMA AYARLARI ---
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-backgrounding-occluded-windows")
                options.add_argument("--disable-renderer-backgrounding")
                
                options.page_load_strategy = 'eager'
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
                # Bot algılamayı minimize et
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.maximize_window()
                self.driver.get(self.url)
                self._save_session()
            except Exception as e:
                self.log(f"❌ Başlatma Hatası: {str(e)}")
                self.is_running = False
                return
        else:
            # Driver zaten açık — sekmeyi kapat/yeniden yükleme, kaldığı yerden devam et
            try:
                _ = self.driver.window_handles
            except Exception:
                self.log("❌ Tarayıcı bağlantısı kopmuş, yeniden bağlanılıyor...")
                self.driver = None
                self.is_running = False
                self.start()
                return
            self.log("▶️ Ayarlar güncellendi, aynı sekme üzerinden devam ediliyor...")
        self.monitor_loop()

    def _poll_2captcha(self, request_id, max_wait=30):
        """2Captcha sonucunu 1s aralıkla max_wait saniye bekler. Token/koordinat döndürür."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            time.sleep(1)
            try:
                poll = requests.get(
                    f"https://2captcha.com/res.php?key={self.api_key}&action=get&id={request_id}&json=1",
                    timeout=5
                ).json()
                if poll.get("status") == 1:
                    return poll.get("request")
                if poll.get("request") == "ERROR_ZERO_BALANCE":
                    self.log("🛑 2Captcha bakiyesi bitti!")
                    return None
            except:
                pass
        return None

    def handle_security_check(self):
        """AŞAMA 1: Cloudflare Turnstile — 2Captcha Token Yöntemi (hızlı)"""
        try:
            sitekey = None

            widgets = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")
            if widgets:
                sitekey = widgets[0].get_attribute("data-sitekey")

            if not sitekey:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for frame in iframes:
                    src = frame.get_attribute("src") or ""
                    if "cloudflare" in src or "turnstile" in src:
                        match = re.search(r'sitekey=([^&]+)', src)
                        if match:
                            sitekey = match.group(1)
                            break

            if not sitekey:
                return

            self.log("🛡️ Turnstile saptandı, çözülüyor...")
            page_url = self.driver.current_url

            res = requests.post("https://2captcha.com/in.php", data={
                "key": self.api_key,
                "method": "turnstile",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1
            }, timeout=10).json()

            if res.get("status") != 1:
                self.log(f"❌ Turnstile API Reddi: {res.get('request')}")
                return

            token = self._poll_2captcha(res["request"], max_wait=30)
            if not token:
                self.log("⚠️ Turnstile token alınamadı.")
                return

            self.driver.execute_script("""
                document.querySelectorAll(
                    'input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"]'
                ).forEach(function(el){ el.value = arguments[0]; });
                try {
                    document.querySelectorAll('[data-sitekey]').forEach(function(w) {
                        var cb = w.getAttribute('data-callback');
                        if (cb && typeof window[cb] === 'function') window[cb](arguments[0]);
                    });
                } catch(e) {}
            """, token)

            self.log("✅ Turnstile token enjekte edildi.")
            time.sleep(1)

        except Exception as e:
            self.log(f"⚠️ Turnstile Hatası: {str(e)}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass

    def solve_puzzle_v2(self):
        """AŞAMA 2: Slider Captcha — Arka Plan + Parça ile Çöz"""
        try:
            # Yaygın slider container selector'ları — siteye göre ilkini dene
            CONTAINER_SELECTORS = [
                "#captcha-container", ".captcha-container",
                "[class*='captcha']", "[id*='captcha']",
                "[class*='slider']", "[id*='slider']",
                ".geetest_holder", "#gc-root"
            ]
            SLIDER_SELECTORS = [
                "#captcha-slider-handle", ".slider-btn", ".captcha-slider",
                "[class*='slider-handle']", "[class*='drag-btn']",
                ".geetest_slider_button", "span[role='slider']"
            ]

            captcha_box = None
            for sel in CONTAINER_SELECTORS:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    captcha_box = els[0]
                    break

            if not captcha_box:
                return  # Slider captcha yok

            self.log("🧩 Slider captcha saptandı, 2Captcha'ya yükleniyor...")

            # Arka plan + parça görselini ayrı ayrı almayı dene; yoksa tüm box'ı gönder
            bg_base64 = None
            piece_base64 = None
            try:
                bg_el = captcha_box.find_element(By.CSS_SELECTOR,
                    "[class*='bg'], [class*='background'], canvas:first-of-type, img:first-of-type")
                piece_el = captcha_box.find_element(By.CSS_SELECTOR,
                    "[class*='piece'], [class*='puzzle'], canvas:last-of-type, img:last-of-type")
                if bg_el != piece_el:
                    bg_base64 = bg_el.screenshot_as_base64
                    piece_base64 = piece_el.screenshot_as_base64
            except:
                pass

            # Tek görsel moduna düş
            if not bg_base64:
                bg_base64 = captcha_box.screenshot_as_base64

            # 2Captcha'ya gönder
            post_data = {
                "key": self.api_key,
                "method": "base64",
                "body": bg_base64,
                "json": 1,
                "imginstructions": (
                    ("data:image/png;base64," + piece_base64)
                    if piece_base64 else None
                ),
                "textinstructions": "Drag the slider to fit the puzzle piece into the gap. Reply with x=<pixels>."
            }
            # None değerleri temizle
            post_data = {k: v for k, v in post_data.items() if v is not None}

            res = requests.post("https://2captcha.com/in.php", data=post_data).json()
            if res.get("status") != 1:
                self.log(f"❌ Slider API Reddi: {res.get('request')}")
                return

            request_id = res.get("request")
            self.log("⏳ Slider çözümü bekleniyor...")

            solution = self._poll_2captcha(request_id, max_wait=30)
            if not solution:
                self.log("⚠️ Slider koordinatı alınamadı.")
                return
            match = re.search(r'x=(\d+)', str(solution))
            x_offset = int(match.group(1)) if match else None
            if not x_offset:
                self.log("⚠️ Slider koordinatı alınamadı.")
                return

            # Slider handle'ı bul
            slider_handle = None
            for sel in SLIDER_SELECTORS:
                els = captcha_box.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    slider_handle = els[0]
                    break
            if not slider_handle:
                # Son çare: captcha_box içindeki ilk div/span
                slider_handle = captcha_box.find_element(By.CSS_SELECTOR, "div, span")

            self.log(f"🎯 Hedef: {x_offset}px — Hayalet kaydırma başlıyor...")

            # PointerEvent + MouseEvent çift ateş (uyumluluk için)
            self.driver.execute_script("""
                var el = arguments[0]; var offset = arguments[1];
                function fire(type, x, y) {
                    ['PointerEvent', 'MouseEvent'].forEach(function(evType) {
                        try {
                            el.dispatchEvent(new window[evType](type, {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y, isPrimary: true
                            }));
                        } catch(e) {}
                    });
                }
                var r = el.getBoundingClientRect();
                var sx = r.left + r.width / 2;
                var sy = r.top + r.height / 2;
                fire('mousedown', sx, sy);
                fire('pointerdown', sx, sy);
                var steps = 30;
                for (var i = 1; i <= steps; i++) {
                    var progress = i / steps;
                    // ease-in-out eğrisi — daha doğal hareket
                    var eased = progress < 0.5
                        ? 2 * progress * progress
                        : -1 + (4 - 2 * progress) * progress;
                    var jitter = (Math.random() * 2) - 1;
                    fire('mousemove', sx + eased * offset, sy + jitter);
                    fire('pointermove', sx + eased * offset, sy + jitter);
                }
                fire('mouseup', sx + offset, sy);
                fire('pointerup', sx + offset, sy);
            """, slider_handle, x_offset)

            self.log("🚀 Slider engeli temizlendi.")
            time.sleep(2)

        except Exception as e:
            self.log(f"⚠️ Slider Hatası: {str(e)}")

    def _has_captcha(self):
        """Sayfada aktif captcha var mı hızlıca kontrol et."""
        try:
            # Turnstile
            if self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]"):
                return True
            for frame in self.driver.find_elements(By.TAG_NAME, "iframe"):
                src = frame.get_attribute("src") or ""
                if "cloudflare" in src or "turnstile" in src:
                    return True
            # Slider
            for sel in ["[class*='captcha']", "[id*='captcha']", "[class*='slider']"]:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    return True
        except:
            pass
        return False

    def _solve_captcha_background(self):
        """Captcha'yı arka plan thread'inde çöz — botu bloklamaz."""
        self.handle_security_check()
        self.solve_puzzle_v2()

    def monitor_loop(self):
        self.log("🔫 Pusu aktif, fırsatlar bekleniyor...")
        captcha_thread = None
        while self.is_running:
            try:
                if not self.is_running: break

                # Yalnızca captcha varsa ve thread çalışmıyorsa yeni thread başlat
                thread_idle = captcha_thread is None or not captcha_thread.is_alive()
                if thread_idle and self._has_captcha():
                    captcha_thread = threading.Thread(
                        target=self._solve_captcha_background, daemon=True)
                    captcha_thread.start()

                # Tablo tazeleme (JS Tetikleme)
                try: self.driver.execute_script("try{tablo();}catch(e){}")
                except: pass

                rows = self.driver.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    if not self.is_running: break
                    amounts = self.extract_amounts(row.text)
                    if amounts and self.min_amount <= max(amounts) <= self.max_amount:
                        btn = row.find_element(By.CSS_SELECTOR, self.button_selector)
                        if btn.is_enabled():
                            self.driver.execute_script("arguments[0].click();", btn)
                            self.log(f"🔥 İşlem Alındı: {max(amounts)}")

                            # Tıklama sonrası captcha — arka plan thread'i
                            time.sleep(1)
                            captcha_thread = threading.Thread(
                                target=self._solve_captcha_background, daemon=True)
                            captcha_thread.start()

                            if not self.continuous_mode:
                                captcha_thread.join(timeout=35)
                                self.is_running = False
                                return

                time.sleep(self.refresh_ms / 1000)
            except:
                continue

    def extract_amounts(self, text):
        found = re.findall(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?', text)
        valid = []
        for m in found:
            try:
                c = m.replace('.', '').replace(',', '')
                val = int(c) / 100 if len(c) > 2 else int(c)
                if val >= 100: valid.append(val)
            except: continue
        return valid

    def stop(self): 
        self.is_running = False

    def quit_all(self):
        """Bot paneli kapanırken çağrılır — tarayıcıyı kapatmaz, sadece döngüyü durdurur.
        Sekmeyi kapatmak kullanıcının tercihine bırakılmıştır."""
        self.is_running = False
        # Tarayıcı kasıtlı olarak kapatılmıyor; kullanıcı isterse manuel kapatabilir.