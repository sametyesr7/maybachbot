import hashlib
import base64
import uuid
import requests
from datetime import datetime

# --- ADMIN KEY AYARI ---
# "montanasawo" anahtarının SHA256 Hash hali
ADMIN_KEY_HASH = base64.b64encode(
    hashlib.sha256(b"montanasawo").digest()
).decode()

def get_mac_address():
    """Bilgisayarın MAC adresini çeker (Cihaz Kilidi için)"""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2)).upper()

def get_device_id():
    """MainApp'in beklediği fonksiyon ismi"""
    return get_mac_address()

def verify_admin_key(input_key):
    """Giren anahtar admin anahtarı mı kontrol eder"""
    hashed_input = base64.b64encode(
        hashlib.sha256(input_key.encode()).digest()
    ).decode()
    return hashed_input == ADMIN_KEY_HASH

def verify_user_key(key):
    """Key'i Firebase üzerinden kontrol eder ve MAC adresine kitler"""
    # SENİN VERİTABANI URL'N
    db_url = "https://maybach-bot-default-rtdb.europe-west1.firebasedatabase.app/keys"
    
    # Önce Admin mi diye bak (Admin ise veritabanına sormadan geç)
    if verify_admin_key(key):
        return True, "admin" # Admin olduğunu belirtmek için özel dönüş

    try:
        # Firebase'den anahtar bilgilerini çek
        response = requests.get(f"{db_url}/{key}.json", timeout=5)
        key_info = response.json()
        
        if not key_info:
            return False, "Geçersiz Anahtar!"
        
        if not key_info.get('active', False):
            return False, "Anahtar Deaktif!"
        
        current_mac = get_mac_address()
        stored_mac = key_info.get('mac_address')
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Senaryo: Key ilk kez kullanılıyor (BEKLIYOR durumunda)
        if stored_mac == "BEKLIYOR" or stored_mac == "":
            requests.patch(f"{db_url}/{key}.json", json={"mac_address": current_mac, "last_login": now})
            return True, "Cihaz Kaydedildi ve Giriş Yapıldı!"
            
        # 2. Senaryo: Key zaten bir cihaza kayıtlı
        if stored_mac == current_mac:
            requests.patch(f"{db_url}/{key}.json", json={"last_login": now})
            return True, "Giriş Başarılı"
        else:
            return False, "Bu anahtar başka bir bilgisayara kayıtlı!"
            
    except Exception as e:
        return False, f"Bağlantı Hatası: {str(e)}"