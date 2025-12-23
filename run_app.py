"""
AracımSağlam - Web Application Runner
"""
import os
import sys
import webbrowser
import socket
from threading import Timer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine base path
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Add paths for modules
sys.path.insert(0, os.path.join(base_path, 'website'))
sys.path.insert(0, os.path.join(base_path, 'agent'))

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from car_agent import CarAgent
import json
from openai import OpenAI

import re

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(base_path, 'website', 'templates'),
            static_folder=os.path.join(base_path, 'website', 'static'))

# Enable CORS
cors_origin = os.environ.get('FRONTEND_ORIGIN', '*')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize Agent
agent = CarAgent()

# Initialize OpenAI Client
api_key = os.environ.get("OPENAI_API_KEY")
client = None
if api_key:
    client = OpenAI(api_key=api_key)

def load_cars():
    try:
        cars_path = os.path.join(base_path, 'data', 'cars.json')
        with open(cars_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Helper Functions
def clean_price(price_str):
    if not price_str: return 0
    # Remove TL, space, dots
    clean = str(price_str).replace('TL', '').replace('.', '').replace(',', '').strip()
    try:
        return int(clean)
    except:
        return 0

def clean_km(km_str):
    if not km_str: return 0
    clean = str(km_str).replace('.', '').replace(',', '').strip()
    try:
        return int(clean)
    except:
        return 0

@app.route('/')
def index():
    cars = load_cars()
    return render_template('index.html', cars=cars[:20])

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/api/assistant', methods=['POST'])
def assistant():
    data = request.get_json(silent=True) or {}
    user_msg = data.get('message', '').lower()
    cars = load_cars()
    
    # --- 1. Robust Intent Parsing ---
    criteria = {
        'budget_max': None,
        'budget_min': None,
        'brands': [],
        'cities': [],
        'fuels': [],
        'year_min': None,
        'year_max': None,
        'transmissions': [],
        'sort': 'default' # default, price_asc, km_asc, best
    }
    
    # A. Brands (Exact match from dataset)
    all_brands = set(c.get('brand', '').lower() for c in cars)
    for b in all_brands:
        # Check strict word match to avoid partials inside other words
        if re.search(r'\b' + re.escape(b) + r'\b', user_msg):
            criteria['brands'].append(b)

    # B. Cities (Suffix handling: istanbulda -> istanbul)
    all_cities = set(c.get('city', '').lower() for c in cars)
    for city in all_cities:
        # Regex to match city followed by common Turkish suffixes or boundary
        # Suffixes: da, de, da, 'da, 'de, da'ki... simplify: check if city is prefix of a word
        # "istanbulda" -> startswith "istanbul"
        # We scan words in user_msg
        for word in user_msg.split():
            # Remove punctuation for check
            clean_word = re.sub(r'[^\w\s]', '', word) 
            if clean_word.startswith(city):
                 # Verification: is the rest a suffix?
                 suffix = clean_word[len(city):]
                 if suffix in ['', 'da', 'de', 'ta', 'te', 'dan', 'den', 'tan', 'ten', 'daki', 'deki']:
                     criteria['cities'].append(city)
                     break
    
    # C. Fuel
    fuel_map = {
        'benzin': ['benzin'],
        'dizel': ['dizel'],
        'motorin': ['dizel'], # alias
        'hibrit': ['hybrid', 'hibrit'],
        'elektrik': ['elektrik'],
        'lpg': ['lpg']
    }
    for key, values in fuel_map.items():
        if key in user_msg:
            criteria['fuels'].extend(values)

    # D. Transmission
    if 'otomatik' in user_msg:
        criteria['transmissions'].extend(['otomatik', 'yarı otomatik', 'dct', 'cvt', 'pdk', 'dsg', 'triptonik'])
    if 'manuel' in user_msg:
        criteria['transmissions'].append('manuel')

    # E. Year
    # "2018 ve üstü", "2018 üzeri"
    year_min_match = re.search(r'(\d{4})\s*(ve\s*)?(üstü|üzeri|sonrası)', user_msg)
    if year_min_match:
        criteria['year_min'] = int(year_min_match.group(1))
    
    # Range: "2015-2020", "2015 ile 2020"
    year_range_match = re.search(r'(\d{4})\s*[-ile]\s*(\d{4})', user_msg)
    if year_range_match:
        y1, y2 = int(year_range_match.group(1)), int(year_range_match.group(2))
        criteria['year_min'] = min(y1, y2)
        criteria['year_max'] = max(y1, y2)
        
    # F. Budget
    # Normalizers
    def parse_money_token(token):
        token = token.replace(',', '.')
        mult = 1
        if 'm' in token or 'milyon' in token: mult = 1000000
        elif 'k' in token or 'bin' in token: mult = 1000
        # clean nums
        nums = re.findall(r'\d+(?:[.]\d+)?', token)
        if not nums: return None
        val = float(nums[0])
        # specialized logic: if val < 1000 and mult==1 => probably implied 'bin' if user says "500-600 arası" ? 
        # But risky. Let's stick to explicit.
        # However, "500k" -> 500 * 1000
        return int(val * mult)

    # Max budget: "2m altı", "500.000 tl altı"
    max_budget_match = re.search(r'(\d+(?:[.,]\d+)?\s*(?:m|k|bin|milyon|tl)?)\s*(?:altı|altında)', user_msg)
    if max_budget_match:
        val = parse_money_token(max_budget_match.group(1))
        if val and val > 1000: criteria['budget_max'] = val

    # Range budget: "500 - 1000 arası", "500k - 1m"
    # This is hard with regex alone, simple heuristic: find two money amounts
    money_tokens = re.findall(r'\d+(?:[.,]\d+)?\s*(?:m|k|bin|milyon|tl)?', user_msg)
    if len(money_tokens) >= 2 and ('arası' in user_msg or '-' in user_msg):
        v1 = parse_money_token(money_tokens[0])
        v2 = parse_money_token(money_tokens[1])
        if v1 and v2 and v1 > 1000 and v2 > 1000:
            criteria['budget_min'] = min(v1, v2)
            criteria['budget_max'] = max(v1, v2)

    # Sorting intent
    if 'en ucuz' in user_msg or 'fiyatı düşük' in user_msg: criteria['sort'] = 'price_asc'
    elif 'en az km' in user_msg or 'kilometresi düşük' in user_msg: criteria['sort'] = 'km_asc'
    elif 'en iyi' in user_msg or 'öner' in user_msg: criteria['sort'] = 'best'

    # --- 2. Filtering Logic ---
    filtered_cars = []
    
    # If explicit city requested but none found, we might want to inform user.
    # Currently we'll filter strictly if city matches.
    
    for car in cars:
        c_brand = car.get('brand', '').lower()
        c_city = car.get('city', '').lower()
        c_fuel = car.get('fuel', '').lower()
        c_trans = car.get('transmission', '').lower()
        c_year = int(car.get('year', 0))
        c_price = clean_price(car.get('price'))

        # Strict Checks
        if criteria['brands'] and not any(b == c_brand for b in criteria['brands']): continue
        if criteria['cities'] and not any(c == c_city for c in criteria['cities']): continue
        if criteria['fuels'] and not any(f in c_fuel for f in criteria['fuels']): continue
        if criteria['transmissions'] and not any(t in c_trans for t in criteria['transmissions']): continue
        
        if criteria['year_min'] and c_year < criteria['year_min']: continue
        if criteria['year_max'] and c_year > criteria['year_max']: continue
        
        if criteria['budget_max'] and c_price > criteria['budget_max']: continue
        if criteria['budget_min'] and c_price < criteria['budget_min']: continue

        filtered_cars.append(car)

    # Fallback removed strictly as per requirements: 
    # if city is specified, DO NOT return cars from other cities
    hit_city_fallback = False

    # --- 3. Sorting/Ranking ---
    def get_sort_key(car):
        p = clean_price(car.get('price'))
        k = clean_km(car.get('km'))
        y = int(car.get('year', 0))
        
        if criteria['sort'] == 'price_asc': return (p, k)
        if criteria['sort'] == 'km_asc': return (k, p)
        if criteria['sort'] == 'best': 
            # Weighted score: low price, low km, high year
            # Max price approx 10m, Max km 200k. Normalize roughly.
            # Score = (Year * 5000) - (Price / 1000) - (KM / 10)
            # This is heuristic.
            return -((y * 5000) - (p / 200) - (k / 10))
            
        # Default: just budget compliance (already filtered) then price
        return (p, k)

    filtered_cars.sort(key=get_sort_key)
    
    # Top results
    matches = filtered_cars[:6]
    
    # --- 4. Reply Generation ---
    reply_text = ""
    
    # Check if we have an OpenAI client and use it
    if client:
        try:
            # Prepare context for OpenAI
            if not matches:
                system_prompt = "Sen Türkçe konuşan yardımsever bir otomobil asistanısın. Kullanıcıya kriterlerine uygun araç bulunamadığını nazikçe söyle ve kriterlerini (şehir, bütçe vb) değiştirmesini öner."
                user_content = f"Kullanıcı mesajı: '{user_msg}'. Hiç araç bulunamadı."
            else:
                system_prompt = "Sen Türkçe konuşan yardımsever bir otomobil asistanısın. SANA VERİLEN ARAÇ LİSTESİ DIŞINDA ARAÇ UYDURMA. Sadece listedeki araçları kullanarak kısa, samimi ve satış odaklı bir özet cevap yaz. Neden bu araçların uygun olduğunu maddeleyerek anlat."
                # Compact car list
                car_context = []
                for m in matches:
                    car_context.append(f"- {m['title']} ({m['year']}), {m['price']}, {m['km']} km, {m['city']}, {m['fuel']}, {m['transmission']}")
                
                car_list_str = "\n".join(car_context)
                user_content = f"Kullanıcı mesajı: '{user_msg}'.\n\nBulunan Araçlar:\n{car_list_str}\n\nLütfen bu araçları kullanıcıya sunan yardımsever bir cevap yaz."

            completion = client.chat.completions.create(
                model="gpt-4o", # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            reply_text = completion.choices[0].message.content
            return jsonify({'reply': reply_text, 'matches': matches})

        except Exception as e:
            print(f"OpenAI Error: {e}")
            # Fallback will happen below
            pass

    # LOCAL FALLBACK
    reply_parts = []
    
    if not matches:
        reply_parts.append("😔 Maalesef belirttiğiniz kriterlere uygun araç bulamadım.")
        reply_parts.append("Kriterlerinizi (bütçe, yıl vb.) biraz esnetmeyi deneyebilirsiniz.")
        return jsonify({'reply': "\n".join(reply_parts), 'matches': []})
    
    count = len(filtered_cars)
    shown = len(matches)
    
    summary_adjs = []
    if criteria['brands']: summary_adjs.append(f"{','.join(criteria['brands']).upper()}")
    if criteria['year_min']: summary_adjs.append(f"{criteria['year_min']}+ model")
    if criteria['budget_max']: summary_adjs.append(f"{criteria['budget_max']/1000:.0f}k TL altı")
    
    desc = " ".join(summary_adjs)
    if not desc: desc = "uygun"
    
    reply_parts.append(f"🔍 Aradığınız kriterlere {desc} toplam {count} araç buldum.")
    reply_parts.append(f"İşte en iyi {shown} tanesi:")
    
    bullet_list = []
    for m in matches:
        bullet_list.append(f"• {m.get('title')} ({m.get('price')})")
        
    reply_parts.append("\n".join(bullet_list))
    
    return jsonify({
        'reply': "\n\n".join(reply_parts),
        'matches': matches
    })

@app.route('/api/analyze/<car_id>')
def analyze(car_id):
    cars = load_cars()
    car = next((c for c in cars if c['id'] == car_id), None)
    if not car:
        return jsonify({'analysis': "Araç bulunamadı."})
        
    # OpenAI Analysis
    if client:
        try:
            prompt = f"""
            Şu araba hakkında potansiyel alıcıya detaylı bir analiz raporu yaz:
            Araç: {car.get('title')}
            Fiyat: {car.get('price')}
            Yıl: {car.get('year')}
            Km: {car.get('km')}
            Şehir: {car.get('city')}
            Yakıt: {car.get('fuel')}
            Vites: {car.get('transmission')}

            Lütfen şu formatta yanıt ver (Markdown):
            ## 📊 {car.get('title')} Analiz Raporu
            **Artılar** (5 madde)
            **Eksiler** (5 madde)
            **Bu araç kime uygun?**
            **Fiyat/Kilometre Değerlendirmesi** (Sadece verilen veriye göre mantıklı bir yorum yap, uydurma)
            
            Türkçe, samimi ve profesyonel ol.
            """
            
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return jsonify({'analysis': completion.choices[0].message.content})
        except Exception as e:
            print(f"OpenAI Error in analyze: {e}")
            pass

    # Heuristics for analysis (FALLBACK)
    price = clean_price(car.get('price'))
    km = clean_km(car.get('km'))
    year = int(car.get('year', 0))
    fuel = car.get('fuel')
    
    # Averages (approx from typical DB)
    avg_price = sum(clean_price(c.get('price')) for c in cars) / len(cars) if cars else 0
    avg_km = sum(clean_km(c.get('km')) for c in cars) / len(cars) if cars else 0
    
    pros = []
    cons = []
    
    if year >= 2022: pros.append("Model yılı çok yeni, güncel kasa.")
    if km < 30000: pros.append("Düşük kilometre, motor kondisyonu muhtemelen çok iyi.")
    if 'Hybrid' in fuel or 'Elektrik' in fuel: pros.append("Yakıt tüketimi ekonomik ve çevreci.")
    if 'Otomatik' in car.get('transmission') or 'DCT' in car.get('transmission'): pros.append("Konforlu otomatik vites.")
    
    if price > avg_price * 1.5: cons.append("Fiyatı piyasa ortalamasının üzerinde.")
    if year < 2018: cons.append("Model yılı biraz eski, donanımları kontrol edin.")
    if km > 150000: cons.append("Kilometresi yüksek, ağır bakım geçmişini sorgulayın.")
    
    market_comment = "Fiyat/performans dengeli görünüyor."
    if price < avg_price * 0.8: market_comment = "Bu araç piyasaya göre FIRSAT niteliğinde olabilir, fiyatı uygun."
    elif price > avg_price * 1.2: market_comment = "Premium segment veya yüksek donanımlı bir araç olduğu için fiyatı ortalamadan yüksek."
    
    personas = []
    if 'Suv' in car.get('model') or 'Jeep' in car.get('brand') or 'Tucson' in car.get('title'): personas.append("Geniş aileler")
    if price < 1000000: personas.append("İlk aracını alacaklar")
    if 'Sport' in car.get('title'): personas.append("Performans severler")
    
    analysis_text = f"""
## 📊 {car.get('title')} Analiz Raporu

**Özet**
{car.get('year')} model, {car.get('city')} konumunda bulunan bu araç {car.get('km')} km'de. {car.get('fuel')} yakıt tipi ve {car.get('transmission')} vites seçeneği sunuyor.

**✅ Artılar**
{chr(10).join(['- '+p for p in pros] if pros else ['- Genel durumu iyi görünüyor.'])}

**⚠️ Dikkat Edilmesi Gerekenler**
{chr(10).join(['- '+c for c in cons] if cons else ['- Belirgin bir eksi özellik görülmedi.'])}

**💰 Piyasa Yorumu**
{market_comment}

**👥 Kimler İçin Uygun?**
{', '.join(personas) if personas else 'Her tür kullanıcı grubu için değerlendirilebilir.'}
"""
    return jsonify({'analysis': analysis_text.strip()})

@app.route('/api/cars')
def get_cars():
    cars = load_cars()
    return jsonify(cars)

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "service": "AracimSaglam Backend",
        "mode": "api-ready"
    })


def open_browser(url):
    """Attempt to open the browser safely."""
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == '__main__':
    # Configuration from environment or defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    url = f'http://localhost:{port}'
    
    print("=" * 60)
    print("🚗 AracımSağlam Web App")
    print("=" * 60)
    print(f"✓ Server running on: http://{host}:{port}")
    if host == '0.0.0.0':
        print(f"✓ Local Access:     {url}")
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"✓ Network Access:   http://{local_ip}:{port}")
        except:
            pass
    print("=" * 60)

    # Open browser only if not in debug mode (to avoid double tabs)
    if not debug:
        Timer(1.5, lambda: open_browser(url)).start()
    
    app.run(host=host, port=port, debug=debug)
