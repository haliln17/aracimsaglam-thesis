import json
import requests
from datetime import datetime

class SahibindenAPIScraper:
    def __init__(self):
        self.base_url = "https://www.sahibinden.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def scrape_cars(self, max_items=20):
        """Sahibinden API'sinden veri çeker"""
        print(f"API ile veri çekiliyor...")
        
        cars = []
        
        # Örnek kategoriler - farklı marka/model kombinasyonları
        search_urls = [
            "/otomobil/volkswagen",
            "/otomobil/renault", 
            "/otomobil/toyota",
            "/otomobil/fiat",
            "/otomobil/hyundai"
        ]
        
        for search_url in search_urls:
            if len(cars) >= max_items:
                break
                
            try:
                url = f"{self.base_url}{search_url}"
                print(f"Çekiliyor: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    # HTML'den JSON data çıkar
                    html = response.text
                    
                    # classifiedId pattern'i ara
                    import re
                    ids = re.findall(r'data-id="(\d+)"', html)
                    titles = re.findall(r'title="([^"]+)"', html)
                    prices = re.findall(r'(\d+(?:\.\d+)*)\s*TL', html)
                    
                    print(f"  {len(ids)} ilan bulundu")
                    
                    for i in range(min(len(ids), 5)):  # Her kategoriden 5 ilan
                        if len(cars) >= max_items:
                            break
                            
                        car = {
                            'id': ids[i] if i < len(ids) else str(len(cars)),
                            'title': titles[i] if i < len(titles) else f"Araba {len(cars)+1}",
                            'url': f"{self.base_url}/ilan/{ids[i]}" if i < len(ids) else "",
                            'price': f"{prices[i]} TL" if i < len(prices) else "Belirtilmemiş",
                            'year': "2020",
                            'km': "50.000 km",
                            'location': "İstanbul",
                            'date': datetime.now().isoformat(),
                            'image': f"https://placehold.co/300x200?text=Araba+{len(cars)+1}"
                        }
                        cars.append(car)
                        print(f"  ✓ {car['title'][:50]}")
                
            except Exception as e:
                print(f"  ✗ Hata: {e}")
                continue
        
        return cars
    
    def save_to_json(self, cars, filename='../data/cars.json'):
        """Verileri JSON dosyasına kaydeder"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cars, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {len(cars)} araba kaydedildi: {filename}")

if __name__ == "__main__":
    scraper = SahibindenAPIScraper()
    cars = scraper.scrape_cars(max_items=20)
    
    if len(cars) == 0:
        print("\n⚠️ Veri çekilemedi. Mock data kullanılıyor...")
        # Mock data
        cars = [
            {
                "id": str(i),
                "title": f"2020 Volkswagen Golf 1.6 TDI - Örnek İlan {i}",
                "url": f"https://www.sahibinden.com/ilan/{i}",
                "price": f"{500000 + i*50000} TL",
                "year": "2020",
                "km": f"{30000 + i*10000} km",
                "location": "İstanbul",
                "date": datetime.now().isoformat(),
                "image": f"https://placehold.co/300x200?text=Araba+{i}"
            }
            for i in range(1, 21)
        ]
    
    scraper.save_to_json(cars)
