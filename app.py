# app.py - Minimal restore version to ensure site loads
# This file returns safe placeholder images (data-URI SVG) so the frontend always has images.
# Once site is stable you can re-introduce the DuckDuckGo logic and caching.

import os
import logging
from urllib.parse import quote_plus
from flask import Flask, render_template, request, jsonify

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rightfit_restore")

app = Flask(__name__, static_folder='static', template_folder='templates')

def cup_group_from_diff(diff: int) -> str:
    if diff < 14:
        return "small"
    if 14 <= diff < 16:
        return "medium"
    return "large"

def activity_key_name(activity_label: str) -> str:
    mapping = {
        'Daily / Casual': 'casual',
        'Daily/Casual': 'casual',
        'Daily': 'casual',
        'Casual': 'casual',
        'Sports / Active': 'sports',
        'Sports/Active': 'sports',
        'Sports': 'sports',
        'High Impact': 'highimpact',
        'High-Impact': 'highimpact',
        'HighImpact': 'highimpact'
    }
    return mapping.get(activity_label, 'casual')

# Safe inline SVG placeholders (data URIs) — always available, no external files required
PLACEHOLDER_FRONT = ("data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'>"
    "<rect width='100%' height='100%' fill='%23fff7f7'/>"
    "<text x='50%' y='48%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='26' fill='%236b7280'>Front image not available</text>"
    "<text x='50%' y='58%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='18' fill='%23999'>RightFit placeholder</text>"
    "</svg>")

PLACEHOLDER_SIDE = ("data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'>"
    "<rect width='100%' height='100%' fill='%23fffaf0'/>"
    "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='26' fill='%236b7280'>Side image not available</text>"
    "</svg>")

PLACEHOLDER_CLOSE = ("data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'>"
    "<rect width='100%' height='100%' fill='%23f0fff6'/>"
    "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='26' fill='%236b7280'>Closeup image not available</text>"
    "</svg>")

@app.route('/')
def index():
    # Renders templates/index.html — ensure file exists under templates/
    return render_template('index.html')

@app.route('/api/results', methods=['POST'])
def results():
    try:
        payload = request.get_json(silent=True) or {}
        band = float(payload.get('band', 78))
        bust = float(payload.get('bust', 90))
    except Exception as e:
        log.warning("Invalid input; using defaults: %s", e)
        band, bust = 78.0, 90.0

    activity = payload.get('activity', 'Daily / Casual')
    root = payload.get('root', 'Narrow')

    diff = max(0, round(bust - band))
    cup = "A"
    if 12 <= diff < 14: cup = "B"
    elif 14 <= diff < 16: cup = "C"
    elif 16 <= diff < 18: cup = "D"
    elif diff >= 18: cup = "DD/E"

    band_rounded = int(round(band / 5.0) * 5)
    size = f"{band_rounded}{cup}"
    product_name = f"Comfort {size} {activity} bra" if root != 'Wide' else f"Full coverage {size} bra"

    # For stability while debugging, return placeholders (data URIs) instead of external images
    images = [PLACEHOLDER_FRONT, PLACEHOLDER_SIDE, PLACEHOLDER_CLOSE]

    query_term = quote_plus(product_name)
    query_term = quote_plus(product_name)

store_urls = {
    # Indian lingerie brands FIRST
    'zivame': f'https://www.zivame.com/catalogsearch/result/?q={query_term}',
    'clovia': f'https://www.clovia.com/search/?q={query_term}',
    'shyaway': f'https://www.shyaway.com/catalogsearch/result/?q={query_term}',
    'enamor': f'https://www.enamor.co.in/search?q={query_term}',
    'amante': f'https://www.amantelingerie.com/search?q={query_term}',

    # E-commerce platforms after brand stores
    'amazon': f'https://www.amazon.in/s?k={query_term}',
    'flipkart': f'https://www.flipkart.com/search?q={query_term}',
    'myntra': f'https://www.myntra.com/search?q={query_term}',
}


    response = {
        'product_name': product_name,
        'size': size,
        'cup_diff': diff,
        'band': band,
        'bust': bust,
        'images': images,
        'store_urls': store_urls
    }
    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
    
