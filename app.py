# app.py - RightFit final backend
import os
from flask import Flask, render_template, request, jsonify

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


def static_file_exists(path_from_static_root: str) -> bool:
    full = os.path.join(app.static_folder, path_from_static_root)
    return os.path.exists(full)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/results', methods=['POST'])
def results():
    payload = request.get_json(silent=True) or {}
    try:
        band = float(payload.get('band', 78))
        bust = float(payload.get('bust', 90))
    except (ValueError, TypeError):
        band = 78.0
        bust = 90.0

    activity = payload.get('activity', 'Daily / Casual')
    root = payload.get('root', 'Narrow')

    diff = max(0, round(bust - band))
    cup = "A"
    if 12 <= diff < 14:
        cup = "B"
    elif 14 <= diff < 16:
        cup = "C"
    elif 16 <= diff < 18:
        cup = "D"
    elif diff >= 18:
        cup = "DD/E"

    band_rounded = int(round(band / 5.0) * 5)
    size = f"{band_rounded}{cup}"
    product_name = f"Comfort {size} {activity} bra" if root != 'Wide' else f"Full coverage {size} bra"

    cup_group = cup_group_from_diff(diff)
    activity_key = activity_key_name(activity)

    ai_base = 'images/ai'
    views = ['front', 'side', 'closeup']
    desired = [os.path.join(ai_base, f"model_{activity_key}_{cup_group}_{v}.jpg") for v in views]

    fallback_placeholder = 'images/p1.svg'
    returned_images = []
    for rel in desired:
        if static_file_exists(rel):
            returned_images.append('/' + rel.replace(os.path.sep, '/'))
            continue
        alt_png = rel.replace('.jpg', '.png')
        if static_file_exists(alt_png):
            returned_images.append('/' + alt_png.replace(os.path.sep, '/'))
            continue
        alt_svg = rel.replace('.jpg', '.svg')
        if static_file_exists(alt_svg):
            returned_images.append('/' + alt_svg.replace(os.path.sep, '/'))
            continue
        returned_images.append('/' + fallback_placeholder)

    query_term = product_name.replace(" ", "+")
    store_urls = {
        'amazon': f'https://www.amazon.in/s?k={query_term}',
        'flipkart': f'https://www.flipkart.com/search?q={query_term}',
        'myntra': f'https://www.myntra.com/search?q={query_term}'
    }

    response = {
        'product_name': product_name,
        'size': size,
        'cup_diff': diff,
        'band': band,
        'bust': bust,
        'images': returned_images,
        'store_urls': store_urls
    }

    return jsonify(response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
