import json
import os
import requests

class CarAgent:
    def __init__(self, use_ollama=True):
        self.use_ollama = use_ollama
        self.ollama_url = os.environ.get('OLLAMA_URL', "http://localhost:11434/api/generate")
        self.cars_data = self.load_cars()
        
    def load_cars(self):
        """Çekilen araba verilerini yükler"""
        try:
            # Use absolute path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cars_path = os.path.join(base_dir, 'data', 'cars.json')
            with open(cars_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def search_cars(self, query):
        """Kullanıcı sorgusuna göre araba önerir"""
        context = self._prepare_context()
        
        prompt = f"""Sen bir araba galerisi asistanısın. Elimizde şu arabalar var:

{context}

Müşteri sorusu: {query}

Müşteriye en uygun arabaları öner ve detaylı açıklama yap. Fiyat, kilometre, yıl gibi kriterleri göz önünde bulundur."""

        if self.use_ollama:
            return self._call_ollama(prompt)
        else:
            return self._simple_search(query)
    
    def _prepare_context(self):
        """Araba verilerini AI için hazırlar"""
        if not self.cars_data:
            return "Henüz araba verisi yok."
        
        context = []
        for i, car in enumerate(self.cars_data[:20], 1):  # İlk 20 araba
            context.append(
                f"{i}. {car['title']}\n"
                f"   Fiyat: {car['price']}\n"
                f"   Yıl: {car['year']}, KM: {car['km']}\n"
                f"   Konum: {car['location']}\n"
            )
        
        return "\n".join(context)
    
    def analyze_car(self, car_id):
        """Belirli bir arabayı detaylı analiz eder"""
        car = next((c for c in self.cars_data if c['id'] == car_id), None)
        
        if not car:
            return "Araba bulunamadı."
        
        prompt = f"""Bu araba hakkında detaylı analiz yap:

Başlık: {car['title']}
Fiyat: {car['price']}
Yıl: {car['year']}
Kilometre: {car['km']}
Konum: {car['location']}

Arabanın artıları, eksileri ve fiyat değerlendirmesi yap."""

        if self.use_ollama:
            return self._call_ollama(prompt)
        else:
            return f"""
📊 {car['title']} Analizi:

💰 Fiyat: {car['price']}
📅 Yıl: {car['year']}
🛣️ Kilometre: {car['km']}
📍 Konum: {car['location']}

Bu araç için basit analiz. Daha detaylı analiz için Ollama kurabilirsiniz.
"""
    
    def _call_ollama(self, prompt):
        """Ollama API'sine istek gönderir"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', 'Yanıt alınamadı')
            else:
                return self._simple_search(prompt)
        except:
            return "⚠️ Ollama bağlantısı kurulamadı. Basit arama kullanılıyor.\n\n" + self._simple_search(prompt)
    
    def _simple_search(self, query):
        """Basit kural tabanlı arama"""
        query_lower = query.lower()
        results = []
        
        # Fiyat filtresi
        if 'ucuz' in query_lower or 'düşük' in query_lower:
            results = sorted(self.cars_data, key=lambda x: self._extract_price(x['price']))[:5]
        elif 'pahalı' in query_lower or 'yüksek' in query_lower:
            results = sorted(self.cars_data, key=lambda x: self._extract_price(x['price']), reverse=True)[:5]
        else:
            results = self.cars_data[:5]
        
        response = "🚗 Size uygun arabalar:\n\n"
        for i, car in enumerate(results, 1):
            response += f"{i}. {car['title']}\n"
            response += f"   💰 {car['price']} | 📅 {car['year']} | 🛣️ {car['km']}\n"
            response += f"   📍 {car['location']}\n\n"
        
        return response
    
    def _extract_price(self, price_str):
        """Fiyat string'inden sayı çıkarır"""
        try:
            return int(''.join(filter(str.isdigit, price_str)))
        except:
            return 0

if __name__ == "__main__":
    agent = CarAgent()
    response = agent.search_cars("50000 TL altında düşük kilometreli araba")
    print(response)
