# Domates Partisi (DOP)

Flask + SQLite resmi parti platformu.

## Kurulum

```powershell
pip install -r requirements.txt
python app.py
```

http://127.0.0.1:5000

## Üyelik ve giriş

- **Üye ol:** `/uye-ol` — Ad, soyad, kullanıcı adı, şifre ile kayıt. Kayıt sonrası otomatik giriş.
- **Giriş:** `/giris` — Kayıtlı kullanıcı adı ve şifre (demo bilgisi sayfada gösterilmez).

Kayıtlı üyeler **Üye Listesi**'nde görünür (soyad KVKK maskeli). Genel Başkan üyeleri **Kadrolar** şemasına atayabilir.

## Genel Başkan hesabı

| Alan | Değer |
|------|--------|
| Kullanıcı adı | `genelbaskan` |
| Varsayılan şifre | `DomatesGB2026` (ortam değişkeni `DOP_CHAIRMAN_PASSWORD` ile değiştirilebilir) |

Giriş sonrası **Genel Başkan Paneli** (`/yonetim`): haber, manşet, gündem, vaat, medya, kadro, fotoğraf yükleme. Yalnızca bu hesap düzenleme yapar.

## Roller

- **Genel Başkan** (`admin`) — tam CMS
- **Yetkili** — salt okunur + sınırlı modüller
- **Üye** — kurultay oylaması, şikayet (üye modu)

## Fotoğraf yükleme

Panelde her görsel alanının yanında dosya seçici vardır. Dosyalar `static/uploads/` altına kaydedilir.
