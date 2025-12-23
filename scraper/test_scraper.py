import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Chrome setup
chrome_options = Options()
# chrome_options.add_argument('--headless')  # Headless kapalı - görmek için
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("Sayfa açılıyor...")
    driver.get("https://www.sahibinden.com/otomobil")
    time.sleep(5)
    
    # Sayfayı kaydet
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ Sayfa kaydedildi: page_source.html")
    
    # Farklı selector'ları dene
    selectors = [
        "tr.searchResultsItem",
        "tbody tr",
        "table.searchResultsTable tr",
        "[class*='searchResults']",
        "a[href*='/ilan/']"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"✓ '{selector}': {len(elements)} element bulundu")
            if elements and len(elements) > 0:
                print(f"  İlk element: {elements[0].text[:100]}")
        except Exception as e:
            print(f"✗ '{selector}': {e}")
    
    input("\nTarayıcıyı kapatmak için Enter'a bas...")
    
finally:
    driver.quit()
