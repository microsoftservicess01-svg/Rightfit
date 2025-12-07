from flask import Flask, render_template, request, jsonify
import os
app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/results', methods=['POST'])
def results():
    data = request.get_json() or {}
    band = float(data.get('band', 78))
    bust = float(data.get('bust', 90))
    activity = data.get('activity','Daily / Casual')
    root = data.get('root','Narrow')

    diff = max(0, round(bust - band))
    cup = "A"
    if 12 <= diff < 14: cup = "B"
    if 14 <= diff < 16: cup = "C"
    if 16 <= diff < 18: cup = "D"
    if diff >= 18: cup = "DD/E"
    band_rounded = int(round(band/5.0)*5)
    size = f"{band_rounded}{cup}"
    product_name = f"Comfort {size} {activity} bra" if root != 'Wide' else f"Full coverage {size} bra"

    images = [
        '/static/images/p1.svg',
        '/static/images/p2.svg',
        '/static/images/p3.svg'
    ]
    urls = {
        'amazon': f'https://www.amazon.in/s?k={product_name.replace(" ", "+")}',
        'flipkart': f'https://www.flipkart.com/search?q={product_name.replace(" ", "+")}',
        'myntra': f'https://www.myntra.com/search?q={product_name.replace(" ", "+")}'
    }
    return jsonify({
        'product_name': product_name,
        'size': size,
        'cup_diff': diff,
        'band': band,
        'bust': bust,
        'images': images,
        'store_urls': urls
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
