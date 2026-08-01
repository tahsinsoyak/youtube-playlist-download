# Ses kalitesi

## “En yüksek kalite MP3” ne anlama gelir?

YouTube çoğu zaman sesi MP3 olarak sunmaz; AAC veya Opus gibi kayıplı bir
akış sunar. Bu proje:

1. `bestaudio/best` ile mevcut en iyi ses akışını seçer.
2. FFmpeg ve LAME ile MP3'e dönüştürür.
3. Varsayılan olarak `--audio-quality 0` kullanır.

`0`, FFmpeg'in MP3 VBR ölçeğinde en iyi kalite ayarıdır. Ancak kayıplı bir
kaynağı yüksek bitrate ile yeniden kodlamak kaynağın kaybettiği ayrıntıları
geri getirmez. Sonuç uyumluluk açısından MP3'tür; arşivsel “kayıpsız” ses
değildir.

## Kalite ve dosya boyutu

| Değer | Yaklaşık yaklaşım | Kullanım |
|---:|---|---|
| `0` | En iyi VBR | Varsayılan; kalite öncelikli |
| `2` | Yüksek VBR | Daha küçük dosya |
| `5` | Orta VBR | Alan öncelikli |
| `10` | En düşük VBR | Önerilmez |

Örnek:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --audio-quality 2 `
  --confirm-rights
```

## Metadata ve kapak

Varsayılan olarak video başlığı, yükleyen gibi mevcut metadata ve küçük resim
MP3 dosyasına gömülür. Bazı YouTube başlıkları gerçek `Sanatçı - Parça`
şemasını takip etmediği için sanatçı alanı her içerikte kusursuz olmayabilir.

Kapak veya metadata istemiyorsanız:

```powershell
uv run youtube-playlist-download download "PLAYLIST_URL" `
  --no-thumbnail `
  --no-metadata `
  --confirm-rights
```

Kaynak: [yt-dlp post-processing options](https://github.com/yt-dlp/yt-dlp#post-processing-options)
