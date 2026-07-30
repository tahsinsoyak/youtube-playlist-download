# Mimari ve geliştirme

## Bileşenler

```text
CLI girdisi
  -> validation.py     URL ve seçenek doğrulama
  -> models.py         Değişmez istek modeli
  -> options.py        yt-dlp seçenek üretimi
  -> downloader.py     yt-dlp çalışma adaptörü
  -> runtime.py        Deno/Node seçimi
  -> FFmpeg            MP3 dönüştürme ve metadata

doctor
  -> preflight.py      Yerel bağımlılık kontrolleri
```

Private erişim için seçilen tarayıcı ve profil bilgisi `yt-dlp` API'sine
iletilir. Uygulama cookie içeriğini doğrudan okumaz, yazmaz veya loglamaz.

## Dosya sorumlulukları

- `src/playlist_audio/cli.py`: kullanıcı arayüzü ve exit kodları
- `src/playlist_audio/validation.py`: saf girdi doğrulama fonksiyonları
- `src/playlist_audio/options.py`: saf yt-dlp seçenek üretimi
- `src/playlist_audio/downloader.py`: dosya sistemi ve yt-dlp yan etkileri
- `src/playlist_audio/preflight.py`: yerel araç tanılama
- `src/playlist_audio/runtime.py`: desteklenen JavaScript runtime seçimi
- `tests/`: ağ erişimi olmadan birim testleri

## Geliştirme kurulumu

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Tasarım kararları

- Web uygulaması yerine CLI: oturum verisini uzak sunucuya taşımamak için.
- `youtube-dl` yerine `yt-dlp`: aktif bakım, modern YouTube desteği ve tarayıcı
  cookie entegrasyonu için.
- Cookie dosyası yok: yanlışlıkla Git'e ekleme ve paylaşma riskini azaltmak için.
- Arşiv dosyası: büyük playlistlerde güvenli, tekrar çalıştırılabilir indirmeler.
- Zorunlu hak onayı: public dağıtıma uygun sorumlu kullanım sınırı.

## Gelecek geliştirmeler

- Yerel-only web arayüzü
- M4A/Opus gibi yeniden kodlama gerektirmeyen çıktı seçenekleri
- Playlist manifesti ve değişiklik raporu
- MP3 etiketlerini etkileşimli düzeltme
- İmzalı release paketleri
