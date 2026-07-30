# Sorun giderme

## Önce tanı komutunu çalıştırın

```powershell
uv run playlist-audio doctor
```

## `ffmpeg not found`

Windows:

```powershell
winget install Gyan.FFmpeg
```

Terminali kapatıp yeniden açın ve `doctor` komutunu tekrar çalıştırın.

## JavaScript runtime bulunamadı

Güncel YouTube akışlarında `yt-dlp`, JavaScript doğrulamalarını çözmek için
Deno 2.3+ (önerilen) veya Node.js 22+ ister. Windows'ta:

```powershell
winget install DenoLand.Deno
```

Terminali yeniden açıp `doctor` komutunda `JavaScript` satırının hazır olduğunu
doğrulayın. Proje `yt-dlp[default]` bağımlılığı sayesinde eşleşen
`yt-dlp-ejs` paketini de kurar.

## Private playlist bulunamıyor

- Tarayıcıda doğru Google hesabının açık olduğunu doğrulayın.
- URL'nin tamamını çift tırnak içinde verin.
- `--browser firefox` ekleyin.
- Tarayıcıyı tamamen kapatıp yeniden deneyin.
- Önce `--dry-run` ile erişimi test edin.

## Tarayıcı cookie veritabanı kilitli

Tarayıcı pencerelerini ve arka plan süreçlerini kapatın. Windows'ta sorun
sürüyorsa Firefox ile oturum açıp `--browser firefox` kullanın.

## `Sign in to confirm you're not a bot`

`yt-dlp` ve bu proje güncel olmalıdır:

```powershell
uv lock --upgrade
uv sync
```

Ardından tarayıcıda YouTube'u normal şekilde açıp hesabın çalıştığını
doğrulayın. CAPTCHA veya platform korumalarını otomatik aşmaya çalışmayın.

## Bazı videolar atlanıyor

Bir playlistte silinmiş, bölgesel olarak engellenmiş veya hesabınıza kapalı
öğeler olabilir. CLI kullanılabilir öğelere devam eder, sonunda başarısız
öğeler olduğunu bildirir.

## Aynı parça yeniden inmiyor

İndirme arşivi daha önce başarıyla indirilen video kimliklerini tutar.
Koleksiyonu bilinçli olarak yeniden oluşturmak istiyorsanız farklı bir
`--archive` yolu seçin. Mevcut arşivi silmeden önce yedeklemeyi düşünün.

## Hata raporu paylaşma

Şunları paylaşmayın:

- cookie dosyaları veya tarayıcı profil dosyaları
- Google hesabı bilgileri
- private playlist URL'si/kimliği
- kişisel klasör yolları

Gerekirse private değerleri `[REDACTED]` ile değiştirin ve `doctor` çıktısını,
işletim sistemi sürümünü, tekrar üretme adımlarını ekleyin.
