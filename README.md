# 🚗 AI Araba Galerisi

AI destekli, modern araba galerisi uygulaması. Python, Flask ve Selenium ile geliştirilmiştir.

![AracımSağlam](https://placehold.co/1200x600/0f172a/3b82f6?text=AracimSaglam+AI)

## 🌍 Global Erişim (İnternete Açma)

Projeyi internette yayınlamak (arkadaşınıza göstermek veya mobilden test etmek) için Cloudflare Tunnel kullanıyoruz. Modem ayarı veya port açma gerektirmez.

### 1. Cloudflare Tunnel (cloudflared) Kurulumu

**Windows:**
1. [İndirme Sayfası](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)na gidin.
2. Windows sürümünü indirin (`cloudflared-windows-amd64.exe`).
3. İndirilen dosyanın adını `cloudflared.exe` olarak değiştirin.
4. Bu dosyayı `C:\Windows\System32` klasörüne kopyalayın (veya projenin olduğu klasöre koyun).

**macOS:**
```bash
brew install cloudflare/cloudflare/cloudflared
```

### 2. Uygulamayı İnternete Açma

Kurulum tamamlandıktan sonra proje klasöründe şu dosyayı çalıştırın:
- **Windows:** `run_with_tunnel.bat`
- **Mac/Linux:** `bash run_with_tunnel.sh`

Bu script size şuna benzer geçici bir adres verecektir:
👉 `https://random-name.trycloudflare.com`

Bu adresi herhangi bir cihazdan (telefon, tablet, başka bilgisayar) açabilirsiniz.

---

## 🚀 Yerel Kurulum (Sadece Kendi Bilgisayarınız)

### Windows
```powershell
# 1. Sanal ortam oluşturun
python -m venv venv

# 2. Aktif edin
.\venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Ayar dosyasını oluşturun
copy .env.example .env

# 5. Başlatın
python run_app.py
```

### macOS / Linux
```bash
# 1. Sanal ortam oluşturun
python3 -m venv venv

# 2. Aktif edin
source venv/bin/activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Ayar dosyasını oluşturun
cp .env.example .env

# 5. Başlatın
python3 run_app.py
```

## ⚙️ Yapılandırma (`.env`)

Dosyayı (`.env`) düzenleyerek ayarları değiştirebilirsiniz:

- **PORT**: Uygulamanın çalışacağı port (Varsayılan: `5000`)
- **CHROME_HEADLESS**: Scraper arka planda mı çalışsın? (`true`/`false`)
- **OLLAMA_URL**: AI modeli için endpoint (Varsayılan: `http://localhost:11434`)
- **ANTHROPIC_API_KEY**: Claude kullanıyorsanız API anahtarı

## 🤖 Selenium & Scraper

Bu proje veri çekmek için Google Chrome kullanır.
- `webdriver-manager` sayesinde Chrome Driver otomatik indirilir.
- Bilgisayarınızda Google Chrome tarayıcısının yüklü olması yeterlidir.

Veri çekmek için:
```bash
python scraper/sahibinden_scraper.py
```

---
© 2024 AracımSağlam. Tüm hakları saklıdır.

---

## 🚀 Deployment (Netlify & Backend)

### Backend (Python Flask)
Backend API bir sunucuda çalışmalıdır (Render, Railway, VPS vb.).
1. `pip install -r requirements.txt`
2. `python run_app.py`
3. Çevresel değişken (Environment Variable) olarak `FRONTEND_ORIGIN` ayarlanmalıdır:
   - Örnek: `FRONTEND_ORIGIN=https://aracimsaglam.netlify.app`

### Frontend (Netlify)
1. `frontend` klasörünü Netlify'a sürükleyip bırakın.
2. `Publish directory` olarak `frontend` seçili olduğundan emin olun.
3. API Bağlantısı:
   - `frontend/config.js` dosyası varsayılan olarak `http://localhost:5000` kullanır.
   - Canlı ortam için bu dosyayı düzenleyerek veya Netlify build ayarlarında (eğer build kullanıyorsanız) API URL'ini güncelleyin.
   - Örnek `frontend/config.js`:
     ```javascript
     window.API_BASE_URL = 'https://sizin-backend-adresiniz.com';
     ```

### Yerel Geliştirme (Local Dev)
1. Backend'i başlatın: `python run_app.py`
2. Frontend'i açın:
   - `frontend/index.html` dosyasına çift tıklayabilirsiniz (ancak bazı tarayıcılar `file://` protokolünde fetch isteğine izin vermez).
   - Öneri: `cd frontend` ve `python -m http.server 8000` komutuyla frontend'i 8000 portunda başlatın.
   - Tarayıcıda `http://localhost:8000` adresine gidin.
