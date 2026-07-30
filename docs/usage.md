# Kullanım rehberi

## Komutlar

### Yerel web arayüzü

```powershell
uv run playlist-audio ui
```

Günlük kullanım için önerilen yöntemdir. Tarayıcı otomatik açılır; CLI
seçeneklerinin önemli bölümü form üzerinden kullanılabilir. Ayrıntılar:
[Yerel web arayüzü](web-ui.md).

### Sistem kontrolü

```powershell
uv run playlist-audio doctor
```

Python, `yt-dlp`, FFmpeg ve `ffprobe` sürümlerini kontrol eder. Bu komut
YouTube'a bağlanmaz.

### İndirme

```powershell
uv run playlist-audio download "PLAYLIST_URL" --confirm-rights
```

Temel seçenekler:

| Seçenek | Varsayılan | Açıklama |
|---|---:|---|
| `--output`, `-o` | `downloads` | Müzik kitaplığının kök klasörü |
| `--browser` | yok | Private içerik için tarayıcı oturumu |
| `--browser-profile` | yok | Belirli tarayıcı profili |
| `--audio-quality` | `0` | FFmpeg VBR kalitesi; `0` en iyi |
| `--playlist-items` | tümü | İndirilecek sıra/aralık |
| `--archive` | çıktı altında | Başarılı indirmelerin kimlik listesi |
| `--dry-run` | kapalı | Dosya yazmadan erişim/seçim kontrolü |
| `--no-thumbnail` | kapalı | Kapak gömmeyi devre dışı bırakır |
| `--no-metadata` | kapalı | Metadata gömmeyi devre dışı bırakır |
| `--confirm-rights` | zorunlu | İndirme izni onayı |

Tüm seçenekleri görmek için:

```powershell
uv run playlist-audio download --help
```

## Playlistin bir bölümünü indirme

İlk 10 öğe:

```powershell
uv run playlist-audio download "PLAYLIST_URL" `
  --playlist-items "1:10" `
  --confirm-rights
```

Belirli öğeler:

```powershell
uv run playlist-audio download "PLAYLIST_URL" `
  --playlist-items "1,3,7" `
  --confirm-rights
```

## Farklı hedef klasör

```powershell
uv run playlist-audio download "PLAYLIST_URL" `
  --output "D:\Music\YouTube Archive" `
  --confirm-rights
```

## Tekrar indirmeyi önleme

Her başarılı indirme, varsayılan olarak çıktı klasöründeki
`.playlist-audio-archive.txt` dosyasına kaydedilir. Aynı URL daha sonra tekrar
çalıştırıldığında kayıtlı videolar atlanır. Bu dosya yalnızca medya kimlikleri
içerir; oturum çerezi içermez.

Farklı arşiv dosyaları kullanarak aynı videoyu farklı koleksiyonlarda
saklayabilirsiniz:

```powershell
uv run playlist-audio download "PLAYLIST_URL" `
  --archive ".state\my-playlist.txt" `
  --confirm-rights
```
