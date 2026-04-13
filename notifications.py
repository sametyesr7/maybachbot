from win10toast import ToastNotifier
import threading

class NotificationManager:
    def __init__(self):
        self.toaster = ToastNotifier()
    
    def notify(self, title, message, duration=5):
        """Windows notification gönder (arka planda)"""
        def show():
            self.toaster.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True
            )
        
        thread = threading.Thread(target=show, daemon=True)
        thread.start()
    
    def notify_detected(self, amount):
        """Tutar detecte edildi"""
        self.notify(
            "💰 Miktar Detecte Edildi",
            f"Tutar: {amount:,.0f}"
        )
    
    def notify_clicked(self, amount):
        """İşleme Al tıklandı"""
        self.notify(
            "✅ İşlem Yapıldı",
            f"{amount:,.0f} tutar işleme alındı"
        )
    
    def notify_error(self, message):
        """Hata bildirimi"""
        self.notify(
            "❌ Hata",
            message,
            duration=10
        )