# Katkıda bulunma

Katkılar küçük, tek amaçlı ve testli olmalıdır.

## Yerel kontrol

```powershell
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=playlist_audio
```

## Kapsam

- İndirme yetkisi modelini veya `--confirm-rights` kontrolünü kaldırmayın.
- Parola, cookie içeriği ya da oturum belirteci loglamayın.
- DRM veya erişim kontrolü aşma özelliği eklemeyin.
- Ağ kullanan testler varsayılan test paketine girmemelidir.
- Kaynak ve Markdown dosyalarını tek sorumlulukta, 500 satırın altında tutun.

Hata raporlarında private playlist URL'lerini, cookie dosyalarını ve kişisel
hesap bilgilerini mutlaka maskeleyin.
