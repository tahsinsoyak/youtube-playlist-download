# Private playlist erişimi

YouTube kullanıcı adı/parola ile doğrudan CLI girişini güvenilir biçimde
desteklemez. `yt-dlp` tarafından önerilen yöntem, zaten oturum açılmış
tarayıcının çerezlerini okumaktır.

## Önerilen akış

1. Firefox'ta playlisti görebilen YouTube hesabına giriş yapın.
2. Playlist URL'sini tarayıcıda açıp erişimi doğrulayın.
3. Firefox'u tamamen kapatın.
4. Önizleme çalıştırın:

```powershell
uv run playlist-audio download "PRIVATE_PLAYLIST_URL" `
  --browser firefox `
  --dry-run `
  --confirm-rights
```

5. Liste doğruysa `--dry-run` seçeneğini kaldırın.

## Chrome veya Edge kullanımı

```powershell
uv run playlist-audio download "PRIVATE_PLAYLIST_URL" `
  --browser chrome `
  --confirm-rights
```

Windows'ta Chromium tabanlı tarayıcılar çerez veritabanını kilitleyebilir veya
işletim sistemi destekli şifreleme nedeniyle çözülemeyebilir. Önce tarayıcıyı
ve arka plan süreçlerini tamamen kapatın. Sorun sürerse Firefox profili
kullanmak genellikle daha güvenilirdir.

Belirli bir profil:

```powershell
uv run playlist-audio download "PRIVATE_PLAYLIST_URL" `
  --browser firefox `
  --browser-profile "default-release" `
  --confirm-rights
```

Profil yolunu Firefox'ta `about:profiles`, Chrome'da `chrome://version`,
Edge'de `edge://version` sayfasından görebilirsiniz.

## Güvenlik modeli

- Uygulama Google parolanızı istemez.
- Uygulama cookie dosyası kabul etmez veya üretmez.
- `yt-dlp`, seçilen tarayıcı profilinden gereken oturumu çalışma anında okur.
- Çerezler yalnızca erişim isteği için `yt-dlp` tarafından YouTube'a gönderilir.
- İndirme klasörünü veya ayrıntılı hata kayıtlarını paylaşmadan önce içeriğini
  kontrol edin.

Tarayıcı oturumu hesap erişimi sağlayan hassas veridir. Herhangi bir
`cookies.txt` dosyasını repoya, issue'ya, mesaja veya bulut depolamaya
yüklemeyin.

Kaynak: [yt-dlp FAQ - cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
