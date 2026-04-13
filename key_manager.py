import requests
import json
from datetime import datetime

class KeyManager:
    def __init__(self):
        # Senin Firebase linkin (Sonuna .json koymuyoruz, fonksiyonlar halledecek)
        self.db_url = "https://maybach-bot-default-rtdb.europe-west1.firebasedatabase.app/keys"

    def get_all_keys(self):
        """Tüm anahtarları Firebase'den çek"""
        try:
            response = requests.get(f"{self.db_url}.json")
            if response.status_code == 200:
                data = response.json()
                return data if data else {}
            return {}
        except:
            return {}

    def add_key(self, key):
        """Yeni anahtarı Firebase'e ekle"""
        if not key: 
            return False, "Anahtar adı boş olamaz!"
        
        # Önce bu anahtar var mı kontrol et
        if self.get_key_info(key):
            return False, f"'{key}' anahtarı zaten mevcut!"

        # Yeni anahtar verileri
        data = {
            'active': True,
            'mac_address': 'BEKLIYOR',
            'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_login': None
        }
        
        try:
            response = requests.put(f"{self.db_url}/{key}.json", json=data)
            if response.status_code == 200:
                return True, f"Anahtar '{key}' başarıyla Firebase'e eklendi."
            return False, f"Hata: {response.status_code}"
        except Exception as e:
            return False, f"Bağlantı hatası: {str(e)}"

    def remove_key(self, key):
        """Anahtarı Firebase'den sil"""
        try:
            requests.delete(f"{self.db_url}/{key}.json")
            return True, f"Anahtar '{key}' silindi."
        except:
            return False, "Silme işlemi başarısız."

    def toggle_key(self, key):
        """Anahtarı aktif/pasif yap"""
        info = self.get_key_info(key)
        if not info: 
            return False, "Anahtar bulunamadı."
        
        new_status = not info.get('active', False)
        try:
            requests.patch(f"{self.db_url}/{key}.json", json={'active': new_status})
            return True, f"Durum: {'Aktif' if new_status else 'Pasif'}"
        except:
            return False, "Güncelleme hatası."

    def reset_mac(self, key):
        """Anahtarın MAC adresini sıfırla (BEKLIYOR'a döndür)"""
        try:
            requests.patch(f"{self.db_url}/{key}.json", json={'mac_address': 'BEKLIYOR'})
            return True, "MAC adresi sıfırlandı."
        except:
            return False, "MAC sıfırlama hatası."

    def get_key_info(self, key):
        """Spesifik anahtar bilgisini getir"""
        try:
            response = requests.get(f"{self.db_url}/{key}.json")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None