import json
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

class SahibindenScraper:
    def __init__(self):
        self.base_url = "https://www.sahibinden.com/otomobil"
        self.driver = None
        
    def setup_driver(self):
        """Chrome driver'ı ayarla"""
        chrome_options = Options()
        
        # Check environment variable for headless mode (default to true)
        is_headless = os.environ.get('CHROME_HEADLESS', 'true').lower() == 'true'
        if is_headless:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        user_agent = os.environ.get('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print("\n❌ Chrome Driver başlatılamadı!")
            print(f"Hata: {e}")
            print("\nOlası Çözümler:")
            print("1. Google Chrome tarayıcısının yüklü olduğundan emin olun.")
            print("2. İnternet bağlantınızı kontrol edin (Driver indirmek için).")
            sys.exit(1)
        
    def scrape_cars(self, max_items=20):
        """Sahibinden.com'dan araba ilanlarını çeker"""
        print(f"Selenium ile veri çekiliyor: {self.base_url}")
        
        try:
            self.setup_driver()
            self.driver.get(self.base_url)
            
            # Sayfanın yüklenmesini bekle
            time.sleep(3)
            
            cars = []
            
            # İlanları bul
            try:
                # Farklı selector'ları dene
                listings = self.driver.find_elements(By.CSS_SELECTOR, "tr.searchResultsItem")
                
                if not listings:
                    listings = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                print(f"{len(listings)} ilan bulundu")
                
                for idx, listing in enumerate(listings[:max_items]):
                    try:
                        car = self._parse_listing(listing, idx)
                        if car:
                            cars.append(car)
                            print(f"✓ {idx+1}. {car['title'][:50]}...")
                    except Exception as e:
                        print(f"✗ İlan {idx+1} parse hatası: {e}")
                        continue
                        
            except Exception as e:
                print(f"İlan bulunamadı: {e}")
            
            return cars
            
        except Exception as e:
            print(f"Scraper hatası: {e}")
            return []
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _parse_listing(self, listing, idx):
        """Tek bir ilanı parse eder"""
        try:
            # Başlık
            title_elem = listing.find_element(By.CSS_SELECTOR, "a.classifiedTitle")
            title = title_elem.text.strip()
            url = title_elem.get_attribute('href')
            
            if not title or not url:
                return None
            
            # Fiyat
            try:
                price_elem = listing.find_element(By.CSS_SELECTOR, "td.searchResultsPriceValue")
                price = price_elem.text.strip()
            except:
                price = "Belirtilmemiş"
            
            # Özellikler (yıl, km)
            try:
                attrs = listing.find_elements(By.CSS_SELECTOR, "td.searchResultsAttributeValue")
                year = attrs[0].text.strip() if len(attrs) > 0 else ""
                km = attrs[1].text.strip() if len(attrs) > 1 else ""
            except:
                year = ""
                km = ""
            
            # Konum
            try:
                loc_elem = listing.find_element(By.CSS_SELECTOR, "td.searchResultsLocationValue")
                location = loc_elem.text.strip()
            except:
                location = ""
            
            # Resim
            try:
                img_elem = listing.find_element(By.CSS_SELECTOR, "img")
                image = img_elem.get_attribute('data-src') or img_elem.get_attribute('src')
            except:
                image = ""
            
            # ID
            car_id = listing.get_attribute('data-id') or str(idx)
            
            return {
                'id': car_id,
                'title': title,
                'url': url,
                'price': price,
                'year': year,
                'km': km,
                'location': location,
                'date': datetime.now().isoformat(),
                'image': image
            }
            
        except Exception as e:
            # print(f"Parse hatası: {e}") # Sessiz mod
            return None
    
    def save_to_json(self, cars, filename=None):
        """Verileri JSON dosyasına kaydeder"""
        if filename is None:
            # Absolute path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filename = os.path.join(base_dir, 'data', 'cars.json')

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cars, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {len(cars)} araba kaydedildi: {filename}")

if __name__ == "__main__":
    scraper = SahibindenScraper()
    cars = scraper.scrape_cars(max_items=20)
    scraper.save_to_json(cars)
