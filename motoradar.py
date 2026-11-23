import os
import re
import time
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

TOKEN = os.environ.get("BOT_TOKEN", "")
KANAL = @motoradarfirsat 
AMAZON_TAG = ""  # İleride Amazon ortaklık kodun gelince buraya yazacaksın

HAFIZA_DOSYASI = "fiyat_hafizasi.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9"
}

def gonder(mesaj):
    if not TOKEN:
        return
    url = "https://api." + f"telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": KANAL,
        "text": mesaj,
        "parse_mode": "HTML"
    }).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=15)
    except Exception:
        pass

def cek(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")

def fiyat_temizle(f_str):
    # "1.450,90 TL" -> 1450.90 float değere çevirir
    s = re.sub(r'[^\d,]', '', f_str).replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0

def motomax_tara(hafiza, ilk_kurulum):
    # Motomax İndirimli Ürünler / Fırsat Vitrinini ve Kategori Sayfalarını Tarar
    sayfalar = [
        "https://www." + "motomax.com.tr/indirimli-urunler",
        "https://www." + "motomax.com.tr/motosiklet-kasklari",
        "https://www." + "motomax.com.tr/motosiklet-montlari",
        "https://www." + "motomax.com.tr/motosiklet-eldivenleri"
    ]
    for sayfa_url in sayfalar:
        try:
            html = cek(sayfa_url)
            # Ticimax altyapısı ürün kartları ve fiyatlarını ayıkla
            urunler = re.findall(r'class="productName[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?class="discountPrice[^"]*"[^>]*>.*?<span>([^<]+)</span>', html, re.S)
            for link, baslik, fiyat_str in urunler[:15]:
                tam_link = link if link.startswith("http") else ("https://www." + "motomax.com.tr" + link)
                fiyat = fiyat_temizle(fiyat_str)
                if fiyat <= 0:
                    continue
                eski_fiyat = hafiza.get(tam_link, 0)
                if eski_fiyat == 0:
                    hafiza[tam_link] = fiyat
                elif fiyat < eski_fiyat * 0.92:  # En az %8 gerçek fiyat düşüşü varsa
                    indirim = round(((eski_fiyat - fiyat) / eski_fiyat) * 100)
                    hafiza[tam_link] = fiyat
                    if not ilk_kurulum:
                        gonder(f"🔴 <b>MOTOMAX FİYAT DÜŞÜŞÜ (-%{indirim})</b>\n\n📦 <b>Ürün:</b> {baslik.strip()}\n❌ <b>Eski Fiyat:</b> {eski_fiyat:.2f} TL\n💰 <b>Yeni Fiyat:</b> {fiyat:.2f} TL\n\n👉 <a href=\"{tam_link}\">Motomax'ta İncele</a>")
                        time.sleep(3)
        except Exception:
            pass
        time.sleep(2)

def mototas_tara(hafiza, ilk_kurulum):
    # Mototaş İndirimli Ürünler ve Ana Ekipman Kategorilerini Tarar
    sayfalar = [
        "https://www." + "mototas.com.tr/indirimli-urunler",
        "https://www." + "mototas.com.tr/kasklar",
        "https://www." + "mototas.com.tr/montlar",
        "https://www." + "mototas.com.tr/eldivenler"
    ]
    for sayfa_url in sayfalar:
        try:
            html = cek(sayfa_url)
            urunler = re.findall(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>.*?class="[^"]*price[^"]*"[^>]*>([^<]+TL)<', html, re.S)
            for link, baslik, fiyat_str in urunler[:15]:
                tam_link = link if link.startswith("http") else ("https://www." + "mototas.com.tr" + link)
                fiyat = fiyat_temizle(fiyat_str)
                if fiyat <= 0:
                    continue
                eski_fiyat = hafiza.get(tam_link, 0)
                if eski_fiyat == 0:
                    hafiza[tam_link] = fiyat
                elif fiyat < eski_fiyat * 0.92:
                    indirim = round(((eski_fiyat - fiyat) / eski_fiyat) * 100)
                    hafiza[tam_link] = fiyat
                    if not ilk_kurulum:
                        gonder(f"🟡 <b>MOTOTAŞ FİYAT DÜŞÜŞÜ (-%{indirim})</b>\n\n📦 <b>Ürün:</b> {baslik.strip()}\n❌ <b>Eski Fiyat:</b> {eski_fiyat:.2f} TL\n💰 <b>Yeni Fiyat:</b> {fiyat:.2f} TL\n\n👉 <a href=\"{tam_link}\">Mototaş'ta İncele</a>")
                        time.sleep(3)
        except Exception:
            pass
        time.sleep(2)

def pazaryeri_moto_tara(hafiza, ilk_kurulum):
    # Amazon Türkiye ve Hepsiburada Motosiklet Kategorisi Fırsatlarını Tarar
    # 1. Amazon Türkiye Motosiklet Kategorisi (İndirimli / Popüler)
    try:
        amz_url = "https://www." + "amazon.com.tr/s?i=automotive&rh=n%3A13546635031&s=featured-rank"
        html = cek(amz_url)
        urunler = re.findall(r'data-asin="([A-Z0-9]{10})".*?class="a-size-base-plus a-color-base a-text-normal">([^<]+)</span>.*?class="a-price-whole">([^<]+)</span>', html, re.S)
        for asin, baslik, fiyat_str in urunler[:15]:
            tam_link = "https://www." + f"amazon.com.tr/dp/{asin}"
            fiyat = fiyat_temizle(fiyat_str + ",00")
            if fiyat <= 0:
                continue
            eski_fiyat = hafiza.get(tam_link, 0)
            if eski_fiyat == 0:
                hafiza[tam_link] = fiyat
            elif fiyat < eski_fiyat * 0.90:  # Amazon'da en az %10 düşüş
                indirim = round(((eski_fiyat - fiyat) / eski_fiyat) * 100)
                hafiza[tam_link] = fiyat
                git_link = f"{tam_link}?tag={AMAZON_TAG}" if AMAZON_TAG else tam_link
                if not ilk_kurulum:
                    gonder(f"🟠 <b>AMAZON MOTOSİKLET FIRSATI (-%{indirim})</b>\n\n📦 <b>Ürün:</b> {baslik.strip()}\n❌ <b>Eski Fiyat:</b> {eski_fiyat:.2f} TL\n💰 <b>Yeni Fiyat:</b> {fiyat:.2f} TL\n\n👉 <a href=\"{git_link}\">Amazon'da İncele</a>")
                    time.sleep(3)
    except Exception:
        pass

    # 2. Hepsiburada Motosiklet Kategorisi (İndirim Oranına Göre Sıralı)
    try:
        hb_url = "https://www." + "://hepsiburada.com"
        html = cek(hb_url)
        urunler = re.findall(r'href="([^"]+)"[^>]*title="([^"]+)".*?data-test-id="price-current-price">([^<]+)</div>', html, re.S)
        for link, baslik, fiyat_str in urunler[:15]:
            tam_link = link if link.startswith("http") else ("https://www." + "hepsiburada.com" + link)
            fiyat = fiyat_temizle(fiyat_str)
            if fiyat <= 0:
                continue
            eski_fiyat = hafiza.get(tam_link, 0)
            if eski_fiyat == 0:
                hafiza[tam_link] = fiyat
            elif fiyat < eski_fiyat * 0.90:
                indirim = round(((eski_fiyat - fiyat) / eski_fiyat) * 100)
                hafiza[tam_link] = fiyat
                if not ilk_kurulum:
                    gonder(f"🟧 <b>HEPSİBURADA MOTOSİKLET FIRSATI (-%{indirim})</b>\n\n📦 <b>Ürün:</b> {baslik.strip()}\n❌ <b>Eski Fiyat:</b> {eski_fiyat:.2f} TL\n💰 <b>Yeni Fiyat:</b> {fiyat:.2f} TL\n\n👉 <a href=\"{tam_link}\">Hepsiburada'da İncele</a>")
                    time.sleep(3)
    except Exception:
        pass

def main():
    ilk_kurulum = not os.path.exists(HAFIZA_DOSYASI)
    hafiza = {}
    if not ilk_kurulum:
        with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
            hafiza = json.load(f)

    motomax_tara(hafiza, ilk_kurulum)
    mototas_tara(hafiza, ilk_kurulum)
    pazaryeri_moto_tara(hafiza, ilk_kurulum)

    with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(hafiza, f, ensure_ascii=False, indent=2)

    if ilk_kurulum:
        gonder(f"🏍️ <b>MotoRadar Pro 7/24 Bulut Botu Aktif!</b>\n\n✅ Motomax (Kask, Mont, Eldiven, İndirimler)\n✅ Mototaş (Ekipman & İndirimler)\n✅ Amazon Türkiye (Motosiklet Kategorisi)\n✅ Hepsiburada (Motosiklet Kategorisi)\n\n📊 İlk taramada <b>{len(hafiza)} adet</b> ürün hafızaya alındı. Fiyatı en az %8-%10 düşen ilk üründe anında buraya bildirim gelecek!")

if __name__ == "__main__":
    main()
