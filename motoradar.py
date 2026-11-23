import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

TOKEN = os.environ.get("BOT_TOKEN", "")
KANAL = "@motoradarfirsat"
HAFIZA_DOSYASI = "fiyat_hafizasi.json"

KELIMELER = [
    "motul 7100 indirim",
    "motul 5100 fiyat",
    "castrol power1 indirim",
    "motosiklet kask indirim",
    "motosiklet interkom fiyat",
    "zincir temizleme spreyi fiyat"
]

def gonder(mesaj):
    url = "https://api." + f"telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": KANAL,
        "text": mesaj,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=data)
    urllib.request.urlopen(req, timeout=10)

def main():
    if os.path.exists(HAFIZA_DOSYASI):
        with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
            hafiza = set(json.load(f))
    else:
        hafiza = set()

    gonderilen = 0

    for kelime in KELIMELER:
        q = urllib.parse.quote(kelime)
        rss_url = f"https://google.com{q}&hl=tr&gl=TR&ceid=TR:tr"
        try:
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
            xml_veri = urllib.request.urlopen(req, timeout=10).read()
            root = ET.fromstring(xml_veri)
            
            for item in root.findall(".//item")[:2]:
                baslik = item.find("title").text
                link = item.find("link").text
                if link not in hafiza:
                    hafiza.add(link)
                    mesaj = (
                        f"🏍️ <b>MOTO FIRSAT & KAMPANYA RADARI</b>\n\n"
                        f"📦 <b>{baslik}</b>\n"
                        f"🏷️ Etiket: #{kelime.split()[0].upper()}\n\n"
                        f"👉 <a href='{link}'>Kampanyayı ve Fiyatları Gör</a>"
                    )
                    gonder(mesaj)
                    gonderilen += 1
        except Exception as e:
            print(f"Hata ({kelime}): {e}")

    if gonderilen == 0:
        gonder("✅ <b>MotoRadar Bağlantısı Başarılı!</b>\nTarama tamamlandı, yeni kampanyalar takip ediliyor.")

    with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(list(hafiza), f, ensure_ascii=False)

if __name__ == "__main__":
    main()
