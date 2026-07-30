# Yerel web arayüzü

## Başlatma

```powershell
uv run playlist-audio ui
```

Varsayılan tarayıcı `http://127.0.0.1:8765` adresinde açılır. Açılmazsa adresi
elle ziyaret edin.

Farklı port:

```powershell
uv run playlist-audio ui --port 9000
```

Tarayıcıyı otomatik açmadan:

```powershell
uv run playlist-audio ui --no-open
```

Sunucuyu kapatmak için çalıştığı terminalde `Ctrl+C` kullanın.

## Kullanım akışı

1. YouTube playlist veya video URL’sini yapıştırın.
2. Public playlist için oturum kaynağını değiştirmeyin.
3. Private playlist için oturum açık Firefox, Chrome veya diğer tarayıcıyı
   seçin.
4. Çıktı klasörünü belirleyin.
5. `Güvenli önizleme` açıkken hak onayını işaretleyip başlatın.
6. Önizleme tamamlanınca `Güvenli önizleme`yi kapatın.
7. Düğmeye basarak gerçek indirmeyi başlatın.

İnce ayarlar bölümünden MP3 kalitesi, playlist sırası, browser profili, kapak
ve metadata ayarları değiştirilebilir.

## Kuyruk ve canlı ilerleme

Bir indirme sürerken URL alanına başka bir playlist yapıştırıp düğmeye tekrar
basabilirsiniz. Yeni iş devam eden indirmeyi kesmez; kuyruğun sonuna eklenir.
İşler aynı çıktı klasörünü güvenle paylaşabilsin diye sırayla çalıştırılır.

Canlı panel şu bilgileri gösterir:

- Playlist genel ilerlemesi ve mevcut parça sırası
- Anlık indirme hızı (`KB/s` veya `MB/s`)
- Mevcut parçanın indirilen ve tahmini toplam boyutu
- yt-dlp tarafından hesaplanan tahmini kalan süre
- Bekleyen iş sayısı ve FIFO kuyruk sırası

Playlistte silinmiş veya bölgenizde kullanılamayan öğeler varsa erişilebilir
öğeler işlenmeye devam eder. Sonuç paneli kaç öğenin erişilebilir olduğunu ve
kaçının atlandığını uyarı olarak gösterir.

Kuyruk uygulama belleğindedir. Sunucuyu kapatmak bekleyen işleri siler; bitmiş
MP3 dosyaları ve indirme arşivi etkilenmez.

## Güvenlik sınırları

- Sunucu sabit olarak `127.0.0.1` arayüzüne bağlanır.
- LAN veya internete yayınlama seçeneği yoktur.
- POST istekleri aynı host/origin ve `application/json` koşullarıyla kabul
  edilir.
- Aynı anda yalnızca bir indirme çalışır; diğer işler yerel FIFO kuyruğunda bekler.
- UI kaynak URL’yi iş durumu yanıtlarında geri göndermez.
- Parola, cookie dosyası veya API anahtarı alınmaz.
- Uzak CDN, font veya JavaScript kullanılmaz.

Bu arayüzü reverse proxy ile internete açmayın. Uzak erişim gerekecekse cookie
modeli ve kimlik doğrulama mimarisi yeniden tasarlanmalıdır.

## Gerçek tarayıcı testi

Geliştirme bağımlılıkları ve Chromium kurulduktan sonra:

```powershell
uv sync --extra dev
uv run playwright install chromium
uv run python scripts/ui_smoke_test.py
```

Smoke test, UI sunucusunun `127.0.0.1:8765` üzerinde çalıştığını varsayar.
Desktop/mobile yerleşimi, kuyruk ve hız metrikleri, form davranışı, gerçek
`dry-run` ve browser konsolu kontrol edilir.
