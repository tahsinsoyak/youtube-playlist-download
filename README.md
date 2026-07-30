# Playlist Audio Downloader

Kendinize ait veya indirme izniniz bulunan YouTube video ve playlistlerini
yüksek kaliteli MP3 dosyaları olarak yerel bilgisayarınızda arşivleyen,
[`yt-dlp`](https://github.com/yt-dlp/yt-dlp) tabanlı bir CLI.

> [!IMPORTANT]
> Bu proje, telif hakkı ihlali veya YouTube kısıtlamalarını aşmak için
> tasarlanmamıştır. Yalnızca size ait, hak sahibinden izin aldığınız ya da
> yürürlükteki hukukun indirmeye izin verdiği içeriklerde kullanın.

## Hafif yerel arayüz

Kurulumdan sonra tek komut:

```powershell
uv run playlist-audio ui
```

Tarayıcı otomatik olarak `http://127.0.0.1:8765` adresinde açılır. URL’yi
yapıştırın, private playlist için tarayıcıyı seçin ve önce güvenli önizlemeyi
çalıştırın. CLI kullanmak zorunda değilsiniz; mevcut CLI otomasyon ve gelişmiş
kullanım için korunur.

## Neden localhost?

Private playlist erişimi, oturum açılmış tarayıcının çerezlerini gerektirir.
Arayüz yalnızca `127.0.0.1` adresine bağlanır; Google oturumunuz kendi
cihazınızdan çıkmaz ve hiçbir uzak sunucuda saklanmaz. Proje çerezleri dışa
aktarmaz veya diske yazmaz.

## Özellikler

- Public, unlisted ve erişim yetkiniz olan private playlist desteği
- Framework gerektirmeyen hafif localhost web arayüzü
- En iyi mevcut ses akışını MP3'e dönüştürme
- En yüksek FFmpeg VBR kalitesi (`0`) varsayılanı
- Kapak görseli ve medya metadata'sı
- Playlist sırasını koruyan klasör ve dosya adları
- Başarılı indirmeleri arşivleyerek tekrarları önleme
- Önizleme (`--dry-run`) ve bağımlılık kontrolü (`doctor`)
- Parola veya cookie dosyası kabul etmeyen güvenli oturum modeli

## Hızlı başlangıç

Gereksinimler:

- Python 3.11+
- [FFmpeg](https://ffmpeg.org/download.html)
- [Deno 2.3+](https://docs.deno.com/runtime/getting_started/installation/)
  (önerilen) veya Node.js 22+
- Windows için önerilen geliştirme aracı: [uv](https://docs.astral.sh/uv/)

```powershell
winget install Gyan.FFmpeg
winget install DenoLand.Deno
git clone https://github.com/tahsinsoyak/youtube-private-list-downloader.git
cd youtube-private-list-downloader
uv sync
uv run playlist-audio doctor
uv run playlist-audio ui
```

Arayüz tarayıcıyı otomatik açmazsa `http://127.0.0.1:8765` adresine gidin.

CLI ile public playlist önizlemesi:

```powershell
uv run playlist-audio download "PLAYLIST_URL" --dry-run --confirm-rights
```

Public playlist indirme:

```powershell
uv run playlist-audio download "PLAYLIST_URL" --confirm-rights
```

Private playlist indirme (önce tarayıcıda doğru YouTube hesabına giriş yapın):

```powershell
uv run playlist-audio download "PLAYLIST_URL" `
  --browser firefox `
  --confirm-rights
```

Çıktılar varsayılan olarak `downloads/<playlist adı>/` altına yazılır.

## Dokümantasyon

- [Kullanım ve tüm seçenekler](docs/usage.md)
- [Yerel web arayüzü](docs/web-ui.md)
- [Private playlist erişimi](docs/private-playlists.md)
- [Kalite ve dosya formatı](docs/audio-quality.md)
- [Sorun giderme](docs/troubleshooting.md)
- [Hukuki ve etik sınırlar](docs/legal-and-ethics.md)
- [Mimari ve katkı rehberi](docs/architecture.md)

## Proje durumu

Bu sürüm yerel kullanım odaklı ilk CLI sürümüdür. Web arayüzü düşünülürse
kimlik doğrulama çerezlerini sunucuya göndermeyen, yerel yardımcı süreç kullanan
bir mimari tercih edilmelidir.

## Lisans

Projenin kendi kaynak kodu [MIT Lisansı](LICENSE) ile sunulur. `yt-dlp`,
FFmpeg ve diğer bağımlılıklar kendi lisanslarına tabidir.
