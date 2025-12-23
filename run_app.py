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
    
    # 1. Parse Criteria
    criteria = {
        'budget': None,
        'brands': [],
        'city': [],
        'fuel': [],
        'year_min': None,
        'transmission': []
    }
    
    # Extract unique values from DB for matching
    all_brands = set(c.get('brand', '').lower() for c in cars)
    all_cities = set(c.get('city', '').lower() for c in cars)
    
    # Budget (look for large numbers)
    # Matches: 500000, 1.500.000, 1500000
    numbers = re.findall(r'\d+(?:[.]\d+)*', user_msg)
    for num_str in numbers:
        val = int(num_str.replace('.', ''))
        if val > 10000: # Assumption: budget is likely > 10k
            # If multiple, take the largest as budget usually
            if criteria['budget'] is None or val > criteria['budget']:
                criteria['budget'] = val
                
    # Brands
    for b in all_brands:
        if b in user_msg:
            criteria['brands'].append(b)
            
    # Cities
    for c in all_cities:
        if c in user_msg:
            criteria['city'].append(c)
            
    # Fuel
    fuel_types = ['benzin', 'dizel', 'hibrit', 'elektrik', 'lpg']
    for f in fuel_types:
        if f in user_msg:
            criteria['fuel'].append(f)
            
    # Transmission
    trans_types = ['otomatik', 'manuel', 'yarı otomatik']
    for t in trans_types:
        if t in user_msg:
            criteria['transmission'].append(t)
            
    # Year (e.g., "2020 model", "2020 üzeri", "2020+")
    year_match = re.search(r'(20\d{2})', user_msg)
    if year_match:
        y = int(year_match.group(1))
        # If budget was confused with year, fix it (unlikely given >10k check above for budget, but possible if small budget)
        criteria['year_min'] = y

    # 2. Score Cars
    scored_cars = []
    for car in cars:
        score = 0
        c_price = clean_price(car.get('price'))
        c_brand = car.get('brand', '').lower()
        c_city = car.get('city', '').lower()
        c_fuel = car.get('fuel', '').lower()
        c_trans = car.get('transmission', '').lower()
        c_year = int(car.get('year', 0))
        
        # Budget
        if criteria['budget']:
            if c_price <= criteria['budget']:
                score += 4
            else:
                score -= 2 # Penalize over budget
                
        # Brand
        if any(b in c_brand for b in criteria['brands']):
            score += 3
            
        # City
        if any(city in c_city for city in criteria['city']):
            score += 2
            
        # Fuel
        if any(f in c_fuel for f in criteria['fuel']):
            score += 2
            
        # Transmission
        if any(t in c_trans for t in criteria['transmission']):
            score += 2
            
        # Year
        if criteria['year_min']:
            if c_year >= criteria['year_min']:
                score += 2
        
        if score > 0:
            scored_cars.append({'score': score, 'data': car, 'price_val': c_price})

    # 3. Sort (Score DESC, Price ASC)
    scored_cars.sort(key=lambda x: (-x['score'], x['price_val']))
    top_results = [x['data'] for x in scored_cars[:6]]
    
    # 4. Generate Reply
    reply_lines = []
    
    # Summary
    constraints = []
    if criteria['brands']: constraints.append(f"Marka: {', '.join(criteria['brands']).title()}")
    if criteria['budget']: constraints.append(f"Bütçe: {criteria['budget']:,} TL")
    if criteria['city']: constraints.append(f"Şehir: {', '.join(criteria['city']).title()}")
    
    if not constraints and not criteria['fuel'] and not criteria['year_min']:
         reply_lines.append("Herhangi bir kriter belirtmediniz, işte vitrindeki araçlarımız:")
    else:
        summary = ", ".join(constraints)
        reply_lines.append(f"Aradığınız kriterlere ({summary}) en uygun araçları listeledim:")

    if not top_results:
        return jsonify({
            'reply': "Belirttiğiniz kriterlere uygun araç bulamadım. Lütfen bütçeyi artırmayı veya kriterleri değiştirmeyi deneyin.",
            'results': []
        })

    reply_lines.append("") # Spacer
    for car in top_results:
        p = car.get('price')
        c = car.get('city')
        y = car.get('year')
        reply_lines.append(f"• {car.get('title')} — {p} — {c} — {y}")

    return jsonify({
        'reply': "\n".join(reply_lines),
        'results': top_results
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    if not query:
        return jsonify({'response': 'Lütfen bir arama terimi girin.'})
        
    response = agent.search_cars(query)
    return jsonify({'response': response})

@app.route('/api/analyze/<car_id>')
def analyze(car_id):
    response = agent.analyze_car(car_id)
    return jsonify({'analysis': response})

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
