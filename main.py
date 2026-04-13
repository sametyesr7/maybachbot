import PySimpleGUI as sg
import json
import os
import threading
import time
from security import verify_admin_key, verify_user_key, get_device_id
from bot_engine import BotEngine
from updater import check_and_update_async

sg.theme('DarkGray15')
GOLD_TEXT = '#D4AF37'
BG_COLOR = '#121212'
INPUT_BG = '#1E1E1E'

class MainApp:
    def __init__(self):
        self.bot_engine = None
        self.bot_thread = None

    def login_window(self):
        layout = [
            [sg.VPush()],
            [sg.Text('Premium kaliteyi ve önceliği tercih edenlerin adresi', font=('Helvetica', 8, 'italic'), text_color=GOLD_TEXT)],
            [sg.Text('MAYBACH LOGIN', font=('Helvetica', 20, 'bold'), text_color=GOLD_TEXT)],
            [sg.Text('Giriş Anahtarı:', font=('Helvetica', 10))],
            [sg.InputText(password_char='*', size=(30, 1), key='-KEY-', background_color=INPUT_BG)],
            [sg.Button('GİRİŞ YAP', button_color=('#000000', GOLD_TEXT), size=(15,1)), 
             sg.Button('ÇIKIŞ', button_color=(GOLD_TEXT, '#1A1A1A'), size=(10,1))],
            [sg.Text('', key='-MSG-', text_color='red')],
            [sg.VPush()]
        ]
        window = sg.Window('MAYBACH LOGIN', layout, size=(350, 450), element_justification='center', finalize=True)
        
        while True:
            event, values = window.read()
            if event in (sg.WINDOW_CLOSED, 'ÇIKIŞ'):
                window.close(); return None
            
            if event == 'GİRİŞ YAP':
                key = values['-KEY-']
                # ADMIN KONTROLÜ
                if verify_admin_key(key):
                    window.close()
                    return 'admin'
                
                # USER KONTROLÜ
                success, msg = verify_user_key(key)
                if success:
                    window.close()
                    return 'user'
                else:
                    window['-MSG-'].update(f"❌ {msg}")

    def bot_window(self):
        config = self.load_config()
        layout = [
            [sg.Text(' MAYBACH CONTROL PANEL', font=('Helvetica', 15, 'bold'), text_color=GOLD_TEXT)],
            [sg.Text('Hedef URL:'), sg.InputText(config.get('url',''), size=(45,1), key='-URL-')],
            [sg.Frame('Tutar ve Hız', [
                [sg.Text('Min:'), sg.InputText(config.get('min_amount','1000'), size=(8,1), key='-MIN-'),
                 sg.Text('Max:'), sg.InputText(config.get('max_amount','30000'), size=(8,1), key='-MAX-')],
                [sg.Text('Refresh (ms):'), sg.InputText(config.get('refresh_ms','250'), size=(8,1), key='-REFRESH-'),
                 sg.Text('Seçici:'), sg.InputText(config.get('button_selector','.btn-success'), size=(12,1), key='-BUTTON-')]
            ])],
            [sg.Checkbox('İşlem Sonrası Devam Et', default=config.get('continuous_mode', False), key='-CONTINUOUS-')],
            [sg.Button('BAŞLAT', button_color=('white', 'green'), size=(12,1)),
             sg.Button('DURDUR', button_color=('white', 'red'), size=(12,1)),
             sg.Button('KAYDET', size=(10,1))],
            [sg.Multiline(size=(60, 10), key='-LOG-', disabled=True, autoscroll=True, background_color='black', text_color='lime')],
            [sg.Button('ÇIKIŞ', button_color=(GOLD_TEXT, '#1A1A1A'), size=(10,1))]
        ]
        window = sg.Window('MAYBACH BOT v3.0', layout, finalize=True)
        
        while True:
            event, values = window.read(timeout=100)
            if event in (sg.WINDOW_CLOSED, 'ÇIKIŞ'):
                if self.bot_engine: self.bot_engine.quit_all()
                window.close(); break
            
            if event == 'BAŞLAT':
                if self.bot_engine is None:
                    self.bot_engine = BotEngine(values['-URL-'], int(values['-MIN-']), int(values['-MAX-']), 
                                               values['-BUTTON-'], int(values['-REFRESH-']), values['-CONTINUOUS-'],
                                               lambda m: window.write_event_value('-LOG-MSG-', m))
                else:
                    self.bot_engine.url = values['-URL-']
                    self.bot_engine.min_amount = int(values['-MIN-'])
                    self.bot_engine.max_amount = int(values['-MAX-'])
                    self.bot_engine.refresh_ms = int(values['-REFRESH-'])
                    self.bot_engine.button_selector = values['-BUTTON-']
                    self.bot_engine.continuous_mode = values['-CONTINUOUS-']
                
                if not self.bot_engine.is_running:
                    # Eski thread tamamen bitmeden yeni thread açma
                    if self.bot_thread and self.bot_thread.is_alive():
                        self.bot_thread.join(timeout=2)
                    self.bot_thread = threading.Thread(target=self.bot_engine.start, daemon=True)
                    self.bot_thread.start()
            
            if event == '-LOG-MSG-':
                self.log_to_window(window, values['-LOG-MSG-'])

            if event == 'DURDUR':
                if self.bot_engine: self.bot_engine.stop(); self.log_to_window(window, "⏹️ Pusu durduruldu.")
            
            if event == 'KAYDET':
                self.save_config(values)
                self.log_to_window(window, "✅ Ayarlar kaydedildi.")

    def log_to_window(self, window, message):
        window['-LOG-'].update(window['-LOG-'].get() + f"[{time.strftime('%H:%M:%S')}] {message}\n")

    def load_config(self):
        try:
            with open('config.json', 'r') as f: return json.load(f)
        except: return {}

    def save_config(self, v):
        try:
            cfg = {'url':v['-URL-'], 'min_amount':v['-MIN-'], 'max_amount':v['-MAX-'], 'refresh_ms':v['-REFRESH-'], 'button_selector':v['-BUTTON-'], 'continuous_mode':v['-CONTINUOUS-']}
            with open('config.json', 'w') as f: json.dump(cfg, f, indent=4)
        except: pass

    def run(self):
        # Güncelleme kontrolü — arka planda, login ekranını bloklamaz
        check_and_update_async()
        mode = self.login_window()
        if mode == 'admin':
            try:
                # DİKKAT: admin_panel.py dosyanın isminden ve içindeki AdminPanel sınıfından emin ol
                from admin_panel import AdminPanel
                admin = AdminPanel()
                admin.run()
            except Exception as e:
                sg.popup_error(f"Admin Paneli Hatası: {e}\nDosyanın varlığını kontrol et!")
        elif mode == 'user':
            self.bot_window()

if __name__ == '__main__':
    MainApp().run()