from flask import Flask, render_template, request, jsonify
import json
import sys
sys.path.append('../agent')
from car_agent import CarAgent

app = Flask(__name__)
agent = CarAgent()

def load_cars():
    try:
        with open('../data/cars.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    cars = load_cars()
    return render_template('index.html', cars=cars[:20])

@app.route('/api/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
