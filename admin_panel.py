import PySimpleGUI as sg
import json
import os
from key_manager import KeyManager

# --- MAYBACH ADMIN TEMA AYARLARI ---
sg.theme('DarkGray15')
GOLD_TEXT = '#D4AF37'
BG_COLOR = '#121212'
INPUT_BG = '#1E1E1E'
sg.set_options(font=('Helvetica', 10), background_color=BG_COLOR)

class AdminPanel:
    def __init__(self):
        self.key_manager = KeyManager()

    def run(self):
        """Ana pencereyi başlatır"""
        self.main_menu()

    def main_menu(self):
        layout = [
            [sg.Text('MAYBACH', font=('Helvetica', 26, 'bold'), text_color=GOLD_TEXT, justification='center', expand_x=True)],
            [sg.Text('ADMIN CONTROL PANEL', font=('Helvetica', 10), text_color='#666666', justification='center', expand_x=True)],
            [sg.HSeparator(color='#333333', pad=(0, 15))],
            
            [sg.Button('ANAHTAR VERİTABANI & YÖNETİM', size=(35, 2), button_color=('#000000', GOLD_TEXT), font=('Helvetica', 11, 'bold'))],
            [sg.Button('SİSTEM LOGLARINI İNCELE', size=(35, 1), button_color=('#FFFFFF', '#2C2C2C'))],
            
            [sg.Text('', pad=(0, 10))],
            [sg.HSeparator(color='#333333', pad=(0, 15))],
            [sg.Button('GÜVENLİ ÇIKIŞ', size=(35, 1), button_color=('#FFFFFF', '#333333'))],
        ]
        
        window = sg.Window('Maybach Admin Control', layout, size=(400, 380), element_justification='center', finalize=True)
        
        while True:
            event, values = window.read()
            if event in (sg.WINDOW_CLOSED, 'GÜVENLİ ÇIKIŞ'):
                window.close()
                break
            
            if event == 'ANAHTAR VERİTABANI & YÖNETİM':
                window.hide()
                self.view_all_keys()
                window.un_hide()
            
            if event == 'SİSTEM LOGLARINI İNCELE':
                self.view_logs()

    def view_all_keys(self):
        """Lisansları listeler, ekler ve yönetir (Hepsi Tek Ekranda)"""
        while True:
            keys_data = self.key_manager.get_all_keys()
            table_data = []
            for key, info in keys_data.items():
                table_data.append([
                    key,
                    info.get('mac_address', 'Bağlı Değil'),
                    '✅ Aktif' if info.get('active') else '❌ Pasif',
                    info.get('created', 'N/A'),
                    info.get('last_login', 'Hiç yok')
                ])
            
            layout = [
                [sg.Text('ANAHTAR YÖNETİM MERKEZİ', font=('Helvetica', 14, 'bold'), text_color=GOLD_TEXT)],
                
                # --- YENİ KEY EKLEME BÖLÜMÜ (Tablonun Üstünde) ---
                [sg.Frame(' Hızlı Anahtar Ekle ', [
                    [sg.Input(key='-NEW-KEY-', size=(25, 1), background_color=INPUT_BG, text_color='#FFFFFF'),
                     sg.Button('ANAHTARI EKLE', button_color=('#000000', GOLD_TEXT), font=('Helvetica', 9, 'bold'))]
                ], title_color=GOLD_TEXT, pad=(0, 15))],
                
                # --- TABLO ---
                [sg.Table(values=table_data, 
                          headings=['Anahtar', 'MAC Adresi', 'Durum', 'Oluşturulma', 'Son Giriş'],
                          auto_size_columns=True, 
                          display_row_numbers=False, 
                          key='-TABLE-',
                          enable_events=True,
                          background_color=INPUT_BG,
                          header_background_color=GOLD_TEXT,
                          header_text_color='#000000',
                          alternating_row_color='#252525',
                          num_rows=10)],
                
                # --- AKSİYON BUTONLARI ---
                [
                    sg.Button('DURUM DEĞİŞTİR', size=(15, 1), button_color=('#FFFFFF', '#2C2C2C')),
                    sg.Button('ANAHTARI SİL', size=(15, 1), button_color=('#FFFFFF', '#B22222')),
                    sg.Button('MAC SIFIRLA', size=(15, 1), button_color=('#FFFFFF', '#444444'))
                ],
                [sg.Button('ANA MENÜYE DÖN', pad=(0, 15), size=(20, 1), button_color=('#000000', GOLD_TEXT))]
            ]
            
            win = sg.Window('Maybach Veritabanı Yönetimi', layout, element_justification='center', finalize=True)
            
            refresh_needed = False
            while True:
                event, values = win.read()
                
                if event in (sg.WINDOW_CLOSED, 'ANA MENÜYE DÖN'):
                    win.close()
                    return

                # --- YENİ KEY EKLEME İŞLEMİ ---
                if event == 'ANAHTARI EKLE':
                    new_key = values['-NEW-KEY-'].strip()
                    if new_key:
                        res, msg = self.key_manager.add_key(new_key)
                        sg.popup(msg, background_color=BG_COLOR, text_color=GOLD_TEXT)
                        refresh_needed = True; break
                    else:
                        sg.popup_error("Lütfen bir anahtar değeri girin!", background_color=BG_COLOR)

                # --- TABLO İŞLEMLERİ ---
                selected_rows = values['-TABLE-']
                if event in ('DURUM DEĞİŞTİR', 'ANAHTARI SİL', 'MAC SIFIRLA'):
                    if not selected_rows:
                        sg.popup_error("Hata: Önce tablodan bir anahtar seçmelisin!", background_color=BG_COLOR)
                        continue
                    
                    key_value = table_data[selected_rows[0]][0]
                    
                    if event == 'DURUM DEĞİŞTİR':
                        self.key_manager.toggle_key(key_value)
                        refresh_needed = True; break
                        
                    if event == 'ANAHTARI SİL':
                        if sg.popup_yes_no(f"{key_value} silinecek. Emin misin?", background_color=BG_COLOR) == 'Yes':
                            self.key_manager.remove_key(key_value)
                            refresh_needed = True; break

                    if event == 'MAC SIFIRLA':
                        self.key_manager.reset_mac(key_value)
                        sg.popup(f"{key_value} MAC adresi temizlendi.", background_color=BG_COLOR)
                        refresh_needed = True; break
            
            win.close()
            if not refresh_needed: break

    def view_logs(self):
        """Log dosyasını güvenli okur"""
        try:
            if not os.path.exists('bot.log'):
                sg.popup("Henüz log dosyası oluşturulmamış.", background_color=BG_COLOR)
                return

            with open('bot.log', 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.readlines()
                last_logs = "".join(logs[-50:])
            
            sg.popup_scrolled(last_logs, title="Sistem Logları", 
                              background_color=BG_COLOR, text_color='#00FF00', 
                              font=('Consolas', 10), size=(80, 20))
        except Exception as e:
            sg.popup(f"Log okunurken hata: {e}", background_color=BG_COLOR)