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

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(base_path, 'website', 'templates'),
            static_folder=os.path.join(base_path, 'website', 'static'))

# Enable CORS
cors_origin = os.environ.get('FRONTEND_ORIGIN', '*')
CORS(app, resources={r"/api/*": {"origins": cors_origin}})

# Initialize Agent
agent = CarAgent()

def load_cars():
    try:
        cars_path = os.path.join(base_path, 'data', 'cars.json')
        with open(cars_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    cars = load_cars()
    return render_template('index.html', cars=cars[:20])

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok"})

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
