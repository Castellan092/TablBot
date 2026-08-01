import os
import json
import requests
import datetime
import schedule
import time
import threading

# --- AYARLAR ---
BOT_TOKEN = "8925220258:AAGekjgtA8V8rF931sL6vgb-chGBXAnqL4g"

USERS_FILE = "kullanicilar.json"
DATA_FILE = "haftalik_menu_temiz.txt"
ADMIN_FILE = "admin_id.json"

def admin_belirle(chat_id):
    if not os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump({"admin_id": chat_id}, f)

def admin_getir():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("admin_id")
            except:
                return None
    return None

def kullanici_ekle(chat_id, first_name):
    kullanicilar = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                kullanicilar = json.load(f)
            except:
                kullanicilar = {}
    kullanicilar[str(chat_id)] = first_name
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(kullanicilar, f, ensure_ascii=False, indent=4)

def kullanicilari_getir():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def telegram_mesaj_gonder(chat_id, metin):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": metin}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def bugunun_menusunu_bul():
    if not os.path.exists(DATA_FILE):
        return None

    gunler_tr = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı",
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }
    # Türkiye Saati (UTC+3) Hesaplama
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    tr_now = utc_now + datetime.timedelta(hours=3)
    bugun_ingilizce = tr_now.strftime("%A")
    bugun_tr = gunler_tr.get(bugun_ingilizce, "")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        tum_metin = f.read().strip()

    if not tum_metin:
        return None

    parcalar = tum_metin.split("\n\n")
    for parca in parcalar:
        if bugun_tr.lower() in parca.lower():
            return f"📅 **Gün:** {bugun_tr}\n\n{parca}"

    return None

def gunluk_bildirim_gonder():
    bugun_menu = bugunun_menusunu_bul()
    kullanicilar = kullanicilari_getir()
    
    for chat_id, isim in kullanicilar.items():
        if bugun_menu:
            mesaj = f"Merhaba {isim}! 🍽️\n\n{bugun_menu}"
        else:
            mesaj = f"Merhaba {isim}! ☀️\n\n⚠️ **Henüz bugün/bu hafta için yemek menüsü bilgisi yüklenmedi.**"
            
        telegram_mesaj_gonder(chat_id, mesaj)

# Türkiye Saati ile 09:30 (UTC 06:30) ve 17:00 (UTC 14:00)
schedule.every().day.at("06:30").do(gunluk_bildirim_gonder)
schedule.every().day.at("14:00").do(gunluk_bildirim_gonder)

def zamanlayici_calistir():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=zamanlayici_calistir, daemon=True).start()

def bot_baslat():
    last_update_id = 0
    print("Kullanıcı Dostu TabldotBot Dinlemede...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            res = requests.get(url).json()
            
            for update in res.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message")
                if not message:
                    continue
                
                chat_id = message["chat"]["id"]
                first_name = message["from"].get("first_name", "Dostum")
                
                if not admin_getir():
                    admin_belirle(chat_id)

                kullanici_ekle(chat_id, first_name)
                text = message.get("text", "").strip()
                admin_id = admin_getir()
                
                if text.lower() in ["/start", "start", "merhaba", "selam"]:
                    if chat_id == admin_id:
                        mesaj = (
                            f"Merhaba Patron {first_name}! 👋 TabldotBot Yönetici Paneline Hoş Geldin.\n\n"
                            "👑 **Yönetici Komutları:**\n"
                            "• Kayıtlı kullanıcıları görmek için: **/kullanicilar**\n"
                            "• Güncel menüyü test etmek için: **/bugun**\n"
                            "• Yeni haftalık menüyü güncellemek için doğrudan metin olarak bana gönderebilirsin."
                        )
                    else:
                        mesaj = (
                            f"Merhaba {first_name}! 👋 Ben **TabldotBot**.\n\n"
                            "Yemekhanede 'Bugün ne yemek var?' derdine son vermek için buradayım! 🍽️\n\n"
                            "🔔 **Sana Nasıl Bildirim Atacağım?**\n"
                            "• **Sabah 09:30**'da (Öğle yemeğini hatırlatmak için)\n"
                            "• **Öğleden sonra 17:00**'de (Akşam yemeğini hatırlatmak için)\n"
                            "otomatik olarak o günün menüsünü cebine mesaj olarak göndereceğim! *(Bot bildirimlerini açık tutmayı unutma)* 📲\n\n"
                            "💡 **Menüyü İstediğin An Öğrenmek İçin:**\n"
                            "Bana sadece **'bugün'** veya **'/bugun'** yazıp göndermen yeterli! Sana anında o günün öğle ve akşam yemeğini getireceğim.\n\n"
                            "Şimdiden afiyet olsun! ✨"
                        )
                    telegram_mesaj_gonder(chat_id, mesaj)
                
                elif text.lower() in ["/bugun", "bugün", "bugun", "menü", "menu"]:
                    gunun_yemekleri = bugunun_menusunu_bul()
                    if gunun_yemekleri:
                        telegram_mesaj_gonder(chat_id, f"🍽️ {first_name}, işte günün menüsü:\n\n{gunun_yemekleri}")
                    else:
                        telegram_mesaj_gonder(chat_id, f"⚠️ {first_name}, henüz güncel yemek menüsü yüklenmemiş.")
                
                elif text.lower() in ["/kullanicilar", "/kullanıcılar", "kullanıcılar"]:
                    if chat_id == admin_id:
                        kullanicilar = kullanicilari_getir()
                        toplam = len(kullanicilar)
                        
                        liste_metni = f"👥 **Aktif Kayıtlı Kullanıcı Sayısı:** {toplam}\n\n"
                        sayac = 1
                        for uid, isim in kullanicilar.items():
                            liste_metni += f"{sayac}. {isim} (ID: `{uid}`)\n"
                            sayac += 1
                        
                        telegram_mesaj_gonder(chat_id, liste_metni)
                    else:
                        telegram_mesaj_gonder(chat_id, "⛔ Bu komut gizlidir ve yalnızca bot yöneticisi tarafından kullanılabilir.")

                elif len(text) > 30 and ("öğle" in text.lower() or "çorba" in text.lower() or "pazartesi" in text.lower()):
                    if chat_id == admin_id:
                        with open(DATA_FILE, "w", encoding="utf-8") as f:
                            f.write(text)
                        telegram_mesaj_gonder(chat_id, "✅ Haftalık yemek menüsü başarıyla güncellendi!")
                    else:
                        telegram_mesaj_gonder(chat_id, "⛔ Menüyü yalnızca bot yöneticisi güncelleyebilir.")

        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    bot_baslat()
